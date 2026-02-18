# FactoryOps AI Engineering

FactoryOps is an industrial IoT platform for monitoring and analyzing factory equipment in real-time. It provides device management, rule-based alerting, analytics with ML-powered anomaly detection and failure prediction, and automated reporting.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                Frontend (React + TypeScript)            │
│                         http://localhost:3000                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Nginx Reverse Proxy                          │
│                              http://localhost                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌─────────┐    ┌───────────┐    ┌───────────┐
              │   API   │    │ Telemetry │    │   Front   │
              │ (FastAPI)│    │ Subscriber│    │   end     │
              └────┬────┘    └─────┬─────┘    └───────────┘
                   │               │
        ┌──────────┼──────────┬─────┴────┐
        ▼          ▼          ▼          ▼
    ┌──────┐  ┌────────┐ ┌────────┐ ┌──────────┐
    │ MySQL│  │InfluxDB│ │ Redis  │ │  MinIO   │
    │8.0   │  │  2.7   │ │   7    │ │ S3 compat│
    └──────┘  └────────┘ └────────┘ └──────────┘
        │          │          │          │
        │          ▼          ▼          │
        │    ┌──────────┐ ┌─────────┐   │
        │    │ Celery   │ │ Celery  │   │
        │    │ Workers  │ │ Workers │   │
        │    └──────────┘ └─────────┘   │
        │          │          │          │
        └──────────┴──────────┴──────────┘
                   MQTT (EMQX)
```

## Quick Start

```bash
# Clone and setup
git clone <repository>
cp .env.example .env

# Start all services
docker compose -f docker/docker-compose.yml up --build -d

# Seed database with initial data
docker compose -f docker/docker-compose.yml exec api python scripts/seed.py

# Access the application
open http://localhost
```

## Publish Test Telemetry

Publish MQTT telemetry messages using mosquitto_pub:

```bash
mosquitto_pub -h localhost -p 1883 \
  -t "factories/vpc/devices/M01/telemetry" \
  -m '{"metrics":{"voltage":231.4,"current":3.2,"power":745.6,"frequency":50.01}}'
```

## Default Credentials

| Role      | Email           | Password   |
|-----------|-----------------|------------|
| Super Admin | admin@vpc.com  | Admin@123  |

## API Documentation

Interactive API documentation is available at:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Running Tests

```bash
# Run all tests
docker compose -f docker/docker-compose.yml exec api pytest tests/ -v

# Run unit tests
docker compose -f docker/docker-compose.yml exec api pytest tests/unit/ -v

# Run integration tests
docker compose -f docker/docker-compose.yml exec api pytest tests/integration/ -v

# Run E2E tests
docker compose -f docker/docker-compose.yml exec api pytest tests/e2e/ -v
```

## Monitoring

- Health Check: http://localhost:8000/health
- Prometheus Metrics: http://localhost:8000/metrics

## Key Features

- **Device Management**: Register and monitor IoT devices
- **Real-time Telemetry**: MQTT-based ingestion with InfluxDB storage
- **Rule-based Alerting**: Define conditions and get notified via Email/WhatsApp
- **Analytics**: ML-powered anomaly detection, failure prediction, energy forecasting
- **AI Copilot**: Natural language insights about your equipment
- **Reports**: Generate PDF/Excel reports with aggregated data and analytics
- **User Management**: Invite admins with granular permissions
