from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.db.models import Base
from src.db.schema import (
    count_document_keyword_matches,
    count_qa_keyword_matches,
    create_fts5_indexes,
    ensure_vector_index_embedding_column,
    rebuild_fts5_indexes,
)
from src.db.seed import seed_demo_data


def test_demo_schema_seed_and_fts5_use_isolated_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "customer_service_test.db"

    asyncio.run(_exercise_isolated_database(db_path))

    assert db_path.exists()


def test_vector_index_embedding_column_is_added_to_existing_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy_vector_indexes.db"

    asyncio.run(_exercise_legacy_vector_index_compatibility(db_path))


async def _exercise_isolated_database(db_path: Path) -> None:
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await create_fts5_indexes(conn)

        session_factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        async with session_factory() as session:
            summary = await seed_demo_data(session)

        assert summary.users >= 1
        assert summary.tickets >= 6
        assert summary.conversation_messages >= 7
        assert summary.qa_items >= 3
        assert summary.documents >= 3
        assert summary.document_chunks == 12
        assert summary.vector_indexes >= summary.qa_items + summary.document_chunks
        assert summary.customer_memories >= 1

        async with test_engine.begin() as conn:
            await rebuild_fts5_indexes(conn)
            qa_matches = await count_qa_keyword_matches(conn, "退款多久到账")
            document_matches = await count_document_keyword_matches(conn, "售后政策及退款流程")
            table_result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'table'")
            )
            table_rows = table_result.fetchall()

        table_names = {str(row[0]) for row in table_rows}
        expected_tables = {
            "users",
            "customers",
            "tickets",
            "conversation_messages",
            "qa_items",
            "documents",
            "document_chunks",
            "vector_indexes",
            "customer_memories",
            "qa_fts",
            "document_chunks_fts",
        }
        assert expected_tables.issubset(table_names)
        assert qa_matches >= 1
        assert document_matches >= 1
    finally:
        await test_engine.dispose()


async def _exercise_legacy_vector_index_compatibility(db_path: Path) -> None:
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    try:
        async with test_engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    CREATE TABLE vector_indexes (
                        id VARCHAR(64) PRIMARY KEY,
                        source_type VARCHAR(32) NOT NULL,
                        source_id VARCHAR(64) NOT NULL,
                        vector_dimension INTEGER NOT NULL,
                        embedding_model VARCHAR(128) NOT NULL,
                        created_at DATETIME NOT NULL
                    )
                    """
                )
            )
            await ensure_vector_index_embedding_column(conn)
            columns_result = await conn.execute(text("PRAGMA table_info(vector_indexes)"))
            column_names = {str(row[1]) for row in columns_result.fetchall()}

        assert "embedding_vector" in column_names
    finally:
        await test_engine.dispose()
