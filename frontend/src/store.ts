import { create } from "zustand";
import type { Alert, ConnectionStatus, Geofence, Vehicle } from "./types";

interface State {
  vehicles: Map<number, Vehicle>;
  geofences: Map<number, Geofence>;
  alerts: Alert[];
  connectionStatus: ConnectionStatus;
  selectedVehicleId: number | null;

  setConnectionStatus: (status: ConnectionStatus) => void;
  applySnapshot: (vehicles: Vehicle[], geofences: Geofence[], alerts: Alert[]) => void;
  applyTick: (vehicles: Vehicle[]) => void;
  addAlert: (alert: Alert) => void;
  addGeofence: (geofence: Geofence) => void;
  removeGeofence: (id: number) => void;
  setGeofences: (geofences: Geofence[]) => void;
  selectVehicle: (id: number | null) => void;
}

export const useStore = create<State>((set) => ({
  vehicles: new Map(),
  geofences: new Map(),
  alerts: [],
  connectionStatus: "connecting",
  selectedVehicleId: null,

  setConnectionStatus: (status) => set({ connectionStatus: status }),

  applySnapshot: (vehicles, geofences, alerts) =>
    set({
      vehicles: new Map(vehicles.map((v) => [v.id, v])),
      geofences: new Map(geofences.map((g) => [g.id, g])),
      alerts,
    }),

  applyTick: (vehicles) =>
    set((state) => {
      const next = new Map(state.vehicles);
      for (const v of vehicles) next.set(v.id, v);
      return { vehicles: next };
    }),

  addAlert: (alert) =>
    set((state) => ({ alerts: [alert, ...state.alerts].slice(0, 100) })),

  addGeofence: (geofence) =>
    set((state) => {
      const next = new Map(state.geofences);
      next.set(geofence.id, geofence);
      return { geofences: next };
    }),

  removeGeofence: (id) =>
    set((state) => {
      const next = new Map(state.geofences);
      next.delete(id);
      return { geofences: next };
    }),

  setGeofences: (geofences) => set({ geofences: new Map(geofences.map((g) => [g.id, g])) }),

  selectVehicle: (id) => set({ selectedVehicleId: id }),
}));
