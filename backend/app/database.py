import asyncio
import logging

import asyncpg

from app.config import settings

logger = logging.getLogger("gis.database")


async def create_pool(max_attempts: int = 8) -> asyncpg.Pool:
    """Create the asyncpg pool, retrying while Postgres finishes starting up."""
    delay = 1.0
    for attempt in range(1, max_attempts + 1):
        try:
            pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
            logger.info("Connected to database (attempt %d)", attempt)
            return pool
        except (OSError, asyncpg.PostgresError) as exc:
            if attempt == max_attempts:
                raise
            logger.warning("Database not ready (attempt %d/%d): %s", attempt, max_attempts, exc)
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 10)
    raise RuntimeError("unreachable")
