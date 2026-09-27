import re
import uuid
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.core.config import settings
from apps.api.app.core.exceptions import ConflictException, UnauthorizedException
from apps.api.app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from apps.api.app.infrastructure.database.models import User, Workspace, WorkspaceMember
from apps.api.app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserProfileResponse, WorkspaceBrief

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, req: RegisterRequest) -> Tuple[User, TokenResponse]:
        # Check if user already exists
        existing = await self.db.execute(select(User).where(User.email == req.email.lower()))
        if existing.scalar_one_or_none():
            raise ConflictException(f"User with email '{req.email}' already exists.")

        # Create user
        user = User(
            email=req.email.lower(),
            hashed_password=get_password_hash(req.password),
            full_name=req.full_name,
            is_active=True,
            is_superuser=False,
        )
        self.db.add(user)
        await self.db.flush()

        # Create default workspace for user
        ws_name = req.workspace_name or f"{req.full_name}'s Workspace"
        base_slug = re.sub(r"[^a-zA-Z0-9]+", "-", ws_name.lower()).strip("-")
        unique_slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

        workspace = Workspace(
            name=ws_name,
            slug=unique_slug,
            description="Default workspace created upon signup.",
        )
        self.db.add(workspace)
        await self.db.flush()

        # Add user as OWNER of workspace
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role="OWNER",
        )
        self.db.add(member)
        await self.db.commit()

        token = create_access_token(
            subject=user.id,
            workspace_id=workspace.id,
            role="OWNER",
        )

        token_resp = TokenResponse(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            workspace_id=workspace.id,
            role="OWNER",
        )
        return user, token_resp

    async def login(self, req: LoginRequest, selected_workspace_id: Optional[str] = None) -> Tuple[User, TokenResponse]:
        result = await self.db.execute(
            select(User).options(selectinload(User.memberships).selectinload(WorkspaceMember.workspace)).where(User.email == req.email.lower())
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(req.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedException("Account is disabled.")

        # Determine workspace and role
        workspace_id = None
        role = "VIEWER"

        if selected_workspace_id:
            for m in user.memberships:
                if m.workspace_id == selected_workspace_id:
                    workspace_id = m.workspace_id
                    role = m.role
                    break
        elif user.memberships:
            workspace_id = user.memberships[0].workspace_id
            role = user.memberships[0].role

        token = create_access_token(
            subject=user.id,
            workspace_id=workspace_id,
            role=role,
        )

        token_resp = TokenResponse(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            workspace_id=workspace_id,
            role=role,
        )
        return user, token_resp

    async def get_user_profile(self, user_id: str) -> UserProfileResponse:
        stmt = (
            select(User)
            .options(selectinload(User.memberships).selectinload(WorkspaceMember.workspace))
            .where(User.id == user_id)
        )
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise UnauthorizedException("User not found.")

        workspaces = [
            WorkspaceBrief(
                id=m.workspace.id,
                name=m.workspace.name,
                slug=m.workspace.slug,
                role=m.role,
            )
            for m in user.memberships
        ]

        return UserProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            workspaces=workspaces,
        )
