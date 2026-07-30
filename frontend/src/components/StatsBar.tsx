import { useStore } from "../store";

const STATUS_LABEL: Record<string, string> = {
  connecting: "Connecting...",
  connected: "Live",
  disconnected: "Reconnecting...",
};

export default function StatsBar() {
  const vehicleCount = useStore((s) => s.vehicles.size);
  const geofenceCount = useStore((s) => s.geofences.size);
  const alertCount = useStore((s) => s.alerts.length);
  const status = useStore((s) => s.connectionStatus);

  return (
    <header className="stats-bar">
      <div className="brand">
        <span className="brand-title">Live Fleet Tracker</span>
        <span className="brand-sub">Real-time GIS data engineering demo</span>
      </div>
      <div className="stats">
        <div className="stat">
          <span className="stat-value">{vehicleCount}</span>
          <span className="stat-label">Vehicles</span>
        </div>
        <div className="stat">
          <span className="stat-value">{geofenceCount}</span>
          <span className="stat-label">Geofences</span>
        </div>
        <div className="stat">
          <span className="stat-value">{alertCount}</span>
          <span className="stat-label">Alerts</span>
        </div>
        <div className={`status-pill status-${status}`}>
          <span className="status-dot" />
          {STATUS_LABEL[status]}
        </div>
      </div>
    </header>
  );
}
