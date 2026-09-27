from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin

class Experiment(Base, UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceMixin):
    __tablename__ = "experiments"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    dataset_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("dataset_versions.id"), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)  # logistic_regression, random_forest, hist_gradient_boosting
    hyperparameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    random_seed: Mapped[int] = mapped_column(Integer, default=42, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED

    training_jobs: Mapped[list["TrainingJob"]] = relationship(back_populates="experiment", cascade="all, delete-orphan")
    metrics: Mapped["ExperimentMetric"] = relationship(back_populates="experiment", uselist=False, cascade="all, delete-orphan")

class TrainingJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "training_jobs"

    experiment_id: Mapped[str] = mapped_column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", nullable=False)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    logs: Mapped[str] = mapped_column(Text, default="", nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)

    experiment: Mapped["Experiment"] = relationship(back_populates="training_jobs")

class ExperimentMetric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "experiment_metrics"

    experiment_id: Mapped[str] = mapped_column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), unique=True, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    f1_score: Mapped[float] = mapped_column(Float, nullable=False)
    roc_auc: Mapped[float] = mapped_column(Float, nullable=True)
    pr_auc: Mapped[float] = mapped_column(Float, nullable=True)
    confusion_matrix: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # [[TN, FP], [FN, TP]]
    classification_report: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    feature_importances: Mapped[dict] = mapped_column(JSON, nullable=True)
    mlflow_run_id: Mapped[str] = mapped_column(String(255), nullable=True)
    artifact_path: Mapped[str] = mapped_column(String(500), nullable=True)

    experiment: Mapped["Experiment"] = relationship(back_populates="metrics")
