import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field, model_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App
    PROJECT_NAME: str = "ModelOps Studio"
    ENVIRONMENT: str = "development"  # "development", "testing", "production"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-insecure-secret-key-replace-in-production-min-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_V1_STR: str = "/api/v1"
    ENABLE_DOCS_IN_PRODUCTION: bool = False

    # Security & Headers
    SECURE_COOKIES: bool = False
    COOKIE_SAMESITE: str = "lax"
    MAX_UPLOAD_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120
    TRUSTED_HOSTS: str = "localhost,127.0.0.1,api,web,0.0.0.0"

    @computed_field
    @property
    def trusted_hosts_list(self) -> List[str]:
        return [h.strip() for h in self.TRUSTED_HOSTS.split(",") if h.strip()]

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://web:3000"

    @computed_field
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./modelops_dev.db"
    DATABASE_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

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
    USE_IN_PROCESS_WORKER: bool = True  # In dev/test: fallback to in-process async worker

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"

    # Monitoring & Telemetry
    PROMETHEUS_METRICS_ENABLED: bool = True

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            self.DEBUG = False
            # Secret key must not be default and must be at least 32 chars
            if (
                "dev-insecure" in self.SECRET_KEY
                or len(self.SECRET_KEY) < 32
            ):
                raise ValueError(
                    "Production configuration error: SECRET_KEY must be a securely generated random string of at least 32 characters."
                )
            # Database must not be SQLite
            if "sqlite" in self.DATABASE_URL.lower():
                raise ValueError(
                    "Production configuration error: SQLite is not permitted in production. A production PostgreSQL database URL must be configured."
                )
            # Storage backend should be S3 or MinIO
            if self.STORAGE_BACKEND == "local":
                raise ValueError(
                    "Production configuration error: STORAGE_BACKEND must be configured to 's3' (MinIO or AWS S3) in production."
                )
            # MinIO credentials check
            if self.MINIO_ROOT_PASSWORD == "minioadmin" and self.STORAGE_BACKEND == "s3":
                raise ValueError(
                    "Production configuration error: Default MINIO_ROOT_PASSWORD ('minioadmin') is prohibited in production."
                )
        return self

settings = Settings()
