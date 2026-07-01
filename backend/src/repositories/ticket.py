"""Ticket data access."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import ConversationMessage, Ticket


@dataclass(frozen=True)
class DashboardTicketCounts:
    open: int
    processing: int
    completed: int


class TicketRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_pool(
        self,
        *,
        status: str | None,
        priority: str | None,
        keyword: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Ticket], int]:
        statement = self._pool_statement(status=status, priority=priority, keyword=keyword)
        count_statement = select(func.count()).select_from(statement.subquery())

        total_result = await self.db.execute(count_statement)
        total = int(total_result.scalar_one())

        rows_result = await self.db.execute(
            statement.options(
                selectinload(Ticket.assignee),
                selectinload(Ticket.customer),
            )
            .order_by(Ticket.created_at.desc(), Ticket.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows_result.scalars().all()), total

    async def list_mine(
        self,
        *,
        assignee_id: str,
        status: str | None,
        priority: str | None,
        keyword: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Ticket], int]:
        statement = self._mine_statement(
            assignee_id=assignee_id,
            status=status,
            priority=priority,
            keyword=keyword,
        )
        count_statement = select(func.count()).select_from(statement.subquery())

        total_result = await self.db.execute(count_statement)
        total = int(total_result.scalar_one())

        rows_result = await self.db.execute(
            statement.options(
                selectinload(Ticket.assignee),
                selectinload(Ticket.customer),
            )
            .order_by(Ticket.updated_at.desc(), Ticket.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows_result.scalars().all()), total

    async def dashboard_counts(self, *, assignee_id: str) -> DashboardTicketCounts:
        open_result = await self.db.execute(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.status == "open", Ticket.assignee_id.is_(None))
        )
        processing_result = await self.db.execute(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.assignee_id == assignee_id, Ticket.status == "processing")
        )
        completed_result = await self.db.execute(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.assignee_id == assignee_id, Ticket.status == "completed")
        )
        return DashboardTicketCounts(
            open=int(open_result.scalar_one()),
            processing=int(processing_result.scalar_one()),
            completed=int(completed_result.scalar_one()),
        )

    async def list_dashboard_tickets(self, *, assignee_id: str, limit: int) -> list[Ticket]:
        priority_rank = case(
            (Ticket.priority == "high", 0),
            (Ticket.priority == "medium", 1),
            (Ticket.priority == "low", 2),
            else_=3,
        )
        result = await self.db.execute(
            select(Ticket)
            .where(Ticket.assignee_id == assignee_id, Ticket.status == "processing")
            .options(
                selectinload(Ticket.assignee),
                selectinload(Ticket.customer),
            )
            .order_by(priority_rank.asc(), Ticket.updated_at.desc(), Ticket.id.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, ticket_id: str) -> Ticket | None:
        result = await self.db.execute(
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(
                selectinload(Ticket.assignee),
                selectinload(Ticket.customer),
            )
        )
        return result.scalar_one_or_none()

    async def list_messages(self, ticket_id: str) -> list[ConversationMessage]:
        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.ticket_id == ticket_id)
            .order_by(ConversationMessage.created_at.asc(), ConversationMessage.id.asc())
        )
        return list(result.scalars().all())

    async def add_message(self, message: ConversationMessage) -> ConversationMessage:
        self.db.add(message)
        await self.db.flush()
        return message

    async def commit(self) -> None:
        await self.db.commit()

    def _pool_statement(
        self,
        *,
        status: str | None,
        priority: str | None,
        keyword: str | None,
    ) -> Select[tuple[Ticket]]:
        statement = select(Ticket).where(
            Ticket.status == "open",
            Ticket.assignee_id.is_(None),
        )
        if status:
            statement = statement.where(Ticket.status == status)
        if priority:
            statement = statement.where(Ticket.priority == priority)
        if keyword:
            pattern = f"%{keyword}%"
            statement = statement.where(
                or_(
                    Ticket.title.ilike(pattern),
                    Ticket.description.ilike(pattern),
                )
            )
        return statement

    def _mine_statement(
        self,
        *,
        assignee_id: str,
        status: str | None,
        priority: str | None,
        keyword: str | None,
    ) -> Select[tuple[Ticket]]:
        statement = select(Ticket).where(
            Ticket.assignee_id == assignee_id,
            Ticket.status.in_(("processing", "completed")),
        )
        if status:
            statement = statement.where(Ticket.status == status)
        if priority:
            statement = statement.where(Ticket.priority == priority)
        if keyword:
            pattern = f"%{keyword}%"
            statement = statement.where(
                or_(
                    Ticket.title.ilike(pattern),
                    Ticket.description.ilike(pattern),
                )
            )
        return statement
