from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.core.exceptions import ModelOpsException, NotFoundException
from apps.api.app.infrastructure.database.models import Experiment, ModelApproval, ModelRegistry, ModelVersion
from apps.api.app.modules.models.schemas import (
    ApprovalRequest,
    ModelApprovalDetail,
    ModelRegistryResponse,
    ModelVersionResponse,
    RegisterModelRequest,
)

class ModelRegistryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_model(self, workspace_id: str, req: RegisterModelRequest) -> ModelRegistryResponse:
        # 1. Fetch experiment and metrics
        exp_res = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.metrics))
            .where(
                Experiment.id == req.experiment_id,
                Experiment.workspace_id == workspace_id,
            )
        )
        experiment = exp_res.scalar_one_or_none()
        if not experiment:
            raise NotFoundException("Experiment", req.experiment_id)
        if experiment.status != "COMPLETED" or not experiment.metrics:
            raise ModelOpsException("Cannot register model: Experiment has not successfully completed or lacks metrics.")

        # 2. Find or create ModelRegistry
        reg_res = await self.db.execute(
            select(ModelRegistry)
            .options(selectinload(ModelRegistry.versions))
            .where(
                ModelRegistry.workspace_id == workspace_id,
                ModelRegistry.name == req.name,
            )
        )
        registry = reg_res.scalar_one_or_none()
        if not registry:
            registry = ModelRegistry(
                workspace_id=workspace_id,
                name=req.name,
                description=req.description,
                task_type="binary_classification",
            )
            self.db.add(registry)
            await self.db.flush()
            version_number = 1
        else:
            version_number = len(registry.versions) + 1

        # 3. Create ModelVersion
        m_version = ModelVersion(
            model_registry_id=registry.id,
            experiment_id=experiment.id,
            version_number=version_number,
            algorithm=experiment.algorithm,
            artifact_uri=experiment.metrics.artifact_path or "",
            feature_schema={"task": "churn_prediction", "target": "Churn"},
            lifecycle_stage="EVALUATED",  # Transition from draft to evaluated upon registration
        )
        self.db.add(m_version)
        await self.db.commit()

        return await self.get_model(workspace_id, registry.id)

    async def list_models(self, workspace_id: str) -> List[ModelRegistryResponse]:
        stmt = (
            select(ModelRegistry)
            .options(
                selectinload(ModelRegistry.versions).selectinload(ModelVersion.approvals)
            )
            .where(ModelRegistry.workspace_id == workspace_id)
            .order_by(desc(ModelRegistry.created_at))
        )
        res = await self.db.execute(stmt)
        registries = res.scalars().all()

        responses = []
        for reg in registries:
            version_responses = [
                ModelVersionResponse(
                    id=v.id,
                    model_registry_id=v.model_registry_id,
                    experiment_id=v.experiment_id,
                    version_number=v.version_number,
                    algorithm=v.algorithm,
                    artifact_uri=v.artifact_uri,
                    lifecycle_stage=v.lifecycle_stage,
                    created_at=v.created_at.isoformat(),
                    approvals=[
                        ModelApprovalDetail(
                            id=a.id,
                            decision=a.decision,
                            comments=a.comments,
                            approved_by_user_id=a.approved_by_user_id,
                            created_at=a.created_at.isoformat(),
                        )
                        for a in v.approvals
                    ],
                )
                for v in sorted(reg.versions, key=lambda x: x.version_number, reverse=True)
            ]
            latest = version_responses[0] if version_responses else None

            responses.append(
                ModelRegistryResponse(
                    id=reg.id,
                    name=reg.name,
                    description=reg.description,
                    task_type=reg.task_type,
                    created_at=reg.created_at.isoformat(),
                    versions=version_responses,
                    latest_version=latest,
                )
            )
        return responses

    async def get_model(self, workspace_id: str, model_id: str) -> ModelRegistryResponse:
        stmt = (
            select(ModelRegistry)
            .options(
                selectinload(ModelRegistry.versions).selectinload(ModelVersion.approvals)
            )
            .where(
                ModelRegistry.id == model_id,
                ModelRegistry.workspace_id == workspace_id,
            )
        )
        res = await self.db.execute(stmt)
        reg = res.scalar_one_or_none()
        if not reg:
            raise NotFoundException("ModelRegistry", model_id)

        version_responses = [
            ModelVersionResponse(
                id=v.id,
                model_registry_id=v.model_registry_id,
                experiment_id=v.experiment_id,
                version_number=v.version_number,
                algorithm=v.algorithm,
                artifact_uri=v.artifact_uri,
                lifecycle_stage=v.lifecycle_stage,
                created_at=v.created_at.isoformat(),
                approvals=[
                    ModelApprovalDetail(
                        id=a.id,
                        decision=a.decision,
                        comments=a.comments,
                        approved_by_user_id=a.approved_by_user_id,
                        created_at=a.created_at.isoformat(),
                    )
                    for a in v.approvals
                ],
            )
            for v in sorted(reg.versions, key=lambda x: x.version_number, reverse=True)
        ]
        latest = version_responses[0] if version_responses else None

        return ModelRegistryResponse(
            id=reg.id,
            name=reg.name,
            description=reg.description,
            task_type=reg.task_type,
            created_at=reg.created_at.isoformat(),
            versions=version_responses,
            latest_version=latest,
        )

    async def approve_model_version(
        self, workspace_id: str, user_id: str, model_id: str, req: ApprovalRequest
    ) -> ModelVersionResponse:
        # Verify model version belongs to workspace's model registry
        stmt = (
            select(ModelVersion)
            .options(
                selectinload(ModelVersion.approvals),
                selectinload(ModelVersion.model_registry),
            )
            .where(
                ModelVersion.id == req.version_id,
                ModelVersion.model_registry_id == model_id,
            )
        )
        res = await self.db.execute(stmt)
        version = res.scalar_one_or_none()
        if not version or version.model_registry.workspace_id != workspace_id:
            raise NotFoundException("ModelVersion", req.version_id)

        # Update stage
        version.lifecycle_stage = req.decision  # APPROVED or REJECTED

        # Record approval event
        approval = ModelApproval(
            model_version_id=version.id,
            approved_by_user_id=user_id,
            decision=req.decision,
            comments=req.comments,
        )
        self.db.add(approval)
        await self.db.commit()

        return ModelVersionResponse(
            id=version.id,
            model_registry_id=version.model_registry_id,
            experiment_id=version.experiment_id,
            version_number=version.version_number,
            algorithm=version.algorithm,
            artifact_uri=version.artifact_uri,
            lifecycle_stage=version.lifecycle_stage,
            created_at=version.created_at.isoformat(),
            approvals=[
                ModelApprovalDetail(
                    id=approval.id,
                    decision=approval.decision,
                    comments=approval.comments,
                    approved_by_user_id=approval.approved_by_user_id,
                    created_at=approval.created_at.isoformat(),
                )
            ],
        )
