from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health & Status"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe endpoint."""
    return HealthResponse(
        status="ok",
        environment=settings.APP_ENV,
        database="unknown",
        redis="unknown",
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness probe checking database connectivity."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        environment=settings.APP_ENV,
        database=db_status,
        redis="connected",
    )
