from enum import Enum


class ShipmentStatus(str, Enum):
    CREATED = "created"
    # Origin leg
    PICKED_UP = "picked_up"
    CONSOLIDATED = "consolidated"
    DRAYAGE = "drayage"
    EXPORT_CUSTOMS = "export_customs"
    # Main haul
    HANDOVER = "handover"
    IN_TRANSIT = "in_transit"
    # Destination leg
    IMPORT_CUSTOMS = "import_customs"
    INLAND_HAUL = "inland_haul"
    DELIVERED = "delivered"
    CLOSED_OUT = "closed_out"


class CustomsStatus(str, Enum):
    DECLARATION_FILED = "declaration_filed"
    UNDER_REVIEW = "under_review"
    HELD_QUERY = "held_query"
    RELEASED = "released"
    ESCALATED = "escalated"


class EventType(str, Enum):
    # Origin leg
    CARGO_PICKED_UP = "cargo_picked_up"
    CONSOLIDATED = "consolidated"
    AT_PORT = "at_port"
    # Customs
    EXPORT_DECLARATION_FILED = "export_declaration_filed"
    IMPORT_DECLARATION_FILED = "import_declaration_filed"
    CUSTOMS_RELEASED = "customs_released"
    CUSTOMS_HELD = "customs_held"
    QUERY_RESPONDED = "query_responded"
    # Main haul
    HANDOVER = "handover"
    TRANSIT_PING = "transit_ping"
    ARRIVED = "arrived"
    # Destination leg
    INLAND_DISPATCHED = "inland_dispatched"
    DELIVERED = "delivered"
    CLOSED_OUT = "closed_out"


# Events that advance the main milestone chain
MILESTONE_EVENTS: set[EventType] = {
    EventType.CARGO_PICKED_UP,
    EventType.CONSOLIDATED,
    EventType.AT_PORT,
    EventType.HANDOVER,
    EventType.TRANSIT_PING,
    EventType.ARRIVED,
    EventType.INLAND_DISPATCHED,
    EventType.DELIVERED,
    EventType.CLOSED_OUT,
}

# Events that belong to the customs child workflow
CUSTOMS_EVENTS: set[EventType] = {
    EventType.EXPORT_DECLARATION_FILED,
    EventType.IMPORT_DECLARATION_FILED,
    EventType.CUSTOMS_RELEASED,
    EventType.CUSTOMS_HELD,
    EventType.QUERY_RESPONDED,
}

# Which events are legal given the current shipment status
ALLOWED_EVENTS: dict[ShipmentStatus, list[EventType]] = {
    ShipmentStatus.CREATED: [EventType.CARGO_PICKED_UP],
    ShipmentStatus.PICKED_UP: [EventType.CONSOLIDATED],
    ShipmentStatus.CONSOLIDATED: [EventType.AT_PORT],
    ShipmentStatus.DRAYAGE: [EventType.EXPORT_DECLARATION_FILED],
    ShipmentStatus.EXPORT_CUSTOMS: [
        EventType.EXPORT_DECLARATION_FILED,  # opens the gate (child's first recv)
        EventType.CUSTOMS_RELEASED,
        EventType.CUSTOMS_HELD,
        EventType.QUERY_RESPONDED,
    ],
    ShipmentStatus.HANDOVER: [EventType.TRANSIT_PING, EventType.ARRIVED],
    ShipmentStatus.IN_TRANSIT: [EventType.TRANSIT_PING, EventType.ARRIVED],
    ShipmentStatus.IMPORT_CUSTOMS: [
        EventType.IMPORT_DECLARATION_FILED,
        EventType.CUSTOMS_RELEASED,
        EventType.CUSTOMS_HELD,
        EventType.QUERY_RESPONDED,
    ],
    ShipmentStatus.INLAND_HAUL: [EventType.DELIVERED],
    ShipmentStatus.DELIVERED: [EventType.CLOSED_OUT],
    ShipmentStatus.CLOSED_OUT: [],
}

# Human-readable labels for the UI
STATUS_LABELS: dict[ShipmentStatus, str] = {
    ShipmentStatus.CREATED: "Created",
    ShipmentStatus.PICKED_UP: "Picked Up",
    ShipmentStatus.CONSOLIDATED: "Consolidated",
    ShipmentStatus.DRAYAGE: "Drayage to Port",
    ShipmentStatus.EXPORT_CUSTOMS: "Export Customs",
    ShipmentStatus.HANDOVER: "Carrier Handover",
    ShipmentStatus.IN_TRANSIT: "In Transit",
    ShipmentStatus.IMPORT_CUSTOMS: "Import Customs",
    ShipmentStatus.INLAND_HAUL: "Inland Haul",
    ShipmentStatus.DELIVERED: "Delivered",
    ShipmentStatus.CLOSED_OUT: "Closed Out",
}

EVENT_LABELS: dict[EventType, str] = {
    EventType.CARGO_PICKED_UP: "Cargo Picked Up",
    EventType.CONSOLIDATED: "Consolidated at Warehouse",
    EventType.AT_PORT: "Arrived at Port (Drayage Complete)",
    EventType.EXPORT_DECLARATION_FILED: "Export Declaration Filed",
    EventType.IMPORT_DECLARATION_FILED: "Import Declaration Filed",
    EventType.CUSTOMS_RELEASED: "Customs Released",
    EventType.CUSTOMS_HELD: "Customs Hold Issued",
    EventType.QUERY_RESPONDED: "Query Response Submitted",
    EventType.HANDOVER: "Handed Over to Carrier",
    EventType.TRANSIT_PING: "In-Transit Ping",
    EventType.ARRIVED: "Arrived at Destination Port",
    EventType.INLAND_DISPATCHED: "Dispatched Inland",
    EventType.DELIVERED: "Delivered (PoD Captured)",
    EventType.CLOSED_OUT: "Shipment Closed Out",
}

# Customs gate statuses (when a status is a gate, we run a child customs workflow)
CUSTOMS_GATE_STATUSES: set[ShipmentStatus] = {
    ShipmentStatus.EXPORT_CUSTOMS,
    ShipmentStatus.IMPORT_CUSTOMS,
}

MAX_CUSTOMS_ATTEMPTS = 3
