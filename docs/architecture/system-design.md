# ModelOps Studio — System Architecture & Design

## 1. Executive Summary

ModelOps Studio is a production-oriented, full-stack Machine Learning Model-to-Production platform. The platform manages the entire lifecycle of tabular machine learning models: from dataset ingestion, validation, exploratory analysis, reproducible training, MLflow experiment tracking, model registry and approval, through to real-time & batch inference, data drift detection, and automated monitoring.

## 2. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer (Next.js 15 App Router)"]
        UI["Web UI (React 19 / TypeScript / Material 3 Tokens)"]
        State["TanStack Query v5 Server State & Cache"]
    end

    subgraph APILayer ["API Layer (FastAPI Modular Monolith)"]
        Gateway["FastAPI Gateway / Router (/api/v1)"]
        AuthModule["Auth & RBAC Module (JWT / Cookie)"]
        DatasetModule["Datasets Module (Upload / Validation / Stats)"]
        ExpModule["Experiments Module (Trigger / Status / Compare)"]
        ModelModule["Model Registry & Lifecycle (Approval / Versions)"]
        DeployModule["Deployment Service (Serving Engine / Canary)"]
        InferenceModule["Inference Engine (Realtime / Batch)"]
        MonitoringModule["Monitoring & Drift Module (Evidently / Stats)"]
    end

    subgraph AsyncWorkerLayer ["Asynchronous Execution (Celery + Background Worker)"]
        Worker["Celery Worker / Background Task Engine"]
        IngestTask["Dataset Ingestion & Profiling Task"]
        TrainTask["ML Training & Evaluation Task"]
        BatchTask["Batch Inference Task"]
        DriftTask["Evidently Drift Report Task"]
    end

    subgraph MLLayer ["Core ML Engine (ml/ package)"]
        SchemaVal["Pandera / Strict Schema Validator"]
        Preproc["Scikit-Learn Pipeline & ColumnTransformer"]
        Trainers["Estimators (Logistic, RandomForest, HistGradientBoosting)"]
        Eval["Metrics Engine (ROC-AUC, PR-AUC, F1, Confusion Matrix)"]
        Explain["SHAP Explainer"]
    end

    subgraph DataStorageLayer ["Data & Storage Layer"]
        Postgres[(PostgreSQL 18 - Relational DB & Metadata)]
        Redis[(Redis - Broker, Cache & Task State)]
        MinIO[(MinIO / S3 - Datasets & Model Artifacts)]
        MLflowServer["MLflow Tracking & Registry Server"]
    end

    subgraph ObservabilityLayer ["Observability & Metrics"]
        Prometheus["Prometheus Metrics Collector"]
        Grafana["Grafana Dashboards"]
    end

    UI -->|HTTP / REST| Gateway
    Gateway --> AuthModule
    Gateway --> DatasetModule
    Gateway --> ExpModule
    Gateway --> ModelModule
    Gateway --> DeployModule
    Gateway --> InferenceModule
    Gateway --> MonitoringModule

    ExpModule -->|Enqueues Tasks| Worker
    DatasetModule -->|Enqueues Profiling| Worker
    InferenceModule -->|Batch Inference| Worker
    MonitoringModule -->|Runs Drift Analysis| Worker

    Worker --> SchemaVal
    Worker --> Preproc
    Worker --> Trainers
    Worker --> Eval
    Worker --> MLflowServer

    Gateway --> Postgres
    Worker --> Postgres
    Worker --> Redis
    Worker --> MinIO
    InferenceModule --> MinIO

    Gateway -.->|Exposes /metrics| Prometheus
    Prometheus --> Grafana
```

## 3. Component Breakdown

### 3.1 Frontend (`apps/web`)
- **Framework**: Next.js (App Router), React, TypeScript (strict mode).
- **Design System**: Google Material 3 design tokens implemented using Tailwind CSS and Radix UI primitives.
- **State Management**: TanStack Query v5 for server state caching, optimistic updates, and background refetching.
- **Forms & Validation**: React Hook Form with Zod schemas matching backend Pydantic contracts.
- **Visualizations**: Recharts for latency histograms, ROC/PR curves, confusion matrices, and drift distributions.

### 3.2 Backend Modular Monolith (`apps/api`)
- **Framework**: FastAPI with Pydantic v2 and `pydantic-settings`.
- **Database Engine**: SQLAlchemy 2.0 (asyncio) with Alembic migrations.
- **Domain Modules**:
  - `auth`: JWT token generation, password hashing (Argon2id/Bcrypt), workspace context injection.
  - `workspaces`: Multi-tenant workspace data isolation.
  - `datasets`: Streaming CSV ingestion, Pandera schema validation, column-level profiling.
  - `experiments`: Hyperparameter validation, run triggering, MLflow synchronization.
  - `models`: Model versioning, stage transitions (`draft` -> `evaluated` -> `approved` -> `deployed` -> `archived`).
  - `deployments`: Active deployment manager, traffic routing, rollbacks.
  - `predictions`: Low-latency real-time inference endpoint and asynchronous batch inference.
  - `monitoring`: Drift calculation jobs, prediction latency/throughput metrics, alerts.

### 3.3 ML Engine (`ml/`)
- **Self-Contained Pipeline**: Standalone package that can be invoked via CLI, imported by the worker, or executed in testing.
- **Zero Training/Serving Skew**:
  - `ColumnTransformer` handles numerical scaling, categorical imputation, and one-hot encoding.
  - Serialized as a single `Pipeline(steps=[('preprocessor', preprocessor), ('classifier', model)])` saved via `joblib`.
  - Inference requests pass raw JSON features into `pipeline.predict_proba(df)` with identical transformations guaranteed.

### 3.4 Storage & Task Execution Layer
- **Relational DB**: PostgreSQL 18 stores user accounts, workspace memberships, dataset metadata, experiment metrics, model registry records, deployments, predictions, and audit logs.
- **Object Storage**: MinIO (S3 compatible) stores raw uploaded CSVs and serialized model `.joblib` artifacts.
- **Broker & Queue**: Celery with Redis broker for asynchronous compute-intensive tasks, with an automatic in-process fallback engine for standalone developer machines without Redis running.

## 4. Security Architecture
1. **Tenant Isolation**: Every database entity has a `workspace_id`. Repositories filter on `workspace_id` automatically via dependency injection.
2. **Untrusted Input Sanitization**:
   - Max file size limits on CSV uploads (default 50MB).
   - Strict Pandera and Pydantic validation before any data touches ML pipelines.
   - SQL injection prevention via parameterized SQLAlchemy queries.
   - Filenames sanitized to prevent directory traversal (`secure_filename`).
3. **Secrets Management**: No secrets committed; loaded strictly via environment variables.
