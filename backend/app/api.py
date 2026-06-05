"""
FastAPI route handlers.
"""
import asyncio
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from dbos import DBOS

from .domain import ALLOWED_EVENTS, CUSTOMS_EVENTS, ShipmentStatus
from . import db, workflows

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CreateShipmentRequest(BaseModel):
    reference: str


class FireEventRequest(BaseModel):
    event_type: str
    note: str = ""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@router.get("/shipments")
def list_shipments() -> list[dict]:
    ships = db.list_shipments()
    return [
        {
            "id": s.id,
            "reference": s.reference,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in ships
    ]


@router.post("/shipments", status_code=201)
def create_shipment(body: CreateShipmentRequest) -> dict:
    shipment_id = str(uuid4())
    db.create_shipment_row(shipment_id, body.reference)
    handle = DBOS.start_workflow(workflows.shipment_workflow, shipment_id)
    db.save_workflow_ids(shipment_id, handle.workflow_id)
    return {"id": shipment_id, "reference": body.reference, "workflow_id": handle.workflow_id}


@router.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: str) -> dict:
    data = db.get_shipment_full(shipment_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return data


@router.post("/shipments/{shipment_id}/events")
def fire_event(shipment_id: str, body: FireEventRequest) -> dict:
    ship = db.get_shipment(shipment_id)
    if ship is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    try:
        current_status = ShipmentStatus(ship.status)
    except ValueError:
        raise HTTPException(status_code=409, detail=f"Unknown status: {ship.status}")

    allowed = ALLOWED_EVENTS.get(current_status, [])
    allowed_values = {e.value for e in allowed}
    if body.event_type not in allowed_values:
        raise HTTPException(
            status_code=422,
            detail=f"Event '{body.event_type}' not allowed in status '{ship.status}'. Allowed: {sorted(allowed_values)}",
        )

    from .domain import EventType

    event_type = EventType(body.event_type)

    if event_type in CUSTOMS_EVENTS:
        # Route to the active customs child workflow
        if not ship.customs_workflow_id:
            raise HTTPException(status_code=409, detail="No active customs workflow for this shipment")
        DBOS.send(ship.customs_workflow_id, body.event_type, "customs")
    else:
        # Route to the main shipment workflow
        if not ship.workflow_id:
            raise HTTPException(status_code=409, detail="Shipment has no active workflow")
        DBOS.send(ship.workflow_id, body.event_type, "milestone")

    return {"accepted": True, "event_type": body.event_type}


@router.get("/shipments/{shipment_id}/stream")
async def stream_status(shipment_id: str):
    """
    Server-Sent Events endpoint — pushes status snapshots when the workflow
    updates the 'status' event key. Falls back to polling the DB every 2s.
    """
    ship = db.get_shipment(shipment_id)
    if ship is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    async def generator():
        last_status = None
        while True:
            try:
                data = db.get_shipment_full(shipment_id)
                if data and data.get("status") != last_status:
                    last_status = data["status"]
                    yield {"data": _json(data), "event": "update"}
                if last_status == "closed_out":
                    yield {"data": '{"done":true}', "event": "done"}
                    break
            except Exception as exc:
                logger.warning("SSE error for %s: %s", shipment_id, exc)
            await asyncio.sleep(2)

    return EventSourceResponse(generator())


def _json(data: dict) -> str:
    import json
    return json.dumps(data)
