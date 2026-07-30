from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health(request: Request) -> HealthOut:
    pool = request.app.state.db_pool
    db_status = "unknown"
    try:
        await pool.fetchval("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"

    sim_status = "running" if getattr(request.app.state, "simulator_task", None) else "stopped"

    return HealthOut(
        status="ok",
        db=db_status,
        simulator=sim_status,
        timestamp=datetime.now(timezone.utc),
    )
