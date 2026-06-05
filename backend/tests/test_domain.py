"""
Unit tests for domain logic — no DBOS or DB required.
"""
from app.domain import (
    ALLOWED_EVENTS,
    CUSTOMS_EVENTS,
    MILESTONE_EVENTS,
    MAX_CUSTOMS_ATTEMPTS,
    EventType,
    ShipmentStatus,
)


def test_every_status_has_allowed_events_entry():
    for status in ShipmentStatus:
        assert status in ALLOWED_EVENTS, f"{status} missing from ALLOWED_EVENTS"


def test_customs_events_not_in_milestone_events():
    overlap = CUSTOMS_EVENTS & MILESTONE_EVENTS
    assert not overlap, f"Event appears in both sets: {overlap}"


def test_happy_path_events_legal():
    chain = [
        (ShipmentStatus.CREATED, EventType.CARGO_PICKED_UP),
        (ShipmentStatus.PICKED_UP, EventType.CONSOLIDATED),
        (ShipmentStatus.CONSOLIDATED, EventType.AT_PORT),
        (ShipmentStatus.DRAYAGE, EventType.EXPORT_DECLARATION_FILED),
        (ShipmentStatus.IMPORT_CUSTOMS, EventType.IMPORT_DECLARATION_FILED),
        (ShipmentStatus.INLAND_HAUL, EventType.DELIVERED),
        (ShipmentStatus.DELIVERED, EventType.CLOSED_OUT),
    ]
    for status, event in chain:
        assert event in ALLOWED_EVENTS[status], f"{event} should be allowed in {status}"


def test_illegal_event_not_in_allowed():
    assert EventType.CLOSED_OUT not in ALLOWED_EVENTS[ShipmentStatus.CREATED]
    assert EventType.CARGO_PICKED_UP not in ALLOWED_EVENTS[ShipmentStatus.CLOSED_OUT]


def test_max_customs_attempts_positive():
    assert MAX_CUSTOMS_ATTEMPTS > 0
