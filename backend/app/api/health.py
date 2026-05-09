from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.schemas.scan import HealthCheckResponse


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
def health() -> JSONResponse:
    postgres_status = "healthy"
    redis_status = "healthy"

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        postgres_status = "unhealthy"

    try:
        Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1).ping()
    except Exception:
        redis_status = "unhealthy"

    overall = "healthy" if postgres_status == redis_status == "healthy" else "degraded"
    status_code = status.HTTP_200_OK if overall == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={"status": overall, "api": "healthy", "postgres": postgres_status, "redis": redis_status},
    )

