import json

from fastapi import APIRouter, HTTPException, Request, Response

from app.geofence_engine import engine as geofence_engine
from app.schemas import GeofenceCreate, GeofenceOut
from app.ws_manager import manager

router = APIRouter(prefix="/api/geofences", tags=["geofences"])


def _row_to_geofence(row) -> GeofenceOut:
    geojson = json.loads(row["geojson"])
    return GeofenceOut(
        id=row["id"],
        name=row["name"],
        color=row["color"],
        coordinates=geojson["coordinates"][0],
        created_at=row["created_at"],
    )


@router.get("", response_model=list[GeofenceOut])
async def list_geofences(request: Request) -> list[GeofenceOut]:
    pool = request.app.state.db_pool
    rows = await pool.fetch(
        "SELECT id, name, color, ST_AsGeoJSON(geom) AS geojson, created_at FROM geofences ORDER BY id"
    )
    return [_row_to_geofence(row) for row in rows]


@router.post("", response_model=GeofenceOut, status_code=201)
async def create_geofence(request: Request, payload: GeofenceCreate) -> GeofenceOut:
    coords = [list(pt) for pt in payload.coordinates]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    if len(coords) < 4:
        raise HTTPException(status_code=422, detail="A polygon needs at least 3 distinct points")

    geojson = json.dumps({"type": "Polygon", "coordinates": [coords]})
    pool = request.app.state.db_pool
    row = await pool.fetchrow(
        """
        INSERT INTO geofences (name, color, geom)
        VALUES ($1, $2, ST_SetSRID(ST_GeomFromGeoJSON($3), 4326))
        RETURNING id, name, color, ST_AsGeoJSON(geom) AS geojson, created_at
        """,
        payload.name,
        payload.color,
        geojson,
    )
    await geofence_engine.reload_cache()
    result = _row_to_geofence(row)
    await manager.broadcast({"type": "geofence_created", "geofence": result.model_dump(mode="json")})
    return result


@router.delete("/{geofence_id}", status_code=204)
async def delete_geofence(request: Request, geofence_id: int) -> Response:
    pool = request.app.state.db_pool
    deleted = await pool.fetchval("DELETE FROM geofences WHERE id = $1 RETURNING id", geofence_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Geofence not found")
    geofence_engine.forget_geofence(geofence_id)
    await manager.broadcast({"type": "geofence_deleted", "geofence_id": geofence_id})
    return Response(status_code=204)
