import re
import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.core.exceptions import ConflictException, NotFoundException
from apps.api.app.infrastructure.database.models import User, Workspace, WorkspaceMember
from apps.api.app.modules.workspaces.schemas import AddMemberRequest, CreateWorkspaceRequest, MemberDetail, WorkspaceDetailResponse

class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workspace(self, user_id: str, req: CreateWorkspaceRequest) -> WorkspaceDetailResponse:
        base_slug = re.sub(r"[^a-zA-Z0-9]+", "-", req.name.lower()).strip("-")
        slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

        ws = Workspace(name=req.name, slug=slug, description=req.description)
        self.db.add(ws)
        await self.db.flush()

        member = WorkspaceMember(workspace_id=ws.id, user_id=user_id, role="OWNER")
        self.db.add(member)
        await self.db.commit()

        return await self.get_workspace(ws.id)

    async def get_workspace(self, workspace_id: str) -> WorkspaceDetailResponse:
        stmt = (
            select(Workspace)
            .options(selectinload(Workspace.members).selectinload(WorkspaceMember.user))
            .where(Workspace.id == workspace_id)
        )
        res = await self.db.execute(stmt)
        ws = res.scalar_one_or_none()
        if not ws:
            raise NotFoundException("Workspace", workspace_id)

        members = [
            MemberDetail(
                user_id=m.user.id,
                email=m.user.email,
                full_name=m.user.full_name,
                role=m.role,
                joined_at=m.created_at.isoformat(),
            )
            for m in ws.members
        ]

        return WorkspaceDetailResponse(
            id=ws.id,
            name=ws.name,
            slug=ws.slug,
            description=ws.description,
            created_at=ws.created_at.isoformat(),
            members=members,
        )

    async def add_member(self, workspace_id: str, req: AddMemberRequest) -> MemberDetail:
        # Find user by email
        user_res = await self.db.execute(select(User).where(User.email == req.email.lower()))
        user = user_res.scalar_one_or_none()
        if not user:
            raise NotFoundException("User", req.email)

        # Check existing membership
        existing = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user.id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException(f"User '{req.email}' is already a member of this workspace.")

        member = WorkspaceMember(workspace_id=workspace_id, user_id=user.id, role=req.role.value)
        self.db.add(member)
        await self.db.commit()

        return MemberDetail(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=member.role,
            joined_at=member.created_at.isoformat(),
        )
