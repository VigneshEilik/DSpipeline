import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import text

from apps.api.app.core.config import settings
from apps.api.app.core.exceptions import (
    ModelOpsException,
    modelops_exception_handler,
    unhandled_exception_handler,
)
from apps.api.app.core.logging import logger, setup_logging
from apps.api.app.infrastructure.database.session import AsyncSessionLocal, init_db

# Prometheus Metrics
REQUEST_COUNT = Counter(
    "modelops_http_requests_total",
    "Total HTTP requests handled by ModelOps Studio",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "modelops_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Initializing ModelOps Studio...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down ModelOps Studio...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-Grade ML Model-to-Production Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(ModelOpsException, modelops_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracking middleware
@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()

    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)
        duration = time.time() - start_time
        response.headers["X-Request-ID"] = request_id

        if settings.PROMETHEUS_METRICS_ENABLED and not path.startswith("/metrics"):
            REQUEST_COUNT.labels(method=method, endpoint=path, status_code=response.status_code).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(duration)

        return response
    except Exception as exc:
        duration = time.time() - start_time
        if settings.PROMETHEUS_METRICS_ENABLED and not path.startswith("/metrics"):
            REQUEST_COUNT.labels(method=method, endpoint=path, status_code=500).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(duration)
        raise exc

# Liveness check
@app.get("/healthz", tags=["System"])
async def liveness_check():
    return {"status": "ok", "timestamp": time.time()}

# Readiness check (verifies database)
@app.get("/readyz", tags=["System"])
async def readiness_check():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0",
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": f"error: {str(e)}",
            },
        )

# Metrics endpoint
@app.get("/metrics", tags=["System"])
async def metrics_endpoint():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }
