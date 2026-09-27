from sqlalchemy import BigInteger, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin

class Prediction(Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin):
    __tablename__ = "predictions"
    __table_args__ = (
        Index("ix_predictions_workspace_created", "workspace_id", "created_at"),
    )

    deployment_id: Mapped[str] = mapped_column(String(36), ForeignKey("deployments.id"), nullable=False, index=True)
    model_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("model_versions.id"), nullable=False, index=True)
    input_features: Mapped[dict] = mapped_column(JSON, nullable=False)
    prediction_label: Mapped[str] = mapped_column(String(50), nullable=False)  # "Yes" or "No" (or 1/0)
    prediction_probability: Mapped[float] = mapped_column(Float, nullable=False)  # e.g., 0.82
    risk_category: Mapped[str] = mapped_column(String(50), nullable=False)  # Low, Medium, High
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    ground_truth: Mapped[str] = mapped_column(String(50), nullable=True)  # Optional feedback/delayed label

    deployment: Mapped["Deployment"] = relationship(back_populates="predictions")

class BatchPredictionJob(Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin):
    __tablename__ = "batch_prediction_jobs"

    deployment_id: Mapped[str] = mapped_column(String(36), ForeignKey("deployments.id"), nullable=False)
    input_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    output_file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, PROCESSING, COMPLETED, FAILED
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
