"""FastAPI application entrypoint built on PyCore APIServer."""

from __future__ import annotations

from fastapi import FastAPI
from pycore.api import APIConfig, APIServer, RequestContextMiddleware
from pycore.core import Logger, LoggerConfig, LogLevel, get_logger
from starlette.routing import BaseRoute

from src.api.errors import register_exception_handlers
from src.core.config import AppSettings, get_settings


def create_api_server() -> APIServer:
    settings = get_settings()
    _configure_logging(settings)
    from src.api.routes.assistant import router as assistant_router
    from src.api.routes.auth import router as auth_router
    from src.api.routes.dashboard import router as dashboard_router
    from src.api.routes.documents import router as documents_router
    from src.api.routes.health import router as health_router
    from src.api.routes.knowledge import router as knowledge_router
    from src.api.routes.settings import router as settings_router
    from src.api.routes.tickets import router as tickets_router

    server = APIServer(
        APIConfig(
            title="Customer Service Bot API",
            description="Backend API for the customer service bot MVP.",
            version="0.1.0",
            debug=settings.debug,
            host=settings.host,
            port=settings.port,
            cors_enabled=True,
            cors_origins=settings.cors_origins,
            cors_methods=settings.cors_methods,
            cors_headers=settings.cors_headers,
        )
    )

    app_instance = server.app
    _remove_pycore_default_health(app_instance)
    app_instance.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app_instance)
    server.include_router(health_router)
    server.include_router(auth_router)
    server.include_router(dashboard_router)
    server.include_router(assistant_router)
    server.include_router(settings_router)
    server.include_router(tickets_router)
    server.include_router(knowledge_router)
    server.include_router(documents_router)
    get_logger().info("API application configured", service=settings.service_name)
    return server


def _configure_logging(settings: AppSettings) -> None:
    Logger.configure(
        LoggerConfig(
            level=LogLevel.DEBUG if settings.debug else LogLevel.INFO,
            log_dir=settings.log_dir,
            file_enabled=settings.log_file_enabled,
            app_name=settings.service_name,
        )
    )


def _remove_pycore_default_health(app_instance: FastAPI) -> None:
    app_instance.router.routes = [
        route
        for route in app_instance.router.routes
        if not _is_pycore_default_health(route)
    ]


def _is_pycore_default_health(route: BaseRoute) -> bool:
    methods: set[str] = set(getattr(route, "methods", ()))
    return (
        getattr(route, "path", None) == "/health"
        and "GET" in methods
        and getattr(route, "name", None) == "health_check"
    )


api_server = create_api_server()
app = api_server.app
