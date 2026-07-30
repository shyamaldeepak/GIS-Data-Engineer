import asyncio
import logging
import math
import random
from dataclasses import dataclass, field

from app.config import settings
from app.geofence_engine import engine as geofence_engine
from app.ws_manager import manager

logger = logging.getLogger("gis.simulator")

VEHICLE_TYPES = ["car", "van", "truck", "motorcycle"]
COLORS = ["#3388ff", "#ff8833", "#33cc66", "#cc33ff", "#ffcc00", "#00cccc"]

GRID_SIZE = 8  # 8x8 node grid -> road-like paths without needing real OSM data
POSITION_INSERT_EVERY_N_TICKS = 3  # throttle time-series inserts


def _haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _bearing_degrees(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlambda)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def build_grid(bbox: tuple[float, float, float, float], size: int = GRID_SIZE):
    """Synthetic grid graph over the bounding box: gives vehicles road-like
    straight-line movement between intersections without needing a real
    road network / external map data."""
    min_lon, min_lat, max_lon, max_lat = bbox
    nodes: list[tuple[float, float]] = []
    for row in range(size):
        for col in range(size):
            lon = min_lon + (max_lon - min_lon) * col / (size - 1)
            lat = min_lat + (max_lat - min_lat) * row / (size - 1)
            nodes.append((lon, lat))

    adjacency: dict[int, list[int]] = {i: [] for i in range(len(nodes))}
    for row in range(size):
        for col in range(size):
            idx = row * size + col
            if col + 1 < size:
                adjacency[idx].append(idx + 1)
                adjacency[idx + 1].append(idx)
            if row + 1 < size:
                adjacency[idx].append(idx + size)
                adjacency[idx + size].append(idx)
    return nodes, adjacency


@dataclass
class SimVehicle:
    id: int
    name: str
    vehicle_type: str
    color: str
    current_node: int
    target_node: int
    progress: float = 0.0  # 0..1 along the current edge
    speed_kmh: float = field(default_factory=lambda: random.uniform(30, 80))
    tick_count: int = 0


class Simulator:
    def __init__(self) -> None:
        self._pool = None
        self._nodes: list[tuple[float, float]] = []
        self._adjacency: dict[int, list[int]] = {}
        self._vehicles: list[SimVehicle] = []
        self._running = False

    def bind(self, pool) -> None:
        self._pool = pool

    async def _seed_vehicles(self) -> None:
        # Fresh fleet on every boot keeps the demo simple and avoids
        # reconciling stale state against a persisted volume.
        await self._pool.execute("DELETE FROM vehicles")
        self._vehicles = []
        for i in range(settings.sim_vehicle_count):
            start = random.randrange(len(self._nodes))
            target = random.choice(self._adjacency[start])
            name = f"Fleet-{i + 1:02d}"
            vehicle_type = random.choice(VEHICLE_TYPES)
            color = random.choice(COLORS)
            lon, lat = self._nodes[start]
            row = await self._pool.fetchrow(
                """
                INSERT INTO vehicles (name, vehicle_type, color, current_geom, heading_degrees, speed_kmh, status)
                VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326), 0, 0, 'active')
                RETURNING id
                """,
                name,
                vehicle_type,
                color,
                lon,
                lat,
            )
            self._vehicles.append(
                SimVehicle(
                    id=row["id"],
                    name=name,
                    vehicle_type=vehicle_type,
                    color=color,
                    current_node=start,
                    target_node=target,
                )
            )
        logger.info("Seeded %d simulated vehicles", len(self._vehicles))

    def _advance(self, v: SimVehicle, tick_seconds: float) -> tuple[float, float, float]:
        lon1, lat1 = self._nodes[v.current_node]
        lon2, lat2 = self._nodes[v.target_node]
        edge_km = max(_haversine_km(lon1, lat1, lon2, lat2), 0.001)

        v.speed_kmh = max(15.0, min(90.0, v.speed_kmh + random.uniform(-5, 5)))
        step = (v.speed_kmh * (tick_seconds / 3600)) / edge_km
        v.progress += step

        while v.progress >= 1.0:
            v.progress -= 1.0
            v.current_node = v.target_node
            candidates = [n for n in self._adjacency[v.current_node] if n != v.target_node]
            v.target_node = random.choice(candidates or self._adjacency[v.current_node])
            lon1, lat1 = self._nodes[v.current_node]
            lon2, lat2 = self._nodes[v.target_node]
            edge_km = max(_haversine_km(lon1, lat1, lon2, lat2), 0.001)

        lon = lon1 + (lon2 - lon1) * v.progress
        lat = lat1 + (lat2 - lat1) * v.progress
        heading = _bearing_degrees(lon1, lat1, lon2, lat2)
        return lon, lat, heading

    async def run(self) -> None:
        self._nodes, self._adjacency = build_grid(settings.bbox)
        await self._seed_vehicles()
        await geofence_engine.reload_cache()
        await geofence_engine.init_state_from_db()

        self._running = True
        tick_seconds = settings.sim_tick_seconds
        tick_number = 0
        while self._running:
            tick_number += 1
            batch = []
            for v in self._vehicles:
                lon, lat, heading = self._advance(v, tick_seconds)
                v.tick_count += 1

                await self._pool.execute(
                    """
                    UPDATE vehicles
                    SET current_geom = ST_SetSRID(ST_MakePoint($1, $2), 4326),
                        heading_degrees = $3,
                        speed_kmh = $4,
                        last_seen = now()
                    WHERE id = $5
                    """,
                    lon,
                    lat,
                    heading,
                    v.speed_kmh,
                    v.id,
                )

                if v.tick_count % POSITION_INSERT_EVERY_N_TICKS == 0:
                    await self._pool.execute(
                        """
                        INSERT INTO positions (vehicle_id, geom, speed_kmh, heading_degrees)
                        VALUES ($1, ST_SetSRID(ST_MakePoint($2, $3), 4326), $4, $5)
                        """,
                        v.id,
                        lon,
                        lat,
                        v.speed_kmh,
                        heading,
                    )

                await geofence_engine.check(v.id, v.name, lon, lat)

                batch.append(
                    {
                        "id": v.id,
                        "name": v.name,
                        "vehicle_type": v.vehicle_type,
                        "color": v.color,
                        "lat": lat,
                        "lon": lon,
                        "heading_degrees": heading,
                        "speed_kmh": round(v.speed_kmh, 1),
                    }
                )

            await manager.broadcast({"type": "tick", "vehicles": batch})
            await asyncio.sleep(tick_seconds)

    def stop(self) -> None:
        self._running = False


simulator = Simulator()
