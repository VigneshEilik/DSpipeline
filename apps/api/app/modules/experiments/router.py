from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import WorkspaceContext, require_permission
from apps.api.app.infrastructure.database.session import get_db
from apps.api.app.modules.experiments.schemas import (
    CreateExperimentRequest,
    ExperimentDetailResponse,
    ExperimentMetricResponse,
    ExperimentSummary,
)
from apps.api.app.modules.experiments.service import ExperimentService
from apps.api.app.shared.enums.roles import Permission
from apps.api.app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/experiments", tags=["Experiments"])

@router.post("", response_model=APIResponse[ExperimentDetailResponse], status_code=status.HTTP_201_CREATED)
async def create_experiment(
    req: CreateExperimentRequest,
    ctx: WorkspaceContext = Depends(require_permission(Permission.EXPERIMENT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = ExperimentService(db)
    exp = await service.create_and_trigger_experiment(ctx.workspace_id, req)
    return APIResponse(data=exp, message="Experiment initiated and queued for background training.")

@router.get("", response_model=APIResponse[List[ExperimentSummary]])
async def list_experiments(
    ctx: WorkspaceContext = Depends(require_permission(Permission.EXPERIMENT_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = ExperimentService(db)
    items = await service.list_experiments(ctx.workspace_id)
    return APIResponse(data=items)

@router.get("/{experiment_id}", response_model=APIResponse[ExperimentDetailResponse])
async def get_experiment(
    experiment_id: str,
    ctx: WorkspaceContext = Depends(require_permission(Permission.EXPERIMENT_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = ExperimentService(db)
    exp = await service.get_experiment(ctx.workspace_id, experiment_id)
    return APIResponse(data=exp)

@router.get("/{experiment_id}/logs", response_model=APIResponse[dict])
async def get_experiment_logs(
    experiment_id: str,
    ctx: WorkspaceContext = Depends(require_permission(Permission.EXPERIMENT_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = ExperimentService(db)
    exp = await service.get_experiment(ctx.workspace_id, experiment_id)
    return APIResponse(data={"logs": exp.logs, "progress": exp.progress_percentage, "status": exp.status})

@router.get("/{experiment_id}/metrics", response_model=APIResponse[ExperimentMetricResponse])
async def get_experiment_metrics(
    experiment_id: str,
    ctx: WorkspaceContext = Depends(require_permission(Permission.EXPERIMENT_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = ExperimentService(db)
    exp = await service.get_experiment(ctx.workspace_id, experiment_id)
    if not exp.metrics:
        return APIResponse(data=None, message="No metrics available yet. Training may still be in progress.")
    return APIResponse(data=exp.metrics)
