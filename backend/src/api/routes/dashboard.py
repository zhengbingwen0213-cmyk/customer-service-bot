"""Customer-service dashboard routes."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Query, status
from pycore.api import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.models.common import ApiEnvelope
from src.models.dashboard import DashboardSummaryResponseData, DashboardTicketsResponseData
from src.repositories.knowledge import KnowledgeRepository
from src.repositories.ticket import TicketRepository
from src.services.dashboard import DashboardService, DashboardValidationError

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=ApiEnvelope[DashboardSummaryResponseData])
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[DashboardSummaryResponseData]:
    service = DashboardService(TicketRepository(db), KnowledgeRepository(db))
    data = await service.get_summary(user=current_user)
    return ApiEnvelope(code=200, message="success", data=data)


@router.get("/tickets", response_model=ApiEnvelope[DashboardTicketsResponseData])
async def get_dashboard_tickets(
    limit: int = Query(5),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[DashboardTicketsResponseData]:
    service = DashboardService(TicketRepository(db), KnowledgeRepository(db))
    try:
        data = await service.list_tickets(user=current_user, limit=limit)
    except DashboardValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ApiEnvelope(code=200, message="success", data=data)
