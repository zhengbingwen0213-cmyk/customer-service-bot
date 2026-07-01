"""Knowledge overview and QA management business logic."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import cast
from uuid import uuid4

from pycore.core import get_logger

from src.db.models import Document, QaItem
from src.models.knowledge import (
    KnowledgeEmbeddingStatus,
    KnowledgeOverviewResponseData,
    KnowledgeQaListResponseData,
    KnowledgeQaRead,
    KnowledgeQaStatus,
    KnowledgeRecentItem,
    KnowledgeRecentResponseData,
)
from src.repositories.knowledge import KnowledgeRepository
from src.services.ai_gateway import BailianGateway

CHINA_STANDARD_TIME = timezone(timedelta(hours=8))
VALID_QA_STATUSES = {"enabled", "disabled"}


class KnowledgeValidationError(ValueError):
    """Raised when knowledge API input is outside the public contract."""


class KnowledgeNotFoundError(ValueError):
    """Raised when the requested knowledge item does not exist."""


class KnowledgeService:
    def __init__(self, repo: KnowledgeRepository) -> None:
        self.repo = repo
        self.logger = get_logger()

    async def get_overview(self) -> KnowledgeOverviewResponseData:
        qa_count, enabled_qa_count = await self.repo.count_qa()
        document_count, completed_document_count = await self.repo.count_documents()
        latest_updated_at = await self.repo.latest_updated_at()

        return KnowledgeOverviewResponseData(
            qa_count=qa_count,
            enabled_qa_count=enabled_qa_count,
            document_count=document_count,
            completed_document_count=completed_document_count,
            latest_updated_at=_format_datetime(latest_updated_at) if latest_updated_at else "",
        )

    async def list_recent(self, *, limit: int) -> KnowledgeRecentResponseData:
        if limit < 1 or limit > 20:
            raise KnowledgeValidationError("limit 必须为 1 到 20 的整数")

        qa_items = await self.repo.list_recent_qa(limit=limit)
        documents = await self.repo.list_recent_documents(limit=limit)
        items = [
            *[_to_recent_qa_item(qa) for qa in qa_items],
            *[_to_recent_document_item(document) for document in documents],
        ]
        items.sort(key=lambda item: item.updated_at, reverse=True)
        return KnowledgeRecentResponseData(items=items[:limit])

    async def list_qa(
        self,
        *,
        keyword: str | None,
        status: str | None,
        page: int,
        page_size: int,
    ) -> KnowledgeQaListResponseData:
        normalized_status = _normalize_status(status)
        if page < 1 or page_size < 1:
            raise KnowledgeValidationError("分页参数不合法")
        normalized_keyword = keyword.strip() if keyword else None

        qa_items, total = await self.repo.list_qa(
            keyword=normalized_keyword,
            status=normalized_status,
            page=page,
            page_size=page_size,
        )
        return KnowledgeQaListResponseData(
            items=[_to_qa_read(qa) for qa in qa_items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_qa(
        self,
        *,
        question: str,
        answer: str,
        status: str,
    ) -> tuple[KnowledgeQaRead, KnowledgeEmbeddingStatus]:
        normalized_question, normalized_answer, normalized_status = _normalize_payload(
            question=question,
            answer=answer,
            status=status,
        )
        now = datetime.now(CHINA_STANDARD_TIME)
        qa = QaItem(
            id=f"qa_{uuid4().hex[:12]}",
            question=normalized_question,
            answer=normalized_answer,
            status=normalized_status,
            created_at=now,
            updated_at=now,
        )
        created = await self.repo.create_qa(qa)
        embedding_status = await self._sync_embedding(created, updated_at=now)
        await self.repo.commit()
        return _to_qa_read(created), embedding_status

    async def update_qa(
        self,
        *,
        qa_id: str,
        question: str,
        answer: str,
        status: str,
    ) -> tuple[KnowledgeQaRead, KnowledgeEmbeddingStatus]:
        qa = await self.repo.get_qa(qa_id)
        if qa is None:
            raise KnowledgeNotFoundError("QA 不存在")

        normalized_question, normalized_answer, normalized_status = _normalize_payload(
            question=question,
            answer=answer,
            status=status,
        )
        now = datetime.now(CHINA_STANDARD_TIME)
        qa.question = normalized_question
        qa.answer = normalized_answer
        qa.status = normalized_status
        qa.updated_at = now
        embedding_status = await self._sync_embedding(qa, updated_at=now)
        await self.repo.commit()
        return _to_qa_read(qa), embedding_status

    async def delete_qa(self, *, qa_id: str) -> None:
        qa = await self.repo.get_qa(qa_id)
        if qa is None:
            raise KnowledgeNotFoundError("QA 不存在")

        await self.repo.delete_qa_vector(qa_id)
        await self.repo.delete_qa(qa)
        await self.repo.commit()

    async def _sync_embedding(
        self,
        qa: QaItem,
        *,
        updated_at: datetime,
    ) -> KnowledgeEmbeddingStatus:
        try:
            result = await BailianGateway().create_embeddings([f"{qa.question}\n{qa.answer}"])
        except Exception as exc:
            self.logger.warning(
                "QA embedding unavailable; using keyword retrieval fallback",
                qa_id=qa.id,
                error_msg=str(exc),
            )
            return "fallback"

        await self.repo.upsert_qa_vector(
            source_id=qa.id,
            embedding_model=result.model,
            vector_dimension=result.dimensions,
            created_at=updated_at,
        )
        return "completed"


def _normalize_status(value: str | None) -> str | None:
    normalized = value.strip() if value else None
    if not normalized:
        return None
    if normalized not in VALID_QA_STATUSES:
        raise KnowledgeValidationError("status 参数不合法")
    return normalized


def _normalize_payload(*, question: str, answer: str, status: str) -> tuple[str, str, str]:
    normalized_question = question.strip()
    normalized_answer = answer.strip()
    if not normalized_question or not normalized_answer:
        raise KnowledgeValidationError("问题和答案不能为空")
    normalized_status = _normalize_status(status)
    if normalized_status is None:
        raise KnowledgeValidationError("status 参数不合法")
    return normalized_question, normalized_answer, normalized_status


def _to_qa_read(qa: QaItem) -> KnowledgeQaRead:
    return KnowledgeQaRead(
        id=qa.id,
        question=qa.question,
        answer=qa.answer,
        status=cast(KnowledgeQaStatus, qa.status),
        created_at=_format_datetime(qa.created_at),
        updated_at=_format_datetime(qa.updated_at),
    )


def _to_recent_qa_item(qa: QaItem) -> KnowledgeRecentItem:
    return KnowledgeRecentItem(
        type="qa",
        id=qa.id,
        title=qa.question,
        status=cast(KnowledgeQaStatus, qa.status),
        updated_at=_format_datetime(qa.updated_at),
    )


def _to_recent_document_item(document: Document) -> KnowledgeRecentItem:
    return KnowledgeRecentItem(
        type="document",
        id=document.id,
        title=document.name,
        status=cast(str, document.status),
        updated_at=_format_datetime(document.updated_at),
    )


def _format_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=CHINA_STANDARD_TIME)
    else:
        value = value.astimezone(CHINA_STANDARD_TIME)
    return value.isoformat()
