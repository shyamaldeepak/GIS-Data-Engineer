import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_pool
from app.geofence_engine import engine as geofence_engine
from app.routers import alerts, geofences, health, vehicles, ws
from app.simulator import simulator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("gis.main")


async def _retention_loop(pool) -> None:
    """Purge time-series positions older than POSITION_RETENTION_HOURS, hourly."""
    while True:
        await asyncio.sleep(3600)
        try:
            deleted = await pool.fetchval(
                "WITH d AS (DELETE FROM positions "
                "WHERE recorded_at < now() - ($1 || ' hours')::interval RETURNING 1) "
                "SELECT count(*) FROM d",
                str(settings.position_retention_hours),
            )
            logger.info("Retention sweep: purged %s old position rows", deleted)
        except Exception:
            logger.exception("Retention sweep failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await create_pool()
    app.state.db_pool = pool
    geofence_engine.bind(pool)
    simulator.bind(pool)

    app.state.simulator_task = asyncio.create_task(simulator.run())
    app.state.retention_task = asyncio.create_task(_retention_loop(pool))

    logger.info("Startup complete: simulator running with %d vehicles", settings.sim_vehicle_count)
    try:
        yield
    finally:
        simulator.stop()
        app.state.simulator_task.cancel()
        app.state.retention_task.cancel()
        await pool.close()


app = FastAPI(title="Real-Time GIS Fleet Tracking Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(vehicles.router)
app.include_router(geofences.router)
app.include_router(alerts.router)
app.include_router(ws.router)
