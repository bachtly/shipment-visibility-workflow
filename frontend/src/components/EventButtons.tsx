import { useState } from "react";
import type { ShipmentStatus } from "../types";
import { ALLOWED_EVENTS, EVENT_LABELS } from "../domain";
import { api } from "../api";

interface Props {
  shipmentId: string;
  currentStatus: ShipmentStatus;
  onEventFired: () => void;
}

// Visual style per event category
function eventStyle(eventType: string): { bg: string; border: string; text: string } {
  if (eventType.includes("customs_held"))
    return { bg: "#fff3cd", border: "#854f0b", text: "#633806" };
  if (eventType.includes("customs_released") || eventType === "delivered" || eventType === "closed_out")
    return { bg: "#e1f5ee", border: "#0f6e56", text: "#085041" };
  if (eventType.includes("customs") || eventType.includes("declaration"))
    return { bg: "#fff3cd", border: "#854f0b", text: "#633806" };
  return { bg: "#e6f1fb", border: "#185fa5", text: "#0c447c" };
}

export function EventButtons({ shipmentId, currentStatus, onEventFired }: Props) {
  const [loading, setLoading] = useState<string | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);

  const allowed = ALLOWED_EVENTS[currentStatus] ?? [];

  if (allowed.length === 0) {
    return (
      <div style={{ color: "#5f5e5a", fontSize: 14, padding: "8px 0" }}>
        No further actions — shipment is {currentStatus}.
      </div>
    );
  }

  async function fire(eventType: string) {
    setLoading(eventType);
    setLastError(null);
    try {
      await api.fireEvent(shipmentId, eventType);
      onEventFired();
    } catch (e) {
      setLastError(String(e));
    } finally {
      setLoading(null);
    }
  }

  return (
    <div>
      <div style={{ fontSize: 12, color: "#5f5e5a", marginBottom: 8, fontWeight: 500 }}>
        SIMULATE VENDOR EVENT
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {allowed.map((evt) => {
          const s = eventStyle(evt);
          const busy = loading === evt;
          return (
            <button
              key={evt}
              disabled={loading !== null}
              onClick={() => fire(evt)}
              style={{
                padding: "8px 14px",
                borderRadius: 7,
                border: `1.5px solid ${s.border}`,
                backgroundColor: busy ? s.border : s.bg,
                color: busy ? "#fff" : s.text,
                fontWeight: 600,
                fontSize: 13,
                cursor: loading !== null ? "not-allowed" : "pointer",
                opacity: loading !== null && !busy ? 0.5 : 1,
                transition: "all 0.15s",
              }}
            >
              {busy ? "…" : EVENT_LABELS[evt] ?? evt}
            </button>
          );
        })}
      </div>
      {lastError && (
        <div style={{ color: "#c62828", fontSize: 13, marginTop: 8 }}>{lastError}</div>
      )}
    </div>
  );
}
