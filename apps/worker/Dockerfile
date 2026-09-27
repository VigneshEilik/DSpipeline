# ==============================================================================
# ModelOps Studio — Hardened Production Worker Dockerfile
# ==============================================================================

# Stage 1: Build Dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /build/requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r /build/requirements.txt

# Stage 2: Final Runtime Image
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -M appuser

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source code
COPY --chown=appuser:appgroup apps/api /app/apps/api
COPY --chown=appuser:appgroup apps/worker /app/apps/worker
COPY --chown=appuser:appgroup ml /app/ml

# Create temporary storage directory with correct ownership
RUN mkdir -p /app/storage && chown -R appuser:appgroup /app/storage

USER appuser

CMD ["celery", "-A", "apps.worker.app.celery_app:celery_app", "worker", "--loglevel=info", "--concurrency=2"]
