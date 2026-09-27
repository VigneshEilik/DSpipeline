from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin

class MonitoringRun(Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin):
    __tablename__ = "monitoring_runs"

    deployment_id: Mapped[str] = mapped_column(String(36), ForeignKey("deployments.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)
    p50_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p95_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p99_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    drift_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    drift_report: Mapped["DriftReport"] = relationship(back_populates="monitoring_run", uselist=False, cascade="all, delete-orphan")

class DriftReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "drift_reports"

    monitoring_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("monitoring_runs.id", ondelete="CASCADE"), unique=True, nullable=False)
    dataset_version_reference_id: Mapped[str] = mapped_column(String(36), nullable=False)
    drift_share: Mapped[float] = mapped_column(Float, nullable=False)  # share of drifted features
    feature_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # per-feature p-values, distance metrics
    drifted_features: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    monitoring_run: Mapped["MonitoringRun"] = relationship(back_populates="drift_report")

class Alert(Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin):
    __tablename__ = "alerts"

    deployment_id: Mapped[str] = mapped_column(String(36), ForeignKey("deployments.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="WARNING", nullable=False)  # INFO, WARNING, CRITICAL
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
