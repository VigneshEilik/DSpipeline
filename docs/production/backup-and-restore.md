# ModelOps Studio — Backup and Disaster Recovery Runbook

**Objective**: Guarantee business continuity, zero data loss for datasets and models, and rapid recovery in the event of hardware failure, database corruption, or security incidents.

---

## 1. Backup Strategy Overview

| Asset | Storage Engine | Backup Method | Frequency | Retention |
| :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL Database** | PostgreSQL 16 | `pg_dump` compressed SQL dump | Daily (02:00 UTC) | 30 Days |
| **Model & Dataset Artifacts**| MinIO / AWS S3 | `mc mirror` or S3 Cross-Region Replication | Real-time / Daily | 90 Days |
| **Environment Configuration**| `.env.production` | Encrypted Secret Vault (Vault / AWS Secrets) | On Change | Versioned |

---

## 2. Automated PostgreSQL Backup Procedure

### Manual Database Snapshot
```bash
# Create timestamped backup
BACKUP_FILE="backup_modelops_$(date +%Y%m%d_%H%M%S).sql.gz"

docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U modelops_user -d modelops_db | gzip > "/var/backups/modelops/${BACKUP_FILE}"

echo "Backup saved to /var/backups/modelops/${BACKUP_FILE}"
```

### Automated Cron Job (`/etc/cron.d/modelops-db-backup`)
```cron
0 2 * * * root /opt/modelops/scripts/backup_db.sh > /var/log/modelops_backup.log 2>&1
```

---

## 3. Database Restoration Procedure

```bash
# 1. Stop write traffic to API
docker compose -f docker-compose.prod.yml stop api worker

# 2. Restore database from backup
gunzip -c /var/backups/modelops/backup_modelops_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres psql -U modelops_user -d modelops_db

# 3. Verify database integrity
docker compose -f docker-compose.prod.yml exec -T postgres psql -U modelops_user -d modelops_db -c "SELECT COUNT(*) FROM predictions;"

# 4. Restart application services
docker compose -f docker-compose.prod.yml start api worker
```

---

## 4. Disaster Recovery Testing Schedule

Disaster recovery drills must be performed quarterly:
1. Spin up an isolated staging server.
2. Restore the latest database backup.
3. Synchronize artifacts from storage replica.
4. Execute `pytest apps/api/tests/integration/` against restored database.
5. Verify that active model inference operates with expected accuracy and latency.
