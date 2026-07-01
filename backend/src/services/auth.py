"""Authentication service for the MVP employee login flow."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from src.core.security import verify_password
from src.db.models import User
from src.models.auth import UserRead
from src.repositories.user import UserRepository

ACCESS_TOKEN_EXPIRES_SECONDS = 86_400
CHINA_STANDARD_TIME = timezone(timedelta(hours=8))

_ACTIVE_TOKENS: dict[str, str] = {}


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def authenticate(self, username: str, password: str) -> tuple[str, User] | None:
        user = await self.user_repo.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            return None

        token = _create_access_token()
        _ACTIVE_TOKENS[token] = user.id
        return token, user

    async def get_user_by_token(self, access_token: str) -> User | None:
        user_id = _ACTIVE_TOKENS.get(access_token)
        if user_id is None:
            return None
        return await self.user_repo.get_by_id(user_id)

    async def logout(self, access_token: str) -> bool:
        return _ACTIVE_TOKENS.pop(access_token, None) is not None


def to_user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        name=user.name,
        username=user.username,
        created_at=_format_datetime(user.created_at),
    )


def reset_token_store() -> None:
    _ACTIVE_TOKENS.clear()


def _create_access_token() -> str:
    while True:
        token = token_urlsafe(32)
        if token not in _ACTIVE_TOKENS:
            return token


def _format_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=CHINA_STANDARD_TIME)
    else:
        value = value.astimezone(CHINA_STANDARD_TIME)
    return value.isoformat()
