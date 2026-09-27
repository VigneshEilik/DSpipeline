# ADR 0001: Monorepo Modular Monolith Architecture

## Status
Accepted

## Context
ModelOps Studio requires coordinating a web frontend, REST API services, asynchronous background workers, ML training pipelines, infrastructure configurations, and shared contracts. Splitting these into separate repositories or multiple microservices early introduces substantial operational overhead, complex distributed transactions, deployment coordination friction, and cross-repo version drift for a single-developer or small team environment.

## Decision
We choose a **Monorepo Modular Monolith** architecture:
1. `apps/web`: Single Next.js application managing all UI views, dashboards, and client state.
2. `apps/api`: A unified FastAPI application organized into clean domain modules (`auth`, `workspaces`, `datasets`, `experiments`, `models`, `deployments`, `predictions`, `monitoring`).
3. `apps/worker`: Celery worker executing background training, batch inference, and drift calculation tasks, sharing domain models and database connections with the API.
4. `ml/`: Pure Python ML engine isolated from web and HTTP transport logic.

## Consequences
- **Positive**: Single codebase, atomic commits, shared schemas and validation rules, simplified local testing and CI/CD pipelines.
- **Negative**: Monorepo tooling and build setup must be maintained; boundary enforcement between modules requires engineering discipline.
