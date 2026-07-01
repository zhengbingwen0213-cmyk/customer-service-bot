"""Document ingestion API DTOs aligned with docs/api-contracts.md."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

DocumentStatus = Literal["processing", "completed", "failed"]


class DocumentRead(BaseModel):
    id: str
    name: str
    status: DocumentStatus
    chunk_count: int
    uploaded_by: str
    created_at: str
    updated_at: str


class DocumentListResponseData(BaseModel):
    items: list[DocumentRead]
    total: int
    page: int
    page_size: int


class DocumentMutationResponseData(BaseModel):
    document: DocumentRead


class DocumentDetailResponseData(BaseModel):
    document: DocumentRead


class DocumentDeleteResponseData(BaseModel):
    deleted: bool
    document_id: str
