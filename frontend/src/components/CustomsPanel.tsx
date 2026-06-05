import type { CustomsInfo } from "../types";

interface Props {
  customs: CustomsInfo[];
  shipmentStatus: string;
}

const STATUS_LABELS: Record<string, string> = {
  declaration_filed: "Declaration Filed",
  under_review: "Under Review",
  held_query: "Held / Query",
  released: "Released",
  escalated: "Escalated",
};

const STATUS_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  declaration_filed: { bg: "#e6f1fb", border: "#185fa5", text: "#0c447c" },
  under_review:      { bg: "#e6f1fb", border: "#185fa5", text: "#0c447c" },
  held_query:        { bg: "#fff3cd", border: "#854f0b", text: "#633806" },
  released:          { bg: "#e1f5ee", border: "#0f6e56", text: "#085041" },
  escalated:         { bg: "#fde8e8", border: "#c62828", text: "#7f0000" },
};

function CustomsStep({ label, active }: { label: string; active: boolean }) {
  return (
    <div
      style={{
        padding: "6px 14px",
        borderRadius: 6,
        border: `1px solid ${active ? "#185fa5" : "#c5c4bc"}`,
        backgroundColor: active ? "#e6f1fb" : "#f1efe8",
        color: active ? "#0c447c" : "#9f9e98",
        fontSize: 13,
        fontWeight: active ? 600 : 400,
      }}
    >
      {label}
    </div>
  );
}

export function CustomsPanel({ customs, shipmentStatus }: Props) {
  const activeLeg =
    shipmentStatus === "export_customs" ? "export" : "import";
  const active = customs.find((c) => c.leg === activeLeg);

  if (!active) return null;

  const c = STATUS_COLORS[active.status] ?? STATUS_COLORS.under_review;

  return (
    <div
      style={{
        border: `1.5px solid ${c.border}`,
        borderRadius: 10,
        backgroundColor: c.bg,
        padding: 16,
        marginBottom: 16,
      }}
    >
      <div style={{ fontWeight: 600, color: c.text, marginBottom: 8 }}>
        {activeLeg === "export" ? "Export" : "Import"} Customs Gate
      </div>

      {/* Sub-state machine flow */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <CustomsStep label="Declaration Filed" active={active.status === "declaration_filed"} />
        <span style={{ color: "#73726c" }}>→</span>
        <CustomsStep label="Under Review" active={active.status === "under_review"} />
        <span style={{ color: "#73726c" }}>→</span>
        <CustomsStep label="Outcome?" active={false} />
      </div>

      <div style={{ display: "flex", gap: 16, marginTop: 8, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: "#73726c", fontSize: 12 }}>cleared →</span>
          <CustomsStep label="Released" active={active.status === "released"} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: "#73726c", fontSize: 12 }}>held →</span>
          <CustomsStep label="Held / Query" active={active.status === "held_query"} />
          <span style={{ color: "#73726c", fontSize: 12 }}>→ respond →</span>
          <CustomsStep label="Resubmit" active={false} />
        </div>
      </div>

      <div style={{ marginTop: 10, fontSize: 13, color: c.text }}>
        <strong>Status:</strong> {STATUS_LABELS[active.status] ?? active.status}
        {active.attempts > 0 && (
          <span style={{ marginLeft: 12, color: "#854f0b" }}>
            Attempt {active.attempts} / 3
          </span>
        )}
        {active.status === "escalated" && (
          <span style={{ marginLeft: 12, color: "#c62828", fontWeight: 600 }}>
            ⚠ Escalated — manual intervention required
          </span>
        )}
      </div>
    </div>
  );
}
