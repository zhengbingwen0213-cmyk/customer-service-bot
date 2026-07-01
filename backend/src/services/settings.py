"""Account settings service."""

from __future__ import annotations

from src.core.config import get_settings
from src.db.models import User
from src.models.settings import AccountSettingsResponseData, SystemSettingsRead
from src.services.auth import to_user_read


class SettingsService:
    def get_account_settings(self, user: User) -> AccountSettingsResponseData:
        settings = get_settings()
        return AccountSettingsResponseData(
            user=to_user_read(user),
            system=SystemSettingsRead(
                database="SQLite",
                model_provider="百炼",
                chat_model=settings.bailian_chat_model,
                embedding_model=settings.bailian_embedding_model,
                embedding_dimensions=settings.bailian_embedding_dimensions,
                api_key_configured=bool(settings.dashscope_api_key),
            ),
        )
