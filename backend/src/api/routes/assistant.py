"""Assistant ask route for quick, ticket, and debug scenes."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from pycore.api import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.models.assistant import AssistantAskRequest, AssistantAskResponseData
from src.models.common import ApiEnvelope
from src.services.assistant import AssistantModelUnavailableError, AssistantService

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/ask", response_model=ApiEnvelope[AssistantAskResponseData])
async def ask_assistant(
    payload: AssistantAskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[AssistantAskResponseData]:
    del current_user
    service = AssistantService()
    try:
        answer = await service.ask(db, payload)
    except AssistantModelUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="模型服务暂时不可用",
        ) from exc
    return ApiEnvelope(
        code=200,
        message="success",
        data=AssistantAskResponseData(answer=answer),
    )
