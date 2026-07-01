"""Dashboard API DTOs aligned with docs/api-contracts.md."""

from __future__ import annotations

from pydantic import BaseModel

from src.models.tickets import TicketPriority, TicketStatus


class DashboardSummaryResponseData(BaseModel):
    open_ticket_count: int
    processing_ticket_count: int
    completed_ticket_count: int
    qa_count: int
    document_count: int
    latest_knowledge_updated_at: str


class DashboardTicketDto(BaseModel):
    id: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    assignee_id: str | None
    assignee_name: str | None
    customer_name: str
    created_at: str
    completed_at: str | None


class DashboardTicketsResponseData(BaseModel):
    items: list[DashboardTicketDto]
