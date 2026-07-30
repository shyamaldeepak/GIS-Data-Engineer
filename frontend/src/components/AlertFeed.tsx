import { useStore } from "../store";

function timeAgo(iso: string): string {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.floor(minutes / 60)}h ago`;
}

export default function AlertFeed() {
  const alerts = useStore((s) => s.alerts);

  return (
    <section className="alert-feed">
      <h2 className="panel-title">Live Alerts</h2>
      <ul className="alert-list">
        {alerts.map((a) => (
          <li key={a.id} className={`alert-row alert-${a.event_type}`}>
            <span className="alert-badge">{a.event_type === "enter" ? "IN" : "OUT"}</span>
            <span className="alert-text">
              <strong>{a.vehicle_name}</strong> {a.event_type === "enter" ? "entered" : "exited"}{" "}
              <strong>{a.geofence_name}</strong>
            </span>
            <span className="alert-time">{timeAgo(a.occurred_at)}</span>
          </li>
        ))}
        {alerts.length === 0 && <li className="alert-empty">No geofence activity yet.</li>}
      </ul>
    </section>
  );
}
