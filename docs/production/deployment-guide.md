# ModelOps Studio — Production Deployment Guide

**Target Audience**: DevOps Engineers, Platform Architects, Site Reliability Engineers  
**Target Environment**: Linux Virtual Machine (Ubuntu 22.04 LTS / 24.04 LTS) with Docker Engine & Docker Compose

---

## 1. System Requirements & Prerequisites

### Hardware Recommendations
* **CPU**: Minimum 4 vCPUs (8 vCPUs recommended for concurrent ML training).
* **RAM**: Minimum 8 GB (16 GB recommended).
* **Disk**: 50 GB+ SSD storage (NVMe preferred for high IOPS model loading).

### Software Requirements
* Docker Engine 24.0+
* Docker Compose v2.20+
* Domain name with DNS `A` records pointing to server public IP (e.g. `modelops.yourdomain.com`).

---

## 2. Server Initial Setup & Hardening

```bash
# 1. Update system packages
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl git ufw fail2ban

# 2. Configure Firewall (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 3. Deployment Steps

### Step 1: Clone Repository
```bash
git clone https://github.com/VigneshEilik/DSpipeline.git /opt/modelops
cd /opt/modelops
```

### Step 2: Configure Production Environment
```bash
cp .env.production.example .env.production

# Generate secure cryptographic keys
openssl rand -hex 32  # Use for SECRET_KEY
openssl rand -hex 16  # Use for POSTGRES_PASSWORD
openssl rand -hex 16  # Use for MINIO_ROOT_PASSWORD
openssl rand -hex 16  # Use for REDIS_PASSWORD
```

Edit `.env.production` using your preferred editor:
```bash
nano .env.production
```

### Step 3: Run Database Migrations
```bash
docker compose -f docker-compose.prod.yml --env-file .env.production run --rm api alembic -c apps/api/alembic.ini upgrade head
```

### Step 4: Start Production Services
```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### Step 5: Verify Deployment Health
```bash
curl -f http://localhost:8000/healthz
curl -f http://localhost:8000/readyz
```

---

## 4. Reverse Proxy & HTTPS Configuration (Caddy / Nginx)

### Example Caddyfile (`/etc/caddy/Caddyfile`)
```caddy
modelops.yourdomain.com {
    # Web Frontend
    handle {
        reverse_proxy localhost:3000
    }

    # API Endpoints
    handle /api/* {
        reverse_proxy localhost:8000
    }

    # Health Checks
    handle /healthz {
        reverse_proxy localhost:8000
    }
}
```

---

## 5. Zero-Downtime Application Updates

```bash
# Pull new release
git pull origin main

# Run migrations
docker compose -f docker-compose.prod.yml --env-file .env.production run --rm api alembic -c apps/api/alembic.ini upgrade head

# Rolling container restart
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build --no-deps api worker web
```
