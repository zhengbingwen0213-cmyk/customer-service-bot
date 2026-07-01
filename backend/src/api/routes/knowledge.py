"""Knowledge overview and QA management routes."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Query, status
from pycore.api import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.models.common import ApiEnvelope
from src.models.knowledge import (
    KnowledgeOverviewResponseData,
    KnowledgeQaCreate,
    KnowledgeQaDeleteResponseData,
    KnowledgeQaListResponseData,
    KnowledgeQaMutationResponseData,
    KnowledgeQaUpdate,
    KnowledgeRecentResponseData,
)
from src.repositories.knowledge import KnowledgeRepository
from src.services.knowledge import (
    KnowledgeNotFoundError,
    KnowledgeService,
    KnowledgeValidationError,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/overview", response_model=ApiEnvelope[KnowledgeOverviewResponseData])
async def get_knowledge_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[KnowledgeOverviewResponseData]:
    del current_user
    service = KnowledgeService(KnowledgeRepository(db))
    return ApiEnvelope(code=200, message="success", data=await service.get_overview())


@router.get("/recent", response_model=ApiEnvelope[KnowledgeRecentResponseData])
async def get_recent_knowledge(
    limit: int = Query(5),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[KnowledgeRecentResponseData]:
    del current_user
    service = KnowledgeService(KnowledgeRepository(db))
    try:
        data = await service.list_recent(limit=limit)
    except KnowledgeValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ApiEnvelope(code=200, message="success", data=data)


@router.get("/qa", response_model=ApiEnvelope[KnowledgeQaListResponseData])
async def list_knowledge_qa(
    keyword: str | None = Query(None),
    qa_status: str | None = Query(None, alias="status"),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[KnowledgeQaListResponseData]:
    del current_user
    service = KnowledgeService(KnowledgeRepository(db))
    try:
        data = await service.list_qa(
            keyword=keyword,
            status=qa_status,
            page=page,
            page_size=page_size,
        )
    except KnowledgeValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ApiEnvelope(code=200, message="success", data=data)


@router.post("/qa", response_model=ApiEnvelope[KnowledgeQaMutationResponseData])
async def create_knowledge_qa(
    payload: KnowledgeQaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[KnowledgeQaMutationResponseData]:
    del current_user
    service = KnowledgeService(KnowledgeRepository(db))
    try:
        qa, embedding_status = await service.create_qa(
            question=payload.question,
            answer=payload.answer,
            status=payload.status,
        )
    except KnowledgeValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ApiEnvelope(
        code=200,
        message="success",
        data=KnowledgeQaMutationResponseData(qa=qa, embedding_status=embedding_status),
    )


@router.put("/qa/{qa_id}", response_model=ApiEnvelope[KnowledgeQaMutationResponseData])
async def update_knowledge_qa(
    qa_id: str,
    payload: KnowledgeQaUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[KnowledgeQaMutationResponseData]:
    del current_user
    service = KnowledgeService(KnowledgeRepository(db))
    try:
        qa, embedding_status = await service.update_qa(
            qa_id=qa_id,
            question=payload.question,
            answer=payload.answer,
            status=payload.status,
        )
    except KnowledgeValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ApiEnvelope(
        code=200,
        message="success",
        data=KnowledgeQaMutationResponseData(qa=qa, embedding_status=embedding_status),
    )


@router.delete("/qa/{qa_id}", response_model=ApiEnvelope[KnowledgeQaDeleteResponseData])
async def delete_knowledge_qa(
    qa_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[KnowledgeQaDeleteResponseData]:
    del current_user
    service = KnowledgeService(KnowledgeRepository(db))
    try:
        await service.delete_qa(qa_id=qa_id)
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ApiEnvelope(
        code=200,
        message="success",
        data=KnowledgeQaDeleteResponseData(deleted=True, qa_id=qa_id),
    )
