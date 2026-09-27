from typing import List, Optional
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.core.exceptions import ModelOpsException, NotFoundException
from apps.api.app.infrastructure.database.models import Deployment, DeploymentEvent, ModelVersion
from apps.api.app.modules.deployments.schemas import (
    CreateDeploymentRequest,
    DeploymentDetailResponse,
    DeploymentEventDetail,
    DeploymentSummary,
    RollbackDeploymentRequest,
)
from apps.api.app.modules.deployments.serving_cache import serving_cache

class DeploymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_deployment(
        self, workspace_id: str, user_email: str, req: CreateDeploymentRequest
    ) -> DeploymentDetailResponse:
        # 1. Fetch model version and verify it belongs to workspace and is APPROVED
        stmt = (
            select(ModelVersion)
            .options(selectinload(ModelVersion.model_registry))
            .where(ModelVersion.id == req.model_version_id)
        )
        res = await self.db.execute(stmt)
        version = res.scalar_one_or_none()
        if not version or version.model_registry.workspace_id != workspace_id:
            raise NotFoundException("ModelVersion", req.model_version_id)

        if version.lifecycle_stage != "APPROVED":
            raise ModelOpsException(
                f"Cannot deploy model version with stage '{version.lifecycle_stage}'. Only APPROVED models can be deployed."
            )

        # 2. Deactivate any existing active deployments in this environment
        await self.db.execute(
            update(Deployment)
            .where(
                Deployment.workspace_id == workspace_id,
                Deployment.environment == req.environment,
                Deployment.status == "ACTIVE",
            )
            .values(status="INACTIVE")
        )

        # 3. Create Deployment record
        endpoint_url = f"/api/v1/predictions?deployment_id="
        deployment = Deployment(
            workspace_id=workspace_id,
            name=req.name,
            model_version_id=version.id,
            status="ACTIVE",
            traffic_percentage=req.traffic_percentage,
            endpoint_url=endpoint_url,
            environment=req.environment,
        )
        self.db.add(deployment)
        await self.db.flush()

        deployment.endpoint_url = f"/api/v1/predictions?deployment_id={deployment.id}"

        # 4. Record Deployment Event
        event = DeploymentEvent(
            deployment_id=deployment.id,
            event_type="CREATED",
            description=f"Model version {version.version_number} deployed to {req.environment} by {user_email}.",
            actor=user_email,
            details={"model_version_id": version.id, "traffic": req.traffic_percentage},
        )
        self.db.add(event)

        # 5. Mark ModelVersion as DEPLOYED
        version.lifecycle_stage = "DEPLOYED"

        await self.db.commit()

        # 6. Preload model artifact in serving cache
        try:
            await serving_cache.get_or_load_version(version.id, version.artifact_uri)
        except Exception as e:
            # If load fails, update deployment status
            deployment.status = "FAILED"
            await self.db.commit()
            raise ModelOpsException(f"Failed to load model artifact for serving: {str(e)}")

        return await self.get_deployment(workspace_id, deployment.id)

    async def list_deployments(self, workspace_id: str) -> List[DeploymentSummary]:
        stmt = (
            select(Deployment)
            .options(selectinload(Deployment.model_version))
            .where(Deployment.workspace_id == workspace_id)
            .order_by(desc(Deployment.created_at))
        )
        res = await self.db.execute(stmt)
        deployments = res.scalars().all()

        return [
            DeploymentSummary(
                id=d.id,
                name=d.name,
                model_version_id=d.model_version_id,
                status=d.status,
                traffic_percentage=d.traffic_percentage,
                endpoint_url=d.endpoint_url,
                environment=d.environment,
                created_at=d.created_at.isoformat(),
                algorithm=d.model_version.algorithm if d.model_version else None,
            )
            for d in deployments
        ]

    async def get_deployment(self, workspace_id: str, deployment_id: str) -> DeploymentDetailResponse:
        stmt = (
            select(Deployment)
            .options(
                selectinload(Deployment.events),
                selectinload(Deployment.model_version),
            )
            .where(
                Deployment.id == deployment_id,
                Deployment.workspace_id == workspace_id,
            )
        )
        res = await self.db.execute(stmt)
        d = res.scalar_one_or_none()
        if not d:
            raise NotFoundException("Deployment", deployment_id)

        events = [
            DeploymentEventDetail(
                id=e.id,
                event_type=e.event_type,
                description=e.description,
                actor=e.actor,
                created_at=e.created_at.isoformat(),
                details=e.details,
            )
            for e in sorted(d.events, key=lambda x: str(x.created_at), reverse=True)
        ]

        return DeploymentDetailResponse(
            id=d.id,
            name=d.name,
            model_version_id=d.model_version_id,
            status=d.status,
            traffic_percentage=d.traffic_percentage,
            endpoint_url=d.endpoint_url,
            environment=d.environment,
            created_at=d.created_at.isoformat(),
            model_algorithm=d.model_version.algorithm if d.model_version else None,
            events=events,
        )

    async def rollback_deployment(
        self, workspace_id: str, user_email: str, deployment_id: str, req: RollbackDeploymentRequest
    ) -> DeploymentDetailResponse:
        deployment = await self.db.execute(
            select(Deployment).where(
                Deployment.id == deployment_id,
                Deployment.workspace_id == workspace_id,
            )
        )
        dep = deployment.scalar_one_or_none()
        if not dep:
            raise NotFoundException("Deployment", deployment_id)

        # Validate target model version
        stmt = (
            select(ModelVersion)
            .options(selectinload(ModelVersion.model_registry))
            .where(ModelVersion.id == req.target_model_version_id)
        )
        res = await self.db.execute(stmt)
        target_version = res.scalar_one_or_none()
        if not target_version or target_version.model_registry.workspace_id != workspace_id:
            raise NotFoundException("ModelVersion", req.target_model_version_id)

        old_version_id = dep.model_version_id
        dep.model_version_id = target_version.id
        dep.status = "ACTIVE"

        event = DeploymentEvent(
            deployment_id=dep.id,
            event_type="ROLLED_BACK",
            description=f"Rolled back from version {old_version_id} to version {target_version.version_number}. Reason: {req.reason}",
            actor=user_email,
            details={"previous_version": old_version_id, "new_version": target_version.id},
        )
        self.db.add(event)
        await self.db.commit()

        # Preload target version in cache
        await serving_cache.get_or_load_version(target_version.id, target_version.artifact_uri)

        return await self.get_deployment(workspace_id, dep.id)
