"""Authentication routes."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from pycore.api import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.models.auth import (
    AuthMeResponseData,
    LoginRequest,
    LoginResponseData,
    LogoutRequest,
    LogoutResponseData,
)
from src.models.common import ApiEnvelope
from src.repositories.user import UserRepository
from src.services.auth import ACCESS_TOKEN_EXPIRES_SECONDS, AuthService, to_user_read

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=ApiEnvelope[LoginResponseData])
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[LoginResponseData]:
    auth_service = AuthService(UserRepository(db))
    authenticated = await auth_service.authenticate(payload.username, payload.password)
    if authenticated is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    access_token, user = authenticated
    return ApiEnvelope(
        code=200,
        message="success",
        data=LoginResponseData(
            access_token=access_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRES_SECONDS,
            user=to_user_read(user),
        ),
    )


@router.get("/me", response_model=ApiEnvelope[AuthMeResponseData])
async def get_me(
    current_user: User = Depends(get_current_user),
) -> ApiEnvelope[AuthMeResponseData]:
    return ApiEnvelope(
        code=200,
        message="success",
        data=AuthMeResponseData(user=to_user_read(current_user)),
    )


@router.post("/logout", response_model=ApiEnvelope[LogoutResponseData])
async def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[LogoutResponseData]:
    del current_user
    auth_service = AuthService(UserRepository(db))
    if not await auth_service.logout(payload.access_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效",
        )

    return ApiEnvelope(
        code=200,
        message="success",
        data=LogoutResponseData(logged_out=True),
    )
