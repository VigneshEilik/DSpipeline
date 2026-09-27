# ModelOps Studio — Operations Runbook

**Purpose**: Standard operating procedures for day-to-day administration, routine maintenance, and model lifecycle management.

---

## 1. Routine Health & Telemetry Checks

### Liveness & Readiness Probes
```bash
# Check API liveness
curl -s http://localhost:8000/healthz | jq

# Check database and system readiness
curl -s http://localhost:8000/readyz | jq
```

### Container Status & Resource Utilization
```bash
# Check running containers
docker compose -f docker-compose.prod.yml ps

# Check live memory and CPU usage
docker stats --no-stream
```

---

## 2. Model Lifecycle Operations

### Promoting a Model to Active Serving
1. Navigate to **Models** in the web dashboard (or invoke `POST /api/v1/models/{id}/approve`).
2. Verify that the model version is in `APPROVED` stage.
3. Submit deployment request via `POST /api/v1/deployments`.
4. Verify deployment state in `GET /api/v1/deployments`.

### Executing an Emergency Rollback
When an active model shows performance degradation or input drift:
```bash
curl -X POST "http://localhost:8000/api/v1/deployments/{deployment_id}/rollback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-ID: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d '{"target_model_version_id": "PREVIOUS_APPROVED_VERSION_ID", "reason": "Emergency rollback due to prediction drift"}'
```

---

## 3. Log Inspection & Troubleshooting

```bash
# View live API logs
docker compose -f docker-compose.prod.yml logs -f --tail=100 api

# View worker task logs
docker compose -f docker-compose.prod.yml logs -f --tail=100 worker

# Search for 5xx errors
docker compose -f docker-compose.prod.yml logs api | grep "500 Internal Server Error"
```

---

## 4. Celery Queue Management & Stalled Task Recovery

```bash
# Inspect Celery active workers
docker compose -f docker-compose.prod.yml exec worker celery -A apps.worker.app.celery_app:celery_app inspect active

# Purge queued tasks in emergency
docker compose -f docker-compose.prod.yml exec worker celery -A apps.worker.app.celery_app:celery_app purge
```
