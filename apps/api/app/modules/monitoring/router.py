from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import WorkspaceContext, require_permission
from apps.api.app.infrastructure.database.session import get_db
from apps.api.app.modules.monitoring.schemas import (
    DriftReportResponse,
    MonitoringOverviewResponse,
    RunDriftRequest,
)
from apps.api.app.modules.monitoring.service import MonitoringService
from apps.api.app.shared.enums.roles import Permission
from apps.api.app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/monitoring", tags=["Monitoring & Drift"])

@router.get("/overview", response_model=APIResponse[MonitoringOverviewResponse])
async def get_monitoring_overview(
    ctx: WorkspaceContext = Depends(require_permission(Permission.MONITORING_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = MonitoringService(db)
    data = await service.get_overview(ctx.workspace_id)
    return APIResponse(data=data)

@router.get("/drift", response_model=APIResponse[Optional[DriftReportResponse]])
async def get_latest_drift(
    ctx: WorkspaceContext = Depends(require_permission(Permission.MONITORING_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = MonitoringService(db)
    report = await service.get_latest_drift_report(ctx.workspace_id)
    return APIResponse(data=report)

@router.post("/drift/run", response_model=APIResponse[DriftReportResponse], status_code=status.HTTP_201_CREATED)
async def run_drift_calculation(
    req: RunDriftRequest,
    ctx: WorkspaceContext = Depends(require_permission(Permission.MONITORING_RUN)),
    db: AsyncSession = Depends(get_db),
):
    service = MonitoringService(db)
    report = await service.run_drift_analysis(ctx.workspace_id, req)
    return APIResponse(data=report, message="Drift analysis completed.")
