"""
Database operations — each function is a @DBOS.step so DBOS checkpoints its execution.
Using a plain SQLAlchemy session per step (not @DBOS.transaction) keeps the API surface
version-agnostic; the checkpoint + DB write are separate but idempotent at the step level.
"""
import os
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from dbos import DBOS

from .models import Base, CustomsDeclaration, Shipment, ShipmentEvent

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        # Force the psycopg v3 driver: the image ships psycopg[binary] (v3), not
        # psycopg2, so a bare "postgresql://" URL (which SQLAlchemy maps to the
        # psycopg2 dialect by default) fails with ModuleNotFoundError. The replace
        # is idempotent — "postgresql+psycopg://" has no "postgresql://" substring.
        url = os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1)
        _engine = create_engine(url)
    return _engine


def init_db() -> None:
    Base.metadata.create_all(get_engine())


# ---------------------------------------------------------------------------
# Shipment writes
# ---------------------------------------------------------------------------

@DBOS.step()
def create_shipment_row(shipment_id: str, reference: str) -> None:
    with Session(get_engine()) as s:
        s.add(Shipment(id=shipment_id, reference=reference))
        s.commit()


@DBOS.step()
def save_workflow_ids(shipment_id: str, workflow_id: str, customs_workflow_id: str | None = None) -> None:
    with Session(get_engine()) as s:
        vals: dict = {"workflow_id": workflow_id}
        if customs_workflow_id is not None:
            vals["customs_workflow_id"] = customs_workflow_id
        s.execute(update(Shipment).where(Shipment.id == shipment_id).values(**vals))
        s.commit()


@DBOS.step()
def record_status_change(
    shipment_id: str,
    event_type: str,
    status_after: str,
    note: str = "",
) -> None:
    now = datetime.now(timezone.utc)
    with Session(get_engine()) as s:
        s.execute(
            update(Shipment)
            .where(Shipment.id == shipment_id)
            .values(status=status_after, updated_at=now)
        )
        s.add(
            ShipmentEvent(
                id=str(uuid4()),
                shipment_id=shipment_id,
                event_type=event_type,
                status_after=status_after,
                note=note or "",
                timestamp=now,
            )
        )
        s.commit()


# ---------------------------------------------------------------------------
# Customs writes
# ---------------------------------------------------------------------------

@DBOS.step()
def create_customs_row(
    shipment_id: str, leg: str, customs_workflow_id: str
) -> str:
    customs_id = str(uuid4())
    now = datetime.now(timezone.utc)
    with Session(get_engine()) as s:
        s.add(
            CustomsDeclaration(
                id=customs_id,
                shipment_id=shipment_id,
                leg=leg,
                status="declaration_filed",
                attempts=0,
                workflow_id=customs_workflow_id,
                created_at=now,
                updated_at=now,
            )
        )
        s.execute(
            update(Shipment)
            .where(Shipment.id == shipment_id)
            .values(customs_workflow_id=customs_workflow_id)
        )
        s.commit()
    return customs_id


@DBOS.step()
def update_customs_status(shipment_id: str, leg: str, status: str, attempts: int) -> None:
    with Session(get_engine()) as s:
        s.execute(
            update(CustomsDeclaration)
            .where(
                CustomsDeclaration.shipment_id == shipment_id,
                CustomsDeclaration.leg == leg,
            )
            .values(status=status, attempts=attempts, updated_at=datetime.now(timezone.utc))
        )
        s.commit()


@DBOS.step()
def clear_customs_workflow_id(shipment_id: str) -> None:
    with Session(get_engine()) as s:
        s.execute(
            update(Shipment)
            .where(Shipment.id == shipment_id)
            .values(customs_workflow_id=None)
        )
        s.commit()


# ---------------------------------------------------------------------------
# Reads (no DBOS checkpoint needed — read-only, called from API endpoints)
# ---------------------------------------------------------------------------

def get_shipment(shipment_id: str) -> Shipment | None:
    with Session(get_engine()) as s:
        return s.get(Shipment, shipment_id)


def list_shipments() -> list[Shipment]:
    with Session(get_engine()) as s:
        return s.execute(select(Shipment).order_by(Shipment.created_at.desc())).scalars().all()


def get_shipment_full(shipment_id: str) -> dict | None:
    with Session(get_engine()) as s:
        ship = s.get(Shipment, shipment_id)
        if ship is None:
            return None
        events = (
            s.execute(
                select(ShipmentEvent)
                .where(ShipmentEvent.shipment_id == shipment_id)
                .order_by(ShipmentEvent.timestamp)
            )
            .scalars()
            .all()
        )
        customs = (
            s.execute(
                select(CustomsDeclaration)
                .where(CustomsDeclaration.shipment_id == shipment_id)
                .order_by(CustomsDeclaration.created_at)
            )
            .scalars()
            .all()
        )
        return {
            "id": ship.id,
            "reference": ship.reference,
            "status": ship.status,
            "workflow_id": ship.workflow_id,
            "customs_workflow_id": ship.customs_workflow_id,
            "created_at": ship.created_at.isoformat() if ship.created_at else None,
            "updated_at": ship.updated_at.isoformat() if ship.updated_at else None,
            "events": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "status_after": e.status_after,
                    "note": e.note,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                }
                for e in events
            ],
            "customs": [
                {
                    "leg": c.leg,
                    "status": c.status,
                    "attempts": c.attempts,
                }
                for c in customs
            ],
        }
