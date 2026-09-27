from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.core.exceptions import NotFoundException
from apps.api.app.infrastructure.database.models import DatasetVersion, Experiment, ExperimentMetric, TrainingJob
from apps.api.app.infrastructure.tasks.runner import task_runner
from apps.api.app.modules.experiments.schemas import (
    CreateExperimentRequest,
    ExperimentDetailResponse,
    ExperimentMetricResponse,
    ExperimentSummary,
)
from apps.worker.app.tasks.training_tasks import execute_training_job_async

class ExperimentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_and_trigger_experiment(
        self, workspace_id: str, req: CreateExperimentRequest
    ) -> ExperimentDetailResponse:
        # Validate dataset version exists
        v_res = await self.db.execute(
            select(DatasetVersion).where(DatasetVersion.id == req.dataset_version_id)
        )
        version = v_res.scalar_one_or_none()
        if not version:
            raise NotFoundException("DatasetVersion", req.dataset_version_id)

        experiment = Experiment(
            workspace_id=workspace_id,
            name=req.name,
            description=req.description,
            dataset_version_id=req.dataset_version_id,
            algorithm=req.algorithm,
            hyperparameters=req.hyperparameters or {},
            random_seed=req.random_seed,
            status="QUEUED",
        )
        self.db.add(experiment)
        await self.db.flush()

        job = TrainingJob(
            experiment_id=experiment.id,
            status="QUEUED",
            progress_percentage=0,
            logs=f"Training job queued for experiment '{req.name}'.\n",
        )
        self.db.add(job)
        await self.db.commit()

        # Dispatch async training task in background
        task_runner.run_task(execute_training_job_async, job.id, experiment.id, workspace_id)

        return await self.get_experiment(workspace_id, experiment.id)

    async def list_experiments(self, workspace_id: str) -> List[ExperimentSummary]:
        stmt = (
            select(Experiment)
            .options(
                selectinload(Experiment.metrics),
                selectinload(Experiment.training_jobs),
            )
            .where(Experiment.workspace_id == workspace_id)
            .order_by(desc(Experiment.created_at))
        )
        res = await self.db.execute(stmt)
        experiments = res.scalars().all()

        summaries = []
        for exp in experiments:
            latest_job = exp.training_jobs[-1] if exp.training_jobs else None
            metric = exp.metrics
            summaries.append(
                ExperimentSummary(
                    id=exp.id,
                    name=exp.name,
                    description=exp.description,
                    dataset_version_id=exp.dataset_version_id,
                    algorithm=exp.algorithm,
                    status=exp.status,
                    random_seed=exp.random_seed,
                    created_at=exp.created_at.isoformat(),
                    accuracy=metric.accuracy if metric else None,
                    f1_score=metric.f1_score if metric else None,
                    duration_seconds=latest_job.duration_seconds if latest_job else None,
                )
            )
        return summaries

    async def get_experiment(self, workspace_id: str, experiment_id: str) -> ExperimentDetailResponse:
        stmt = (
            select(Experiment)
            .options(
                selectinload(Experiment.metrics),
                selectinload(Experiment.training_jobs),
            )
            .where(
                Experiment.id == experiment_id,
                Experiment.workspace_id == workspace_id,
            )
        )
        res = await self.db.execute(stmt)
        exp = res.scalar_one_or_none()
        if not exp:
            raise NotFoundException("Experiment", experiment_id)

        latest_job = exp.training_jobs[-1] if exp.training_jobs else None

        metric_resp = None
        if exp.metrics:
            m = exp.metrics
            metric_resp = ExperimentMetricResponse(
                accuracy=m.accuracy,
                precision=m.precision,
                recall=m.recall,
                f1_score=m.f1_score,
                roc_auc=m.roc_auc,
                pr_auc=m.pr_auc,
                confusion_matrix=m.confusion_matrix,
                classification_report=m.classification_report,
                feature_importances=m.feature_importances,
                artifact_path=m.artifact_path,
            )

        return ExperimentDetailResponse(
            id=exp.id,
            name=exp.name,
            description=exp.description,
            dataset_version_id=exp.dataset_version_id,
            algorithm=exp.algorithm,
            status=exp.status,
            hyperparameters=exp.hyperparameters,
            random_seed=exp.random_seed,
            created_at=exp.created_at.isoformat(),
            training_job_id=latest_job.id if latest_job else None,
            progress_percentage=latest_job.progress_percentage if latest_job else 0,
            logs=latest_job.logs if latest_job else "",
            metrics=metric_resp,
        )
