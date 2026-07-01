"""Account settings API models aligned with docs/api-contracts.md."""

from __future__ import annotations

from pydantic import BaseModel

from src.models.auth import UserRead


class SystemSettingsRead(BaseModel):
    database: str
    model_provider: str
    chat_model: str
    embedding_model: str
    embedding_dimensions: int
    api_key_configured: bool


class AccountSettingsResponseData(BaseModel):
    user: UserRead
    system: SystemSettingsRead
