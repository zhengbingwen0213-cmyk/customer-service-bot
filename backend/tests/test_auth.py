from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.api.deps import get_db
from src.db.models import Base
from src.db.schema import create_fts5_indexes
from src.db.seed import seed_demo_data
from src.main import app
from src.services.auth import reset_token_store


def test_auth_and_settings_real_flow_uses_isolated_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "auth_flow_test.db"
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            yield session

    try:
        asyncio.run(_setup_database(test_engine, session_factory))
        reset_token_store()
        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as client:
            invalid_login = client.post(
                "/api/auth/login",
                json={"username": "agent01", "password": "wrong-password"},
            )
            assert invalid_login.status_code == 401
            assert invalid_login.json() == {
                "code": 401,
                "message": "用户名或密码错误",
                "data": None,
            }

            missing_auth = client.get("/api/auth/me")
            assert missing_auth.status_code == 401
            assert missing_auth.json() == {
                "code": 401,
                "message": "登录状态已失效",
                "data": None,
            }

            login = client.post(
                "/api/auth/login",
                json={"username": "agent01", "password": "password123"},
            )
            assert login.status_code == 200
            login_body = login.json()
            assert login_body["code"] == 200
            assert login_body["message"] == "success"
            assert login_body["data"]["token_type"] == "Bearer"
            assert login_body["data"]["expires_in"] == 86400
            assert login_body["data"]["user"] == {
                "id": "user_001",
                "name": "客服一组员工",
                "username": "agent01",
                "created_at": "2026-05-23T09:00:00+08:00",
            }

            token = str(login_body["data"]["access_token"])
            headers = {"Authorization": f"Bearer {token}"}

            current_user = client.get("/api/auth/me", headers=headers)
            assert current_user.status_code == 200
            assert current_user.json()["data"]["user"]["username"] == "agent01"

            agent02_login = client.post(
                "/api/auth/login",
                json={"username": "agent02", "password": "password123"},
            )
            assert agent02_login.status_code == 200
            agent02_token = str(agent02_login.json()["data"]["access_token"])
            assert agent02_token != token
            agent02_headers = {"Authorization": f"Bearer {agent02_token}"}

            agent01_after_agent02_login = client.get("/api/auth/me", headers=headers)
            assert agent01_after_agent02_login.status_code == 200
            assert agent01_after_agent02_login.json()["data"]["user"]["id"] == "user_001"

            agent02_user = client.get("/api/auth/me", headers=agent02_headers)
            assert agent02_user.status_code == 200
            assert agent02_user.json()["data"]["user"]["id"] == "user_002"

            settings = client.get("/api/settings/account", headers=headers)
            assert settings.status_code == 200
            settings_data = settings.json()["data"]
            assert settings_data["user"]["id"] == "user_001"
            assert settings_data["system"] == {
                "database": "SQLite",
                "model_provider": "百炼",
                "chat_model": "qwen-plus",
                "embedding_model": "text-embedding-v4",
                "embedding_dimensions": 1024,
                "api_key_configured": settings_data["system"]["api_key_configured"],
            }
            assert isinstance(settings_data["system"]["api_key_configured"], bool)

            logout = client.post(
                "/api/auth/logout",
                headers=headers,
                json={"access_token": token},
            )
            assert logout.status_code == 200
            assert logout.json() == {
                "code": 200,
                "message": "success",
                "data": {"logged_out": True},
            }

            expired_user = client.get("/api/auth/me", headers=headers)
            assert expired_user.status_code == 401
            assert expired_user.json() == {
                "code": 401,
                "message": "登录状态已失效",
                "data": None,
            }
    finally:
        app.dependency_overrides.pop(get_db, None)
        reset_token_store()
        asyncio.run(test_engine.dispose())


async def _setup_database(
    test_engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await create_fts5_indexes(conn)

    async with session_factory() as session:
        await seed_demo_data(session)
