from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.api.deps import get_db
from src.db.models import Base, QaItem, VectorIndex
from src.db.schema import create_fts5_indexes, rebuild_fts5_indexes
from src.db.seed import seed_demo_data
from src.main import app
from src.services.ai_gateway import EmbeddingResult
from src.services.auth import reset_token_store


def test_knowledge_overview_recent_and_qa_crud_use_real_database(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    db_path = tmp_path / "knowledge_test.db"
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    fake_gateway = FakeEmbeddingGateway()

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            yield session

    try:
        asyncio.run(_setup_database(test_engine, session_factory))
        reset_token_store()
        app.dependency_overrides[get_db] = override_get_db
        monkeypatch.setattr("src.services.knowledge.BailianGateway", lambda: fake_gateway)

        with TestClient(app) as client:
            missing_auth = client.get("/api/knowledge/overview")
            assert missing_auth.status_code == 401
            assert missing_auth.json() == {
                "code": 401,
                "message": "登录状态已失效",
                "data": None,
            }

            headers = _login_headers(client)

            overview = client.get("/api/knowledge/overview", headers=headers)
            assert overview.status_code == 200
            assert overview.json()["data"] == {
                "qa_count": 3,
                "enabled_qa_count": 2,
                "document_count": 3,
                "completed_document_count": 1,
                "latest_updated_at": "2026-05-24T10:15:00+08:00",
            }

            recent = client.get("/api/knowledge/recent", headers=headers, params={"limit": 3})
            assert recent.status_code == 200
            recent_items = recent.json()["data"]["items"]
            assert [item["id"] for item in recent_items] == ["qa_002", "doc_002", "doc_003"]
            assert recent_items[0] == {
                "type": "qa",
                "id": "qa_002",
                "title": "支付状态为什么延迟？",
                "status": "enabled",
                "updated_at": "2026-05-24T10:15:00+08:00",
            }

            invalid_recent = client.get(
                "/api/knowledge/recent",
                headers=headers,
                params={"limit": 0},
            )
            assert invalid_recent.status_code == 400
            assert invalid_recent.json() == {
                "code": 400,
                "message": "limit 必须为 1 到 20 的整数",
                "data": None,
            }

            qa_list = client.get(
                "/api/knowledge/qa",
                headers=headers,
                params={"keyword": "退款", "status": "enabled", "page": 1, "page_size": 20},
            )
            assert qa_list.status_code == 200
            qa_data = qa_list.json()["data"]
            assert qa_data["total"] == 1
            assert qa_data["items"][0]["id"] == "qa_001"

            invalid_status = client.get(
                "/api/knowledge/qa",
                headers=headers,
                params={"status": "draft"},
            )
            assert invalid_status.status_code == 400
            assert invalid_status.json() == {
                "code": 400,
                "message": "status 参数不合法",
                "data": None,
            }

            create_response = client.post(
                "/api/knowledge/qa",
                headers=headers,
                json={
                    "question": "测试新增 QA 如何生效？",
                    "answer": "新增后会写入数据库并同步更新向量索引。",
                    "status": "enabled",
                },
            )
            assert create_response.status_code == 200
            create_data = create_response.json()["data"]
            created_qa = create_data["qa"]
            assert created_qa["id"].startswith("qa_")
            assert created_qa["question"] == "测试新增 QA 如何生效？"
            assert create_data["embedding_status"] == "completed"
            assert fake_gateway.inputs[-1] == (
                "测试新增 QA 如何生效？\n新增后会写入数据库并同步更新向量索引。"
            )

            created_vector = asyncio.run(_get_vector(session_factory, created_qa["id"]))
            assert created_vector is not None
            assert created_vector.source_type == "qa"
            assert created_vector.embedding_model == "fake-embedding-model"
            assert created_vector.vector_dimension == 4

            update_response = client.put(
                f"/api/knowledge/qa/{created_qa['id']}",
                headers=headers,
                json={
                    "question": "测试编辑 QA 如何生效？",
                    "answer": "编辑后会重新生成 embedding 并 upsert 索引。",
                    "status": "disabled",
                },
            )
            assert update_response.status_code == 200
            update_data = update_response.json()["data"]
            assert update_data["qa"]["status"] == "disabled"
            assert update_data["embedding_status"] == "completed"
            assert fake_gateway.call_count == 2

            updated_vector = asyncio.run(_get_vector(session_factory, created_qa["id"]))
            assert updated_vector is not None
            assert updated_vector.id == created_vector.id
            assert updated_vector.embedding_model == "fake-embedding-model"

            delete_response = client.delete(
                f"/api/knowledge/qa/{created_qa['id']}",
                headers=headers,
            )
            assert delete_response.status_code == 200
            assert delete_response.json()["data"] == {
                "deleted": True,
                "qa_id": created_qa["id"],
            }
            assert asyncio.run(_get_vector(session_factory, created_qa["id"])) is None
            assert asyncio.run(_get_qa(session_factory, created_qa["id"])) is None

            missing_update = client.put(
                "/api/knowledge/qa/qa_missing",
                headers=headers,
                json={
                    "question": "不存在",
                    "answer": "不存在",
                    "status": "enabled",
                },
            )
            assert missing_update.status_code == 404
            assert missing_update.json() == {
                "code": 404,
                "message": "QA 不存在",
                "data": None,
            }

            missing_delete = client.delete("/api/knowledge/qa/qa_missing", headers=headers)
            assert missing_delete.status_code == 404
            assert missing_delete.json() == {
                "code": 404,
                "message": "QA 不存在",
                "data": None,
            }
    finally:
        app.dependency_overrides.clear()
        asyncio.run(test_engine.dispose())


def test_knowledge_qa_crud_succeeds_with_embedding_fallback(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    db_path = tmp_path / "knowledge_embedding_fallback.db"
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
        monkeypatch.setattr("src.services.knowledge.BailianGateway", FailingEmbeddingGateway)

        with TestClient(app) as client:
            headers = _login_headers(client)
            response = client.post(
                "/api/knowledge/qa",
                headers=headers,
                json={
                    "question": "没有 embedding 时能保存吗？",
                    "answer": "可以保存 QA，并标记关键词检索降级。",
                    "status": "enabled",
                },
            )

            assert response.status_code == 200
            data = response.json()["data"]
            assert data["qa"]["question"] == "没有 embedding 时能保存吗？"
            assert data["embedding_status"] == "fallback"
            assert asyncio.run(_get_vector(session_factory, data["qa"]["id"])) is None
    finally:
        app.dependency_overrides.clear()
        asyncio.run(test_engine.dispose())


async def _setup_database(
    engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await create_fts5_indexes(conn)
    async with session_factory() as session:
        await seed_demo_data(session)
    async with engine.begin() as conn:
        await rebuild_fts5_indexes(conn)


async def _get_vector(
    session_factory: async_sessionmaker[AsyncSession],
    source_id: str,
) -> VectorIndex | None:
    async with session_factory() as session:
        result = await session.execute(
            select(VectorIndex).where(
                VectorIndex.source_type == "qa",
                VectorIndex.source_id == source_id,
            )
        )
        return result.scalar_one_or_none()


async def _get_qa(
    session_factory: async_sessionmaker[AsyncSession],
    qa_id: str,
) -> QaItem | None:
    async with session_factory() as session:
        result = await session.execute(select(QaItem).where(QaItem.id == qa_id))
        return result.scalar_one_or_none()


def _login_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": "agent01", "password": "password123"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


class FakeEmbeddingGateway:
    def __init__(self) -> None:
        self.inputs: list[str] = []
        self.call_count = 0

    async def create_embeddings(self, inputs: list[str]) -> EmbeddingResult:
        self.inputs.extend(inputs)
        self.call_count += 1
        return EmbeddingResult(
            embeddings=[],
            model="fake-embedding-model",
            dimensions=4,
            usage={"total_tokens": 1},
        )


class FailingEmbeddingGateway:
    async def create_embeddings(self, inputs: list[str]) -> EmbeddingResult:
        del inputs
        raise RuntimeError("embedding service unavailable")
