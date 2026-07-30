export interface Vehicle {
  id: number;
  name: string;
  vehicle_type: string;
  color: string;
  lat: number;
  lon: number;
  heading_degrees: number;
  speed_kmh: number;
}

export interface Geofence {
  id: number;
  name: string;
  color: string;
  coordinates: [number, number][];
}

export interface Alert {
  id: number;
  vehicle_id: number;
  vehicle_name: string;
  geofence_id: number;
  geofence_name: string;
  event_type: "enter" | "exit";
  lat: number;
  lon: number;
  occurred_at: string;
}

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

export type ServerMessage =
  | { type: "snapshot"; vehicles: Vehicle[]; geofences: Geofence[]; alerts: Alert[] }
  | { type: "tick"; vehicles: Vehicle[] }
  | ({ type: "alert" } & Alert)
  | { type: "geofence_created"; geofence: Geofence }
  | { type: "geofence_deleted"; geofence_id: number };
