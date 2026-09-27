import io
import time
import traceback
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.infrastructure.database.models import BatchPredictionJob, Deployment, ModelVersion
from apps.api.app.infrastructure.database.session import AsyncSessionLocal
from apps.api.app.infrastructure.storage import get_storage_service
from apps.api.app.modules.deployments.serving_cache import serving_cache

async def execute_batch_inference_async(job_id: str, workspace_id: str):
    storage = get_storage_service()
    start_time = time.time()

    async with AsyncSessionLocal() as session:
        job_res = await session.execute(select(BatchPredictionJob).where(BatchPredictionJob.id == job_id))
        job = job_res.scalar_one_or_none()
        if not job:
            return

        try:
            job.status = "PROCESSING"
            await session.commit()

            # 1. Fetch deployment and model version
            dep_res = await session.execute(select(Deployment).where(Deployment.id == job.deployment_id))
            deployment = dep_res.scalar_one_or_none()
            if not deployment:
                raise ValueError("Associated deployment not found.")

            v_res = await session.execute(select(ModelVersion).where(ModelVersion.id == deployment.model_version_id))
            version = v_res.scalar_one_or_none()
            if not version:
                raise ValueError("Model version not found.")

            # 2. Get predictor
            predictor = serving_cache.get_predictor(deployment.id)
            if not predictor:
                predictor = await serving_cache.load_predictor_for_deployment(deployment.id, version.artifact_uri)

            # 3. Download input CSV
            file_bytes = await storage.download_file(job.input_file_path)
            input_df = pd.read_csv(io.BytesIO(file_bytes))
            job.total_records = len(input_df)
            await session.commit()

            # 4. Predict Batch
            results_df = predictor.predict_batch(input_df)

            # 5. Save output CSV
            output_csv_bytes = results_df.to_csv(index=False).encode("utf-8")
            output_path = f"predictions/batch/{workspace_id}/{job.id}_results.csv"
            await storage.upload_file(
                file_obj=io.BytesIO(output_csv_bytes),
                destination_path=output_path,
                content_type="text/csv",
            )

            duration = round(time.time() - start_time, 2)
            job.status = "COMPLETED"
            job.processed_records = len(results_df)
            job.output_file_path = output_path
            job.duration_seconds = duration
            await session.commit()

        except Exception as e:
            await session.rollback()
            job.status = "FAILED"
            job.error_message = f"{str(e)}\n{traceback.format_exc()}"
            await session.commit()
