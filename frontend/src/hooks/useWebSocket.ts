import { useEffect } from "react";
import { LiveSocket } from "../api/websocket";
import { useStore } from "../store";

function wsUrl(): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/live`;
}

export function useLiveWebSocket(): void {
  useEffect(() => {
    const { applySnapshot, applyTick, addAlert, addGeofence, removeGeofence, setConnectionStatus } =
      useStore.getState();

    const socket = new LiveSocket(
      wsUrl(),
      (message) => {
        switch (message.type) {
          case "snapshot":
            applySnapshot(message.vehicles, message.geofences, message.alerts);
            break;
          case "tick":
            applyTick(message.vehicles);
            break;
          case "alert":
            addAlert(message);
            break;
          case "geofence_created":
            addGeofence(message.geofence);
            break;
          case "geofence_deleted":
            removeGeofence(message.geofence_id);
            break;
        }
      },
      setConnectionStatus,
    );

    socket.connect();
    return () => socket.close();
  }, []);
}
