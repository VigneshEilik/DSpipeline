from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class DatasetSummary(BaseModel):
    id: str
    name: str
    description: Optional[str]
    domain: str
    target_column: str
    created_at: str
    latest_version: Optional[int]
    total_rows: Optional[int]
    total_columns: Optional[int]
    status: Optional[str]

class DatasetVersionDetail(BaseModel):
    id: str
    version_number: int
    file_size_bytes: int
    checksum_sha256: str
    row_count: int
    column_count: int
    schema_metadata: Dict[str, Any]
    is_validated: bool
    created_at: str

class ValidationReportResponse(BaseModel):
    id: str
    dataset_version_id: str
    status: str
    is_valid: bool
    missing_value_summary: Dict[str, float]
    class_balance_summary: Dict[str, Any]
    column_checks: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    created_at: str

class DatasetDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    domain: str
    target_column: str
    created_at: str
    versions: List[DatasetVersionDetail]
    latest_validation: Optional[ValidationReportResponse]

class DatasetPreviewResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    page: int
    page_size: int
