import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/live")
async def ws_live(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    pool = websocket.app.state.db_pool
    try:
        vehicle_rows = await pool.fetch(
            """
            SELECT id, name, vehicle_type, color,
                   ST_X(current_geom) AS lon, ST_Y(current_geom) AS lat,
                   heading_degrees, speed_kmh
            FROM vehicles
            """
        )
        geofence_rows = await pool.fetch(
            "SELECT id, name, color, ST_AsGeoJSON(geom) AS geojson FROM geofences"
        )
        alert_rows = await pool.fetch(
            """
            SELECT a.id, a.vehicle_id, v.name AS vehicle_name,
                   a.geofence_id, g.name AS geofence_name,
                   a.event_type, ST_X(a.geom) AS lon, ST_Y(a.geom) AS lat, a.occurred_at
            FROM alert_events a
            JOIN vehicles v ON v.id = a.vehicle_id
            JOIN geofences g ON g.id = a.geofence_id
            ORDER BY a.occurred_at DESC
            LIMIT 20
            """
        )

        snapshot = {
            "type": "snapshot",
            "vehicles": [dict(row) for row in vehicle_rows],
            "geofences": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "color": row["color"],
                    "coordinates": json.loads(row["geojson"])["coordinates"][0],
                }
                for row in geofence_rows
            ],
            "alerts": [dict(row) for row in alert_rows],
        }
        await websocket.send_text(json.dumps(snapshot, default=str))

        while True:
            # Client doesn't need to send anything; this just keeps the
            # connection open and detects disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
