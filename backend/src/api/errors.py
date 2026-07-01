"""Exception handlers that keep the public API envelope consistent."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pycore.core import get_logger
from starlette.exceptions import HTTPException as StarletteHTTPException


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)


async def _http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    del request
    return _error_response(exc.status_code, _detail_to_message(exc.detail, "请求失败"))


async def _validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    get_logger().warning("Request validation failed", path=request.url.path, detail=exc.errors())
    return _error_response(400, "参数错误")


async def _unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    get_logger().exception("Unhandled API exception", path=request.url.path, error_msg=str(exc))
    return _error_response(500, "服务不可用")


def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": status_code,
            "message": message,
            "data": None,
        },
    )


def _detail_to_message(detail: Any, fallback: str) -> str:
    if isinstance(detail, str) and detail:
        return detail
    return fallback
