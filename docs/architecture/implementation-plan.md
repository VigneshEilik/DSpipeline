# ModelOps Studio — Phased Implementation Plan

## Phase Overview

The project is structured into 7 sequential milestones (0 through 6) to ensure continuous working software, verifiable functionality, and strict adherence to software engineering standards.

---

### Milestone 0: Repository & Environment Audit
- [x] Inspect existing workspace, OS, and toolchains (Python 3.14, Node 24, npm 11, Docker, local Postgres service).
- [x] Initialize Git repository with comprehensive `.gitignore` and `.env.example`.
- [x] Create standardized monorepo directory structure.
- [x] Document system architecture (`docs/architecture/system-design.md`) and implementation plan (`docs/architecture/implementation-plan.md`).
- [x] Record initial Architecture Decision Records (ADRs).
- [x] Establish implementation status tracking (`docs/implementation-status.md`).

---

### Milestone 1: Project Foundation & Core Infrastructure
- [ ] Configure Python backend dependencies (`pyproject.toml` or `requirements.txt`).
- [ ] Implement database models using SQLAlchemy 2.0 async (Users, Workspaces, Datasets, Experiments, Models, Deployments, Predictions).
- [ ] Setup Alembic database migrations.
- [ ] Implement FastAPI core application (`main.py`, config, security, logging, error handling, health checks).
- [ ] Implement Storage service abstraction (S3/MinIO driver + local filesystem fallback).
- [ ] Provide Docker Compose configuration (`docker-compose.yml`) for PostgreSQL, Redis, MinIO, MLflow, Prometheus, Grafana, API, Worker, and Web.
- [ ] Setup Next.js application foundation in `apps/web` with Material 3 design tokens.
- [ ] Verify health endpoints and initial test suites.

---

### Milestone 2: Real Machine Learning Pipeline
- [ ] Implement Telco Customer Churn dataset generator and sample loader with documented schema.
- [ ] Build dataset validation pipeline using Pandera (schema integrity, null checks, target distribution).
- [ ] Build scikit-learn preprocessing pipeline (`ColumnTransformer`) for numeric and categorical features.
- [ ] Implement training pipeline supporting baseline (Logistic Regression) and advanced candidate models (Random Forest, HistGradientBoosting).
- [ ] Implement evaluation module calculating Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, and Confusion Matrix.
- [ ] Implement unified artifact packaging (`joblib` export of complete pipeline).
- [ ] Verify reproducible CLI execution and unit tests for ML pipeline.

---

### Milestone 3: Backend APIs & Background Job Processing
- [ ] Implement Authentication & Workspace Isolation (JWT, password hashing, workspace headers/context).
- [ ] Implement Datasets API (Upload CSV, validate, preview rows, column statistics).
- [ ] Implement Celery worker tasks with in-process background worker fallback (training jobs, batch inference, drift computation).
- [ ] Implement Experiments API (trigger run, poll status, inspect logs/metrics, compare runs).
- [ ] Implement Model Registry API (register, list versions, approve/reject lifecycle transitions).
- [ ] Implement Deployments API (create active deployment, health status, rollback).
- [ ] Implement Predictions API (real-time single inference with schema validation, batch CSV inference).
- [ ] Write integration tests for API endpoints.

---

### Milestone 4: Premium Google Material 3 Frontend
- [ ] Implement Material 3 inspired theme tokens in `apps/web/src/app/globals.css`.
- [ ] Build application shell (collapsible navigation sidebar, top bar, workspace switcher, notifications).
- [ ] Implement Overview Dashboard page (real-time metrics, system status, active deployments, volume graphs).
- [ ] Implement Datasets page (drag-and-drop CSV upload, data preview, summary statistics, validation reports).
- [ ] Implement Experiments page (training job launcher, live logs, model comparison charts, confusion matrix).
- [ ] Implement Model Registry page (version timeline, metric cards, approval actions).
- [ ] Implement Deployments page (active serving endpoints, traffic allocation, rollback modal).
- [ ] Implement Predictions page (interactive single customer churn risk calculator, batch inference uploader).
- [ ] Implement Monitoring page (latency percentiles, error rates, drift detection graphs).
- [ ] Implement Settings page (workspace management, storage status, environment config).

---

### Milestone 5: Observability & Drift Monitoring
- [ ] Implement Prometheus metrics instrumentation in FastAPI (`/metrics`).
- [ ] Configure Prometheus scrape configs and Grafana dashboards for ModelOps.
- [ ] Implement data drift detection module (comparing inference distributions to training baseline).
- [ ] Expose drift reports and feature distribution comparisons in API and UI.

---

### Milestone 6: Deployment, CI/CD & Final Verification
- [ ] Write multi-stage Dockerfiles for `apps/web`, `apps/api`, and `apps/worker`.
- [ ] Create GitHub Actions workflows for linting, testing, and Docker builds.
- [ ] Write end-to-end integration and smoke tests.
- [ ] Complete comprehensive documentation (root README, API docs, ML model card, runbooks).
- [ ] Execute full end-to-end user journey verification: Upload data -> Validate -> Train -> Register -> Approve -> Deploy -> Predict -> Monitor.
