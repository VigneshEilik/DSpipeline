from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class CreateExperimentRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    dataset_version_id: str
    algorithm: str = Field("logistic_regression", description="logistic_regression, random_forest, hist_gradient_boosting")
    hyperparameters: Optional[Dict[str, Any]] = None
    random_seed: int = 42
    description: Optional[str] = None

class ExperimentMetricResponse(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: Optional[float]
    pr_auc: Optional[float]
    confusion_matrix: List[List[int]]
    classification_report: Dict[str, Any]
    feature_importances: Optional[Dict[str, float]]
    artifact_path: Optional[str]

class ExperimentSummary(BaseModel):
    id: str
    name: str
    description: Optional[str]
    dataset_version_id: str
    algorithm: str
    status: str
    random_seed: int
    created_at: str
    accuracy: Optional[float]
    f1_score: Optional[float]
    duration_seconds: Optional[float]

class ExperimentDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    dataset_version_id: str
    algorithm: str
    status: str
    hyperparameters: Dict[str, Any]
    random_seed: int
    created_at: str
    training_job_id: Optional[str]
    progress_percentage: int
    logs: str
    metrics: Optional[ExperimentMetricResponse]
