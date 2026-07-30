import AlertFeed from "./components/AlertFeed";
import MapView from "./components/MapView";
import Sidebar from "./components/Sidebar";
import StatsBar from "./components/StatsBar";
import { useLiveWebSocket } from "./hooks/useWebSocket";

export default function App() {
  useLiveWebSocket();

  return (
    <div className="app-shell">
      <StatsBar />
      <div className="app-body">
        <Sidebar />
        <MapView />
        <AlertFeed />
      </div>
    </div>
  );
}
