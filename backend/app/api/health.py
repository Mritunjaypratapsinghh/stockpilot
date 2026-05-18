"""Health check endpoint — DB + Redis connectivity."""

from fastapi import APIRouter
from ..core.database import get_database
from ..services.cache import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Liveness + readiness probe. Returns component status."""
    checks = {"status": "healthy", "db": "ok", "redis": "ok"}

    # MongoDB
    try:
        db = get_database()
        await db.command("ping")
    except Exception as e:
        checks["db"] = f"error: {str(e)[:50]}"
        checks["status"] = "degraded"

    # Redis
    try:
        r = await get_redis()
        await r.ping()
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:50]}"
        checks["status"] = "degraded"

    status_code = 200 if checks["status"] == "healthy" else 503
    return checks
