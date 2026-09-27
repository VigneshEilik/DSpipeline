from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SinglePredictionRequest(BaseModel):
    deployment_id: Optional[str] = None
    features: Dict[str, Any]

class PredictionResponse(BaseModel):
    id: str
    deployment_id: str
    model_version_id: str
    prediction_label: str  # "Yes" or "No"
    prediction_probability: float  # e.g., 0.7421
    risk_category: str  # "Low", "Medium", "High"
    latency_ms: float
    created_at: str
    features: Dict[str, Any]

class BatchPredictionJobResponse(BaseModel):
    id: str
    deployment_id: str
    status: str
    total_records: int
    processed_records: int
    output_file_url: Optional[str]
    created_at: str
    duration_seconds: Optional[float]
    error_message: Optional[str]
