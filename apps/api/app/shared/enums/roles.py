from enum import Enum
from typing import Set

class UserRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    DATA_SCIENTIST = "DATA_SCIENTIST"
    ML_ENGINEER = "ML_ENGINEER"
    VIEWER = "VIEWER"

class Permission(str, Enum):
    # Workspace
    WORKSPACE_MANAGE = "workspace:manage"
    WORKSPACE_MEMBERS_MANAGE = "workspace:members:manage"
    WORKSPACE_VIEW = "workspace:view"

    # Datasets
    DATASET_CREATE = "dataset:create"
    DATASET_VIEW = "dataset:view"
    DATASET_DELETE = "dataset:delete"

    # Experiments
    EXPERIMENT_CREATE = "experiment:create"
    EXPERIMENT_VIEW = "experiment:view"
    EXPERIMENT_CANCEL = "experiment:cancel"

    # Models
    MODEL_REGISTER = "model:register"
    MODEL_VIEW = "model:view"
    MODEL_APPROVE = "model:approve"
    MODEL_REJECT = "model:reject"

    # Deployments
    DEPLOYMENT_CREATE = "deployment:create"
    DEPLOYMENT_VIEW = "deployment:view"
    DEPLOYMENT_ROLLBACK = "deployment:rollback"

    # Predictions
    PREDICTION_CREATE = "prediction:create"
    PREDICTION_VIEW = "prediction:view"
    PREDICTION_BATCH = "prediction:batch"

    # Monitoring & Audit
    MONITORING_VIEW = "monitoring:view"
    MONITORING_RUN = "monitoring:run"
    AUDIT_VIEW = "audit:view"

ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.OWNER: set(Permission),  # All permissions
    UserRole.ADMIN: {
        Permission.WORKSPACE_VIEW,
        Permission.WORKSPACE_MEMBERS_MANAGE,
        Permission.DATASET_CREATE,
        Permission.DATASET_VIEW,
        Permission.DATASET_DELETE,
        Permission.EXPERIMENT_CREATE,
        Permission.EXPERIMENT_VIEW,
        Permission.EXPERIMENT_CANCEL,
        Permission.MODEL_REGISTER,
        Permission.MODEL_VIEW,
        Permission.MODEL_APPROVE,
        Permission.MODEL_REJECT,
        Permission.DEPLOYMENT_CREATE,
        Permission.DEPLOYMENT_VIEW,
        Permission.DEPLOYMENT_ROLLBACK,
        Permission.PREDICTION_CREATE,
        Permission.PREDICTION_VIEW,
        Permission.PREDICTION_BATCH,
        Permission.MONITORING_VIEW,
        Permission.MONITORING_RUN,
        Permission.AUDIT_VIEW,
    },
    UserRole.DATA_SCIENTIST: {
        Permission.WORKSPACE_VIEW,
        Permission.DATASET_CREATE,
        Permission.DATASET_VIEW,
        Permission.EXPERIMENT_CREATE,
        Permission.EXPERIMENT_VIEW,
        Permission.EXPERIMENT_CANCEL,
        Permission.MODEL_REGISTER,
        Permission.MODEL_VIEW,
        Permission.PREDICTION_CREATE,
        Permission.PREDICTION_VIEW,
        Permission.PREDICTION_BATCH,
        Permission.MONITORING_VIEW,
    },
    UserRole.ML_ENGINEER: {
        Permission.WORKSPACE_VIEW,
        Permission.DATASET_VIEW,
        Permission.EXPERIMENT_VIEW,
        Permission.MODEL_VIEW,
        Permission.MODEL_APPROVE,
        Permission.MODEL_REJECT,
        Permission.DEPLOYMENT_CREATE,
        Permission.DEPLOYMENT_VIEW,
        Permission.DEPLOYMENT_ROLLBACK,
        Permission.PREDICTION_CREATE,
        Permission.PREDICTION_VIEW,
        Permission.PREDICTION_BATCH,
        Permission.MONITORING_VIEW,
        Permission.MONITORING_RUN,
    },
    UserRole.VIEWER: {
        Permission.WORKSPACE_VIEW,
        Permission.DATASET_VIEW,
        Permission.EXPERIMENT_VIEW,
        Permission.MODEL_VIEW,
        Permission.DEPLOYMENT_VIEW,
        Permission.PREDICTION_VIEW,
        Permission.MONITORING_VIEW,
    },
}

def has_permission(role: str, permission: Permission) -> bool:
    try:
        user_role = UserRole(role.upper())
    except ValueError:
        return False
    return permission in ROLE_PERMISSIONS.get(user_role, set())
