from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import WorkspaceContext, require_permission
from apps.api.app.infrastructure.database.session import get_db
from apps.api.app.modules.predictions.schemas import (
    BatchPredictionJobResponse,
    PredictionResponse,
    SinglePredictionRequest,
)
from apps.api.app.modules.predictions.service import PredictionService
from apps.api.app.shared.enums.roles import Permission
from apps.api.app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/predictions", tags=["Predictions & Inference"])

@router.post("", response_model=APIResponse[PredictionResponse], status_code=status.HTTP_201_CREATED)
async def predict_single(
    req: SinglePredictionRequest,
    ctx: WorkspaceContext = Depends(require_permission(Permission.PREDICTION_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = PredictionService(db)
    result = await service.predict_single(ctx.workspace_id, req)
    return APIResponse(data=result)

@router.get("", response_model=APIResponse[List[PredictionResponse]])
async def list_predictions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: WorkspaceContext = Depends(require_permission(Permission.PREDICTION_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = PredictionService(db)
    items = await service.list_predictions(ctx.workspace_id, limit=limit, offset=offset)
    return APIResponse(data=items)

@router.get("/{prediction_id}", response_model=APIResponse[PredictionResponse])
async def get_prediction(
    prediction_id: str,
    ctx: WorkspaceContext = Depends(require_permission(Permission.PREDICTION_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = PredictionService(db)
    pred = await service.get_prediction(ctx.workspace_id, prediction_id)
    return APIResponse(data=pred)

@router.post("/batch", response_model=APIResponse[BatchPredictionJobResponse], status_code=status.HTTP_202_ACCEPTED)
async def create_batch_prediction_job(
    file: UploadFile = File(...),
    deployment_id: Optional[str] = Form(None),
    ctx: WorkspaceContext = Depends(require_permission(Permission.PREDICTION_BATCH)),
    db: AsyncSession = Depends(get_db),
):
    service = PredictionService(db)
    contents = await file.read()
    job = await service.create_batch_prediction_job(
        workspace_id=ctx.workspace_id,
        file_bytes=contents,
        filename=file.filename or "batch_input.csv",
        deployment_id=deployment_id,
    )
    return APIResponse(data=job, message="Batch prediction job submitted and processing in background.")

@router.get("/batch/{job_id}", response_model=APIResponse[BatchPredictionJobResponse])
async def get_batch_prediction_job(
    job_id: str,
    ctx: WorkspaceContext = Depends(require_permission(Permission.PREDICTION_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = PredictionService(db)
    job = await service.get_batch_job(ctx.workspace_id, job_id)
    return APIResponse(data=job)
