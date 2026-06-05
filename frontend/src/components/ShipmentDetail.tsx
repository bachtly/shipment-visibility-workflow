import { useShipmentStream } from "../hooks/useShipmentStream";
import { STATUS_LABELS } from "../domain";
import { MilestoneChain } from "./MilestoneChain";
import { CustomsPanel } from "./CustomsPanel";
import { EventButtons } from "./EventButtons";
import { Timeline } from "./Timeline";

interface Props {
  shipmentId: string;
  onBack: () => void;
}

export function ShipmentDetail({ shipmentId, onBack }: Props) {
  const { shipment, error, refresh } = useShipmentStream(shipmentId);

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <button onClick={onBack} style={backBtn}>← Back</button>
        <div style={{ color: "#c62828", marginTop: 16 }}>{error}</div>
      </div>
    );
  }

  if (!shipment) {
    return (
      <div style={{ padding: 24 }}>
        <button onClick={onBack} style={backBtn}>← Back</button>
        <div style={{ color: "#5f5e5a", marginTop: 16 }}>Loading…</div>
      </div>
    );
  }

  const isCustomsActive =
    shipment.status === "export_customs" || shipment.status === "import_customs";

  return (
    <div style={{ padding: 24, maxWidth: 860, margin: "0 auto" }}>
      <button onClick={onBack} style={backBtn}>← All Shipments</button>

      <div style={{ display: "flex", alignItems: "baseline", gap: 12, margin: "16px 0" }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: "#141413" }}>
          {shipment.reference}
        </h1>
        <StatusBadge status={shipment.status} />
      </div>

      <section style={card}>
        <h2 style={sectionHead}>Milestone Chain</h2>
        <MilestoneChain currentStatus={shipment.status} />
      </section>

      {isCustomsActive && shipment.customs.length > 0 && (
        <section style={card}>
          <h2 style={sectionHead}>Customs Gate</h2>
          <CustomsPanel customs={shipment.customs} shipmentStatus={shipment.status} />
        </section>
      )}

      <section style={card}>
        <h2 style={sectionHead}>Actions</h2>
        <EventButtons
          shipmentId={shipment.id}
          currentStatus={shipment.status}
          onEventFired={refresh}
        />
      </section>

      {shipment.events.length > 0 && (
        <section style={card}>
          <Timeline events={shipment.events} />
        </section>
      )}

      <div style={{ fontSize: 11, color: "#9f9e98", marginTop: 8 }}>
        Workflow ID: {shipment.workflow_id ?? "—"}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const isCustoms = status === "export_customs" || status === "import_customs";
  const isDone = status === "closed_out";
  const bg = isDone ? "#e1f5ee" : isCustoms ? "#fff3cd" : "#e6f1fb";
  const color = isDone ? "#085041" : isCustoms ? "#633806" : "#0c447c";
  return (
    <span
      style={{
        padding: "3px 10px",
        borderRadius: 12,
        backgroundColor: bg,
        color,
        fontSize: 13,
        fontWeight: 600,
      }}
    >
      {STATUS_LABELS[status as keyof typeof STATUS_LABELS] ?? status}
    </span>
  );
}

const backBtn: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "#185fa5",
  cursor: "pointer",
  fontSize: 14,
  padding: 0,
  fontWeight: 500,
};

const card: React.CSSProperties = {
  background: "#fff",
  border: "1px solid #e0dfd8",
  borderRadius: 10,
  padding: 20,
  marginBottom: 16,
};

const sectionHead: React.CSSProperties = {
  margin: "0 0 14px",
  fontSize: 15,
  fontWeight: 600,
  color: "#141413",
};
