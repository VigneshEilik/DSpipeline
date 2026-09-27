from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from apps.api.app.shared.enums.roles import UserRole

class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None

class AddMemberRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.DATA_SCIENTIST

class MemberDetail(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    joined_at: str

class WorkspaceDetailResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    created_at: str
    members: List[MemberDetail]
