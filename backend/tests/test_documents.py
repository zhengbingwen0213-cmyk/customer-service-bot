from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import src.core.config as config_module
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.api.deps import get_db
from src.core.config import AppSettings
from src.db.models import Base, Document, DocumentChunk, User, VectorIndex
from src.db.schema import create_fts5_indexes
from src.main import app
from src.services.ai_gateway import EmbeddingItem, EmbeddingResult
from src.services.auth import reset_token_store
from src.services.retrieval import KnowledgeSearchAdapter


def test_document_api_uploads_indexes_deletes_and_removes_from_search(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    session_factory, engine = _isolated_database(tmp_path, "documents_flow.db")
    upload_dir = tmp_path / "uploads"

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            yield session

    try:
        asyncio.run(_setup_database(engine, session_factory))
        _configure_test_settings(upload_dir, monkeypatch)
        reset_token_store()
        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as client:
            missing_auth = client.get("/api/documents")
            assert missing_auth.status_code == 401
            assert missing_auth.json() == {
                "code": 401,
                "message": "登录状态已失效",
                "data": None,
            }

            headers = _login_headers(client)

            invalid_status = client.get(
                "/api/documents",
                headers=headers,
                params={"status": "draft"},
            )
            assert invalid_status.status_code == 400
            assert invalid_status.json() == {
                "code": 400,
                "message": "status 参数不合法",
                "data": None,
            }

            empty_file = client.post(
                "/api/documents",
                headers=headers,
                files={"file": ("empty.txt", b"", "text/plain")},
            )
            assert empty_file.status_code == 400
            assert empty_file.json() == {
                "code": 400,
                "message": "文件不能为空",
                "data": None,
            }

            unsupported = client.post(
                "/api/documents",
                headers=headers,
                files={
                    "file": (
                        "orders.xlsx",
                        b"not supported",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )
            assert unsupported.status_code == 400
            assert unsupported.json() == {
                "code": 400,
                "message": "不支持的文件类型",
                "data": None,
            }

            monkeypatch.setattr("src.services.documents.BailianGateway", FakeEmbeddingGateway)
            upload = client.post(
                "/api/documents",
                headers=headers,
                data={"name": "补单流程.md"},
                files={
                    "file": (
                        "source.md",
                        "补单流程\n客户申请补单时，客服需要核对订单号并记录补单原因。".encode(),
                        "text/markdown",
                    )
                },
            )
            assert upload.status_code == 200
            created = upload.json()["data"]["document"]
            assert created["id"].startswith("doc_")
            assert created["name"] == "补单流程.md"
            assert created["status"] == "completed"
            assert created["chunk_count"] > 0
            assert created["uploaded_by"] == "客服一组员工"

            stored_file = asyncio.run(_get_document_storage_path(session_factory, created["id"]))
            assert stored_file is not None
            assert stored_file.exists()
            assert upload_dir in stored_file.parents

            chunks = asyncio.run(_count_chunks(session_factory, created["id"]))
            vectors = asyncio.run(_count_document_vectors(session_factory, created["id"]))
            assert chunks == created["chunk_count"]
            assert vectors == chunks
            embedding_vectors = asyncio.run(
                _get_document_embedding_vectors(session_factory, created["id"])
            )
            assert embedding_vectors == [[0.1, 0.2, 0.3, 0.4]]

            list_response = client.get(
                "/api/documents",
                headers=headers,
                params={"keyword": "补单", "status": "completed", "page": 1, "page_size": 20},
            )
            assert list_response.status_code == 200
            list_data = list_response.json()["data"]
            assert list_data["total"] == 1
            assert list_data["page"] == 1
            assert list_data["page_size"] == 20
            assert list_data["items"][0]["id"] == created["id"]

            detail = client.get(f"/api/documents/{created['id']}", headers=headers)
            assert detail.status_code == 200
            assert detail.json()["data"]["document"]["chunk_count"] == chunks

            search_hits = asyncio.run(_search_documents(session_factory, "补单"))
            assert [hit.source_id for hit in search_hits] == [created["id"]]

            delete_response = client.delete(f"/api/documents/{created['id']}", headers=headers)
            assert delete_response.status_code == 200
            assert delete_response.json()["data"] == {
                "deleted": True,
                "document_id": created["id"],
            }
            assert not stored_file.exists()
            assert not stored_file.parent.exists()
            assert asyncio.run(_get_document(session_factory, created["id"])) is None
            assert asyncio.run(_count_chunks(session_factory, created["id"])) == 0
            assert asyncio.run(_count_document_vectors(session_factory, created["id"])) == 0
            assert asyncio.run(_search_documents(session_factory, "补单")) == []

            missing_detail = client.get("/api/documents/doc_missing", headers=headers)
            assert missing_detail.status_code == 404
            assert missing_detail.json() == {
                "code": 404,
                "message": "文档不存在",
                "data": None,
            }

            missing_delete = client.delete("/api/documents/doc_missing", headers=headers)
            assert missing_delete.status_code == 404
            assert missing_delete.json() == {
                "code": 404,
                "message": "文档不存在",
                "data": None,
            }
    finally:
        app.dependency_overrides.clear()
        reset_token_store()
        asyncio.run(engine.dispose())


def test_document_upload_keeps_chunks_and_search_when_embedding_falls_back(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    session_factory, engine = _isolated_database(tmp_path, "documents_fallback.db")
    upload_dir = tmp_path / "uploads"

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            yield session

    try:
        asyncio.run(_setup_database(engine, session_factory))
        _configure_test_settings(upload_dir, monkeypatch)
        reset_token_store()
        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as client:
            assert client.get("/api/documents").status_code == 401
            headers = _login_headers(client)
            monkeypatch.setattr("src.services.documents.BailianGateway", FailingEmbeddingGateway)

            upload = client.post(
                "/api/documents",
                headers=headers,
                data={"name": "退款规则.txt"},
                files={
                    "file": (
                        "refund.txt",
                        "\ufeff退款规则：超过 7 天需要人工复核，保留退款凭证。".encode(),
                        "text/plain",
                    )
                },
            )

            assert upload.status_code == 200
            document = upload.json()["data"]["document"]
            assert document["status"] == "completed"
            assert document["chunk_count"] > 0
            chunk_count = asyncio.run(_count_chunks(session_factory, document["id"]))
            assert chunk_count == document["chunk_count"]
            assert asyncio.run(_count_document_vectors(session_factory, document["id"])) == 0

            hits = asyncio.run(_search_documents(session_factory, "人工复核"))
            assert len(hits) == 1
            assert hits[0].source_id == document["id"]
            assert hits[0].backend in {"fts5", "like"}
    finally:
        app.dependency_overrides.clear()
        reset_token_store()
        asyncio.run(engine.dispose())


def test_document_upload_extracts_simple_text_pdf(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    session_factory, engine = _isolated_database(tmp_path, "documents_pdf.db")
    upload_dir = tmp_path / "uploads"

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            yield session

    try:
        asyncio.run(_setup_database(engine, session_factory))
        _configure_test_settings(upload_dir, monkeypatch)
        reset_token_store()
        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as client:
            assert client.get("/api/documents").status_code == 401
            headers = _login_headers(client)
            monkeypatch.setattr("src.services.documents.BailianGateway", FakeEmbeddingGateway)

            upload = client.post(
                "/api/documents",
                headers=headers,
                data={"name": "shipping.pdf"},
                files={
                    "file": (
                        "shipping.pdf",
                        _simple_pdf_bytes("Shipping delay compensation policy"),
                        "application/pdf",
                    )
                },
            )

            assert upload.status_code == 200
            document = upload.json()["data"]["document"]
            assert document["status"] == "completed"
            assert document["chunk_count"] == 1

            hits = asyncio.run(_search_documents(session_factory, "Shipping"))
            assert [hit.source_id for hit in hits] == [document["id"]]
    finally:
        app.dependency_overrides.clear()
        reset_token_store()
        asyncio.run(engine.dispose())


def _isolated_database(
    tmp_path: Path,
    name: str,
) -> tuple[async_sessionmaker[AsyncSession], AsyncEngine]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / name}", future=True)
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    return session_factory, engine


async def _setup_database(
    engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await create_fts5_indexes(conn)

    async with session_factory() as session:
        session.add(
            User(
                id="user_001",
                name="客服一组员工",
                username="agent01",
                password_hash="$2b$12$N9/3q3XVkkO8cwXwF3U3iupyjenaQnGilHdSoTVJh8fN.JeQ/Cni.",
            )
        )
        await session.commit()


def _configure_test_settings(upload_dir: Path, monkeypatch: Any) -> None:
    monkeypatch.setattr(
        config_module,
        "_settings",
        AppSettings(
            upload_dir=str(upload_dir),
            database_path=str(upload_dir.parent / "unused.db"),
            dashscope_api_key="test-key",
        ),
    )


def _login_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": "agent01", "password": "password123"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _get_document(
    session_factory: async_sessionmaker[AsyncSession],
    document_id: str,
) -> Document | None:
    async with session_factory() as session:
        result = await session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()


async def _get_document_storage_path(
    session_factory: async_sessionmaker[AsyncSession],
    document_id: str,
) -> Path | None:
    document = await _get_document(session_factory, document_id)
    return Path(document.storage_path) if document else None


async def _count_chunks(
    session_factory: async_sessionmaker[AsyncSession],
    document_id: str,
) -> int:
    async with session_factory() as session:
        result = await session.execute(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
        )
        return int(result.scalar_one())


async def _count_document_vectors(
    session_factory: async_sessionmaker[AsyncSession],
    document_id: str,
) -> int:
    async with session_factory() as session:
        chunk_ids = select(DocumentChunk.id).where(DocumentChunk.document_id == document_id)
        result = await session.execute(
            select(func.count()).select_from(VectorIndex).where(
                VectorIndex.source_type == "document_chunk",
                VectorIndex.source_id.in_(chunk_ids),
            )
        )
        return int(result.scalar_one())


async def _get_document_embedding_vectors(
    session_factory: async_sessionmaker[AsyncSession],
    document_id: str,
) -> list[list[float]]:
    async with session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT vector_indexes.embedding_vector
                FROM vector_indexes
                JOIN document_chunks ON vector_indexes.source_id = document_chunks.id
                WHERE vector_indexes.source_type = 'document_chunk'
                  AND document_chunks.document_id = :document_id
                ORDER BY document_chunks.chunk_index ASC
                """
            ),
            {"document_id": document_id},
        )
        return [json.loads(str(row.embedding_vector)) for row in result.fetchall()]


async def _search_documents(
    session_factory: async_sessionmaker[AsyncSession],
    keyword: str,
) -> list[Any]:
    async with session_factory() as session:
        return await KnowledgeSearchAdapter().search_documents(session, keyword, limit=5)


def _simple_pdf_bytes(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n"
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\n"
            b"endobj\n"
        ),
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    stream = f"BT /F1 18 Tf 72 720 Td ({escaped}) Tj ET".encode()
    objects.append(
        b"5 0 obj\n<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"\nendstream\nendobj\n"
    )
    content = b"%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(content))
        content += obj
    xref_offset = len(content)
    xref_entries = [b"0000000000 65535 f \n"]
    xref_entries.extend(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    content += (
        b"xref\n0 6\n"
        + b"".join(xref_entries)
        + b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode()
        + b"\n%%EOF\n"
    )
    return content


class FakeEmbeddingGateway:
    async def create_embeddings(self, inputs: list[str]) -> EmbeddingResult:
        return EmbeddingResult(
            embeddings=[
                EmbeddingItem(index=index, embedding=[0.1, 0.2, 0.3, 0.4])
                for index, _ in enumerate(inputs)
            ],
            model="fake-document-embedding",
            dimensions=4,
            usage={"total_tokens": len(inputs)},
        )


class FailingEmbeddingGateway:
    async def create_embeddings(self, inputs: list[str]) -> EmbeddingResult:
        del inputs
        raise RuntimeError("embedding service unavailable")
