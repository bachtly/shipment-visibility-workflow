import type { EventType, ShipmentStatus } from "./types";

export const STATUS_LABELS: Record<ShipmentStatus, string> = {
  created: "Created",
  picked_up: "Picked Up",
  consolidated: "Consolidated",
  drayage: "Drayage to Port",
  export_customs: "Export Customs",
  handover: "Carrier Handover",
  in_transit: "In Transit",
  import_customs: "Import Customs",
  inland_haul: "Inland Haul",
  delivered: "Delivered",
  closed_out: "Closed Out",
};

export const EVENT_LABELS: Record<EventType, string> = {
  cargo_picked_up: "Cargo Picked Up",
  consolidated: "Consolidated at Warehouse",
  at_port: "Arrived at Port (Drayage Complete)",
  export_declaration_filed: "Export Declaration Filed",
  import_declaration_filed: "Import Declaration Filed",
  customs_released: "Customs Released",
  customs_held: "Customs Hold Issued",
  query_responded: "Query Response Submitted",
  handover: "Handed Over to Carrier",
  transit_ping: "In-Transit Ping",
  arrived: "Arrived at Destination Port",
  inland_dispatched: "Dispatched Inland",
  delivered: "Delivered (PoD Captured)",
  closed_out: "Shipment Closed Out",
};

export const ALLOWED_EVENTS: Record<ShipmentStatus, EventType[]> = {
  created: ["cargo_picked_up"],
  picked_up: ["consolidated"],
  consolidated: ["at_port"],
  drayage: ["export_declaration_filed"],
  export_customs: [
    "export_declaration_filed",
    "customs_released",
    "customs_held",
    "query_responded",
  ],
  handover: ["transit_ping", "arrived"],
  in_transit: ["transit_ping", "arrived"],
  import_customs: [
    "import_declaration_filed",
    "customs_released",
    "customs_held",
    "query_responded",
  ],
  inland_haul: ["delivered"],
  delivered: ["closed_out"],
  closed_out: [],
};

// The ordered list of statuses in the chain (excluding "created")
export const STATUS_ORDER: ShipmentStatus[] = [
  "picked_up",
  "consolidated",
  "drayage",
  "export_customs",
  "handover",
  "in_transit",
  "import_customs",
  "inland_haul",
  "delivered",
  "closed_out",
];

export const ORIGIN_LEG: ShipmentStatus[] = [
  "picked_up",
  "consolidated",
  "drayage",
  "export_customs",
];
export const HAUL_LEG: ShipmentStatus[] = ["handover", "in_transit"];
export const DEST_LEG: ShipmentStatus[] = [
  "import_customs",
  "inland_haul",
  "delivered",
  "closed_out",
];

export const CUSTOMS_STATUSES = new Set<ShipmentStatus>([
  "export_customs",
  "import_customs",
]);

export type NodeState = "completed" | "active" | "customs" | "pending";

export function getNodeState(
  nodeStatus: ShipmentStatus,
  currentStatus: ShipmentStatus
): NodeState {
  const nodeIdx = STATUS_ORDER.indexOf(nodeStatus);
  const curIdx = STATUS_ORDER.indexOf(currentStatus);

  if (nodeIdx < curIdx) return "completed";
  if (nodeIdx === curIdx) {
    return CUSTOMS_STATUSES.has(nodeStatus) ? "customs" : "active";
  }
  return "pending";
}

// Colors matching the SVG palette
export const NODE_COLORS: Record<NodeState, { bg: string; border: string; text: string; sub: string }> = {
  completed: { bg: "#e1f5ee", border: "#0f6e56", text: "#085041", sub: "#0f6e56" },
  active:    { bg: "#e6f1fb", border: "#185fa5", text: "#0c447c", sub: "#185fa5" },
  customs:   { bg: "#faeedа", border: "#854f0b", text: "#633806", sub: "#854f0b" },
  pending:   { bg: "#f1efe8", border: "#c5c4bc", text: "#5f5e5a", sub: "#9f9e98" },
};

// Amber doesn't render so fallback
export const NODE_COLORS_SAFE: Record<NodeState, { bg: string; border: string; text: string; sub: string }> = {
  completed: { bg: "#e1f5ee", border: "#0f6e56", text: "#085041", sub: "#0f6e56" },
  active:    { bg: "#e6f1fb", border: "#185fa5", text: "#0c447c", sub: "#185fa5" },
  customs:   { bg: "#fff3cd", border: "#854f0b", text: "#633806", sub: "#854f0b" },
  pending:   { bg: "#f1efe8", border: "#c5c4bc", text: "#5f5e5a", sub: "#9f9e98" },
};

export const STATUS_SUBTITLES: Partial<Record<ShipmentStatus, string>> = {
  picked_up: "first mile",
  consolidated: "store, pack",
  drayage: "to port",
  export_customs: "customs gate",
  handover: "B/L or AWB",
  in_transit: "en route",
  import_customs: "customs gate",
  inland_haul: "to receiver",
  delivered: "PoD captured",
  closed_out: "reconcile",
};
