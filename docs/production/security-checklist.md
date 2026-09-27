# ModelOps Studio — Production Security Checklist

**Classification**: Confidential / Operational Security  
**Mandatory Compliance Gate**: All items must be checked prior to deploying to a public or internet-facing network.

---

## 1. Authentication & Secrets
- [x] **No Default Passwords**: Strong, high-entropy passwords generated for `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, and `MINIO_ROOT_PASSWORD`.
- [x] **Secret Key Entropy**: `SECRET_KEY` is a securely generated 32+ byte string (e.g. `openssl rand -hex 32`).
- [x] **Disabled Dev Bootstrap**: `/api/v1/auth/bootstrap-dev` is strictly blocked in `ENVIRONMENT=production` with HTTP 403.
- [x] **Password Hashing**: Passwords stored exclusively as Argon2id hashes via `pwdlib`.
- [x] **JWT Security**: Access tokens signed via HMAC-SHA256 with 24-hour expiration.

## 2. Network & Tenant Isolation
- [x] **Tenant Scoping**: All queries for datasets, models, experiments, and deployments explicitly scoped to authorized `workspace_id`.
- [x] **Internal Database Ports**: Port 5432 (Postgres), 6379 (Redis), and 9001 (MinIO console) bound only to internal Docker network, not exposed on public 0.0.0.0.
- [x] **HTTPS Enforcement**: TLS 1.3 termination configured via reverse proxy (Caddy/Nginx) with HSTS headers enabled.
- [x] **Trusted Hosts**: `TrustedHostMiddleware` configured to prevent Host Header Poisoning.
- [x] **CORS Origins**: Restricted to authorized dashboard domains.

## 3. Application Security & Defenses
- [x] **Security Headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
- [x] **Payload Limits**: Request body size limited to 100MB (`MAX_UPLOAD_SIZE_BYTES`).
- [x] **Rate Limiting**: Configured to 120 req/min per IP with HTTP 429 backoff headers.
- [x] **Deep CSV Sniffing**: Binary executables (MZ, ELF), null bytes, and script tags rejected on upload.
- [x] **Model Deserialization Integrity**: SHA-256 checksums verified before deserializing model artifacts.

## 4. Container & Operating System
- [x] **Non-Root Containers**: `api` and `worker` Docker containers run under unprivileged user `appuser` (UID 10001).
- [x] **Multi-Stage Builds**: Minimal runtime container image footprint without build tools.
- [x] **Resource Constraints**: CPU and memory limits set in `docker-compose.prod.yml`.
