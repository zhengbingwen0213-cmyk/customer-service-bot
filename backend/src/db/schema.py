"""SQLite schema helpers that are not represented directly by SQLAlchemy ORM."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

FTS5_SCHEMA_STATEMENTS = (
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS qa_fts
    USING fts5(
        question,
        answer,
        content='qa_items',
        content_rowid='rowid',
        tokenize='unicode61'
    )
    """,
    """
    CREATE TRIGGER IF NOT EXISTS qa_items_ai
    AFTER INSERT ON qa_items
    BEGIN
        INSERT INTO qa_fts(rowid, question, answer)
        VALUES (new.rowid, new.question, new.answer);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS qa_items_ad
    AFTER DELETE ON qa_items
    BEGIN
        INSERT INTO qa_fts(qa_fts, rowid, question, answer)
        VALUES ('delete', old.rowid, old.question, old.answer);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS qa_items_au
    AFTER UPDATE ON qa_items
    BEGIN
        INSERT INTO qa_fts(qa_fts, rowid, question, answer)
        VALUES ('delete', old.rowid, old.question, old.answer);
        INSERT INTO qa_fts(rowid, question, answer)
        VALUES (new.rowid, new.question, new.answer);
    END
    """,
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts
    USING fts5(
        content,
        content='document_chunks',
        content_rowid='rowid',
        tokenize='unicode61'
    )
    """,
    """
    CREATE TRIGGER IF NOT EXISTS document_chunks_ai
    AFTER INSERT ON document_chunks
    BEGIN
        INSERT INTO document_chunks_fts(rowid, content)
        VALUES (new.rowid, new.content);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS document_chunks_ad
    AFTER DELETE ON document_chunks
    BEGIN
        INSERT INTO document_chunks_fts(document_chunks_fts, rowid, content)
        VALUES ('delete', old.rowid, old.content);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS document_chunks_au
    AFTER UPDATE ON document_chunks
    BEGIN
        INSERT INTO document_chunks_fts(document_chunks_fts, rowid, content)
        VALUES ('delete', old.rowid, old.content);
        INSERT INTO document_chunks_fts(rowid, content)
        VALUES (new.rowid, new.content);
    END
    """,
)


async def create_fts5_indexes(conn: AsyncConnection) -> None:
    """Create FTS5 virtual tables, triggers, and lightweight schema compatibility."""

    await ensure_vector_index_embedding_column(conn)
    for statement in FTS5_SCHEMA_STATEMENTS:
        await conn.execute(text(statement))


async def ensure_vector_index_embedding_column(conn: AsyncConnection) -> None:
    """Add nullable embedding payload storage for databases created before T-015."""

    table_result = await conn.execute(
        text(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'vector_indexes'
            """
        )
    )
    if int(table_result.scalar_one()) == 0:
        return

    columns_result = await conn.execute(text("PRAGMA table_info(vector_indexes)"))
    column_names = {str(row[1]) for row in columns_result.fetchall()}
    if "embedding_vector" not in column_names:
        await conn.execute(text("ALTER TABLE vector_indexes ADD COLUMN embedding_vector TEXT"))


async def rebuild_fts5_indexes(conn: AsyncConnection) -> None:
    """Rebuild FTS5 external-content indexes from the business tables."""

    await conn.execute(text("INSERT INTO qa_fts(qa_fts) VALUES ('rebuild')"))
    await conn.execute(
        text("INSERT INTO document_chunks_fts(document_chunks_fts) VALUES ('rebuild')")
    )


async def count_qa_keyword_matches(conn: AsyncConnection, keyword: str) -> int:
    result = await conn.execute(
        text("SELECT COUNT(*) FROM qa_fts WHERE qa_fts MATCH :keyword"),
        {"keyword": keyword},
    )
    return int(result.scalar_one())


async def count_document_keyword_matches(conn: AsyncConnection, keyword: str) -> int:
    result = await conn.execute(
        text(
            "SELECT COUNT(*) FROM document_chunks_fts "
            "WHERE document_chunks_fts MATCH :keyword"
        ),
        {"keyword": keyword},
    )
    return int(result.scalar_one())
