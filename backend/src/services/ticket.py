"""Ticket pool query and manual claim business logic."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import cast
from uuid import uuid4

from src.db.models import ConversationMessage, Ticket, User
from src.models.tickets import (
    ClaimedTicket,
    CompletedTicket,
    TicketCustomer,
    TicketDetail,
    TicketDetailResponseData,
    TicketListItem,
    TicketMessage,
    TicketMessageSender,
    TicketMessagesResponseData,
    TicketPriority,
    TicketsListResponseData,
    TicketStatus,
)
from src.repositories.ticket import TicketRepository

CHINA_STANDARD_TIME = timezone(timedelta(hours=8))
VALID_STATUSES = {"open", "processing", "completed"}
VALID_PRIORITIES = {"low", "medium", "high"}


class InvalidTicketFilter(ValueError):
    """Raised when a ticket list query parameter is outside the API contract."""


class TicketNotFoundError(ValueError):
    """Raised when the requested ticket does not exist."""


class TicketForbiddenError(PermissionError):
    """Raised when the current user cannot view the requested ticket."""


class TicketAlreadyClaimedError(ValueError):
    """Raised when a ticket is no longer claimable from the pool."""


class TicketReplyValidationError(ValueError):
    """Raised when an employee reply payload is outside the API contract."""


class TicketActionForbiddenError(PermissionError):
    """Raised when the current user cannot mutate the requested ticket."""


class TicketService:
    def __init__(self, repo: TicketRepository) -> None:
        self.repo = repo

    async def list_pool(
        self,
        *,
        status: str | None,
        priority: str | None,
        keyword: str | None,
        page: int,
        page_size: int,
    ) -> TicketsListResponseData:
        normalized_status = _normalize_status(status)
        normalized_priority = _normalize_priority(priority)
        normalized_keyword = keyword.strip() if keyword else None

        tickets, total = await self.repo.list_pool(
            status=normalized_status,
            priority=normalized_priority,
            keyword=normalized_keyword,
            page=page,
            page_size=page_size,
        )
        return TicketsListResponseData(
            items=[_to_ticket_list_item(ticket) for ticket in tickets],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def list_mine(
        self,
        *,
        user: User,
        status: str | None,
        priority: str | None,
        keyword: str | None,
        page: int,
        page_size: int,
    ) -> TicketsListResponseData:
        normalized_status = _normalize_status(status)
        normalized_priority = _normalize_priority(priority)
        normalized_keyword = keyword.strip() if keyword else None

        tickets, total = await self.repo.list_mine(
            assignee_id=user.id,
            status=normalized_status,
            priority=normalized_priority,
            keyword=normalized_keyword,
            page=page,
            page_size=page_size,
        )
        return TicketsListResponseData(
            items=[_to_ticket_list_item(ticket) for ticket in tickets],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_detail(self, *, ticket_id: str, user: User) -> TicketDetailResponseData:
        ticket = await self.repo.get_by_id(ticket_id)
        if ticket is None:
            raise TicketNotFoundError("工单不存在")
        if not _is_ticket_visible_to_user(ticket, user):
            raise TicketForbiddenError("无权查看该工单")
        return TicketDetailResponseData(ticket=_to_ticket_detail(ticket))

    async def claim(self, *, ticket_id: str, user: User) -> ClaimedTicket:
        ticket = await self.repo.get_by_id(ticket_id)
        if ticket is None:
            raise TicketNotFoundError("工单不存在")
        if ticket.status != "open" or ticket.assignee_id is not None:
            raise TicketAlreadyClaimedError("工单已被接取")

        updated_at = datetime.now(CHINA_STANDARD_TIME)
        ticket.status = "processing"
        ticket.assignee_id = user.id
        ticket.assignee = user
        ticket.updated_at = updated_at

        await self.repo.commit()
        return ClaimedTicket(
            id=ticket.id,
            status="processing",
            assignee_id=user.id,
            assignee_name=user.name,
            updated_at=_format_datetime(updated_at),
        )

    async def list_messages(self, *, ticket_id: str, user: User) -> TicketMessagesResponseData:
        ticket = await self.repo.get_by_id(ticket_id)
        if ticket is None:
            raise TicketNotFoundError("工单不存在")
        if not _is_ticket_visible_to_user(ticket, user):
            raise TicketForbiddenError("无权查看该工单")

        messages = await self.repo.list_messages(ticket_id)
        return TicketMessagesResponseData(
            items=[_to_ticket_message(message) for message in messages]
        )

    async def send_message(
        self,
        *,
        ticket_id: str,
        user: User,
        content: str,
        used_assistant_answer_id: str | None,
    ) -> TicketMessage:
        ticket = await self.repo.get_by_id(ticket_id)
        if ticket is None:
            raise TicketNotFoundError("工单不存在")
        if not _is_ticket_mutable_by_user(ticket, user):
            raise TicketActionForbiddenError("只能回复当前账号已接取的工单")

        normalized_content = content.strip()
        if not normalized_content:
            raise TicketReplyValidationError("回复内容不能为空")

        created_at = datetime.now(CHINA_STANDARD_TIME)
        message = ConversationMessage(
            id=f"msg_{uuid4().hex[:12]}",
            ticket_id=ticket.id,
            sender="employee",
            sender_name=user.name,
            content=normalized_content,
            used_assistant_answer_id=used_assistant_answer_id,
            created_at=created_at,
        )
        await self.repo.add_message(message)
        ticket.updated_at = created_at
        await self.repo.commit()
        return _to_ticket_message(message)

    async def complete(
        self,
        *,
        ticket_id: str,
        user: User,
        employee_id: str,
        summary: str,
    ) -> CompletedTicket:
        if employee_id != user.id:
            raise TicketActionForbiddenError("只能完成当前账号已接取的工单")

        ticket = await self.repo.get_by_id(ticket_id)
        if ticket is None:
            raise TicketNotFoundError("工单不存在")
        if not _is_ticket_mutable_by_user(ticket, user):
            raise TicketActionForbiddenError("只能完成当前账号已接取的工单")

        normalized_summary = summary.strip()
        if not normalized_summary:
            raise TicketReplyValidationError("处理摘要不能为空")

        completed_at = datetime.now(CHINA_STANDARD_TIME)
        ticket.status = "completed"
        ticket.completed_at = completed_at
        ticket.completion_summary = normalized_summary
        ticket.updated_at = completed_at
        await self.repo.commit()
        return CompletedTicket(
            id=ticket.id,
            status="completed",
            completed_at=_format_datetime(completed_at),
        )


def _normalize_status(value: str | None) -> str | None:
    normalized = value.strip() if value else None
    if not normalized:
        return None
    if normalized not in VALID_STATUSES:
        raise InvalidTicketFilter("status 参数不合法")
    return normalized


def _normalize_priority(value: str | None) -> str | None:
    normalized = value.strip() if value else None
    if not normalized:
        return None
    if normalized not in VALID_PRIORITIES:
        raise InvalidTicketFilter("priority 参数不合法")
    return normalized


def _to_ticket_list_item(ticket: Ticket) -> TicketListItem:
    return TicketListItem(
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


def _to_ticket_detail(ticket: Ticket) -> TicketDetail:
    return TicketDetail(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        status=cast(TicketStatus, ticket.status),
        priority=cast(TicketPriority, ticket.priority),
        assignee_id=ticket.assignee_id,
        assignee_name=ticket.assignee.name if ticket.assignee else None,
        customer=TicketCustomer(
            id=ticket.customer.id,
            name=ticket.customer.name,
            level=ticket.customer.level,
        ),
        related_order_id=ticket.related_order_id or "",
        created_at=_format_datetime(ticket.created_at),
        completed_at=_format_datetime(ticket.completed_at) if ticket.completed_at else None,
    )


def _is_ticket_visible_to_user(ticket: Ticket, user: User) -> bool:
    if ticket.assignee_id == user.id:
        return True
    return ticket.status == "open" and ticket.assignee_id is None


def _is_ticket_mutable_by_user(ticket: Ticket, user: User) -> bool:
    return ticket.assignee_id == user.id and ticket.status == "processing"


def _to_ticket_message(message: ConversationMessage) -> TicketMessage:
    return TicketMessage(
        id=message.id,
        ticket_id=message.ticket_id,
        sender=cast(TicketMessageSender, message.sender),
        sender_name=message.sender_name,
        content=message.content,
        created_at=_format_datetime(message.created_at),
    )


def _format_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=CHINA_STANDARD_TIME)
    else:
        value = value.astimezone(CHINA_STANDARD_TIME)
    return value.isoformat()
