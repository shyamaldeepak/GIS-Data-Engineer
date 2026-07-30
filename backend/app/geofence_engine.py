import asyncio
import json
import logging

from shapely.geometry import Point, shape

from app.ws_manager import manager

logger = logging.getLogger("gis.geofence")


class GeofenceEngine:
    """In-memory Shapely cache for geofence containment checks.

    Containment is checked in-process against a cached polygon set instead
    of hitting Postgres per vehicle per simulator tick, which would not
    scale for a real-time loop. The DB stays the source of truth; this is
    a read-through cache refreshed on create/delete.
    """

    def __init__(self) -> None:
        self._pool = None
        self._polygons: dict[int, dict] = {}  # geofence_id -> {"name", "shape"}
        self._state: dict[tuple[int, int], bool] = {}  # (vehicle_id, geofence_id) -> inside?
        self._lock = asyncio.Lock()

    def bind(self, pool) -> None:
        self._pool = pool

    async def reload_cache(self) -> None:
        async with self._lock:
            rows = await self._pool.fetch(
                "SELECT id, name, ST_AsGeoJSON(geom) AS geojson FROM geofences"
            )
            self._polygons = {
                row["id"]: {"name": row["name"], "shape": shape(json.loads(row["geojson"]))}
                for row in rows
            }

    async def init_state_from_db(self) -> None:
        """Seed enter/exit state from real DB containment so a vehicle that
        already sits inside a fence at startup doesn't fire a spurious 'enter'.
        """
        vehicles = await self._pool.fetch(
            "SELECT id, ST_X(current_geom) AS lon, ST_Y(current_geom) AS lat "
            "FROM vehicles WHERE current_geom IS NOT NULL"
        )
        for v in vehicles:
            point = Point(v["lon"], v["lat"])
            for gid, entry in self._polygons.items():
                self._state[(v["id"], gid)] = entry["shape"].contains(point)

    async def check(self, vehicle_id: int, vehicle_name: str, lon: float, lat: float) -> None:
        if not self._polygons:
            return
        point = Point(lon, lat)
        for gid, entry in list(self._polygons.items()):
            key = (vehicle_id, gid)
            was_inside = self._state.get(key, False)
            is_inside = entry["shape"].contains(point)
            if is_inside == was_inside:
                continue
            self._state[key] = is_inside
            event_type = "enter" if is_inside else "exit"
            row = await self._pool.fetchrow(
                """
                INSERT INTO alert_events (vehicle_id, geofence_id, event_type, geom)
                VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326))
                RETURNING id, occurred_at
                """,
                vehicle_id,
                gid,
                event_type,
                lon,
                lat,
            )
            await manager.broadcast(
                {
                    "type": "alert",
                    "id": row["id"],
                    "vehicle_id": vehicle_id,
                    "vehicle_name": vehicle_name,
                    "geofence_id": gid,
                    "geofence_name": entry["name"],
                    "event_type": event_type,
                    "lat": lat,
                    "lon": lon,
                    "occurred_at": row["occurred_at"],
                }
            )
            logger.info("Vehicle %s %s geofence %s", vehicle_name, event_type, entry["name"])

    def forget_geofence(self, geofence_id: int) -> None:
        self._polygons.pop(geofence_id, None)
        for key in [k for k in self._state if k[1] == geofence_id]:
            self._state.pop(key, None)


engine = GeofenceEngine()
