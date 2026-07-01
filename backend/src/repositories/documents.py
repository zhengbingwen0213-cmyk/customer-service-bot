"""Document ingestion data access."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.db.models import Document, DocumentChunk, VectorIndex


class DocumentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_documents(
        self,
        *,
        keyword: str | None,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Document], int]:
        statement = self._document_statement(keyword=keyword, status=status)
        total_result = await self.db.execute(select(func.count()).select_from(statement.subquery()))
        total = int(total_result.scalar_one())

        rows_result = await self.db.execute(
            statement.options(joinedload(Document.uploaded_by))
            .order_by(Document.updated_at.desc(), Document.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows_result.scalars().all()), total

    async def get_document(self, document_id: str) -> Document | None:
        result = await self.db.execute(
            select(Document)
            .options(joinedload(Document.uploaded_by))
            .where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def create_document(self, document: Document) -> Document:
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def update_document_status(
        self,
        document: Document,
        *,
        status: str,
        chunk_count: int,
        updated_at: datetime,
    ) -> Document:
        document.status = status
        document.chunk_count = chunk_count
        document.updated_at = updated_at
        await self.db.flush()
        await self.db.refresh(document, attribute_names=["uploaded_by"])
        return document

    async def replace_chunks(
        self,
        *,
        document_id: str,
        chunks: list[str],
        created_at: datetime,
    ) -> list[DocumentChunk]:
        await self.delete_document_vectors(document_id)
        await self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        created_chunks = [
            DocumentChunk(
                id=f"{document_id}_chunk_{index + 1:04d}",
                document_id=document_id,
                content=content,
                chunk_index=index,
                created_at=created_at,
            )
            for index, content in enumerate(chunks)
        ]
        self.db.add_all(created_chunks)
        await self.db.flush()
        return created_chunks

    async def insert_chunk_vectors(
        self,
        *,
        chunks: list[DocumentChunk],
        embedding_vectors: list[list[float]],
        embedding_model: str,
        vector_dimension: int,
        created_at: datetime,
    ) -> None:
        vectors = [
            VectorIndex(
                id=f"vec_{chunk.id}",
                source_type="document_chunk",
                source_id=chunk.id,
                vector_dimension=vector_dimension,
                embedding_model=embedding_model,
                embedding_vector=json.dumps(embedding_vectors[index], ensure_ascii=False),
                created_at=created_at,
            )
            for index, chunk in enumerate(chunks)
        ]
        self.db.add_all(vectors)
        await self.db.flush()

    async def delete_document_vectors(self, document_id: str) -> None:
        chunk_ids = select(DocumentChunk.id).where(DocumentChunk.document_id == document_id)
        await self.db.execute(
            delete(VectorIndex).where(
                VectorIndex.source_type == "document_chunk",
                VectorIndex.source_id.in_(chunk_ids),
            )
        )
        await self.db.flush()

    async def delete_document(self, document: Document) -> None:
        await self.delete_document_vectors(document.id)
        await self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        await self.db.delete(document)
        await self.db.flush()

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    def _document_statement(
        self,
        *,
        keyword: str | None,
        status: str | None,
    ) -> Select[tuple[Document]]:
        statement = select(Document)
        if status:
            statement = statement.where(Document.status == status)
        if keyword:
            statement = statement.where(Document.name.ilike(f"%{keyword}%"))
        return statement
