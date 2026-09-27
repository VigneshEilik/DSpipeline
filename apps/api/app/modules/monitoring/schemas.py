from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class RiskDistribution(BaseModel):
    low: int
    medium: int
    high: int

class MonitoringOverviewResponse(BaseModel):
    total_predictions: int
    average_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    risk_distribution: RiskDistribution
    active_deployments_count: int
    registered_models_count: int
    experiments_count: int
    datasets_count: int

class DriftFeatureMetric(BaseModel):
    feature_name: str
    drift_score: float  # p-value or statistic
    is_drifted: bool
    test_name: str
    reference_mean: Optional[float] = None
    current_mean: Optional[float] = None

class DriftReportResponse(BaseModel):
    id: str
    monitoring_run_id: str
    drift_share: float
    drift_detected: bool
    drifted_features: List[str]
    feature_metrics: List[DriftFeatureMetric]
    created_at: str

class RunDriftRequest(BaseModel):
    deployment_id: Optional[str] = None
    sample_size: int = 100
