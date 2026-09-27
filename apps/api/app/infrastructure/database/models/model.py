from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin

class ModelRegistry(Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin):
    __tablename__ = "model_registry"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), default="binary_classification", nullable=False)

    versions: Mapped[list["ModelVersion"]] = relationship(back_populates="model_registry", cascade="all, delete-orphan")

class ModelVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "model_versions"

    model_registry_id: Mapped[str] = mapped_column(String(36), ForeignKey("model_registry.id", ondelete="CASCADE"), nullable=False, index=True)
    experiment_id: Mapped[str] = mapped_column(String(36), ForeignKey("experiments.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    artifact_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    feature_schema: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    lifecycle_stage: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False)  # DRAFT, EVALUATED, APPROVED, DEPLOYED, ARCHIVED, REJECTED

    model_registry: Mapped["ModelRegistry"] = relationship(back_populates="versions")
    approvals: Mapped[list["ModelApproval"]] = relationship(back_populates="model_version", cascade="all, delete-orphan")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="model_version")

class ModelApproval(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "model_approvals"

    model_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    approved_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # APPROVED, REJECTED
    comments: Mapped[str] = mapped_column(Text, nullable=True)

    model_version: Mapped["ModelVersion"] = relationship(back_populates="approvals")
