import type { ShipmentStatus } from "../types";
import {
  DEST_LEG,
  HAUL_LEG,
  NODE_COLORS_SAFE,
  ORIGIN_LEG,
  STATUS_LABELS,
  STATUS_SUBTITLES,
  getNodeState,
} from "../domain";

interface Props {
  currentStatus: ShipmentStatus;
}

function MilestoneNode({
  status,
  currentStatus,
}: {
  status: ShipmentStatus;
  currentStatus: ShipmentStatus;
}) {
  const state = getNodeState(status, currentStatus);
  const c = NODE_COLORS_SAFE[state];
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        width: 120,
        minHeight: 52,
        borderRadius: 8,
        border: `1.5px solid ${c.border}`,
        backgroundColor: c.bg,
        padding: "6px 8px",
        textAlign: "center",
        flexShrink: 0,
      }}
    >
      <span style={{ fontSize: 13, fontWeight: 600, color: c.text }}>
        {STATUS_LABELS[status]}
      </span>
      {STATUS_SUBTITLES[status] && (
        <span style={{ fontSize: 11, color: c.sub, marginTop: 2 }}>
          {STATUS_SUBTITLES[status]}
        </span>
      )}
    </div>
  );
}

function Arrow() {
  return (
    <span style={{ fontSize: 16, color: "#73726c", margin: "0 4px", alignSelf: "center" }}>
      →
    </span>
  );
}

function Leg({
  label,
  statuses,
  currentStatus,
}: {
  label: string;
  statuses: ShipmentStatus[];
  currentStatus: ShipmentStatus;
}) {
  return (
    <div
      style={{
        border: "1px dashed rgba(31,30,29,0.25)",
        borderRadius: 14,
        backgroundColor: "#f5f4ed",
        padding: "10px 16px",
        marginBottom: 10,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 500, color: "#141413", marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 4 }}>
        {statuses.map((s, i) => (
          <span key={s} style={{ display: "flex", alignItems: "center" }}>
            {i > 0 && <Arrow />}
            <MilestoneNode status={s} currentStatus={currentStatus} />
          </span>
        ))}
      </div>
    </div>
  );
}

export function MilestoneChain({ currentStatus }: Props) {
  return (
    <div>
      <Leg label="1 · Origin leg" statuses={ORIGIN_LEG} currentStatus={currentStatus} />
      <Leg label="2 · Main haul — carrier" statuses={HAUL_LEG} currentStatus={currentStatus} />
      <Leg label="3 · Destination leg" statuses={DEST_LEG} currentStatus={currentStatus} />
    </div>
  );
}
