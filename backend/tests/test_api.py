"""
Integration tests against a live Postgres + DBOS.
Run with: pytest tests/test_api.py (requires DB from docker-compose).
"""
import time
import pytest
from fastapi.testclient import TestClient


def _poll_status(client: TestClient, shipment_id: str, target: str, timeout: int = 10) -> str:
    """Poll GET /shipments/{id} until status == target or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/api/shipments/{shipment_id}")
        status = r.json()["status"]
        if status == target:
            return status
        time.sleep(0.3)
    return status  # whatever it ended up at


@pytest.mark.integration
def test_create_shipment(client: TestClient):
    r = client.post("/api/shipments", json={"reference": "TEST-001"})
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["reference"] == "TEST-001"


@pytest.mark.integration
def test_happy_path(client: TestClient):
    r = client.post("/api/shipments", json={"reference": "HAPPY-001"})
    sid = r.json()["id"]

    events = [
        "cargo_picked_up",
        "consolidated",
        "at_port",
    ]
    expected_statuses = ["picked_up", "consolidated", "drayage"]

    for evt, expected in zip(events, expected_statuses):
        r = client.post(f"/api/shipments/{sid}/events", json={"event_type": evt})
        assert r.status_code == 200, r.text
        status = _poll_status(client, sid, expected)
        assert status == expected, f"After {evt}: expected {expected}, got {status}"


@pytest.mark.integration
def test_illegal_event_rejected(client: TestClient):
    r = client.post("/api/shipments", json={"reference": "ILLEGAL-001"})
    sid = r.json()["id"]
    # CREATED status — closed_out not allowed
    r = client.post(f"/api/shipments/{sid}/events", json={"event_type": "closed_out"})
    assert r.status_code == 422


@pytest.mark.integration
def test_customs_hold_and_release(client: TestClient):
    r = client.post("/api/shipments", json={"reference": "CUSTOMS-001"})
    sid = r.json()["id"]

    for evt in ["cargo_picked_up", "consolidated", "at_port"]:
        client.post(f"/api/shipments/{sid}/events", json={"event_type": evt})

    _poll_status(client, sid, "drayage")

    # Start export customs
    client.post(f"/api/shipments/{sid}/events", json={"event_type": "export_declaration_filed"})
    _poll_status(client, sid, "export_customs")

    # Hold → respond → release
    client.post(f"/api/shipments/{sid}/events", json={"event_type": "customs_held"})
    time.sleep(0.5)
    client.post(f"/api/shipments/{sid}/events", json={"event_type": "query_responded"})
    time.sleep(0.5)
    client.post(f"/api/shipments/{sid}/events", json={"event_type": "customs_released"})

    # Should advance past export customs to handover
    final = _poll_status(client, sid, "handover", timeout=15)
    assert final == "handover"
