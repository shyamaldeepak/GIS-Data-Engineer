from fastapi import APIRouter, Query, Request

from app.schemas import TrailOut, TrailPoint, VehicleOut

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleOut])
async def list_vehicles(request: Request) -> list[VehicleOut]:
    pool = request.app.state.db_pool
    rows = await pool.fetch(
        """
        SELECT id, name, vehicle_type, color, status,
               ST_X(current_geom) AS lon, ST_Y(current_geom) AS lat,
               heading_degrees, speed_kmh, last_seen
        FROM vehicles
        ORDER BY id
        """
    )
    return [VehicleOut(**dict(row)) for row in rows]


@router.get("/{vehicle_id}/trail", response_model=TrailOut)
async def vehicle_trail(
    request: Request, vehicle_id: int, minutes: int = Query(default=10, ge=1, le=1440)
) -> TrailOut:
    pool = request.app.state.db_pool
    rows = await pool.fetch(
        """
        SELECT ST_X(geom) AS lon, ST_Y(geom) AS lat, speed_kmh, heading_degrees, recorded_at
        FROM positions
        WHERE vehicle_id = $1 AND recorded_at >= now() - ($2 || ' minutes')::interval
        ORDER BY recorded_at ASC
        """,
        vehicle_id,
        str(minutes),
    )
    return TrailOut(
        vehicle_id=vehicle_id,
        points=[TrailPoint(**dict(row)) for row in rows],
    )
