"""Authentication API models aligned with docs/api-contracts.md."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class UserRead(BaseModel):
    id: str
    name: str
    username: str
    created_at: str


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponseData(BaseModel):
    access_token: str
    token_type: Literal["Bearer"]
    expires_in: int
    user: UserRead


class AuthMeResponseData(BaseModel):
    user: UserRead


class LogoutRequest(BaseModel):
    access_token: str = Field(..., min_length=1)


class LogoutResponseData(BaseModel):
    logged_out: bool
