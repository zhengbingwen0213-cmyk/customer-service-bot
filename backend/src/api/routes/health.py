"""Health check route."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pycore.api import APIRouter
from pydantic import BaseModel

from src.core.config import get_settings
from src.models.common import ApiEnvelope

router = APIRouter(tags=["health"])
CHINA_STANDARD_TIME = timezone(timedelta(hours=8))


class HealthData(BaseModel):
    status: str
    service: str
    time: str


@router.get("/health", response_model=ApiEnvelope[HealthData])
async def get_health() -> ApiEnvelope[HealthData]:
    settings = get_settings()
    return ApiEnvelope(
        code=200,
        message="success",
        data=HealthData(
            status="ok",
            service=settings.service_name,
            time=datetime.now(CHINA_STANDARD_TIME).isoformat(),
        ),
    )
