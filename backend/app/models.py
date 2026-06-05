from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    reference: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="created")
    workflow_id: Mapped[str | None] = mapped_column(String, nullable=True)
    customs_workflow_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    events: Mapped[list["ShipmentEvent"]] = relationship(
        "ShipmentEvent", back_populates="shipment", order_by="ShipmentEvent.timestamp"
    )
    customs: Mapped[list["CustomsDeclaration"]] = relationship(
        "CustomsDeclaration", back_populates="shipment"
    )


class ShipmentEvent(Base):
    __tablename__ = "shipment_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    shipment_id: Mapped[str] = mapped_column(String, ForeignKey("shipments.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    status_after: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="events")


class CustomsDeclaration(Base):
    __tablename__ = "customs_declarations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    shipment_id: Mapped[str] = mapped_column(String, ForeignKey("shipments.id"), nullable=False)
    leg: Mapped[str] = mapped_column(String, nullable=False)  # "export" or "import"
    status: Mapped[str] = mapped_column(String, nullable=False, default="declaration_filed")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    workflow_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="customs")
