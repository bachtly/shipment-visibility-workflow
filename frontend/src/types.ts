export type ShipmentStatus =
  | "created"
  | "picked_up"
  | "consolidated"
  | "drayage"
  | "export_customs"
  | "handover"
  | "in_transit"
  | "import_customs"
  | "inland_haul"
  | "delivered"
  | "closed_out";

export type CustomsStatus =
  | "declaration_filed"
  | "under_review"
  | "held_query"
  | "released"
  | "escalated";

export type EventType =
  | "cargo_picked_up"
  | "consolidated"
  | "at_port"
  | "export_declaration_filed"
  | "import_declaration_filed"
  | "customs_released"
  | "customs_held"
  | "query_responded"
  | "handover"
  | "transit_ping"
  | "arrived"
  | "inland_dispatched"
  | "delivered"
  | "closed_out";

export interface ShipmentEvent {
  id: string;
  event_type: string;
  status_after: string;
  note: string | null;
  timestamp: string;
}

export interface CustomsInfo {
  leg: string;
  status: CustomsStatus;
  attempts: number;
}

export interface Shipment {
  id: string;
  reference: string;
  status: ShipmentStatus;
  workflow_id: string | null;
  customs_workflow_id: string | null;
  created_at: string;
  updated_at: string;
  events: ShipmentEvent[];
  customs: CustomsInfo[];
}

export interface ShipmentSummary {
  id: string;
  reference: string;
  status: ShipmentStatus;
  created_at: string;
}
