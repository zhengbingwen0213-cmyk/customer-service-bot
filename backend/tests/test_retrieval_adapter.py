from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.core.config import AppSettings
from src.db.models import Base
from src.db.schema import create_fts5_indexes, rebuild_fts5_indexes
from src.db.seed import seed_demo_data
from src.services.retrieval import KnowledgeSearchAdapter, SQLiteVectorProbe


def test_vector_probe_reports_fallback_when_extension_path_is_missing() -> None:
    probe = SQLiteVectorProbe(AppSettings(sqlite_vector_extension_path=""))

    result = probe.probe()

    assert not result.available
    assert result.status == "fallback"
    assert result.reason == "SQLITE_VECTOR_EXTENSION_PATH is not configured"


def test_retrieval_adapter_uses_fts5_when_available(tmp_path: Path) -> None:
    async def run() -> None:
        session_factory, engine = await _build_database(tmp_path / "fts5.db", create_fts=True)
        try:
            async with session_factory() as session:
                adapter = KnowledgeSearchAdapter(
                    SQLiteVectorProbe(AppSettings(sqlite_vector_extension_path=""))
                )
                status = await adapter.get_status(session)
                qa_hits = await adapter.search_qa(session, "退款多久到账", limit=3)
                document_hits = await adapter.search_documents(
                    session,
                    "售后政策及退款流程",
                    limit=3,
                )

            assert status.keyword_backend == "fts5"
            assert status.fallback_reason is not None
            assert status.fallback_reason.startswith("vector plugin unavailable")
            assert qa_hits
            assert qa_hits[0].source_id == "qa_001"
            assert qa_hits[0].backend == "fts5"
            assert document_hits
            assert document_hits[0].source_id == "doc_001"
            assert document_hits[0].backend == "fts5"
        finally:
            await engine.dispose()

    asyncio.run(run())


def test_retrieval_adapter_falls_back_to_like_without_fts5(tmp_path: Path) -> None:
    async def run() -> None:
        session_factory, engine = await _build_database(tmp_path / "like.db", create_fts=False)
        try:
            async with session_factory() as session:
                adapter = KnowledgeSearchAdapter(
                    SQLiteVectorProbe(AppSettings(sqlite_vector_extension_path=""))
                )
                status = await adapter.get_status(session)
                qa_hits = await adapter.search_qa(session, "退款", limit=3)
                document_hits = await adapter.search_documents(session, "补单", limit=3)

            assert status.keyword_backend == "like"
            assert qa_hits
            assert qa_hits[0].backend == "like"
            assert document_hits
            assert document_hits[0].backend == "like"
        finally:
            await engine.dispose()

    asyncio.run(run())


async def _build_database(
    db_path: Path,
    *,
    create_fts: bool,
) -> tuple[async_sessionmaker[AsyncSession], AsyncEngine]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if create_fts:
            await create_fts5_indexes(conn)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        await seed_demo_data(session)

    if create_fts:
        async with engine.begin() as conn:
            await rebuild_fts5_indexes(conn)

    return session_factory, engine
