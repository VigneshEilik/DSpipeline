import io
import time
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.core.exceptions import ModelOpsException, NotFoundException
from apps.api.app.infrastructure.database.models import BatchPredictionJob, Deployment, ModelVersion, Prediction
from apps.api.app.infrastructure.storage import get_storage_service
from apps.api.app.infrastructure.tasks.runner import task_runner
from apps.api.app.modules.deployments.serving_cache import serving_cache
from apps.api.app.modules.predictions.schemas import (
    BatchPredictionJobResponse,
    PredictionResponse,
    SinglePredictionRequest,
)
from apps.worker.app.tasks.batch_inference_tasks import execute_batch_inference_async

class PredictionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = get_storage_service()

    async def predict_single(
        self, workspace_id: str, req: SinglePredictionRequest
    ) -> PredictionResponse:
        start_time = time.time()

        # 1. Resolve deployment
        stmt = (
            select(Deployment)
            .options(selectinload(Deployment.model_version))
            .where(
                Deployment.workspace_id == workspace_id,
                Deployment.status == "ACTIVE",
            )
        )
        if req.deployment_id:
            stmt = stmt.where(Deployment.id == req.deployment_id)

        res = await self.db.execute(stmt)
        deployment = res.scalar_one_or_none()
        if not deployment:
            raise NotFoundException("Active Deployment", req.deployment_id or "default")

        # 2. Retrieve or load predictor from cache
        predictor = serving_cache.get_predictor(deployment.id)
        if not predictor:
            predictor = await serving_cache.load_predictor_for_deployment(
                deployment.id, deployment.model_version.artifact_uri
            )

        # 3. Execute inference
        try:
            pred_result = predictor.predict_single(req.features)
        except Exception as e:
            raise ModelOpsException(f"Inference execution failed on supplied features: {str(e)}")

        latency_ms = round((time.time() - start_time) * 1000, 2)

        # 4. Persist Prediction record
        prediction = Prediction(
            workspace_id=workspace_id,
            deployment_id=deployment.id,
            model_version_id=deployment.model_version_id,
            input_features=req.features,
            prediction_label=pred_result["prediction_label"],
            prediction_probability=pred_result["prediction_probability"],
            risk_category=pred_result["risk_category"],
            latency_ms=latency_ms,
        )
        self.db.add(prediction)
        await self.db.commit()

        return PredictionResponse(
            id=prediction.id,
            deployment_id=deployment.id,
            model_version_id=deployment.model_version_id,
            prediction_label=prediction.prediction_label,
            prediction_probability=prediction.prediction_probability,
            risk_category=prediction.risk_category,
            latency_ms=latency_ms,
            created_at=prediction.created_at.isoformat(),
            features=req.features,
        )

    async def list_predictions(
        self, workspace_id: str, limit: int = 50, offset: int = 0
    ) -> List[PredictionResponse]:
        stmt = (
            select(Prediction)
            .where(Prediction.workspace_id == workspace_id)
            .order_by(desc(Prediction.created_at))
            .offset(offset)
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        records = res.scalars().all()

        return [
            PredictionResponse(
                id=p.id,
                deployment_id=p.deployment_id,
                model_version_id=p.model_version_id,
                prediction_label=p.prediction_label,
                prediction_probability=p.prediction_probability,
                risk_category=p.risk_category,
                latency_ms=p.latency_ms,
                created_at=p.created_at.isoformat(),
                features=p.input_features,
            )
            for p in records
        ]

    async def get_prediction(self, workspace_id: str, prediction_id: str) -> PredictionResponse:
        stmt = select(Prediction).where(
            Prediction.id == prediction_id,
            Prediction.workspace_id == workspace_id,
        )
        res = await self.db.execute(stmt)
        p = res.scalar_one_or_none()
        if not p:
            raise NotFoundException("Prediction", prediction_id)

        return PredictionResponse(
            id=p.id,
            deployment_id=p.deployment_id,
            model_version_id=p.model_version_id,
            prediction_label=p.prediction_label,
            prediction_probability=p.prediction_probability,
            risk_category=p.risk_category,
            latency_ms=p.latency_ms,
            created_at=p.created_at.isoformat(),
            features=p.input_features,
        )

    async def create_batch_prediction_job(
        self, workspace_id: str, file_bytes: bytes, filename: str, deployment_id: Optional[str] = None
    ) -> BatchPredictionJobResponse:
        # Resolve active deployment
        stmt = select(Deployment).where(
            Deployment.workspace_id == workspace_id,
            Deployment.status == "ACTIVE",
        )
        if deployment_id:
            stmt = stmt.where(Deployment.id == deployment_id)

        res = await self.db.execute(stmt)
        deployment = res.scalar_one_or_none()
        if not deployment:
            raise NotFoundException("Active Deployment", deployment_id or "default")

        # Upload input batch CSV to storage
        input_path = f"predictions/batch_inputs/{workspace_id}/{int(time.time())}_{filename}"
        await self.storage.upload_file(
            file_obj=io.BytesIO(file_bytes),
            destination_path=input_path,
            content_type="text/csv",
        )

        job = BatchPredictionJob(
            workspace_id=workspace_id,
            deployment_id=deployment.id,
            input_file_path=input_path,
            status="PENDING",
            total_records=0,
            processed_records=0,
        )
        self.db.add(job)
        await self.db.commit()

        # Run background batch inference
        task_runner.run_task(execute_batch_inference_async, job.id, workspace_id)

        return BatchPredictionJobResponse(
            id=job.id,
            deployment_id=job.deployment_id,
            status=job.status,
            total_records=job.total_records,
            processed_records=job.processed_records,
            output_file_url=None,
            created_at=job.created_at.isoformat(),
            duration_seconds=None,
            error_message=None,
        )

    async def get_batch_job(self, workspace_id: str, job_id: str) -> BatchPredictionJobResponse:
        stmt = select(BatchPredictionJob).where(
            BatchPredictionJob.id == job_id,
            BatchPredictionJob.workspace_id == workspace_id,
        )
        res = await self.db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundException("BatchPredictionJob", job_id)

        output_url = None
        if job.output_file_path:
            output_url = self.storage.get_file_url(job.output_file_path)

        return BatchPredictionJobResponse(
            id=job.id,
            deployment_id=job.deployment_id,
            status=job.status,
            total_records=job.total_records,
            processed_records=job.processed_records,
            output_file_url=output_url,
            created_at=job.created_at.isoformat(),
            duration_seconds=job.duration_seconds,
            error_message=job.error_message,
        )
