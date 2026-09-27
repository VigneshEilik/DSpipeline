# ModelOps Studio — Enterprise ML Model-to-Production Platform

> **From Data to Intelligence. From Experiment to Production.**

ModelOps Studio is an enterprise-grade, full-stack Machine Learning Operations (MLOps) platform built to manage the complete lifecycle of tabular machine learning models: from data ingestion and schema validation, to reproducible training, experiment tracking, model registry, zero-skew serving, and continuous data drift monitoring.

---

## 🌟 Core Architecture & Capabilities

```
Raw Data
  → Ingestion & Pandera Schema Validation
  → Column-level Profiling & Missing-Value Audits
  → Reusable Preprocessing (ColumnTransformer)
  → Reproducible Multi-Model Training (Logistic, RF, HistGB)
  → Unified Pipeline Serialization (.joblib)
  → Automated Model Evaluation (ROC-AUC, PR-AUC, F1, Confusion Matrix)
  → Controlled Model Registry (Draft → Evaluated → Approved → Deployed)
  → Real-Time Inference (<20ms) & Batch Predictions
  → Telemetry (Prometheus & Grafana) & Data Drift Detection
```

### Key Engineering Decisions
- **Zero Train/Serve Skew**: Feature imputation and encoding (`ColumnTransformer`) are unified with the estimator in a single `sklearn.pipeline.Pipeline`, fit strictly on training splits, and serialized as an atomic `.joblib` artifact.
- **Resilient Dual Storage**: Production MinIO/S3 object storage driver paired with a path-traversal-guarded local filesystem storage provider for standalone development.
- **Enterprise Security**: Argon2id password hashing via `pwdlib`, short-lived JWT access tokens, SameSite cookies, and strict workspace multi-tenant data isolation.
- **Google Material 3 Design**: Clean tonal palettes, responsive layout, accessible typography, and high-density operational telemetry.

---

## 🏗️ Monorepo Structure

```
DSPipeline/
|-- apps/
|   |-- web/                # Next.js 15 App Router, React 19, Tailwind, Material 3 tokens
|   |-- api/                # FastAPI Modular Monolith (SQLAlchemy 2.0 async, Alembic, Pydantic v2)
|   |-- worker/             # Celery worker service for training, batch inference, drift jobs
|-- ml/
|   |-- pipelines/          # Ingestion, validation, preprocessing, training, inference
|   |-- scripts/            # CLI training & evaluation tools (train_cli.py)
|   |-- tests/              # ML test suite (zero leakage, deterministic training, serialization)
|-- infra/
|   |-- prometheus/         # Prometheus scrape configuration
|   |-- grafana/            # Provisioned datasources and operational dashboards
|-- docs/
|   |-- architecture/       # System design, high-level diagrams, roadmap
|   |-- adr/                # Architecture Decision Records (ADR 0001, 0002, 0003)
|   |-- implementation-status.md
|-- datasets/
|   |-- samples/            # Telco Customer Churn sample dataset (2500 records)
|-- docker-compose.yml      # Multi-container local production stack
|-- pytest.ini
|-- .env.example
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.12+ (tested with Python 3.14)
- Node.js 20+ (tested with Node 24)
- Docker & Docker Compose (optional for standalone local dev)

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/VigneshEilik/DSpipeline.git
cd DSpipeline

# Configure environment variables
cp .env.example .env
```

### 3. Backend & ML Setup (Local Standalone)
```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # On Windows
# source .venv/bin/activate # On Linux/macOS

# Install dependencies
pip install -r apps/api/requirements.txt

# Run database migrations
alembic -c apps/api/alembic.ini upgrade head

# Run tests (Unit & ML pipeline tests)
pytest

# Launch API server
uvicorn apps.api.app.main:app --reload --port 8000
```
- Swagger API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/healthz`
- Prometheus Metrics: `http://localhost:8000/metrics`

### 4. Frontend Setup
```bash
cd apps/web
npm install
npm run dev
```
- Web Application: `http://localhost:3000`

### 5. Running with Docker Compose
To launch the full containerized stack (Postgres, Redis, MinIO, MLflow, Prometheus, Grafana, API, Worker, Web):
```bash
docker compose up -d
```
- Web UI: `http://localhost:3000`
- API Docs: `http://localhost:8000/docs`
- MLflow UI: `http://localhost:5000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001` (admin / admin)
- MinIO Console: `http://localhost:9001` (minioadmin / minioadmin)

---

## 🧪 Testing & Verification

Execute the automated test suite verifying health endpoints, security primitives, storage drivers, and the ML pipeline:
```bash
pytest -v
```

---

## 📄 License
This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
