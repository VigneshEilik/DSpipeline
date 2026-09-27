# ModelOps Studio — Incident Response Runbook

**Severity Definitions**:
* **Sev-1 (Critical)**: Total API outage, unable to serve predictions, database down, or verified security breach.
* **Sev-2 (Major)**: High inference latency (>1s), background training stalled, or elevated 5xx error rate (>5%).
* **Sev-3 (Minor)**: Dashboard visual bug, non-critical telemetry delay, single worker restart.

---

## 1. Sev-1: API Complete Outage or 503 Service Unavailable

### Triage & Diagnostics
1. Check readiness endpoint:
   ```bash
   curl -i http://localhost:8000/readyz
   ```
2. Check container status:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```
3. If PostgreSQL is unhealthy:
   ```bash
   docker compose -f docker-compose.prod.yml logs --tail=50 postgres
   # Restart database container
   docker compose -f docker-compose.prod.yml restart postgres
   ```
4. If API process crashed:
   ```bash
   docker compose -f docker-compose.prod.yml logs --tail=100 api
   docker compose -f docker-compose.prod.yml restart api
   ```

---

## 2. Sev-2: Elevated Prediction Latency or Inference Timeout

### Triage & Resolution
1. Check live active serving cache and deployment:
   ```bash
   curl -s http://localhost:8000/api/v1/deployments -H "Authorization: Bearer $TOKEN" -H "X-Workspace-ID: $WORKSPACE_ID"
   ```
2. Check CPU and memory pressure on API host:
   ```bash
   docker stats --no-stream
   ```
3. If a recently deployed model is causing high compute latency:
   **Execute immediate atomic rollback** to the prior approved model version via dashboard or API:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/deployments/{id}/rollback" \
     -H "Authorization: Bearer $TOKEN" \
     -H "X-Workspace-ID: $WORKSPACE_ID" \
     -H "Content-Type: application/json" \
     -d '{"target_model_version_id": "PREVIOUS_VERSION_ID", "reason": "Sev-2 latency degradation"}'
   ```

---

## 3. Sev-2: Celery Background Training Jobs Stalled

### Triage & Resolution
1. Check Redis connectivity:
   ```bash
   docker compose -f docker-compose.prod.yml exec redis redis-cli -a "$REDIS_PASSWORD" ping
   ```
2. Check Celery worker logs:
   ```bash
   docker compose -f docker-compose.prod.yml logs --tail=100 worker
   ```
3. Restart worker instances:
   ```bash
   docker compose -f docker-compose.prod.yml restart worker
   ```
4. Any training jobs marked `RUNNING` for interrupted tasks will automatically transition to `FAILED` with retry capability.
