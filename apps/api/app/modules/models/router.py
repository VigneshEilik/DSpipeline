from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import WorkspaceContext, require_permission
from apps.api.app.infrastructure.database.session import get_db
from apps.api.app.modules.models.schemas import (
    ApprovalRequest,
    ModelRegistryResponse,
    ModelVersionResponse,
    RegisterModelRequest,
)
from apps.api.app.modules.models.service import ModelRegistryService
from apps.api.app.shared.enums.roles import Permission
from apps.api.app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/models", tags=["Model Registry"])

@router.post("", response_model=APIResponse[ModelRegistryResponse], status_code=status.HTTP_201_CREATED)
async def register_model(
    req: RegisterModelRequest,
    ctx: WorkspaceContext = Depends(require_permission(Permission.MODEL_REGISTER)),
    db: AsyncSession = Depends(get_db),
):
    service = ModelRegistryService(db)
    model = await service.register_model(ctx.workspace_id, req)
    return APIResponse(data=model, message="Model version successfully registered in registry.")

@router.get("", response_model=APIResponse[List[ModelRegistryResponse]])
async def list_models(
    ctx: WorkspaceContext = Depends(require_permission(Permission.MODEL_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = ModelRegistryService(db)
    models = await service.list_models(ctx.workspace_id)
    return APIResponse(data=models)

@router.get("/{model_id}", response_model=APIResponse[ModelRegistryResponse])
async def get_model(
    model_id: str,
    ctx: WorkspaceContext = Depends(require_permission(Permission.MODEL_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = ModelRegistryService(db)
    model = await service.get_model(ctx.workspace_id, model_id)
    return APIResponse(data=model)

@router.post("/{model_id}/approve", response_model=APIResponse[ModelVersionResponse])
async def approve_model_version(
    model_id: str,
    req: ApprovalRequest,
    ctx: WorkspaceContext = Depends(require_permission(Permission.MODEL_APPROVE)),
    db: AsyncSession = Depends(get_db),
):
    service = ModelRegistryService(db)
    updated_version = await service.approve_model_version(
        workspace_id=ctx.workspace_id,
        user_id=ctx.user.id,
        model_id=model_id,
        req=req,
    )
    return APIResponse(data=updated_version, message=f"Model version stage updated to {req.decision}.")
