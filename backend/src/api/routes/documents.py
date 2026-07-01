"""Document ingestion routes."""

from __future__ import annotations

from fastapi import Depends, File, Form, HTTPException, Query, UploadFile, status
from pycore.api import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.models.common import ApiEnvelope
from src.models.documents import (
    DocumentDeleteResponseData,
    DocumentDetailResponseData,
    DocumentListResponseData,
    DocumentMutationResponseData,
)
from src.repositories.documents import DocumentRepository
from src.services.documents import (
    DocumentNotFoundError,
    DocumentService,
    DocumentValidationError,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=ApiEnvelope[DocumentListResponseData])
async def list_documents(
    keyword: str | None = Query(None),
    document_status: str | None = Query(None, alias="status"),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[DocumentListResponseData]:
    del current_user
    service = DocumentService(DocumentRepository(db))
    try:
        data = await service.list_documents(
            keyword=keyword,
            status=document_status,
            page=page,
            page_size=page_size,
        )
    except DocumentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ApiEnvelope(code=200, message="success", data=data)


@router.post("", response_model=ApiEnvelope[DocumentMutationResponseData])
async def upload_document(
    file: UploadFile = File(...),
    name: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[DocumentMutationResponseData]:
    service = DocumentService(DocumentRepository(db))
    try:
        document = await service.upload_document(file=file, name=name, user=current_user)
    except DocumentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ApiEnvelope(
        code=200,
        message="success",
        data=DocumentMutationResponseData(document=document),
    )


@router.get("/{document_id}", response_model=ApiEnvelope[DocumentDetailResponseData])
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[DocumentDetailResponseData]:
    del current_user
    service = DocumentService(DocumentRepository(db))
    try:
        document = await service.get_document(document_id=document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ApiEnvelope(
        code=200,
        message="success",
        data=DocumentDetailResponseData(document=document),
    )


@router.delete("/{document_id}", response_model=ApiEnvelope[DocumentDeleteResponseData])
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiEnvelope[DocumentDeleteResponseData]:
    del current_user
    service = DocumentService(DocumentRepository(db))
    try:
        await service.delete_document(document_id=document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ApiEnvelope(
        code=200,
        message="success",
        data=DocumentDeleteResponseData(deleted=True, document_id=document_id),
    )
