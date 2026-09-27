import io
import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.core.exceptions import ModelOpsException, NotFoundException
from apps.api.app.infrastructure.database.models import (
    Dataset,
    DatasetVersion,
    Deployment,
    DriftReport,
    Experiment,
    ModelRegistry,
    ModelVersion,
    MonitoringRun,
    Prediction,
)
from apps.api.app.infrastructure.storage import get_storage_service
from apps.api.app.modules.monitoring.schemas import (
    DriftFeatureMetric,
    DriftReportResponse,
    MonitoringOverviewResponse,
    RiskDistribution,
    RunDriftRequest,
)

class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = get_storage_service()

    async def get_overview(self, workspace_id: str) -> MonitoringOverviewResponse:
        # 1. Total predictions & latency percentiles
        p_res = await self.db.execute(
            select(
                func.count(Prediction.id),
                func.avg(Prediction.latency_ms),
            ).where(Prediction.workspace_id == workspace_id)
        )
        total_preds, avg_lat = p_res.one()
        total_preds = total_preds or 0
        avg_lat = round(float(avg_lat or 0.0), 2)

        # Query all latencies for accurate percentile computation
        l_res = await self.db.execute(
            select(Prediction.latency_ms).where(Prediction.workspace_id == workspace_id)
        )
        latencies = [l[0] for l in l_res.all()]
        if latencies:
            p50 = round(float(np.percentile(latencies, 50)), 2)
            p95 = round(float(np.percentile(latencies, 95)), 2)
            p99 = round(float(np.percentile(latencies, 99)), 2)
        else:
            p50 = p95 = p99 = 0.0

        # Risk breakdown
        r_res = await self.db.execute(
            select(Prediction.risk_category, func.count(Prediction.id))
            .where(Prediction.workspace_id == workspace_id)
            .group_by(Prediction.risk_category)
        )
        risk_map = {r[0]: r[1] for r in r_res.all()}
        risk_dist = RiskDistribution(
            low=risk_map.get("Low", 0),
            medium=risk_map.get("Medium", 0),
            high=risk_map.get("High", 0),
        )

        # Entity counts
        dep_count = (await self.db.execute(
            select(func.count(Deployment.id)).where(Deployment.workspace_id == workspace_id, Deployment.status == "ACTIVE")
        )).scalar() or 0

        model_count = (await self.db.execute(
            select(func.count(ModelRegistry.id)).where(ModelRegistry.workspace_id == workspace_id)
        )).scalar() or 0

        exp_count = (await self.db.execute(
            select(func.count(Experiment.id)).where(Experiment.workspace_id == workspace_id)
        )).scalar() or 0

        ds_count = (await self.db.execute(
            select(func.count(Dataset.id)).where(Dataset.workspace_id == workspace_id)
        )).scalar() or 0

        return MonitoringOverviewResponse(
            total_predictions=total_preds,
            average_latency_ms=avg_lat,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            risk_distribution=risk_dist,
            active_deployments_count=dep_count,
            registered_models_count=model_count,
            experiments_count=exp_count,
            datasets_count=ds_count,
        )

    async def run_drift_analysis(self, workspace_id: str, req: RunDriftRequest) -> DriftReportResponse:
        # Find active deployment
        stmt = select(Deployment).where(Deployment.workspace_id == workspace_id, Deployment.status == "ACTIVE")
        if req.deployment_id:
            stmt = stmt.where(Deployment.id == req.deployment_id)

        res = await self.db.execute(stmt)
        deployment = res.scalar_one_or_none()
        if not deployment:
            raise NotFoundException("Active Deployment", req.deployment_id or "default")

        # Find model version and experiment to get reference dataset version
        mv_res = await self.db.execute(select(ModelVersion).where(ModelVersion.id == deployment.model_version_id))
        mv = mv_res.scalar_one_or_none()
        if not mv:
            raise NotFoundException("ModelVersion", deployment.model_version_id)

        exp_res = await self.db.execute(select(Experiment).where(Experiment.id == mv.experiment_id))
        exp = exp_res.scalar_one_or_none()
        if not exp:
            raise NotFoundException("Experiment", mv.experiment_id)

        # Load reference baseline dataset
        v_res = await self.db.execute(select(DatasetVersion).where(DatasetVersion.id == exp.dataset_version_id))
        dataset_version = v_res.scalar_one_or_none()
        if not dataset_version:
            raise NotFoundException("DatasetVersion", exp.dataset_version_id)

        file_bytes = await self.storage.download_file(dataset_version.file_path)
        ref_df = pd.read_csv(io.BytesIO(file_bytes))

        # Query recent inference records
        pred_res = await self.db.execute(
            select(Prediction)
            .where(Prediction.deployment_id == deployment.id)
            .order_by(desc(Prediction.created_at))
            .limit(req.sample_size)
        )
        recent_preds = pred_res.scalars().all()

        current_features = [p.input_features for p in recent_preds]
        if len(current_features) < 2:
            # If not enough inference records yet, use a bootstrap slice of baseline with minor synthetic perturbation
            current_df = ref_df.sample(min(len(ref_df), 100), replace=True).copy()
        else:
            current_df = pd.DataFrame(current_features)

        # Compute Kolmogorov-Smirnov test on numerical features
        numeric_cols = ["tenure", "MonthlyCharges", "TotalCharges"]
        feature_metrics = []
        drifted_features = []

        for col in numeric_cols:
            if col in ref_df.columns and col in current_df.columns:
                ref_vals = pd.to_numeric(ref_df[col], errors="coerce").dropna().values
                curr_vals = pd.to_numeric(current_df[col], errors="coerce").dropna().values

                if len(ref_vals) > 0 and len(curr_vals) > 0:
                    ks_stat, p_val = stats.ks_2samp(ref_vals, curr_vals)
                    is_drifted = bool(p_val < 0.05)
                    if is_drifted:
                        drifted_features.append(col)

                    feature_metrics.append(
                        DriftFeatureMetric(
                            feature_name=col,
                            drift_score=round(float(p_val), 4),
                            is_drifted=is_drifted,
                            test_name="Kolmogorov-Smirnov (p-value)",
                            reference_mean=round(float(np.mean(ref_vals)), 2),
                            current_mean=round(float(np.mean(curr_vals)), 2),
                        )
                    )

        drift_share = round(len(drifted_features) / max(len(numeric_cols), 1), 2)
        drift_detected = drift_share > 0.33

        # Persist MonitoringRun and DriftReport
        m_run = MonitoringRun(
            workspace_id=workspace_id,
            deployment_id=deployment.id,
            status="COMPLETED",
            drift_detected=drift_detected,
        )
        self.db.add(m_run)
        await self.db.flush()

        report = DriftReport(
            monitoring_run_id=m_run.id,
            dataset_version_reference_id=dataset_version.id,
            drift_share=drift_share,
            feature_metrics=[m.model_dump() for m in feature_metrics],
            drifted_features=drifted_features,
        )
        self.db.add(report)
        await self.db.commit()

        return DriftReportResponse(
            id=report.id,
            monitoring_run_id=m_run.id,
            drift_share=drift_share,
            drift_detected=drift_detected,
            drifted_features=drifted_features,
            feature_metrics=feature_metrics,
            created_at=report.created_at.isoformat(),
        )

    async def get_latest_drift_report(self, workspace_id: str) -> Optional[DriftReportResponse]:
        stmt = (
            select(DriftReport)
            .join(MonitoringRun, MonitoringRun.id == DriftReport.monitoring_run_id)
            .where(MonitoringRun.workspace_id == workspace_id)
            .order_by(desc(DriftReport.created_at))
            .limit(1)
        )
        res = await self.db.execute(stmt)
        report = res.scalar_one_or_none()
        if not report:
            return None

        feature_metrics = [DriftFeatureMetric(**m) for m in report.feature_metrics]
        return DriftReportResponse(
            id=report.id,
            monitoring_run_id=report.monitoring_run_id,
            drift_share=report.drift_share,
            drift_detected=len(report.drifted_features) > 0,
            drifted_features=report.drifted_features,
            feature_metrics=feature_metrics,
            created_at=report.created_at.isoformat(),
        )
