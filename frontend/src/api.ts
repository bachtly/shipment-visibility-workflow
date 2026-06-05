import type { Shipment, ShipmentSummary } from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listShipments: () => request<ShipmentSummary[]>("/shipments"),

  createShipment: (reference: string) =>
    request<{ id: string; reference: string }>("/shipments", {
      method: "POST",
      body: JSON.stringify({ reference }),
    }),

  getShipment: (id: string) => request<Shipment>(`/shipments/${id}`),

  fireEvent: (id: string, event_type: string, note = "") =>
    request<{ accepted: boolean }>(`/shipments/${id}/events`, {
      method: "POST",
      body: JSON.stringify({ event_type, note }),
    }),
};
