"""
Durable DBOS workflows for the shipment visibility state machine.

shipment_workflow — top-level workflow that walks the full milestone chain.
customs_gate_workflow — child workflow for export/import customs gates,
                        implements the hold→respond→review loop with escalation.
"""
import logging

from dbos import DBOS

from .domain import (
    MAX_CUSTOMS_ATTEMPTS,
    CustomsStatus,
    EventType,
    ShipmentStatus,
)
from . import db, steps

logger = logging.getLogger(__name__)

# How long a workflow waits for the next vendor event (seconds).
# Long enough for a multi-day demo; DBOS persists the wait durably.
RECV_TIMEOUT = 7 * 24 * 3600  # 7 days


# ---------------------------------------------------------------------------
# Customs gate child workflow
# ---------------------------------------------------------------------------

@DBOS.workflow()
def customs_gate_workflow(shipment_id: str, leg: str) -> str:
    """
    Runs the customs gate sub-state machine for one leg (export or import).
    Returns "released" or "escalated".

    Event flow:
      declaration_filed event → UNDER_REVIEW (loop start)
        → customs_released  → RELEASED (return)
        → customs_held      → HELD_QUERY → query_responded → loop back
      After MAX_CUSTOMS_ATTEMPTS holds → ESCALATED (return)
    """
    declaration_event = (
        EventType.EXPORT_DECLARATION_FILED if leg == "export"
        else EventType.IMPORT_DECLARATION_FILED
    )

    # Wait for declaration to be filed
    evt = DBOS.recv("customs", timeout_seconds=RECV_TIMEOUT)
    if evt != declaration_event.value:
        logger.error("customs_gate unexpected first event: %s", evt)

    db.update_customs_status(shipment_id, leg, CustomsStatus.DECLARATION_FILED.value, 0)
    DBOS.set_event("customs_status", {"leg": leg, "status": CustomsStatus.DECLARATION_FILED.value})

    attempts = 0

    while True:
        # Transition to under review
        db.update_customs_status(shipment_id, leg, CustomsStatus.UNDER_REVIEW.value, attempts)
        DBOS.set_event("customs_status", {"leg": leg, "status": CustomsStatus.UNDER_REVIEW.value, "attempts": attempts})

        # Wait for outcome
        outcome = DBOS.recv("customs", timeout_seconds=RECV_TIMEOUT)

        if outcome == EventType.CUSTOMS_RELEASED.value:
            db.update_customs_status(shipment_id, leg, CustomsStatus.RELEASED.value, attempts)
            DBOS.set_event("customs_status", {"leg": leg, "status": CustomsStatus.RELEASED.value})
            steps.notify_customs_outcome(shipment_id, leg, "released", attempts)
            db.clear_customs_workflow_id(shipment_id)
            return CustomsStatus.RELEASED.value

        if outcome == EventType.CUSTOMS_HELD.value:
            attempts += 1
            if attempts >= MAX_CUSTOMS_ATTEMPTS:
                db.update_customs_status(shipment_id, leg, CustomsStatus.ESCALATED.value, attempts)
                DBOS.set_event("customs_status", {"leg": leg, "status": CustomsStatus.ESCALATED.value})
                steps.notify_escalation(shipment_id, leg)
                db.clear_customs_workflow_id(shipment_id)
                return CustomsStatus.ESCALATED.value

            db.update_customs_status(shipment_id, leg, CustomsStatus.HELD_QUERY.value, attempts)
            DBOS.set_event("customs_status", {"leg": leg, "status": CustomsStatus.HELD_QUERY.value, "attempts": attempts})

            # Wait for broker to respond
            DBOS.recv("customs", timeout_seconds=RECV_TIMEOUT)
            # Loop back to UNDER_REVIEW after response

        # Unexpected event — treat as a no-op ping, loop again
        logger.warning("customs_gate unexpected outcome event: %s", outcome)


# ---------------------------------------------------------------------------
# Main shipment workflow
# ---------------------------------------------------------------------------

@DBOS.workflow()
def shipment_workflow(shipment_id: str) -> None:
    """
    Durable workflow that walks the full shipment milestone chain.
    Blocks on DBOS.recv() at each milestone waiting for the next vendor event.
    Customs gate milestones spawn a child customs_gate_workflow and await its result.
    """
    this_id = DBOS.workflow_id
    db.save_workflow_ids(shipment_id, this_id)
    DBOS.set_event("status", _status_snapshot(shipment_id, ShipmentStatus.CREATED.value))

    # ---- Origin leg ----

    _wait_and_advance(
        shipment_id, EventType.CARGO_PICKED_UP, ShipmentStatus.PICKED_UP, "First mile pickup confirmed"
    )
    _wait_and_advance(
        shipment_id, EventType.CONSOLIDATED, ShipmentStatus.CONSOLIDATED, "Consolidated at warehouse"
    )
    _wait_and_advance(
        shipment_id, EventType.AT_PORT, ShipmentStatus.DRAYAGE, "Drayage to port complete"
    )

    # Export customs gate — spawn child workflow
    db.record_status_change(
        shipment_id, "auto", ShipmentStatus.EXPORT_CUSTOMS.value, "Export customs gate opened"
    )
    DBOS.set_event("status", _status_snapshot(shipment_id, ShipmentStatus.EXPORT_CUSTOMS.value))
    steps.notify_status_change(shipment_id, ShipmentStatus.EXPORT_CUSTOMS.value)

    customs_handle = DBOS.start_workflow(customs_gate_workflow, shipment_id, "export")
    db.save_workflow_ids(shipment_id, this_id, customs_handle.workflow_id)
    customs_handle.get_result()

    # ---- Main haul ----

    _wait_and_advance(
        shipment_id, EventType.HANDOVER, ShipmentStatus.HANDOVER, "B/L or AWB issued, handed to carrier"
    )

    # IN_TRANSIT loop — accumulate transit pings until 'arrived'
    db.record_status_change(
        shipment_id, EventType.TRANSIT_PING.value, ShipmentStatus.IN_TRANSIT.value, "En-route tracking started"
    )
    DBOS.set_event("status", _status_snapshot(shipment_id, ShipmentStatus.IN_TRANSIT.value))
    steps.notify_status_change(shipment_id, ShipmentStatus.IN_TRANSIT.value)

    while True:
        ping_evt = DBOS.recv("milestone", timeout_seconds=RECV_TIMEOUT)
        if ping_evt == EventType.ARRIVED.value:
            db.record_status_change(
                shipment_id, EventType.ARRIVED.value, ShipmentStatus.IN_TRANSIT.value, "Arrived at destination port"
            )
            DBOS.set_event("status", _status_snapshot(shipment_id, ShipmentStatus.IN_TRANSIT.value))
            break
        # transit ping
        db.record_status_change(
            shipment_id, EventType.TRANSIT_PING.value, ShipmentStatus.IN_TRANSIT.value, "En-route ping"
        )
        DBOS.set_event("status", _status_snapshot(shipment_id, ShipmentStatus.IN_TRANSIT.value))

    # ---- Destination leg ----

    # Import customs gate — spawn child workflow
    db.record_status_change(
        shipment_id, "auto", ShipmentStatus.IMPORT_CUSTOMS.value, "Import customs gate opened"
    )
    DBOS.set_event("status", _status_snapshot(shipment_id, ShipmentStatus.IMPORT_CUSTOMS.value))
    steps.notify_status_change(shipment_id, ShipmentStatus.IMPORT_CUSTOMS.value)

    customs_handle = DBOS.start_workflow(customs_gate_workflow, shipment_id, "import")
    db.save_workflow_ids(shipment_id, this_id, customs_handle.workflow_id)
    customs_handle.get_result()

    _wait_and_advance(
        shipment_id, EventType.INLAND_DISPATCHED, ShipmentStatus.INLAND_HAUL, "Dispatched inland to receiver"
    )
    _wait_and_advance(
        shipment_id, EventType.DELIVERED, ShipmentStatus.DELIVERED, "Delivered — PoD captured"
    )
    _wait_and_advance(
        shipment_id, EventType.CLOSED_OUT, ShipmentStatus.CLOSED_OUT, "Shipment reconciled and closed out"
    )

    DBOS.set_event("status", _status_snapshot(shipment_id, ShipmentStatus.CLOSED_OUT.value))


# ---------------------------------------------------------------------------
# Helpers (plain functions, not workflows/steps)
# ---------------------------------------------------------------------------

def _wait_and_advance(
    shipment_id: str,
    expected_event: EventType,
    new_status: ShipmentStatus,
    note: str,
) -> None:
    DBOS.recv("milestone", timeout_seconds=RECV_TIMEOUT)
    db.record_status_change(shipment_id, expected_event.value, new_status.value, note)
    DBOS.set_event("status", _status_snapshot(shipment_id, new_status.value))
    steps.notify_status_change(shipment_id, new_status.value, note)


def _status_snapshot(shipment_id: str, status: str) -> dict:
    return {"shipment_id": shipment_id, "status": status}
