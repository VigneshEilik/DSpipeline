from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin

class Deployment(Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin):
    __tablename__ = "deployments"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    model_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("model_versions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, ROLLING_BACK, FAILED
    traffic_percentage: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    endpoint_url: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(50), default="production", nullable=False)

    model_version: Mapped["ModelVersion"] = relationship(back_populates="deployments")
    events: Mapped[list["DeploymentEvent"]] = relationship(back_populates="deployment", cascade="all, delete-orphan")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="deployment")

class DeploymentEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "deployment_events"

    deployment_id: Mapped[str] = mapped_column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATED, PROMOTED, ROLLED_BACK, SCALE, HEALTH_CHECK
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(String(100), default="system", nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    deployment: Mapped["Deployment"] = relationship(back_populates="events")
