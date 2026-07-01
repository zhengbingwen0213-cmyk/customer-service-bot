"""Dashboard overview and quick-ticket business logic."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import cast

from src.db.models import Ticket, User
from src.models.dashboard import (
    DashboardSummaryResponseData,
    DashboardTicketDto,
    DashboardTicketsResponseData,
)
from src.models.tickets import TicketPriority, TicketStatus
from src.repositories.knowledge import KnowledgeRepository
from src.repositories.ticket import TicketRepository

CHINA_STANDARD_TIME = timezone(timedelta(hours=8))


class DashboardValidationError(ValueError):
    """Raised when dashboard query parameters are outside the public contract."""


class DashboardService:
    def __init__(self, ticket_repo: TicketRepository, knowledge_repo: KnowledgeRepository) -> None:
        self.ticket_repo = ticket_repo
        self.knowledge_repo = knowledge_repo

    async def get_summary(self, *, user: User) -> DashboardSummaryResponseData:
        ticket_counts = await self.ticket_repo.dashboard_counts(assignee_id=user.id)
        qa_count, _enabled_qa_count = await self.knowledge_repo.count_qa()
        document_count, _completed_document_count = await self.knowledge_repo.count_documents()
        latest_knowledge_updated_at = await self.knowledge_repo.latest_updated_at()

        return DashboardSummaryResponseData(
            open_ticket_count=ticket_counts.open,
            processing_ticket_count=ticket_counts.processing,
            completed_ticket_count=ticket_counts.completed,
            qa_count=qa_count,
            document_count=document_count,
            latest_knowledge_updated_at=(
                _format_datetime(latest_knowledge_updated_at)
                if latest_knowledge_updated_at
                else ""
            ),
        )

    async def list_tickets(self, *, user: User, limit: int) -> DashboardTicketsResponseData:
        if limit < 1 or limit > 20:
            raise DashboardValidationError("limit 必须为 1 到 20 的整数")

        tickets = await self.ticket_repo.list_dashboard_tickets(
            assignee_id=user.id,
            limit=limit,
        )
        return DashboardTicketsResponseData(
            items=[_to_dashboard_ticket(ticket) for ticket in tickets]
        )


def _to_dashboard_ticket(ticket: Ticket) -> DashboardTicketDto:
    return DashboardTicketDto(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        status=cast(TicketStatus, ticket.status),
        priority=cast(TicketPriority, ticket.priority),
        assignee_id=ticket.assignee_id,
        assignee_name=ticket.assignee.name if ticket.assignee else None,
        customer_name=ticket.customer.name,
        created_at=_format_datetime(ticket.created_at),
        completed_at=_format_datetime(ticket.completed_at) if ticket.completed_at else None,
    )


def _format_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=CHINA_STANDARD_TIME)
    else:
        value = value.astimezone(CHINA_STANDARD_TIME)
    return value.isoformat()
