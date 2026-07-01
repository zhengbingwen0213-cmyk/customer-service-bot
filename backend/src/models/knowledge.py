"""Knowledge API DTOs aligned with docs/api-contracts.md."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

KnowledgeQaStatus = Literal["enabled", "disabled"]
KnowledgeDocumentStatus = Literal["processing", "completed", "failed"]
KnowledgeRecentType = Literal["qa", "document"]
KnowledgeEmbeddingStatus = Literal["completed", "fallback"]


class KnowledgeOverviewResponseData(BaseModel):
    qa_count: int
    enabled_qa_count: int
    document_count: int
    completed_document_count: int
    latest_updated_at: str


class KnowledgeRecentItem(BaseModel):
    type: KnowledgeRecentType
    id: str
    title: str
    status: KnowledgeQaStatus | KnowledgeDocumentStatus
    updated_at: str


class KnowledgeRecentResponseData(BaseModel):
    items: list[KnowledgeRecentItem]


class KnowledgeQaRead(BaseModel):
    id: str
    question: str
    answer: str
    status: KnowledgeQaStatus
    created_at: str
    updated_at: str


class KnowledgeQaListResponseData(BaseModel):
    items: list[KnowledgeQaRead]
    total: int
    page: int
    page_size: int


class KnowledgeQaCreate(BaseModel):
    question: str
    answer: str
    status: KnowledgeQaStatus


class KnowledgeQaUpdate(BaseModel):
    question: str
    answer: str
    status: KnowledgeQaStatus


class KnowledgeQaMutationResponseData(BaseModel):
    qa: KnowledgeQaRead
    embedding_status: KnowledgeEmbeddingStatus


class KnowledgeQaDeleteResponseData(BaseModel):
    deleted: bool
    qa_id: str
