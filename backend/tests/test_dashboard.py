from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.api.deps import get_db
from src.db.models import Base, QaItem
from src.db.schema import create_fts5_indexes
from src.db.seed import seed_demo_data
from src.main import app
from src.services.auth import reset_token_store


def test_dashboard_summary_uses_real_database_and_auth_flow(tmp_path: Path) -> None:
    db_path = tmp_path / "dashboard_summary_test.db"
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
            missing_auth = client.get("/api/dashboard/summary")
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
            token = str(login.json()["data"]["access_token"])
            headers = {"Authorization": f"Bearer {token}"}

            summary = client.get("/api/dashboard/summary", headers=headers)
            assert summary.status_code == 200
            assert summary.json()["data"] == {
                "open_ticket_count": 2,
                "processing_ticket_count": 3,
                "completed_ticket_count": 1,
                "qa_count": 3,
                "document_count": 3,
                "latest_knowledge_updated_at": "2026-05-24T10:15:00+08:00",
            }

            asyncio.run(_add_qa(session_factory))

            changed_summary = client.get("/api/dashboard/summary", headers=headers)
            assert changed_summary.status_code == 200
            changed_data = changed_summary.json()["data"]
            assert changed_data["qa_count"] == 4
            assert changed_data["latest_knowledge_updated_at"] == "2026-05-25T09:00:00+08:00"

            settings = client.get("/api/settings/account", headers=headers)
            assert settings.status_code == 200
            system = settings.json()["data"]["system"]
            assert set(system) == {
                "database",
                "model_provider",
                "chat_model",
                "embedding_model",
                "embedding_dimensions",
                "api_key_configured",
            }
            assert isinstance(system["api_key_configured"], bool)
            assert "dashscope_api_key" not in system
            assert "api_key" not in system
            assert "token" not in system
            assert "base_url" not in system

            logout = client.post(
                "/api/auth/logout",
                headers=headers,
                json={"access_token": token},
            )
            assert logout.status_code == 200

            expired_summary = client.get("/api/dashboard/summary", headers=headers)
            assert expired_summary.status_code == 401
            assert expired_summary.json() == {
                "code": 401,
                "message": "登录状态已失效",
                "data": None,
            }
    finally:
        app.dependency_overrides.pop(get_db, None)
        reset_token_store()
        asyncio.run(test_engine.dispose())


def test_dashboard_tickets_are_current_user_processing_only(tmp_path: Path) -> None:
    db_path = tmp_path / "dashboard_tickets_test.db"
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
            missing_auth = client.get("/api/dashboard/tickets", params={"limit": 2})
            assert missing_auth.status_code == 401
            assert missing_auth.json() == {
                "code": 401,
                "message": "登录状态已失效",
                "data": None,
            }

            headers = _login_headers(client)

            invalid_low = client.get(
                "/api/dashboard/tickets",
                headers=headers,
                params={"limit": 0},
            )
            assert invalid_low.status_code == 400
            assert invalid_low.json() == {
                "code": 400,
                "message": "limit 必须为 1 到 20 的整数",
                "data": None,
            }

            invalid_high = client.get(
                "/api/dashboard/tickets",
                headers=headers,
                params={"limit": 21},
            )
            assert invalid_high.status_code == 400
            assert invalid_high.json() == {
                "code": 400,
                "message": "limit 必须为 1 到 20 的整数",
                "data": None,
            }

            response = client.get("/api/dashboard/tickets", headers=headers, params={"limit": 2})
            assert response.status_code == 200
            items = response.json()["data"]["items"]
            assert [item["id"] for item in items] == ["TK-1005", "TK-1003"]
            assert all(item["status"] == "processing" for item in items)
            assert all(item["assignee_id"] == "user_001" for item in items)
            assert "TK-2001" not in {item["id"] for item in items}
            assert items[0] == {
                "id": "TK-1005",
                "title": "会员支付后未生效",
                "description": "客户反馈在 APP 内购买年度会员，支付宝已扣款，但账户状态未更新。",
                "status": "processing",
                "priority": "high",
                "assignee_id": "user_001",
                "assignee_name": "客服一组员工",
                "customer_name": "张三",
                "created_at": "2026-05-23T14:30:00+08:00",
                "completed_at": None,
            }
    finally:
        app.dependency_overrides.pop(get_db, None)
        reset_token_store()
        asyncio.run(test_engine.dispose())


def test_frontend_dashboard_real_mode_exits_mock_and_hides_internal_ai_fields() -> None:
    project_root = Path(__file__).resolve().parents[2]
    dashboard_service = (project_root / "frontend/src/services/dashboard.ts").read_text()
    dashboard_page = (project_root / "frontend/src/pages/DashboardPage.vue").read_text()

    assert "isMockApiEnabled" in dashboard_service
    assert "api.get('/dashboard/summary'" in dashboard_service
    assert "api.get('/dashboard/tickets'" in dashboard_service

    assert "[Mock]" not in dashboard_page
    assert "mockGetAssistantIntroAnswer" not in dashboard_page
    assert "今日完成" not in dashboard_page
    assert "已完成" in dashboard_page
    assert "查看</RouterLink>" in dashboard_page

    assert "missing_fields" in dashboard_page
    assert "引用来源" in dashboard_page
    assert "reference.type" in dashboard_page
    assert "reference.snippet" in dashboard_page
    assert "reference.score" not in dashboard_page
    assert "confidence" not in dashboard_page
    assert "context_messages_used" not in dashboard_page
    assert "request_id" not in dashboard_page
    assert "prompt" not in dashboard_page
    assert "assistantError" in dashboard_page


async def _setup_database(
    test_engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await create_fts5_indexes(conn)

    async with session_factory() as session:
        await seed_demo_data(session)


async def _add_qa(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        session.add(
            QaItem(
                id="qa_dashboard_new",
                question="新增 QA 是否会影响工作台统计？",
                answer="会，工作台统计应从数据库实时读取 QA 总数。",
                status="enabled",
                created_at=datetime.fromisoformat("2026-05-25T09:00:00+08:00"),
                updated_at=datetime.fromisoformat("2026-05-25T09:00:00+08:00"),
            )
        )
        await session.commit()


def _login_headers(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/api/auth/login",
        json={"username": "agent01", "password": "password123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
