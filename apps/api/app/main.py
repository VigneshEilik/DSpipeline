import re
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Dict, List, Tuple
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
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

# Bounded Cardinality Prometheus Metrics
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

# Helper to normalize endpoints and prevent metric cardinality explosion
UUID_OR_ID_REGEX = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{24,}|\d+",
    re.IGNORECASE,
)

def normalize_path_for_metrics(path: str) -> str:
    """Replaces dynamic IDs and UUIDs with {id} to guarantee bounded label cardinality."""
    return UUID_OR_ID_REGEX.sub("{id}", path)

# Simple in-process rate limiter (requests per minute per client IP)
class InMemoryRateLimiter:
    def __init__(self, limit_per_minute: int = 120):
        self.limit = limit_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0
        # Filter timestamps within current 60s sliding window
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip] if ts > window_start
        ]
        if len(self.requests[client_ip]) >= self.limit:
            return False
        self.requests[client_ip].append(now)
        return True

rate_limiter = InMemoryRateLimiter(limit_per_minute=settings.RATE_LIMIT_PER_MINUTE)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Initializing ModelOps Studio in %s mode...", settings.ENVIRONMENT)
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down ModelOps Studio...")

docs_url = None if settings.ENVIRONMENT == "production" and not settings.ENABLE_DOCS_IN_PRODUCTION else "/docs"
redoc_url = None if settings.ENVIRONMENT == "production" and not settings.ENABLE_DOCS_IN_PRODUCTION else "/redoc"
openapi_url = None if settings.ENVIRONMENT == "production" and not settings.ENABLE_DOCS_IN_PRODUCTION else "/openapi.json"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-Grade ML Model-to-Production Platform",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(ModelOpsException, modelops_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Trusted Host Middleware (prevent Host Header Poisoning)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts_list,
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Request tracking, security headers, rate limiting, and telemetry middleware
@app.middleware("http")
async def enterprise_security_and_telemetry_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()

    method = request.method
    raw_path = request.url.path
    normalized_path = normalize_path_for_metrics(raw_path)

    # 1. Enforce payload size limit
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_UPLOAD_SIZE_BYTES:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "error": {
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": f"Request body exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB",
                }
            },
        )

    # 2. Rate limiting check (skip internal healthz/readyz/metrics)
    if settings.RATE_LIMIT_ENABLED and not raw_path.startswith(("/healthz", "/readyz", "/metrics")):
        client_ip = request.client.host if request.client else "unknown"
        if not rate_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please slow down.",
                    }
                },
                headers={"Retry-After": "60"},
            )

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # Inject standard security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.SECURE_COOKIES:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Record Bounded Prometheus Metrics
        if settings.PROMETHEUS_METRICS_ENABLED and not raw_path.startswith("/metrics"):
            REQUEST_COUNT.labels(
                method=method, endpoint=normalized_path, status_code=response.status_code
            ).inc()
            REQUEST_LATENCY.labels(
                method=method, endpoint=normalized_path
            ).observe(duration)

        return response
    except Exception as exc:
        duration = time.time() - start_time
        if settings.PROMETHEUS_METRICS_ENABLED and not raw_path.startswith("/metrics"):
            REQUEST_COUNT.labels(
                method=method, endpoint=normalized_path, status_code=500
            ).inc()
            REQUEST_LATENCY.labels(
                method=method, endpoint=normalized_path
            ).observe(duration)
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
        "docs": docs_url or "disabled in production",
        "status": "running",
    }

# Mount API v1 domain router
from apps.api.app.api.v1.router import api_v1_router
app.include_router(api_v1_router)
