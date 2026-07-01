"""Shared API envelope models aligned with docs/api-contracts.md."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiEnvelope(BaseModel, Generic[T]):
    code: int
    message: str
    data: T | None
