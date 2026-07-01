"""Document ingestion business logic."""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast
from uuid import uuid4

from fastapi import UploadFile
from pycore.core import get_logger

from src.core.config import get_settings
from src.db.models import Document, DocumentChunk, User
from src.models.documents import DocumentListResponseData, DocumentRead, DocumentStatus
from src.repositories.documents import DocumentRepository
from src.services.ai_gateway import BailianGateway
from src.services.document_parsing import (
    DocumentParseError,
    extract_text,
    validate_supported_filename,
)

CHINA_STANDARD_TIME = timezone(timedelta(hours=8))
VALID_DOCUMENT_STATUSES = {"processing", "completed", "failed"}
MAX_CHUNK_CHARS = 1000
CHUNK_OVERLAP_CHARS = 120


class DocumentValidationError(ValueError):
    """Raised when document API input is outside the public contract."""


class DocumentNotFoundError(ValueError):
    """Raised when the requested document does not exist."""


class DocumentService:
    def __init__(self, repo: DocumentRepository) -> None:
        self.repo = repo
        self.logger = get_logger()

    async def list_documents(
        self,
        *,
        keyword: str | None,
        status: str | None,
        page: int,
        page_size: int,
    ) -> DocumentListResponseData:
        normalized_status = _normalize_status(status)
        if page < 1 or page_size < 1:
            raise DocumentValidationError("分页参数不合法")
        normalized_keyword = keyword.strip() if keyword else None

        documents, total = await self.repo.list_documents(
            keyword=normalized_keyword,
            status=normalized_status,
            page=page,
            page_size=page_size,
        )
        return DocumentListResponseData(
            items=[_to_document_read(document) for document in documents],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_document(self, *, document_id: str) -> DocumentRead:
        document = await self.repo.get_document(document_id)
        if document is None:
            raise DocumentNotFoundError("文档不存在")
        return _to_document_read(document)

    async def upload_document(
        self,
        *,
        file: UploadFile,
        name: str | None,
        user: User,
    ) -> DocumentRead:
        original_filename = Path(file.filename or "").name
        display_name = (name or original_filename).strip()
        if not original_filename or not display_name:
            raise DocumentValidationError("文件不能为空")
        try:
            validate_supported_filename(original_filename)
        except DocumentParseError as exc:
            raise DocumentValidationError(str(exc)) from exc

        content = await file.read()
        if not content:
            raise DocumentValidationError("文件不能为空")

        now = datetime.now(CHINA_STANDARD_TIME)
        document_id = f"doc_{uuid4().hex[:12]}"
        storage_path = _document_storage_path(document_id, original_filename)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_bytes(content)

        document = Document(
            id=document_id,
            name=display_name,
            status="processing",
            chunk_count=0,
            storage_path=str(storage_path),
            uploaded_by_id=user.id,
            created_at=now,
            updated_at=now,
        )
        await self.repo.create_document(document)

        try:
            text = extract_text(storage_path)
            chunks = _split_text(text)
            if not chunks:
                raise DocumentParseError("文档未包含可入库文本")

            created_chunks = await self.repo.replace_chunks(
                document_id=document.id,
                chunks=chunks,
                created_at=now,
            )
            await self._sync_chunk_embeddings(created_chunks, updated_at=now)
            document = await self.repo.update_document_status(
                document,
                status="completed",
                chunk_count=len(created_chunks),
                updated_at=datetime.now(CHINA_STANDARD_TIME),
            )
        except DocumentParseError as exc:
            self.logger.warning(
                "Document parsing failed",
                document_id=document.id,
                error_msg=str(exc),
            )
            document = await self.repo.update_document_status(
                document,
                status="failed",
                chunk_count=0,
                updated_at=datetime.now(CHINA_STANDARD_TIME),
            )

        await self.repo.commit()
        return _to_document_read(document, uploaded_by_name=user.name)

    async def delete_document(self, *, document_id: str) -> None:
        document = await self.repo.get_document(document_id)
        if document is None:
            raise DocumentNotFoundError("文档不存在")

        storage_path = Path(document.storage_path)
        await self.repo.delete_document(document)
        await self.repo.commit()
        _remove_storage_path(storage_path)

    async def _sync_chunk_embeddings(
        self,
        chunks: list[DocumentChunk],
        *,
        updated_at: datetime,
    ) -> None:
        try:
            result = await BailianGateway().create_embeddings(
                [chunk.content for chunk in chunks]
            )
        except Exception as exc:
            self.logger.warning(
                "Document embedding unavailable; using keyword retrieval fallback",
                error_msg=str(exc),
            )
            return

        embedding_vectors = [
            item.embedding for item in sorted(result.embeddings, key=lambda item: item.index)
        ]
        if len(embedding_vectors) != len(chunks):
            self.logger.warning(
                "Document embedding count mismatch; using keyword retrieval fallback",
                chunk_count=len(chunks),
                embedding_count=len(embedding_vectors),
            )
            return

        await self.repo.insert_chunk_vectors(
            chunks=chunks,
            embedding_vectors=embedding_vectors,
            embedding_model=result.model,
            vector_dimension=result.dimensions,
            created_at=updated_at,
        )


def _normalize_status(value: str | None) -> str | None:
    normalized = value.strip() if value else None
    if not normalized:
        return None
    if normalized not in VALID_DOCUMENT_STATUSES:
        raise DocumentValidationError("status 参数不合法")
    return normalized


def _document_storage_path(document_id: str, filename: str) -> Path:
    upload_dir = Path(get_settings().upload_dir)
    safe_name = _safe_filename(filename)
    return (upload_dir / document_id / safe_name).resolve()


def _safe_filename(filename: str) -> str:
    base = Path(filename).name.strip()
    safe = re.sub(r"[^A-Za-z0-9._ -]+", "_", base).strip(" .")
    return safe or f"document_{uuid4().hex}"


def _split_text(text: str) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + MAX_CHUNK_CHARS)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(normalized):
            break
        start = max(end - CHUNK_OVERLAP_CHARS, start + 1)
    return chunks


def _remove_storage_path(path: Path) -> None:
    if path.exists():
        path.unlink()
    parent = path.parent
    try:
        parent.rmdir()
    except OSError:
        shutil.rmtree(parent, ignore_errors=True)


def _to_document_read(
    document: Document,
    *,
    uploaded_by_name: str | None = None,
) -> DocumentRead:
    uploader_name = uploaded_by_name or document.uploaded_by.name
    return DocumentRead(
        id=document.id,
        name=document.name,
        status=cast(DocumentStatus, document.status),
        chunk_count=document.chunk_count,
        uploaded_by=uploader_name,
        created_at=_format_datetime(document.created_at),
        updated_at=_format_datetime(document.updated_at),
    )


def _format_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=CHINA_STANDARD_TIME)
    else:
        value = value.astimezone(CHINA_STANDARD_TIME)
    return value.isoformat()
