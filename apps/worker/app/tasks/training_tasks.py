import asyncio
import io
import time
import traceback
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.infrastructure.database.models import DatasetVersion, Experiment, ExperimentMetric, TrainingJob
from apps.api.app.infrastructure.database.session import AsyncSessionLocal
from apps.api.app.infrastructure.storage import get_storage_service
from apps.worker.app.celery_app import celery_app
from ml.pipelines.training.trainer import train_churn_model

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="tasks.training.execute_job",
    autoretry_for=(ConnectionError, TimeoutError),
)
def celery_training_job_task(self, job_id: str, experiment_id: str, workspace_id: str):
    """Celery worker synchronous task wrapper for asynchronous training routine."""
    return asyncio.run(execute_training_job_async(job_id, experiment_id, workspace_id, celery_task_id=self.request.id))

async def execute_training_job_async(job_id: str, experiment_id: str, workspace_id: str, celery_task_id: str = None):
    storage = get_storage_service()
    start_time = time.time()

    async with AsyncSessionLocal() as session:
        # Load experiment and job
        job_res = await session.execute(select(TrainingJob).where(TrainingJob.id == job_id))
        job = job_res.scalar_one_or_none()

        exp_res = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
        experiment = exp_res.scalar_one_or_none()

        if not job or not experiment:
            return

        try:
            job.status = "RUNNING"
            experiment.status = "RUNNING"
            if celery_task_id:
                job.celery_task_id = celery_task_id
            job.progress_percentage = 10
            job.logs = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Training job started.\n"
            await session.commit()

            # Load dataset version
            v_res = await session.execute(select(DatasetVersion).where(DatasetVersion.id == experiment.dataset_version_id))
            version = v_res.scalar_one_or_none()
            if not version:
                raise ValueError(f"Dataset version '{experiment.dataset_version_id}' not found.")

            job.logs += f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Downloading dataset from {version.file_path}...\n"
            file_bytes = await storage.download_file(version.file_path)
            df = pd.read_csv(io.BytesIO(file_bytes))
            job.progress_percentage = 30
            job.logs += f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Dataset loaded ({len(df)} rows, {len(df.columns)} columns).\n"
            await session.commit()

            # Train model
            job.logs += f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fitting pipeline with algorithm '{experiment.algorithm}'...\n"
            job.progress_percentage = 50
            await session.commit()

            pipeline, metrics = train_churn_model(
                df=df,
                algorithm=experiment.algorithm,
                hyperparameters=experiment.hyperparameters,
                random_seed=experiment.random_seed,
                artifact_output_dir=None,  # Serialize in-memory for upload
            )

            # Serialize pipeline to bytes
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
                tmp_path = tmp.name

            import joblib
            joblib.dump(pipeline, tmp_path)

            with open(tmp_path, "rb") as f:
                artifact_bytes = f.read()

            artifact_storage_path = f"artifacts/{workspace_id}/{experiment_id}/model.joblib"
            await storage.upload_file(
                file_obj=io.BytesIO(artifact_bytes),
                destination_path=artifact_storage_path,
                content_type="application/octet-stream",
            )

            job.progress_percentage = 85
            job.logs += f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Model serialized and uploaded to {artifact_storage_path}.\n"
            job.logs += f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Evaluation complete: Acc={metrics['accuracy']:.4f}, F1={metrics['f1_score']:.4f}, ROC-AUC={metrics.get('roc_auc') or 0:.4f}\n"

            # Save Metrics
            exp_metric = ExperimentMetric(
                experiment_id=experiment.id,
                accuracy=metrics["accuracy"],
                precision=metrics["precision"],
                recall=metrics["recall"],
                f1_score=metrics["f1_score"],
                roc_auc=metrics["roc_auc"],
                pr_auc=metrics["pr_auc"],
                confusion_matrix=metrics["confusion_matrix"],
                classification_report=metrics["classification_report"],
                feature_importances=metrics["feature_importances"],
                artifact_path=artifact_storage_path,
            )
            session.add(exp_metric)

            # Complete job
            duration = round(time.time() - start_time, 2)
            job.status = "SUCCEEDED"
            job.progress_percentage = 100
            job.duration_seconds = duration
            experiment.status = "COMPLETED"
            job.logs += f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Training job succeeded in {duration}s.\n"

            await session.commit()

        except Exception as e:
            await session.rollback()
            err_msg = str(e)
            trace = traceback.format_exc()
            job.status = "FAILED"
            job.error_message = err_msg
            experiment.status = "FAILED"
            job.logs += f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Training FAILED: {err_msg}\n{trace}\n"
            await session.commit()
