from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import WorkspaceContext, require_permission
from apps.api.app.infrastructure.database.session import get_db
from apps.api.app.modules.datasets.schemas import (
    DatasetDetailResponse,
    DatasetPreviewResponse,
    DatasetSummary,
    ValidationReportResponse,
)
from apps.api.app.modules.datasets.service import DatasetService
from apps.api.app.shared.enums.roles import Permission
from apps.api.app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.post("", response_model=APIResponse[DatasetDetailResponse], status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    domain: str = Form("churn"),
    target_column: str = Form("Churn"),
    ctx: WorkspaceContext = Depends(require_permission(Permission.DATASET_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    contents = await file.read()
    ds = await service.create_dataset_with_file(
        workspace_id=ctx.workspace_id,
        name=name,
        file_bytes=contents,
        filename=file.filename or "dataset.csv",
        description=description,
        domain=domain,
        target_column=target_column,
    )
    return APIResponse(data=ds, message="Dataset uploaded and validated successfully.")

@router.get("", response_model=APIResponse[List[DatasetSummary]])
async def list_datasets(
    ctx: WorkspaceContext = Depends(require_permission(Permission.DATASET_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    items = await service.list_datasets(ctx.workspace_id)
    return APIResponse(data=items)

@router.get("/{dataset_id}", response_model=APIResponse[DatasetDetailResponse])
async def get_dataset(
    dataset_id: str,
    ctx: WorkspaceContext = Depends(require_permission(Permission.DATASET_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    ds = await service.get_dataset(ctx.workspace_id, dataset_id)
    return APIResponse(data=ds)

@router.get("/{dataset_id}/preview", response_model=APIResponse[DatasetPreviewResponse])
async def get_dataset_preview(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: WorkspaceContext = Depends(require_permission(Permission.DATASET_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    preview = await service.get_dataset_preview(ctx.workspace_id, dataset_id, page=page, page_size=page_size)
    return APIResponse(data=preview)

@router.get("/{dataset_id}/validation", response_model=APIResponse[Optional[ValidationReportResponse]])
async def get_validation_report(
    dataset_id: str,
    ctx: WorkspaceContext = Depends(require_permission(Permission.DATASET_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    ds = await service.get_dataset(ctx.workspace_id, dataset_id)
    return APIResponse(data=ds.latest_validation)
