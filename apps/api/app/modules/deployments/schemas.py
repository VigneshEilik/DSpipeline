from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class CreateDeploymentRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    model_version_id: str
    environment: str = Field("production", pattern="^(production|staging)$")
    traffic_percentage: int = Field(100, ge=1, le=100)

class RollbackDeploymentRequest(BaseModel):
    target_model_version_id: str
    reason: Optional[str] = "Performance rollback requested"

class DeploymentEventDetail(BaseModel):
    id: str
    event_type: str
    description: str
    actor: str
    created_at: str
    details: Dict[str, Any]

class DeploymentDetailResponse(BaseModel):
    id: str
    name: str
    model_version_id: str
    status: str
    traffic_percentage: int
    endpoint_url: str
    environment: str
    created_at: str
    model_algorithm: Optional[str] = None
    events: List[DeploymentEventDetail]

class DeploymentSummary(BaseModel):
    id: str
    name: str
    model_version_id: str
    status: str
    traffic_percentage: int
    endpoint_url: str
    environment: str
    created_at: str
    algorithm: Optional[str] = None
