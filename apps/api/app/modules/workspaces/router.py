from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import WorkspaceContext, get_current_user, get_workspace_context, require_permission
from apps.api.app.infrastructure.database.models import User
from apps.api.app.infrastructure.database.session import get_db
from apps.api.app.modules.workspaces.schemas import AddMemberRequest, CreateWorkspaceRequest, MemberDetail, WorkspaceDetailResponse
from apps.api.app.modules.workspaces.service import WorkspaceService
from apps.api.app.shared.enums.roles import Permission
from apps.api.app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.post("", response_model=APIResponse[WorkspaceDetailResponse], status_code=status.HTTP_201_CREATED)
async def create_workspace(
    req: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkspaceService(db)
    ws = await service.create_workspace(current_user.id, req)
    return APIResponse(data=ws, message="Workspace created.")

@router.get("/{workspace_id}", response_model=APIResponse[WorkspaceDetailResponse])
async def get_workspace_detail(
    workspace_id: str,
    ctx: WorkspaceContext = Depends(require_permission(Permission.WORKSPACE_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = WorkspaceService(db)
    ws = await service.get_workspace(ctx.workspace_id)
    return APIResponse(data=ws)

@router.post("/{workspace_id}/members", response_model=APIResponse[MemberDetail])
async def add_workspace_member(
    workspace_id: str,
    req: AddMemberRequest,
    ctx: WorkspaceContext = Depends(require_permission(Permission.WORKSPACE_MEMBERS_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = WorkspaceService(db)
    member = await service.add_member(ctx.workspace_id, req)
    return APIResponse(data=member, message=f"User {req.email} added with role {req.role.value}.")
