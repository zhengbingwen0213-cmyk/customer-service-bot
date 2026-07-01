"""Search adapter with SQLite vector-extension probing and keyword fallback."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pycore.core import get_logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import PROJECT_ROOT, AppSettings, get_settings

ReferenceType = Literal["qa", "document"]
KeywordBackend = Literal["fts5", "like"]


@dataclass(frozen=True)
class VectorProbeResult:
    available: bool
    plugin_name: str | None
    version: str | None
    reason: str | None

    @property
    def status(self) -> str:
        if self.available:
            return "available"
        return "fallback"


@dataclass(frozen=True)
class RetrievalStatus:
    vector: VectorProbeResult
    keyword_backend: KeywordBackend
    mode: str
    fallback_reason: str | None


@dataclass(frozen=True)
class SearchHit:
    reference_type: ReferenceType
    source_id: str
    title: str
    snippet: str
    score: float
    backend: KeywordBackend


class SQLiteVectorProbe:
    """Load-probe for local SQLite vector extensions."""

    def __init__(self, settings: AppSettings | None = None) -> None:
        self._settings = settings or get_settings()
        self._logger = get_logger()

    def probe(self) -> VectorProbeResult:
        raw_path = self._settings.sqlite_vector_extension_path.strip()
        if not raw_path:
            return VectorProbeResult(
                available=False,
                plugin_name=None,
                version=None,
                reason="SQLITE_VECTOR_EXTENSION_PATH is not configured",
            )

        extension_path = _resolve_project_path(raw_path)
        if not extension_path.exists():
            return VectorProbeResult(
                available=False,
                plugin_name=None,
                version=None,
                reason=f"SQLite vector extension file does not exist: {extension_path}",
            )

        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(":memory:")
            connection.enable_load_extension(True)
            connection.load_extension(str(extension_path))
            plugin_name, version = _detect_vector_plugin(connection)
            return VectorProbeResult(
                available=True,
                plugin_name=plugin_name,
                version=version,
                reason=None,
            )
        except (OSError, sqlite3.Error) as exc:
            self._logger.warning(
                "SQLite vector extension unavailable",
                extension_path=str(extension_path),
                error_msg=str(exc),
            )
            return VectorProbeResult(
                available=False,
                plugin_name=None,
                version=None,
                reason=str(exc),
            )
        finally:
            if connection is not None:
                try:
                    connection.enable_load_extension(False)
                except sqlite3.Error:
                    pass
                connection.close()


class KnowledgeSearchAdapter:
    """Keyword search facade that reports vector-plugin fallback state."""

    def __init__(self, vector_probe: SQLiteVectorProbe | None = None) -> None:
        self._vector_probe = vector_probe or SQLiteVectorProbe()
        self._logger = get_logger()

    async def get_status(self, session: AsyncSession) -> RetrievalStatus:
        vector_result = self._vector_probe.probe()
        keyword_backend: KeywordBackend = "fts5" if await _has_fts5_tables(session) else "like"
        mode = f"vector+{keyword_backend}" if vector_result.available else keyword_backend
        fallback_reason = None
        if not vector_result.available:
            fallback_reason = f"vector plugin unavailable; using {keyword_backend}"
            if vector_result.reason:
                fallback_reason = f"{fallback_reason}: {vector_result.reason}"

        return RetrievalStatus(
            vector=vector_result,
            keyword_backend=keyword_backend,
            mode=mode,
            fallback_reason=fallback_reason,
        )

    async def search_qa(
        self,
        session: AsyncSession,
        query: str,
        *,
        limit: int = 5,
    ) -> list[SearchHit]:
        keyword = query.strip()
        if not keyword:
            return []

        if await _has_fts5_tables(session):
            try:
                hits = await self._search_qa_fts5(session, keyword, limit=limit)
                if hits:
                    return _rank_qa_hits(keyword, hits)
            except SQLAlchemyError as exc:
                self._logger.warning("QA FTS5 search failed", error_msg=str(exc))

        return _rank_qa_hits(
            keyword,
            await self._search_qa_like(session, keyword, limit=limit),
        )

    async def search_documents(
        self,
        session: AsyncSession,
        query: str,
        *,
        limit: int = 5,
    ) -> list[SearchHit]:
        keyword = query.strip()
        if not keyword:
            return []

        if await _has_fts5_tables(session):
            try:
                hits = await self._search_documents_fts5(session, keyword, limit=limit)
                if hits:
                    return hits
            except SQLAlchemyError as exc:
                self._logger.warning("Document FTS5 search failed", error_msg=str(exc))

        return await self._search_documents_like(session, keyword, limit=limit)

    async def _search_qa_fts5(
        self,
        session: AsyncSession,
        keyword: str,
        *,
        limit: int,
    ) -> list[SearchHit]:
        result = await session.execute(
            text(
                """
                SELECT
                    qa_items.id AS source_id,
                    qa_items.question AS title,
                    qa_items.answer AS snippet,
                    bm25(qa_fts) AS raw_score
                FROM qa_fts
                JOIN qa_items ON qa_fts.rowid = qa_items.rowid
                WHERE qa_fts MATCH :keyword
                  AND qa_items.status = 'enabled'
                ORDER BY raw_score
                LIMIT :limit
                """
            ),
            {"keyword": keyword, "limit": limit},
        )
        return [
            SearchHit(
                reference_type="qa",
                source_id=str(row.source_id),
                title=str(row.title),
                snippet=str(row.snippet),
                score=_normalize_fts_score(float(row.raw_score)),
                backend="fts5",
            )
            for row in result.fetchall()
        ]

    async def _search_documents_fts5(
        self,
        session: AsyncSession,
        keyword: str,
        *,
        limit: int,
    ) -> list[SearchHit]:
        result = await session.execute(
            text(
                """
                SELECT
                    documents.id AS source_id,
                    documents.name AS title,
                    document_chunks.content AS snippet,
                    bm25(document_chunks_fts) AS raw_score
                FROM document_chunks_fts
                JOIN document_chunks ON document_chunks_fts.rowid = document_chunks.rowid
                JOIN documents ON document_chunks.document_id = documents.id
                WHERE document_chunks_fts MATCH :keyword
                  AND documents.status = 'completed'
                ORDER BY raw_score
                LIMIT :limit
                """
            ),
            {"keyword": keyword, "limit": limit},
        )
        return [
            SearchHit(
                reference_type="document",
                source_id=str(row.source_id),
                title=str(row.title),
                snippet=str(row.snippet),
                score=_normalize_fts_score(float(row.raw_score)),
                backend="fts5",
            )
            for row in result.fetchall()
        ]

    async def _search_qa_like(
        self,
        session: AsyncSession,
        keyword: str,
        *,
        limit: int,
    ) -> list[SearchHit]:
        result = await session.execute(
            text(
                """
                SELECT id AS source_id, question AS title, answer AS snippet
                FROM qa_items
                WHERE status = 'enabled'
                  AND (question LIKE :keyword OR answer LIKE :keyword)
                ORDER BY updated_at DESC
                LIMIT :limit
                """
            ),
            {"keyword": f"%{keyword}%", "limit": limit},
        )
        return [
            SearchHit(
                reference_type="qa",
                source_id=str(row.source_id),
                title=str(row.title),
                snippet=str(row.snippet),
                score=0.5,
                backend="like",
            )
            for row in result.fetchall()
        ]

    async def _search_documents_like(
        self,
        session: AsyncSession,
        keyword: str,
        *,
        limit: int,
    ) -> list[SearchHit]:
        result = await session.execute(
            text(
                """
                SELECT
                    documents.id AS source_id,
                    documents.name AS title,
                    document_chunks.content AS snippet
                FROM document_chunks
                JOIN documents ON document_chunks.document_id = documents.id
                WHERE documents.status = 'completed'
                  AND document_chunks.content LIKE :keyword
                ORDER BY document_chunks.chunk_index ASC
                LIMIT :limit
                """
            ),
            {"keyword": f"%{keyword}%", "limit": limit},
        )
        return [
            SearchHit(
                reference_type="document",
                source_id=str(row.source_id),
                title=str(row.title),
                snippet=str(row.snippet),
                score=0.5,
                backend="like",
            )
            for row in result.fetchall()
        ]


async def _has_fts5_tables(session: AsyncSession) -> bool:
    result = await session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN ('qa_fts', 'document_chunks_fts')
            """
        )
    )
    return int(result.scalar_one()) == 2


def _detect_vector_plugin(connection: sqlite3.Connection) -> tuple[str, str | None]:
    probes = (
        ("sqlite-vec", "SELECT vec_version()"),
        ("sqlite-vss", "SELECT vss_version()"),
    )
    for plugin_name, statement in probes:
        try:
            version = connection.execute(statement).fetchone()
        except sqlite3.Error:
            continue
        if version and version[0] is not None:
            return plugin_name, str(version[0])

    return "unknown", None


def _resolve_project_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def _normalize_fts_score(raw_score: float) -> float:
    return 1.0 / (1.0 + abs(raw_score))


def _rank_qa_hits(keyword: str, hits: list[SearchHit]) -> list[SearchHit]:
    ranked = [
        SearchHit(
            reference_type=hit.reference_type,
            source_id=hit.source_id,
            title=hit.title,
            snippet=hit.snippet,
            score=_score_qa_match(keyword, hit.title, hit.snippet),
            backend=hit.backend,
        )
        for hit in hits
    ]
    return sorted(ranked, key=lambda hit: hit.score, reverse=True)


def _score_qa_match(query: str, question: str, answer: str) -> float:
    normalized_query = _normalize_for_match(query)
    normalized_question = _normalize_for_match(question)
    if not normalized_query or not normalized_question:
        return 0.5

    if normalized_query == normalized_question:
        return 1.0

    if normalized_query in normalized_question or normalized_question in normalized_query:
        return 0.9

    overlap = _character_overlap(normalized_query, normalized_question)
    if overlap >= 0.8:
        return 0.85
    if overlap >= 0.6:
        return 0.79
    if overlap >= 0.4:
        return 0.68

    normalized_answer = _normalize_for_match(answer)
    if normalized_query in normalized_answer:
        return 0.72

    return 0.5


def _character_overlap(left: str, right: str) -> float:
    left_chars = set(left)
    right_chars = set(right)
    if not left_chars or not right_chars:
        return 0.0
    return len(left_chars & right_chars) / len(left_chars)


def _normalize_for_match(value: str) -> str:
    return re.sub(r"[\W_]+", "", value, flags=re.UNICODE).lower()
