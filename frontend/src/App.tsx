import { useState } from "react";
import { ShipmentList } from "./components/ShipmentList";
import { ShipmentDetail } from "./components/ShipmentDetail";

export default function App() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#fafaf7", fontFamily: "system-ui, sans-serif" }}>
      {selectedId ? (
        <ShipmentDetail shipmentId={selectedId} onBack={() => setSelectedId(null)} />
      ) : (
        <ShipmentList onSelect={setSelectedId} />
      )}
    </div>
  );
}
