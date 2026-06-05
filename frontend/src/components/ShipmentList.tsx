import { useEffect, useState } from "react";
import type { ShipmentSummary } from "../types";
import { STATUS_LABELS } from "../domain";
import { api } from "../api";

interface Props {
  onSelect: (id: string) => void;
}

export function ShipmentList({ onSelect }: Props) {
  const [shipments, setShipments] = useState<ShipmentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [reference, setReference] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    api.listShipments().then((s) => { setShipments(s); setLoading(false); }).catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  async function create() {
    if (!reference.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const s = await api.createShipment(reference.trim());
      setReference("");
      load();
      onSelect(s.id);
    } catch (e) {
      setError(String(e));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 720, margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: "#141413" }}>
          Shipment Visibility
        </h1>
        <span style={{ fontSize: 13, color: "#5f5e5a" }}>Whale Logistics · DBOS Demo</span>
      </div>

      {/* Create form */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 24,
          padding: 16,
          background: "#fff",
          border: "1px solid #e0dfd8",
          borderRadius: 10,
        }}
      >
        <input
          placeholder="Shipment reference (e.g. PO-2025-001)"
          value={reference}
          onChange={(e) => setReference(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && create()}
          style={{
            flex: 1,
            padding: "8px 12px",
            borderRadius: 7,
            border: "1px solid #c5c4bc",
            fontSize: 14,
            outline: "none",
          }}
        />
        <button
          onClick={create}
          disabled={creating || !reference.trim()}
          style={{
            padding: "8px 18px",
            borderRadius: 7,
            border: "none",
            backgroundColor: "#185fa5",
            color: "#fff",
            fontWeight: 600,
            fontSize: 14,
            cursor: creating ? "not-allowed" : "pointer",
            opacity: creating ? 0.6 : 1,
          }}
        >
          {creating ? "Creating…" : "New Shipment"}
        </button>
      </div>
      {error && <div style={{ color: "#c62828", fontSize: 13, marginBottom: 12 }}>{error}</div>}

      {/* List */}
      {loading ? (
        <div style={{ color: "#5f5e5a" }}>Loading…</div>
      ) : shipments.length === 0 ? (
        <div style={{ color: "#5f5e5a" }}>No shipments yet. Create one above.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {shipments.map((s) => (
            <button
              key={s.id}
              onClick={() => onSelect(s.id)}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "12px 16px",
                background: "#fff",
                border: "1px solid #e0dfd8",
                borderRadius: 10,
                cursor: "pointer",
                textAlign: "left",
                transition: "border-color 0.15s",
              }}
              onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "#185fa5")}
              onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "#e0dfd8")}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 15, color: "#141413" }}>{s.reference}</div>
                <div style={{ fontSize: 12, color: "#9f9e98", marginTop: 2 }}>
                  {new Date(s.created_at).toLocaleDateString()}
                </div>
              </div>
              <StatusBadge status={s.status} />
            </button>
          ))}
        </div>
      )}

      <button
        onClick={load}
        style={{
          marginTop: 16,
          background: "none",
          border: "1px solid #c5c4bc",
          borderRadius: 7,
          padding: "6px 14px",
          fontSize: 13,
          cursor: "pointer",
          color: "#5f5e5a",
        }}
      >
        Refresh
      </button>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const label = STATUS_LABELS[status as keyof typeof STATUS_LABELS] ?? status;
  const isCustoms = status.includes("customs");
  const isDone = status === "closed_out";
  const bg = isDone ? "#e1f5ee" : isCustoms ? "#fff3cd" : "#f1efe8";
  const color = isDone ? "#085041" : isCustoms ? "#633806" : "#5f5e5a";
  return (
    <span style={{ fontSize: 12, padding: "3px 10px", borderRadius: 12, backgroundColor: bg, color, fontWeight: 500 }}>
      {label}
    </span>
  );
}
