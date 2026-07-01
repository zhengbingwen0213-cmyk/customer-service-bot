"""Ticket pool routes."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Query, status
from pycore.api import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.models.common import ApiEnvelope
from src.models.tickets import (
    ClaimTicketRequest,
    ClaimTicketResponseData,
    CompleteTicketRequest,
    CompleteTicketResponseData,
    SendTicketMessageRequest,
    SendTicketMessageResponseData,
    TicketDetailResponseData,
    TicketMessagesResponseData,
    TicketsListResponseData,
)
from src.repositories.ticket import TicketRepository
from src.services.ticket import (
    InvalidTicketFilter,
    TicketActionForbiddenError,
    TicketAlreadyClaimedError,
    TicketForbiddenError,
    TicketNotFoundError,
    TicketReplyValidationError,
    TicketService,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("", response_model=ApiEnvelope[TicketsListResponseData])
async def list_tickets(
    scope: str = Query("pool"),
    ticket_status: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[TicketsListResponseData]:
    service = TicketService(TicketRepository(db))
    try:
        if scope == "pool":
            data = await service.list_pool(
                status=ticket_status,
                priority=priority,
                keyword=keyword,
                page=page,
                page_size=page_size,
            )
        elif scope == "mine":
            data = await service.list_mine(
                user=current_user,
                status=ticket_status,
                priority=priority,
                keyword=keyword,
                page=page,
                page_size=page_size,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scope 参数不合法",
            )
    except InvalidTicketFilter as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ApiEnvelope(code=200, message="success", data=data)


@router.get("/{ticket_id}/messages", response_model=ApiEnvelope[TicketMessagesResponseData])
async def get_ticket_messages(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[TicketMessagesResponseData]:
    service = TicketService(TicketRepository(db))
    try:
        data = await service.list_messages(ticket_id=ticket_id, user=current_user)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TicketForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return ApiEnvelope(code=200, message="success", data=data)


@router.post("/{ticket_id}/messages", response_model=ApiEnvelope[SendTicketMessageResponseData])
async def send_ticket_message(
    ticket_id: str,
    payload: SendTicketMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[SendTicketMessageResponseData]:
    service = TicketService(TicketRepository(db))
    try:
        message = await service.send_message(
            ticket_id=ticket_id,
            user=current_user,
            content=payload.content,
            used_assistant_answer_id=payload.used_assistant_answer_id,
        )
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TicketActionForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TicketReplyValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ApiEnvelope(
        code=200,
        message="success",
        data=SendTicketMessageResponseData(message=message),
    )


@router.post("/{ticket_id}/complete", response_model=ApiEnvelope[CompleteTicketResponseData])
async def complete_ticket(
    ticket_id: str,
    payload: CompleteTicketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[CompleteTicketResponseData]:
    service = TicketService(TicketRepository(db))
    try:
        completed_ticket = await service.complete(
            ticket_id=ticket_id,
            user=current_user,
            employee_id=payload.employee_id,
            summary=payload.summary,
        )
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TicketActionForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TicketReplyValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ApiEnvelope(
        code=200,
        message="success",
        data=CompleteTicketResponseData(ticket=completed_ticket),
    )


@router.get("/{ticket_id}", response_model=ApiEnvelope[TicketDetailResponseData])
async def get_ticket_detail(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[TicketDetailResponseData]:
    service = TicketService(TicketRepository(db))
    try:
        data = await service.get_detail(ticket_id=ticket_id, user=current_user)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TicketForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return ApiEnvelope(code=200, message="success", data=data)


@router.post("/{ticket_id}/claim", response_model=ApiEnvelope[ClaimTicketResponseData])
async def claim_ticket(
    ticket_id: str,
    payload: ClaimTicketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[ClaimTicketResponseData]:
    if payload.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="employee_id 与当前账号不一致",
        )

    service = TicketService(TicketRepository(db))
    try:
        claimed_ticket = await service.claim(ticket_id=ticket_id, user=current_user)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TicketAlreadyClaimedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ApiEnvelope(
        code=200,
        message="success",
        data=ClaimTicketResponseData(ticket=claimed_ticket),
    )
