from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin

class Dataset(Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    domain: Mapped[str] = mapped_column(String(50), default="churn", nullable=False)  # churn, fraud, etc.
    target_column: Mapped[str] = mapped_column(String(100), default="Churn", nullable=False)

    versions: Mapped[list["DatasetVersion"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")

class DatasetVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dataset_versions"

    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # S3 key or local storage path
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # column names, types, summary stats
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    dataset: Mapped["Dataset"] = relationship(back_populates="versions")
    validation_report: Mapped["DatasetValidationReport"] = relationship(back_populates="dataset_version", uselist=False, cascade="all, delete-orphan")

class DatasetValidationReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dataset_validation_reports"

    dataset_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("dataset_versions.id", ondelete="CASCADE"), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # PASSED, FAILED, WARNINGS
    missing_value_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    class_balance_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    column_checks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    errors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    warnings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    dataset_version: Mapped["DatasetVersion"] = relationship(back_populates="validation_report")
