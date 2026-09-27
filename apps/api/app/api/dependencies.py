from typing import Annotated, Optional
from fastapi import Cookie, Depends, Header, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.core.exceptions import ForbiddenException, UnauthorizedException
from apps.api.app.core.security import decode_token
from apps.api.app.infrastructure.database.models import User, Workspace, WorkspaceMember
from apps.api.app.infrastructure.database.session import get_db
from apps.api.app.shared.enums.roles import Permission, has_permission

security_bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    access_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token
    elif "Authorization" in request.headers:
        auth_header = request.headers["Authorization"]
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise UnauthorizedException("Authentication token required.")

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if not user_id or token_type != "access":
            raise UnauthorizedException("Invalid authentication token.")
    except Exception:
        raise UnauthorizedException("Could not validate credentials.")

    result = await db.execute(
        select(User).options(selectinload(User.memberships)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User no longer exists.")
    if not user.is_active:
        raise ForbiddenException("User account is disabled.")

    return user

class WorkspaceContext:
    def __init__(self, workspace: Workspace, membership: WorkspaceMember, user: User):
        self.workspace = workspace
        self.workspace_id = workspace.id
        self.membership = membership
        self.role = membership.role
        self.user = user

async def get_workspace_context(
    request: Request,
    user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceContext:
    target_ws_id = (
        x_workspace_id
        or request.path_params.get("workspace_id")
        or request.query_params.get("workspace_id")
    )

    # If no workspace specified, pick user's first available workspace
    if not target_ws_id:
        if user.memberships:
            target_ws_id = user.memberships[0].workspace_id
        else:
            raise ForbiddenException("User does not belong to any workspace.")

    # Validate membership for tenant isolation
    stmt = (
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.workspace))
        .where(
            WorkspaceMember.workspace_id == target_ws_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership:
        raise ForbiddenException(f"Access denied: You are not a member of workspace '{target_ws_id}'.")

    return WorkspaceContext(
        workspace=membership.workspace,
        membership=membership,
        user=user,
    )

def require_permission(perm: Permission):
    def _permission_checker(ctx: WorkspaceContext = Depends(get_workspace_context)) -> WorkspaceContext:
        if not has_permission(ctx.role, perm):
            raise ForbiddenException(
                f"Role '{ctx.role}' does not have required permission '{perm.value}' in workspace '{ctx.workspace.name}'."
            )
        return ctx
    return _permission_checker
