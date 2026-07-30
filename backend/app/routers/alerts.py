from fastapi import APIRouter, Query, Request

from app.schemas import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
    vehicle_id: int | None = None,
    geofence_id: int | None = None,
) -> list[AlertOut]:
    pool = request.app.state.db_pool
    rows = await pool.fetch(
        """
        SELECT a.id, a.vehicle_id, v.name AS vehicle_name,
               a.geofence_id, g.name AS geofence_name,
               a.event_type, ST_X(a.geom) AS lon, ST_Y(a.geom) AS lat,
               a.occurred_at
        FROM alert_events a
        JOIN vehicles v ON v.id = a.vehicle_id
        JOIN geofences g ON g.id = a.geofence_id
        WHERE ($1::int IS NULL OR a.vehicle_id = $1)
          AND ($2::int IS NULL OR a.geofence_id = $2)
        ORDER BY a.occurred_at DESC
        LIMIT $3
        """,
        vehicle_id,
        geofence_id,
        limit,
    )
    return [AlertOut(**dict(row)) for row in rows]
