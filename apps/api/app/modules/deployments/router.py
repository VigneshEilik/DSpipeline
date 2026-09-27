from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import WorkspaceContext, require_permission
from apps.api.app.infrastructure.database.session import get_db
from apps.api.app.modules.deployments.schemas import (
    CreateDeploymentRequest,
    DeploymentDetailResponse,
    DeploymentSummary,
    RollbackDeploymentRequest,
)
from apps.api.app.modules.deployments.service import DeploymentService
from apps.api.app.shared.enums.roles import Permission
from apps.api.app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/deployments", tags=["Deployments"])

@router.post("", response_model=APIResponse[DeploymentDetailResponse], status_code=status.HTTP_201_CREATED)
async def create_deployment(
    req: CreateDeploymentRequest,
    ctx: WorkspaceContext = Depends(require_permission(Permission.DEPLOYMENT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = DeploymentService(db)
    deployment = await service.create_deployment(ctx.workspace_id, ctx.user.email, req)
    return APIResponse(data=deployment, message="Model version successfully deployed and activated for serving.")

@router.get("", response_model=APIResponse[List[DeploymentSummary]])
async def list_deployments(
    ctx: WorkspaceContext = Depends(require_permission(Permission.DEPLOYMENT_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = DeploymentService(db)
    items = await service.list_deployments(ctx.workspace_id)
    return APIResponse(data=items)

@router.get("/{deployment_id}", response_model=APIResponse[DeploymentDetailResponse])
async def get_deployment(
    deployment_id: str,
    ctx: WorkspaceContext = Depends(require_permission(Permission.DEPLOYMENT_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = DeploymentService(db)
    d = await service.get_deployment(ctx.workspace_id, deployment_id)
    return APIResponse(data=d)

@router.post("/{deployment_id}/rollback", response_model=APIResponse[DeploymentDetailResponse])
async def rollback_deployment(
    deployment_id: str,
    req: RollbackDeploymentRequest,
    ctx: WorkspaceContext = Depends(require_permission(Permission.DEPLOYMENT_ROLLBACK)),
    db: AsyncSession = Depends(get_db),
):
    service = DeploymentService(db)
    rolled_back = await service.rollback_deployment(ctx.workspace_id, ctx.user.email, deployment_id, req)
    return APIResponse(data=rolled_back, message="Deployment successfully rolled back.")
