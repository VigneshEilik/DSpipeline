from fastapi import APIRouter

from apps.api.app.modules.auth.router import router as auth_router
from apps.api.app.modules.workspaces.router import router as workspaces_router
from apps.api.app.modules.datasets.router import router as datasets_router
from apps.api.app.modules.experiments.router import router as experiments_router
from apps.api.app.modules.models.router import router as models_router
from apps.api.app.modules.deployments.router import router as deployments_router
from apps.api.app.modules.predictions.router import router as predictions_router
from apps.api.app.modules.monitoring.router import router as monitoring_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(workspaces_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(experiments_router)
api_v1_router.include_router(models_router)
api_v1_router.include_router(deployments_router)
api_v1_router.include_router(predictions_router)
api_v1_router.include_router(monitoring_router)
