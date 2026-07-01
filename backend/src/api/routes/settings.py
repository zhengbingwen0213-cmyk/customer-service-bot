"""Account settings routes."""

from __future__ import annotations

from fastapi import Depends
from pycore.api import APIRouter

from src.api.deps import get_current_user
from src.db.models import User
from src.models.common import ApiEnvelope
from src.models.settings import AccountSettingsResponseData
from src.services.settings import SettingsService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/account", response_model=ApiEnvelope[AccountSettingsResponseData])
async def get_account_settings(
    current_user: User = Depends(get_current_user),
) -> ApiEnvelope[AccountSettingsResponseData]:
    return ApiEnvelope(
        code=200,
        message="success",
        data=SettingsService().get_account_settings(current_user),
    )
