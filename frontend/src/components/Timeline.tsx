import type { ShipmentEvent } from "../types";
import { EVENT_LABELS } from "../domain";

interface Props {
  events: ShipmentEvent[];
}

export function Timeline({ events }: Props) {
  if (events.length === 0) return null;

  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 600, color: "#141413", marginBottom: 8 }}>
        Event Timeline
      </div>
      <div style={{ borderLeft: "2px solid #e0dfd8", paddingLeft: 16 }}>
        {[...events].reverse().map((e) => (
          <div key={e.id} style={{ marginBottom: 10, position: "relative" }}>
            <div
              style={{
                position: "absolute",
                left: -21,
                top: 4,
                width: 8,
                height: 8,
                borderRadius: "50%",
                backgroundColor: "#185fa5",
                border: "2px solid #fff",
              }}
            />
            <div style={{ fontSize: 13, fontWeight: 600, color: "#141413" }}>
              {EVENT_LABELS[e.event_type as keyof typeof EVENT_LABELS] ?? e.event_type}
            </div>
            {e.note && (
              <div style={{ fontSize: 12, color: "#5f5e5a" }}>{e.note}</div>
            )}
            <div style={{ fontSize: 11, color: "#9f9e98" }}>
              {new Date(e.timestamp).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
