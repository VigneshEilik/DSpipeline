# ADR 0003: Storage and Task Execution Resilient Abstractions

## Status
Accepted

## Context
Production deployments utilize MinIO/AWS S3 for blob storage (datasets, serialized artifacts) and Celery backed by Redis for asynchronous compute (model training, batch inference, drift reports). However, in local single-developer environments or environments where Docker engine is not active, demanding strict external dependencies for basic test runs or development introduces unnecessary friction.

## Decision
We implement clean interface abstractions for storage and task execution:
1. **Storage Interface (`StorageService`)**:
   - `S3StorageService`: Interacts with MinIO/S3 using `boto3`/`botocore`.
   - `LocalStorageService`: Uses the local filesystem directory (`./storage`) with identical semantics (put, get, exists, delete, get_url).
   - Selection is controlled via configuration (`STORAGE_BACKEND=s3` or `STORAGE_BACKEND=local`).
2. **Task Execution Interface (`TaskRunner`)**:
   - When Celery and Redis are reachable, jobs are dispatched to Celery queues (`training`, `batch_inference`, `drift`).
   - If Redis is unavailable or in lightweight standalone dev mode, the platform utilizes an asynchronous `BackgroundWorker` (Python `asyncio` task / `ThreadPoolExecutor`) so all workflows remain fully functional without external containers.

## Consequences
- **Positive**: Seamless developer experience; fully testable in CI and standalone local environments; complete production readiness when running via Docker Compose.
- **Negative**: Requires maintaining two implementations behind each abstraction interface, though both conform strictly to the same contract.
