import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App
    PROJECT_NAME: str = "ModelOps Studio"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-insecure-secret-key-replace-in-production-min-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_V1_STR: str = "/api/v1"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @computed_field
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    # Database
    # Default to sqlite for local tests/standalone execution if postgres is not configured
    DATABASE_URL: str = "sqlite+aiosqlite:///./modelops_dev.db"
    DATABASE_ECHO: bool = False

    # Object Storage (MinIO / S3 or Local fallback)
    STORAGE_BACKEND: str = "local"  # "s3" or "local"
    LOCAL_STORAGE_DIR: str = "./storage"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "modelops-artifacts"
    MINIO_SECURE: bool = False

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    USE_IN_PROCESS_WORKER: bool = True  # Fallback to in-process async worker when Celery/Redis is offline

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"

    # Monitoring & Telemetry
    PROMETHEUS_METRICS_ENABLED: bool = True

settings = Settings()
