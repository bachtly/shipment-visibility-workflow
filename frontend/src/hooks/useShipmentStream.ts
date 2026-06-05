import { useEffect, useRef, useState } from "react";
import type { Shipment } from "../types";
import { api } from "../api";

export function useShipmentStream(id: string | null) {
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!id) return;

    let active = true;

    // Initial fetch
    api.getShipment(id).then(setShipment).catch((e) => setError(String(e)));

    // SSE stream for live updates
    const es = new EventSource(`/api/shipments/${id}/stream`);
    esRef.current = es;

    es.addEventListener("update", (e) => {
      if (!active) return;
      try {
        setShipment(JSON.parse(e.data) as Shipment);
        setError(null);
      } catch {
        // ignore parse errors
      }
    });

    es.addEventListener("done", () => {
      es.close();
    });

    es.onerror = () => {
      // On SSE error fall back to polling
      es.close();
      if (!active) return;
      const poll = setInterval(() => {
        if (!active) { clearInterval(poll); return; }
        api.getShipment(id).then((s) => {
          setShipment(s);
          if (s.status === "closed_out") clearInterval(poll);
        }).catch(() => {/* keep polling */});
      }, 3000);
    };

    return () => {
      active = false;
      es.close();
    };
  }, [id]);

  const refresh = () => {
    if (id) api.getShipment(id).then(setShipment).catch((e) => setError(String(e)));
  };

  return { shipment, error, refresh };
}
