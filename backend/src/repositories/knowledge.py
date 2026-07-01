"""Knowledge data access."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Document, QaItem, VectorIndex


class KnowledgeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def count_qa(self) -> tuple[int, int]:
        total_result = await self.db.execute(select(func.count()).select_from(QaItem))
        enabled_result = await self.db.execute(
            select(func.count()).select_from(QaItem).where(QaItem.status == "enabled")
        )
        return int(total_result.scalar_one()), int(enabled_result.scalar_one())

    async def count_documents(self) -> tuple[int, int]:
        total_result = await self.db.execute(select(func.count()).select_from(Document))
        completed_result = await self.db.execute(
            select(func.count()).select_from(Document).where(Document.status == "completed")
        )
        return int(total_result.scalar_one()), int(completed_result.scalar_one())

    async def latest_updated_at(self) -> datetime | None:
        qa_result = await self.db.execute(select(func.max(QaItem.updated_at)))
        document_result = await self.db.execute(select(func.max(Document.updated_at)))
        candidates = [
            value
            for value in (qa_result.scalar_one_or_none(), document_result.scalar_one_or_none())
            if isinstance(value, datetime)
        ]
        return max(candidates) if candidates else None

    async def list_recent_qa(self, *, limit: int) -> list[QaItem]:
        result = await self.db.execute(
            select(QaItem).order_by(QaItem.updated_at.desc(), QaItem.id.asc()).limit(limit)
        )
        return list(result.scalars().all())

    async def list_recent_documents(self, *, limit: int) -> list[Document]:
        result = await self.db.execute(
            select(Document).order_by(Document.updated_at.desc(), Document.id.asc()).limit(limit)
        )
        return list(result.scalars().all())

    async def list_qa(
        self,
        *,
        keyword: str | None,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[QaItem], int]:
        statement = self._qa_statement(keyword=keyword, status=status)
        total_result = await self.db.execute(select(func.count()).select_from(statement.subquery()))
        total = int(total_result.scalar_one())

        rows_result = await self.db.execute(
            statement.order_by(QaItem.updated_at.desc(), QaItem.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows_result.scalars().all()), total

    async def get_qa(self, qa_id: str) -> QaItem | None:
        result = await self.db.execute(select(QaItem).where(QaItem.id == qa_id))
        return result.scalar_one_or_none()

    async def create_qa(self, qa: QaItem) -> QaItem:
        self.db.add(qa)
        await self.db.flush()
        await self.db.refresh(qa)
        return qa

    async def upsert_qa_vector(
        self,
        *,
        source_id: str,
        embedding_model: str,
        vector_dimension: int,
        created_at: datetime,
    ) -> VectorIndex:
        existing = await self.get_qa_vector(source_id)
        if existing is not None:
            existing.embedding_model = embedding_model
            existing.vector_dimension = vector_dimension
            existing.created_at = created_at
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        vector = VectorIndex(
            id=f"vec_{source_id}",
            source_type="qa",
            source_id=source_id,
            vector_dimension=vector_dimension,
            embedding_model=embedding_model,
            created_at=created_at,
        )
        self.db.add(vector)
        await self.db.flush()
        await self.db.refresh(vector)
        return vector

    async def get_qa_vector(self, source_id: str) -> VectorIndex | None:
        result = await self.db.execute(
            select(VectorIndex).where(
                VectorIndex.source_type == "qa",
                VectorIndex.source_id == source_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_qa_vector(self, source_id: str) -> None:
        await self.db.execute(
            delete(VectorIndex).where(
                VectorIndex.source_type == "qa",
                VectorIndex.source_id == source_id,
            )
        )
        await self.db.flush()

    async def delete_qa(self, qa: QaItem) -> None:
        await self.db.delete(qa)
        await self.db.flush()

    async def commit(self) -> None:
        await self.db.commit()

    def _qa_statement(self, *, keyword: str | None, status: str | None) -> Select[tuple[QaItem]]:
        statement = select(QaItem)
        if status:
            statement = statement.where(QaItem.status == status)
        if keyword:
            pattern = f"%{keyword}%"
            statement = statement.where(
                or_(QaItem.question.ilike(pattern), QaItem.answer.ilike(pattern))
            )
        return statement
