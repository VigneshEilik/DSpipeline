from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class RegisterModelRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    experiment_id: str
    description: Optional[str] = None

class ApprovalRequest(BaseModel):
    version_id: str
    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    comments: Optional[str] = None

class ModelApprovalDetail(BaseModel):
    id: str
    decision: str
    comments: Optional[str]
    approved_by_user_id: str
    created_at: str

class ModelVersionResponse(BaseModel):
    id: str
    model_registry_id: str
    experiment_id: str
    version_number: int
    algorithm: str
    artifact_uri: str
    lifecycle_stage: str
    created_at: str
    approvals: List[ModelApprovalDetail]

class ModelRegistryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    task_type: str
    created_at: str
    versions: List[ModelVersionResponse]
    latest_version: Optional[ModelVersionResponse]
