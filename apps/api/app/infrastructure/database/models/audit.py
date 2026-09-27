from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from apps.api.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin

class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin):
    __tablename__ = "audit_logs"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # DATASET_UPLOAD, EXPERIMENT_TRIGGER, MODEL_APPROVE, MODEL_DEPLOY, etc.
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
