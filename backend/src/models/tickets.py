"""Ticket API DTOs aligned with docs/api-contracts.md."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

TicketStatus = Literal["open", "processing", "completed"]
TicketPriority = Literal["low", "medium", "high"]


class TicketListItem(BaseModel):
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


class TicketsListResponseData(BaseModel):
    items: list[TicketListItem]
    total: int
    page: int
    page_size: int


class TicketCustomer(BaseModel):
    id: str
    name: str
    level: str


class TicketDetail(BaseModel):
    id: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    assignee_id: str | None
    assignee_name: str | None
    customer: TicketCustomer
    related_order_id: str
    created_at: str
    completed_at: str | None


class TicketDetailResponseData(BaseModel):
    ticket: TicketDetail


class ClaimTicketRequest(BaseModel):
    employee_id: str


class ClaimedTicket(BaseModel):
    id: str
    status: Literal["processing"]
    assignee_id: str
    assignee_name: str
    updated_at: str


class ClaimTicketResponseData(BaseModel):
    ticket: ClaimedTicket


class CompleteTicketRequest(BaseModel):
    employee_id: str
    summary: str


class CompletedTicket(BaseModel):
    id: str
    status: Literal["completed"]
    completed_at: str


class CompleteTicketResponseData(BaseModel):
    ticket: CompletedTicket


TicketMessageSender = Literal["customer", "employee", "bot"]


class TicketMessage(BaseModel):
    id: str
    ticket_id: str
    sender: TicketMessageSender
    sender_name: str
    content: str
    created_at: str


class TicketMessagesResponseData(BaseModel):
    items: list[TicketMessage]


class SendTicketMessageRequest(BaseModel):
    content: str = Field(...)
    used_assistant_answer_id: str | None = None


class SendTicketMessageResponseData(BaseModel):
    message: TicketMessage
