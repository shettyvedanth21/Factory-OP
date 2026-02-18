# FactoryOps Deployment Guide

This guide covers deploying FactoryOps to production environments.

## Prerequisites

Before deploying, ensure you have:

1. **Docker & Docker Compose** - Version 24.0 or later
2. **Domain Name** - Pointed to your server's IP
3. **SSL Certificate** - From Let's Encrypt or purchased

### Required Tools

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
apt-get install docker-compose-plugin

# Install mc (MinIO client)
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc && mv mc /usr/local/bin/
```

## Environment Configuration

### 1. Create Secrets

Create the `docker/secrets` directory and generate secure secrets:

```bash
mkdir -p docker/secrets docker/ssl

# Generate random secrets
openssl rand -base64 32 > docker/secrets/mysql_root_password.txt
openssl rand -base64 16 > docker/secrets/mysql_user.txt
openssl rand -base64 16 > docker/secrets/mysql_password.txt
openssl rand -base64 32 > docker/secrets/jwt_secret.txt
openssl rand -base64 32 > docker/secrets/influxdb_token.txt
openssl rand -base64 16 > docker/secrets/influxdb_password.txt
openssl rand -base64 32 > docker/secrets/minio_access_key.txt
openssl rand -base64 32 > docker/secrets/minio_secret_key.txt
openssl rand -base64 16 > docker/secrets/emqx_password.txt

# Secure the secrets
chmod 600 docker/secrets/*.txt
```

### 2. SSL Certificates

Place your SSL certificate and key in `docker/ssl/`:

```bash
# For Let's Encrypt (after obtaining)
cp fullchain.pem docker/ssl/cert.pem
cp privkey.pem docker/ssl/key.pem

# Or generate self-signed (NOT for production)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/ssl/key.pem -out docker/ssl/cert.pem
```

### 3. Environment Variables

Create `.env` file in the project root:

```bash
# GitHub Container Registry
GITHUB_REPOSITORY=your-org/factoryops
```

## First Deployment

### 1. Pull Images

```bash
cd docker
docker compose -f docker-compose.prod.yml pull
```

### 2. Run Database Migrations

```bash
# Start only the database and wait for it to be ready
docker compose -f docker-compose.prod.yml up -d mysql

# Wait for MySQL to be healthy
docker compose -f docker-compose.prod.yml ps

# Run migrations
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### 3. Seed Initial Data

```bash
docker compose -f docker-compose.prod.yml exec api python scripts/seed.py
```

### 4. Start All Services

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 5. Verify Deployment

```bash
# Check service health
curl https://localhost/health

# Check logs
docker compose -f docker-compose.prod.yml logs -f api
```

## Update & Rollout Procedure

### Rolling Restart (Zero Downtime)

```bash
# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Rolling restart each service
docker compose -f docker-compose.prod.yml up -d --no-deps --build api
docker compose -f docker-compose.prod.yml up -d --no-deps --build telemetry
docker compose -f docker-compose.prod.yml up -d --no-deps frontend
```

### Database Migrations

```bash
# Run migrations before restarting API
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# If you need to create a new migration
docker compose -f docker-compose.prod.yml exec api alembic revision --autogenerate -m "description"
```

## Backup & Restore

### Automated Backups

The backup script (`scripts/backup.sh`) runs daily via cron:

```bash
# Add to crontab (runs at 2 AM daily)
0 2 * * * /path/to/factoryops/scripts/backup.sh >> /var/log/factoryops-backup.log 2>&1
```

### Manual Backup

```bash
# Run backup immediately
docker compose -f docker-compose.prod.yml exec -T mysql mysqldump -u factoryops -p factoryops | gzip > backup.sql.gz
```

### Restore from Backup

```bash
# Stop services
docker compose -f docker-compose.prod.yml down

# Restore database
gunzip < backup.sql.gz | docker compose -f docker-compose.prod.yml exec -T mysql mysql -u factoryops -p factoryops

# Start services
docker compose -f docker-compose.prod.yml up -d
```

## Monitoring

### Prometheus + Grafana Setup

Create a `monitoring/docker-compose.yml`:

```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3001:3000"
```

Add to Prometheus targets in `prometheus.yml`:

```yaml
static_configs:
  - targets: ['api:8000']
```

### Key Metrics to Monitor

- `factoryops_api_request_duration_seconds` - API latency
- `factoryops_telemetry_messages_total` - Message throughput
- `factoryops_alerts_triggered_total` - Alert rate
- `factoryops_active_devices_total` - Device count
- Docker container CPU/memory usage

## Scaling Guide

### Adding More Celery Workers

```bash
# Scale analytics workers
docker compose -f docker-compose.prod.yml up -d --scale analytics_worker=3

# Scale rule engine workers
docker compose -f docker-compose.prod.yml up -d --scale rule_engine=2
```

### Horizontal Scaling

For high load, consider:
1. Running multiple API instances behind load balancer
2. Adding more Celery workers for compute-intensive tasks
3. Using read replicas for MySQL
4. Partitioning InfluxDB by factory

## Troubleshooting

### Check Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs

# Specific service
docker compose -f docker-compose.prod.yml logs -f api

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 api
```

### Common Issues

1. **Database connection failures** - Check secrets and network connectivity
2. **Slow queries** - Review MySQL slow query log
3. **Out of memory** - Increase container memory limits in docker-compose.prod.yml
4. **SSL certificate errors** - Ensure certs are valid and not expired

### Health Checks

```bash
# API
curl https://localhost/api/v1/devices

# MySQL
docker compose -f docker-compose.prod.yml exec mysql mysqladmin ping

# Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli ping

# InfluxDB
curl -I http://localhost:8086/ping
```
