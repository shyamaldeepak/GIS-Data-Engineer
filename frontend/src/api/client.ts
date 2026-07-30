import type { Alert, Geofence, Vehicle } from "../types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  listVehicles: () => request<Vehicle[]>("/api/vehicles"),
  listGeofences: () => request<Geofence[]>("/api/geofences"),
  listAlerts: (limit = 50) => request<Alert[]>(`/api/alerts?limit=${limit}`),
  createGeofence: (payload: { name: string; color: string; coordinates: [number, number][] }) =>
    request<Geofence>("/api/geofences", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteGeofence: (id: number) => request<void>(`/api/geofences/${id}`, { method: "DELETE" }),
};
