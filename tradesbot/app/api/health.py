"""
Health check endpoint — verifies all services are alive.
"""
from fastapi import APIRouter
import redis.asyncio as aioredis
from app.config import get_settings
from app.models.schemas import HealthResponse
from app.models.database import engine
from app.utils.logger import get_logger
from sqlalchemy import text

log = get_logger("health")
router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health of all dependent services."""
    services = {}

    # Check PostgreSQL
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        services["database"] = "healthy"
    except Exception as e:
        services["database"] = f"unhealthy: {e}"

    # Check Redis
    try:
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        await r.aclose()
        services["redis"] = "healthy"
    except Exception as e:
        services["redis"] = f"unhealthy: {e}"

    overall = "ok" if all(v == "healthy" for v in services.values()) else "degraded"

    return HealthResponse(status=overall, version="0.1.0", services=services)
