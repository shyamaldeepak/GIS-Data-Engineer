import { useStore } from "../store";

const TYPE_ICON: Record<string, string> = {
  car: "🚗",
  van: "🚐",
  truck: "🚚",
  motorcycle: "🏍️",
};

export default function Sidebar() {
  const vehicles = useStore((s) => [...s.vehicles.values()].sort((a, b) => a.name.localeCompare(b.name)));
  const selectedId = useStore((s) => s.selectedVehicleId);
  const selectVehicle = useStore((s) => s.selectVehicle);

  return (
    <aside className="sidebar">
      <h2 className="panel-title">Fleet ({vehicles.length})</h2>
      <ul className="vehicle-list">
        {vehicles.map((v) => (
          <li
            key={v.id}
            className={`vehicle-row ${selectedId === v.id ? "vehicle-row-selected" : ""}`}
            onClick={() => selectVehicle(v.id)}
          >
            <span className="vehicle-dot" style={{ background: v.color }} />
            <span className="vehicle-icon">{TYPE_ICON[v.vehicle_type] ?? "🚗"}</span>
            <span className="vehicle-name">{v.name}</span>
            <span className="vehicle-speed">{Math.round(v.speed_kmh)} km/h</span>
          </li>
        ))}
        {vehicles.length === 0 && <li className="vehicle-empty">Waiting for fleet data...</li>}
      </ul>
    </aside>
  );
}
