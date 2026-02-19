# FactoryOps Knowledge Transfer Document

**Version:** 1.0.0  
**Last Updated:** 2026-02-19  
**Target Audience:** New developers onboarding to FactoryOps

---

## 1. Project Overview

### 1.1 What Problem Does This Solve?

FactoryOps is an **Industrial IoT (IIoT) Monitoring Platform** designed for manufacturing environments. It solves the following critical problems:

1. **Real-time Equipment Monitoring**: Factories have hundreds of machines (CNC mills, injection molders, conveyors, pumps) that generate telemetry data (voltage, current, temperature, pressure, vibration). FactoryOps collects and visualizes this data in real-time.

2. **Predictive Maintenance**: Instead of waiting for machines to break, FactoryOps uses ML algorithms (anomaly detection, failure prediction) to alert operators before failures occur, reducing downtime by up to 40%.

3. **Alert Management**: Complex rule engine allows defining sophisticated conditions (e.g., "Alert if temperature > 80°C AND vibration > 5mm/s for more than 5 minutes during day shift") to catch problems early.

4. **Energy Optimization**: Tracks power consumption patterns and provides forecasting to optimize energy usage and reduce costs.

5. **Compliance & Reporting**: Generates automated PDF/Excel reports for audits, showing equipment health, alert history, and analytics insights.

### 1.2 Who Uses It and How?

**Primary Users:**

| Role | Typical User | How They Use FactoryOps |
|------|--------------|------------------------|
| **Factory Managers** | Plant supervisors, operations directors | View dashboard, check overall health scores, download compliance reports |
| **Maintenance Engineers** | technicians, reliability engineers | Monitor device KPIs, create alert rules, respond to alerts, run predictive analytics |
| **IT/OT Administrators** | system integrators, IT managers | Manage users, configure factories, set up device onboarding |

**Daily Workflow:**

1. **Morning**: Manager checks dashboard for overnight alerts and device health scores
2. **Throughout day**: Engineers monitor live KPIs, respond to alerts
3. **Weekly**: Generate PDF reports for management review
4. **Monthly**: Run analytics jobs to identify trends and optimize maintenance schedules

### 1.3 Key Business Concepts

#### Factory (Tenant)
A **Factory** is the top-level organizational unit representing a physical manufacturing facility. FactoryOps is multi-tenant - each factory's data is completely isolated.

```
Factory: "Vietnam Precision Components (VPC)"
├── Users (admins, engineers)
├── Devices (100+ machines)
├── Rules (alert conditions)
├── Alerts (triggered incidents)
└── Analytics Jobs (ML analysis)
```

**Key Points:**
- Each factory has a unique `slug` (e.g., "vpc", "singapore-plant-2")
- All data is filtered by `factory_id` - users CANNOT see other factories' data
- First user in a factory is the `super_admin` who can invite other admins

#### Device (Machine/Equipment)
A **Device** represents a single piece of equipment sending telemetry data.

```python
Device Example:
- device_key: "M01"                    # Unique identifier (often machine serial number)
- name: "CNC Mill - Station A"        # Human-readable name
- manufacturer: "Haas"                # Equipment maker
- model: "VF-2"                       # Model number
- region: "Line 3, Building B"        # Physical location
- is_active: true                     # Online/offline status
- last_seen: "2026-02-19T10:30:00Z"   # Last telemetry timestamp
```

**Device Identification:**
- MQTT Topic: `factories/vpc/devices/M01/telemetry`
- Device sends data every 5-60 seconds via MQTT
- FactoryOps auto-discovers new parameters as they appear in telemetry

#### Parameter (Telemetry Metric)
A **Parameter** is a single metric being measured by a device.

```python
Parameters Example for a CNC Mill:
- voltage: 231.4 V      (electrical)
- current: 3.2 A        (electrical)
- power: 745.6 W        (calculated: V × I)
- spindle_rpm: 3500     (mechanical)
- feed_rate: 1200       (mechanical)
- coolant_temp: 45.2    (thermal)
- vibration_x: 2.1      (predictive maintenance)
```

**Parameter Discovery:**
- When device first sends telemetry, FactoryOps automatically creates `DeviceParameter` records
- Engineers can mark parameters as "KPIs" to display on dashboards
- Parameters have display names and units (e.g., "Spindle Speed" with unit "RPM")

#### KPI (Key Performance Indicator)
A **KPI** is a parameter selected for monitoring on dashboards.

```
Live KPIs Card Example:
┌─────────────────┐
│ Voltage         │
│ 231.4 V         │
│ ● Live          │
└─────────────────┘
```

**Types of KPIs:**
- **Live KPIs**: Current value from InfluxDB (updates every few seconds)
- **Historical KPIs**: Time-series data for charts (1m, 5m, 1h, 1d aggregation)
- **Health Score**: Calculated metric (0-100) based on alert history and telemetry patterns

#### Alert (Incident)
An **Alert** is created when a Rule's conditions are met.

```python
Alert Example:
- triggered_at: "2026-02-19T10:30:00Z"
- severity: "critical"
- message: "CNC Mill M01: Spindle temperature exceeded 80°C"
- rule: "Spindle Overheat Warning"
- device: "M01"
- telemetry_snapshot: {temperature: 82.3, ...}
```

**Alert Lifecycle:**
1. Rule conditions met → Alert created (status: `triggered`)
2. Notifications sent (email, WhatsApp)
3. Engineer investigates and fixes issue
4. Engineer marks alert as `resolved`

#### Rule (Alert Condition)
A **Rule** defines when to create alerts using a condition tree.

```python
Rule Example - Spindle Overheat:
{
  "name": "Spindle Overheat Warning",
  "severity": "critical",
  "conditions": {
    "operator": "AND",
    "conditions": [
      {"parameter": "spindle_temp", "operator": "gt", "threshold": 80},
      {"parameter": "coolant_flow", "operator": "lt", "threshold": 5}
    ]
  },
  "cooldown_minutes": 15,  # Don't alert again for 15 min
  "schedule": {"type": "time_window", "start": "06:00", "end": "22:00"}
}
```

**Rule Components:**
- **Condition Tree**: AND/OR logic with nested conditions
- **Severity**: low/medium/high/critical (affects notification urgency)
- **Cooldown**: Prevents alert spam (e.g., wait 15 min before alerting again)
- **Schedule**: Only evaluate during certain times (e.g., only during day shift)
- **Scope**: Device-specific or global (applies to all devices)

---

## 2. System Architecture

### 2.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FACTORYOPS v1.0.0                              │
│                    Industrial IoT Monitoring Platform                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Web Browser                                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │  │
│  │  │  React App  │  │  Live KPIs  │  │   Charts    │  │  Alert Feed  │ │  │
│  │  │ (Port 3000) │  │  (WebSocket)│  │  (Recharts) │  │   (Polling)  │ │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘ │  │
│  │         │                │                │                │         │  │
│  │         └────────────────┴────────────────┴────────────────┘         │  │
│  │                              HTTPS (443)                              │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
└─────────────────────────────────────┼───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REVERSE PROXY (Nginx)                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Port 80/443 → HTTP/2, TLS, Rate Limiting, Static Assets               │  │
│  │                                                                       │  │
│  │  /api/*     → api:8000       (REST API)                               │  │
│  │  /          → frontend:3000  (React App)                              │  │
│  │  /metrics   → api:8000       (Prometheus)                             │  │
│  │  /health    → api:8000       (Health Check)                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐          ┌──────────────────┐          ┌──────────────────┐
│   FRONTEND    │          │   API SERVICE    │          │ TELEMETRY SERVICE│
│  (React/Vite) │          │    (FastAPI)     │          │   (MQTT Client)  │
├───────────────┤          ├──────────────────┤          ├──────────────────┤
│ Port: 3000    │          │ Port: 8000       │          │ Port: N/A        │
│ Framework:    │          │ Framework:       │          │ Protocol: MQTT   │
│   React 18    │          │   FastAPI        │          │ Subscribes to:   │
│ Build: Vite   │          │ Python: 3.11     │          │   factories/#/   │
│ Styling:      │          │ Async: Yes       │          │   devices/#/     │
│   Tailwind    │          │ Docs: /api/docs  │          │   telemetry      │
│ State:        │          │ Auth: JWT        │          │                  │
│   Zustand     │          │ Logging:         │          │ Processes:       │
│ Data:         │          │   structlog      │          │   - Validation   │
│   React Query │          │                  │          │   - InfluxDB     │
│               │          │ Endpoints:       │          │     write        │
│               │          │   30+ REST API   │          │   - Parameter    │
│               │          │                  │          │     discovery    │
│               │          │ Talks to:        │          │   - Rule eval    │
│               │          │   MySQL, Redis,  │          │     dispatch     │
│               │          │   InfluxDB,      │          │                  │
│               │          │   MinIO          │          │ Talks to:        │
│               │          │                  │          │   EMQX,          │
│               │          │ Celery Producer: │          │   InfluxDB,      │
│               │          │   Dispatches     │          │   MySQL, Redis   │
│               │          │   background     │          │                  │
│               │          │   tasks          │          │                  │
└───────────────┘          └──────────────────┘          └──────────────────┘
                                      │                             │
        ┌─────────────────────────────┼─────────────────────────────┤
        │                             │                             │
        ▼                             ▼                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MESSAGE QUEUE (Redis + Celery)                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Redis (Port 6379)                                                    │  │
│  │  ├── DB 0: Cache, Session Store                                       │  │
│  │  ├── DB 1: Celery Broker (task queue)                                 │  │
│  │  └── DB 2: Celery Result Backend                                      │  │
│  │                                                                       │  │
│  │  Celery Worker Queues:                                                │  │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐          │  │
│  │  │ rule_engine     │ │ analytics       │ │ reporting       │          │  │
│  │  │ (concurrency=4) │ │ (concurrency=2) │ │ (concurrency=2) │          │  │
│  │  │                 │ │                 │ │                 │          │  │
│  │  │ Evaluates rules │ │ Runs ML jobs:   │ │ Generates       │          │  │
│  │  │ Creates alerts  │ │ - Anomaly       │ │ PDF/Excel       │          │  │
│  │  │ Sends notifs    │ │ - Forecast      │ │ reports         │          │  │
│  │  │                 │ │ - Prediction    │ │                 │          │  │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘          │  │
│  │                                                                       │  │
│  │  ┌─────────────────┐                                                  │  │
│  │  │ notifications   │                                                  │  │
│  │  │ (concurrency=4) │                                                  │  │
│  │  │                 │                                                  │  │
│  │  │ Sends email &   │                                                  │  │
│  │  │ WhatsApp alerts │                                                  │  │
│  │  └─────────────────┘                                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐          ┌──────────────────┐          ┌──────────────────┐
│     MySQL     │          │    InfluxDB      │          │      MinIO       │
│    (8.0.33)   │          │     (2.7)        │          │  (S3-Compatible) │
├───────────────┤          ├──────────────────┤          ├──────────────────┤
│ Port: 3306    │          │ Port: 8086       │          │ Port: 9000       │
│               │          │                  │          │ Port: 9001 (UI)  │
│ Stores:       │          │ Stores:          │          │                  │
│ - Factories   │          │ Time-series      │          │ Stores:          │
│ - Users       │          │ telemetry data   │          │ - PDF reports    │
│ - Devices     │          │                  │          │ - Excel reports  │
│ - Rules       │          │ Schema:          │          │ - Analytics      │
│ - Alerts      │          │ measurement:     │          │   results        │
│ - Analytics   │          │   telemetry      │          │                  │
│   jobs        │          │ tags:            │          │ Bucket:          │
│ - Reports     │          │   factory_id,    │          │   factoryops     │
│               │          │   device_id      │          │                  │
│ Engine:       │          │ fields:          │          │ Retention:       │
│   InnoDB      │          │   all metrics    │          │   30 days        │
│               │          │ retention:       │          │                  │
│ Relationships:│          │   configurable   │          │                  │
│   Foreign Key │          │                  │          │                  │
│   constraints │          │                  │          │                  │
└───────────────┘          └──────────────────┘          └──────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MQTT BROKER (EMQX 5.x)                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Port 1883: MQTT Protocol                                             │  │
│  │  Port 8083: MQTT over WebSocket                                       │  │
│  │  Port 18083: Dashboard UI                                             │  │
│  │                                                                       │  │
│  │  Topic Structure:                                                     │  │
│  │  factories/{factory_slug}/devices/{device_key}/telemetry              │  │
│  │                                                                       │  │
│  │  Example: factories/vpc/devices/M01/telemetry                         │  │
│  │                                                                       │  │
│  │  Message Format (JSON):                                               │  │
│  │  {                                                                    │  │
│  │    "timestamp": "2026-02-19T10:30:00Z",                               │  │
│  │    "metrics": {                                                       │  │
│  │      "voltage": 231.4,                                                │  │
│  │      "current": 3.2,                                                  │  │
│  │      "power": 745.6                                                   │  │
│  │    }                                                                  │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ▲
                                      │
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DEVICE LAYER                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  CNC Mill│  │  Conveyor│  │   Pump   │  │  Sensor  │  │   PLC/IoT    │  │
│  │   M01    │  │   C02    │  │   P03    │  │  Array   │  │   Gateway    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │             │             │             │                │          │
│       └─────────────┴─────────────┴─────────────┴────────────────┘          │
│                                    │                                        │
│                          MQTT Publish (Port 1883)                           │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     ▼
```

### 2.2 Every Service Explained

#### 1. Frontend (React Application)
**Port:** 3000 (dev), served via Nginx (prod)  
**Technology Stack:** React 18, TypeScript, Vite, Tailwind CSS, React Query, Zustand

**What It Does:**
- Single Page Application (SPA) providing the user interface
- Real-time dashboards with live KPI cards
- Interactive charts using Recharts
- Rule builder with visual condition editor
- Device management interface
- Alert monitoring and resolution workflow

**Key Components:**
- **FactorySelect**: Landing page to choose factory
- **Login**: JWT authentication
- **Dashboard**: Overview with summary cards
- **Machines**: Device list and detail views
- **Rules**: Alert rule management
- **RuleBuilder**: Visual condition editor
- **Analytics**: ML job submission and results
- **Reports**: Report generation interface
- **Users**: User management (super_admin only)

**State Management:**
- **Zustand**: Authentication state (token, user, factory)
- **React Query**: Server state (devices, alerts, rules) with caching
- **Local state**: UI components (modals, forms)

**Talks To:**
- API service via REST calls (Axios)

---

#### 2. API Service (FastAPI)
**Port:** 8000  
**Technology Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic

**What It Does:**
- REST API serving all frontend requests
- JWT authentication and authorization
- Business logic coordination
- Database queries via repositories
- Dispatches background tasks to Celery

**Key Features:**
- Auto-generated OpenAPI docs at `/api/docs`
- Request validation with Pydantic
- Structured JSON logging with structlog
- Factory isolation enforcement
- Health check endpoint at `/health`

**Routers (30+ Endpoints):**
- `/api/v1/auth` - Login, refresh
- `/api/v1/devices` - CRUD operations
- `/api/v1/devices/{id}/parameters` - Parameter management
- `/api/v1/devices/{id}/kpis` - Live and historical KPIs
- `/api/v1/rules` - Alert rule CRUD
- `/api/v1/alerts` - Alert listing and resolution
- `/api/v1/analytics` - ML job management
- `/api/v1/reports` - Report generation
- `/api/v1/users` - User management
- `/api/v1/dashboard` - Summary statistics
- `/metrics` - Prometheus metrics

**Talks To:**
- MySQL (metadata)
- Redis (caching, Celery broker)
- InfluxDB (time-series queries)
- MinIO (file storage)

---

#### 3. Telemetry Service (MQTT Subscriber)
**Port:** N/A (background service)  
**Technology Stack:** Python 3.11, aiomqtt, asyncio

**What It Does:**
- Subscribes to MQTT topics for all factories
- Receives telemetry messages from devices
- Validates message format
- Writes to InfluxDB (time-series storage)
- Discovers new parameters automatically
- Dispatches rule evaluation tasks

**Processing Flow:**
```
1. Subscribe to: factories/+/devices/+/telemetry
2. Parse topic to extract factory_slug, device_key
3. Validate JSON payload
4. Write to InfluxDB (batch writes for efficiency)
5. Update device_parameters (INSERT ... ON DUPLICATE KEY UPDATE)
6. Update device.last_seen timestamp
7. Dispatch evaluate_rules_task to Celery
```

**Talks To:**
- EMQX (MQTT broker)
- InfluxDB (data storage)
- MySQL (device lookup, parameter discovery)
- Redis (Celery task dispatch)

---

#### 4. Rule Engine Worker (Celery)
**Queue:** `rule_engine`  
**Concurrency:** 4 workers  
**Technology Stack:** Python, Celery, SQLAlchemy

**What It Does:**
- Evaluates alert rules against incoming telemetry
- Supports complex condition trees (AND/OR)
- Handles scheduling (time windows, date ranges)
- Manages cooldown periods to prevent spam
- Creates alerts when conditions are met
- Dispatches notification tasks

**Rule Evaluation Logic:**
```python
# Example rule evaluation
if rule.is_active and rule.is_scheduled(now):
    if not is_in_cooldown(rule, device):
        if evaluate_conditions(rule.conditions, telemetry):
            alert = create_alert(rule, device, telemetry)
            dispatch_notification_task(alert.id)
            update_cooldown(rule, device)
```

**Talks To:**
- MySQL (rules, alerts, cooldowns)
- Redis (Celery broker)

---

#### 5. Analytics Worker (Celery)
**Queue:** `analytics`  
**Concurrency:** 2 workers  
**Technology Stack:** Python, Celery, scikit-learn, Prophet, pandas

**What It Does:**
- Runs ML analytics jobs asynchronously
- Supports 4 job types:
  - **Anomaly Detection**: Isolation Forest algorithm
  - **Failure Prediction**: Random Forest classifier
  - **Energy Forecasting**: Prophet time-series forecasting
  - **AI Copilot**: Natural language insights

**Processing Flow:**
```
1. Receive job from queue
2. Fetch telemetry data from InfluxDB
3. Run ML algorithm
4. Generate results (charts, insights, predictions)
5. Upload results to MinIO
6. Update job status in MySQL
```

**Talks To:**
- MySQL (job status)
- InfluxDB (telemetry data)
- MinIO (result storage)
- Redis (Celery broker)

---

#### 6. Reporting Worker (Celery)
**Queue:** `reporting`  
**Concurrency:** 2 workers  
**Technology Stack:** Python, Celery, ReportLab (PDF), OpenPyXL (Excel)

**What It Does:**
- Generates PDF and Excel reports
- Aggregates telemetry data
- Includes analytics results (optional)
- Creates professional formatted reports
- Uploads to MinIO for download

**Report Sections:**
- Executive Summary
- Device Overview
- Telemetry Charts
- Alert Summary
- Analytics Insights
- Appendix with Raw Data

**Talks To:**
- MySQL (report metadata)
- InfluxDB (telemetry aggregation)
- MinIO (PDF/Excel storage)
- Redis (Celery broker)

---

#### 7. Notification Worker (Celery)
**Queue:** `notifications`  
**Concurrency:** 4 workers  
**Technology Stack:** Python, Celery, SMTP, Twilio

**What It Does:**
- Sends email notifications via SMTP
- Sends WhatsApp messages via Twilio
- Formats alert messages with context
- Handles notification failures gracefully

**Notification Format:**
```
Subject: [CRITICAL] FactoryOps Alert - Spindle Overheat

Rule: Spindle Overheat Warning
Device: CNC Mill - Station A (M01)
Severity: CRITICAL
Time: 2026-02-19T10:30:00Z

Spindle temperature exceeded 80°C

Current Values:
- spindle_temp: 82.3°C
- coolant_flow: 3.5 L/min
```

**Talks To:**
- MySQL (alerts, users)
- SMTP server (email)
- Twilio API (WhatsApp)
- Redis (Celery broker)

---

#### 8. MySQL Database
**Port:** 3306  
**Version:** 8.0  
**Purpose:** Metadata storage

**What It Stores:**
- **Factories**: Tenant information
- **Users**: Authentication, permissions, roles
- **Devices**: Machine metadata
- **DeviceParameters**: Discovered metrics with display names
- **Rules**: Alert conditions, schedules
- **Alerts**: Triggered incidents
- **AnalyticsJobs**: ML job status and results
- **Reports**: Report generation status
- **RuleCooldowns**: Alert cooldown tracking

**Key Features:**
- Foreign key constraints for data integrity
- Indexes for query performance
- Factory isolation via factory_id columns
- Soft deletes (is_active flag)

---

#### 9. InfluxDB Time-Series Database
**Port:** 8086  
**Version:** 2.7  
**Purpose:** High-performance time-series storage

**What It Stores:**
- All telemetry data from devices
- Tagged by factory_id and device_id for fast queries
- Configurable retention policies

**Schema:**
```sql
Measurement: telemetry
Tags:
  - factory_id (string)
  - device_id (string)
Fields:
  - voltage (float)
  - current (float)
  - power (float)
  - spindle_temp (float)
  - ... (any metric)
Timestamp: nanosecond precision
```

**Query Example:**
```flux
from(bucket: "factoryops")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "telemetry")
  |> filter(fn: (r) => r.factory_id == "1")
  |> filter(fn: (r) => r.device_id == "M01")
  |> filter(fn: (r) => r._field == "voltage")
  |> aggregateWindow(every: 5m, fn: mean)
```

---

#### 10. Redis
**Port:** 6379  
**Version:** 7  
**Purpose:** Caching, session store, message broker

**Database Usage:**
- **DB 0**: General caching, session storage
- **DB 1**: Celery broker (task queue)
- **DB 2**: Celery result backend

**Key Features:**
- In-memory storage for fast access
- Pub/sub for real-time notifications
- TTL support for automatic expiration

---

#### 11. MinIO Object Storage
**Port:** 9000 (API), 9001 (Web UI)  
**Purpose:** S3-compatible file storage

**What It Stores:**
- Generated PDF reports
- Generated Excel reports
- Analytics results (JSON, charts)
- Database backups

**Bucket Structure:**
```
factoryops/
├── reports/
│   ├── pdf/
│   └── excel/
├── analytics/
│   └── {job_id}/
└── backups/
    └── mysql/
```

**Features:**
- Presigned URLs for secure downloads
- 30-day retention policy
- Encrypted at rest

---

#### 12. EMQX MQTT Broker
**Port:** 1883 (MQTT), 8083 (WebSocket), 18083 (Dashboard)  
**Version:** 5.x  
**Purpose:** IoT device communication

**What It Does:**
- Accepts MQTT connections from devices
- Routes messages based on topic patterns
- Supports QoS 0, 1, 2
- WebSocket support for browser clients
- Built-in dashboard for monitoring

**Topic Pattern:**
```
factories/{factory_slug}/devices/{device_key}/telemetry

Examples:
- factories/vpc/devices/M01/telemetry
- factories/vpc/devices/C02/telemetry
- factories/singapore/devices/P03/telemetry
```

---

#### 13. Nginx Reverse Proxy
**Port:** 80 (HTTP), 443 (HTTPS)  
**Purpose:** Traffic routing and SSL termination

**What It Does:**
- Routes requests to appropriate services
- SSL/TLS termination
- Rate limiting (100 req/min per IP)
- Static asset serving
- Gzip compression
- Security headers

**Routing Rules:**
```
/api/*    → api:8000
/         → frontend:3000
/metrics  → api:8000
/health   → api:8000
```

---

### 2.3 Technology Stack with Reasoning

| Layer | Technology | Reasoning |
|-------|-----------|-----------|
| **Frontend** | React 18 | Industry standard, large ecosystem, component-based |
| | TypeScript | Type safety, better IDE support, fewer runtime errors |
| | Vite | Fast development, modern build tool, hot module replacement |
| | Tailwind CSS | Utility-first, rapid UI development, consistent design |
| | React Query | Powerful data fetching, caching, background updates |
| | Zustand | Lightweight state management, simpler than Redux |
| | Recharts | React-native charting, customizable, good performance |
| **Backend** | Python 3.11 | Great async support, ML ecosystem, readable code |
| | FastAPI | High performance, automatic OpenAPI docs, type hints |
| | SQLAlchemy 2.0 | Mature ORM, async support, type-safe queries |
| | Pydantic | Data validation, serialization, settings management |
| | Celery | Distributed task queue, reliable background processing |
| | structlog | Structured JSON logging for observability |
| **Databases** | MySQL 8.0 | ACID compliance, familiar SQL, good for metadata |
| | InfluxDB 2.7 | Optimized for time-series, high write throughput |
| | Redis 7 | In-memory speed, pub/sub, proven with Celery |
| **Storage** | MinIO | S3-compatible, self-hosted, cost-effective |
| **Messaging** | EMQX 5 | Production-grade MQTT, high performance |
| **ML/Analytics** | scikit-learn | Industry standard for ML, well-documented |
| | Prophet | Facebook's forecasting library, handles seasonality |
| | pandas | Data manipulation, integration with ML libraries |
| **Reporting** | ReportLab | Professional PDF generation, Python-native |
| | OpenPyXL | Excel file creation, formatting, charts |
| **Infrastructure** | Docker | Containerization, consistent environments |
| | Nginx | Proven reverse proxy, SSL termination, load balancing |
| | GitHub Actions | CI/CD integration, free for public repos |

---

## 3. Data Architecture

### 3.1 MySQL Database Schema

#### Table: factories
Stores tenant/factory information.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | INT | PK, AUTO_INCREMENT | Unique factory identifier |
| name | VARCHAR(255) | NOT NULL | Display name (e.g., "Vietnam Precision Components") |
| slug | VARCHAR(100) | NOT NULL, UNIQUE | URL-safe identifier (e.g., "vpc") |
| timezone | VARCHAR(100) | DEFAULT 'UTC' | Factory timezone for scheduling |
| created_at | DATETIME | DEFAULT NOW() | Record creation timestamp |
| updated_at | DATETIME | ON UPDATE | Last modification timestamp |

**Relationships:**
- One-to-Many: users, devices, rules, alerts, analytics_jobs, reports

---

#### Table: users
Authentication and authorization for factory personnel.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | INT | PK, AUTO_INCREMENT | Unique user identifier |
| factory_id | INT | FK → factories.id, NOT NULL | Tenant isolation |
| email | VARCHAR(255) | NOT NULL | Login identifier |
| whatsapp_number | VARCHAR(50) | NULL | For WhatsApp notifications |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| role | ENUM | NOT NULL | 'super_admin' or 'admin' |
| permissions | JSON | NULL | Granular permissions object |
| is_active | BOOLEAN | DEFAULT TRUE | Soft delete flag |
| invite_token | VARCHAR(255) | NULL | Token for invitation flow |
| invited_at | DATETIME | NULL | When invitation was sent |
| last_login | DATETIME | NULL | Last successful login |
| created_at | DATETIME | DEFAULT NOW() | Account creation |

**Indexes:**
- UNIQUE: (factory_id, email)

**Relationships:**
- Many-to-One: factory
- One-to-Many: rules, analytics_jobs, reports

**Permissions JSON Example:**
```json
{
  "create_rules": true,
  "run_analytics": true,
  "generate_reports": true,
  "manage_users": false
}
```

---

#### Table: devices
IoT equipment/machines being monitored.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | INT | PK, AUTO_INCREMENT | Unique device identifier |
| factory_id | INT | FK → factories.id, NOT NULL | Tenant isolation |
| device_key | VARCHAR(100) | NOT NULL | External identifier (e.g., "M01") |
| name | VARCHAR(255) | NULL | Human-readable name |
| manufacturer | VARCHAR(255) | NULL | Equipment manufacturer |
| model | VARCHAR(255) | NULL | Model number |
| region | VARCHAR(255) | NULL | Physical location |
| api_key | VARCHAR(255) | NULL | Device authentication key |
| is_active | BOOLEAN | DEFAULT TRUE | Online/offline status |
| last_seen | DATETIME | NULL | Last telemetry timestamp |
| created_at | DATETIME | DEFAULT NOW() | Registration date |
| updated_at | DATETIME | ON UPDATE | Last modification |

**Indexes:**
- UNIQUE: (factory_id, device_key)
- INDEX: (factory_id)

**Relationships:**
- Many-to-One: factory
- One-to-Many: parameters, alerts
- Many-to-Many: rules

---

#### Table: device_parameters
Discovered metrics from device telemetry.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | INT | PK, AUTO_INCREMENT | Unique parameter identifier |
| factory_id | INT | FK → factories.id, NOT NULL | Tenant isolation |
| device_id | INT | FK → devices.id, NOT NULL | Parent device |
| parameter_key | VARCHAR(100) | NOT NULL | Internal key (e.g., "voltage") |
| display_name | VARCHAR(255) | NULL | Human-readable name |
| unit | VARCHAR(50) | NULL | Unit of measurement |
| data_type | ENUM | DEFAULT 'float' | 'float', 'int', 'string' |
| is_kpi_selected | BOOLEAN | DEFAULT TRUE | Show on dashboard |
| discovered_at | DATETIME | DEFAULT NOW() | First seen timestamp |
| updated_at | DATETIME | ON UPDATE | Last modification |

**Indexes:**
- UNIQUE: (device_id, parameter_key)
- INDEX: (factory_id, device_id)
- INDEX: (device_id, parameter_key)

**Relationships:**
- Many-to-One: factory, device

---

#### Table: rules
Alert condition definitions with sophisticated logic.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | INT | PK, AUTO_INCREMENT | Unique rule identifier |
| factory_id | INT | FK → factories.id, NOT NULL | Tenant isolation |
| name | VARCHAR(255) | NOT NULL | Rule name |
| description | TEXT | NULL | Detailed description |
| scope | ENUM | DEFAULT 'device' | 'device' or 'global' |
| conditions | JSON | NOT NULL | Condition tree (AND/OR) |
| cooldown_minutes | INT | DEFAULT 15 | Min time between alerts |
| is_active | BOOLEAN | DEFAULT TRUE | Enable/disable |
| schedule_type | ENUM | DEFAULT 'always' | 'always', 'time_window', 'date_range' |
| schedule_config | JSON | NULL | Schedule parameters |
| severity | ENUM | DEFAULT 'medium' | 'low', 'medium', 'high', 'critical' |
| notification_channels | JSON | NULL | Email/WhatsApp config |
| created_by | INT | FK → users.id | Rule creator |
| created_at | DATETIME | DEFAULT NOW() | Creation timestamp |
| updated_at | DATETIME | ON UPDATE | Last modification |

**Indexes:**
- INDEX: (factory_id, is_active)

**Relationships:**
- Many-to-One: factory, creator
- One-to-Many: alerts, cooldowns
- Many-to-Many: devices

**Conditions JSON Example:**
```json
{
  "operator": "AND",
  "conditions": [
    {
      "parameter": "spindle_temp",
      "operator": "gt",
      "threshold": 80
    },
    {
      "operator": "OR",
      "conditions": [
        {"parameter": "coolant_flow", "operator": "lt", "threshold": 5},
        {"parameter": "vibration", "operator": "gt", "threshold": 10}
      ]
    }
  ]
}
```

**Schedule Config Example:**
```json
// Time window
{"start_time": "06:00", "end_time": "22:00", "days": [1,2,3,4,5]}

// Date range
{"start_date": "2026-01-01", "end_date": "2026-12-31"}
```

---

#### Table: rule_devices (Association)
Many-to-many relationship between rules and devices.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| rule_id | INT | FK → rules.id, PK | Rule identifier |
| device_id | INT | FK → devices.id, PK | Device identifier |

**Behavior:**
- CASCADE DELETE on both sides
- Only used when rule.scope = 'device'

---

#### Table: alerts
Triggered incidents when rule conditions are met.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | INT | PK, AUTO_INCREMENT | Unique alert identifier |
| factory_id | INT | FK → factories.id, NOT NULL | Tenant isolation |
| rule_id | INT | FK → rules.id, NOT NULL | Triggering rule |
| device_id | INT | FK → devices.id, NOT NULL | Affected device |
| triggered_at | DATETIME | NOT NULL | When alert fired |
| resolved_at | DATETIME | NULL | When resolved (null = active) |
| severity | VARCHAR(20) | NOT NULL | 'low', 'medium', 'high', 'critical' |
| message | TEXT | NULL | Human-readable description |
| telemetry_snapshot | JSON | NULL | Metric values at trigger time |
| notification_sent | BOOLEAN | DEFAULT FALSE | Notification status |
| created_at | DATETIME | DEFAULT NOW() | Record creation |

**Indexes:**
- INDEX: (factory_id, device_id, triggered_at)
- INDEX: (factory_id, triggered_at)

**Relationships:**
- Many-to-One: factory, rule, device

**Telemetry Snapshot Example:**
```json
{
  "spindle_temp": 82.3,
  "coolant_flow": 3.5,
  "vibration": 12.1,
  "timestamp": "2026-02-19T10:30:00Z"
}
```

---

#### Table: rule_cooldowns
Prevents alert spam by tracking last trigger time.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| rule_id | INT | FK → rules.id, PK | Rule identifier |
| device_id | INT | FK → devices.id, PK | Device identifier |
| last_triggered | DATETIME | NOT NULL | Last alert timestamp |

**Behavior:**
- CASCADE DELETE when rule or device deleted
- Checked before creating new alert
- If (now - last_triggered) < cooldown_minutes, skip alert

---

#### Table: analytics_jobs
Background ML analysis jobs.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | VARCHAR(36) | PK | UUID job identifier |
| factory_id | INT | FK → factories.id, NOT NULL | Tenant isolation |
| created_by | INT | FK → users.id, NOT NULL | Job creator |
| job_type | VARCHAR(50) | NOT NULL | 'anomaly', 'failure_prediction', 'energy_forecast', 'ai_copilot' |
| mode | VARCHAR(20) | DEFAULT 'standard' | 'standard' or 'ai_copilot' |
| device_ids | JSON | NOT NULL | Array of device IDs to analyze |
| date_range_start | DATETIME | NOT NULL | Analysis start time |
| date_range_end | DATETIME | NOT NULL | Analysis end time |
| status | VARCHAR(20) | DEFAULT 'pending' | 'pending', 'running', 'complete', 'failed' |
| result_url | VARCHAR(500) | NULL | MinIO URL to results |
| error_message | TEXT | NULL | Error details if failed |
| started_at | DATETIME | NULL | When processing began |
| completed_at | DATETIME | NULL | When processing finished |
| created_at | DATETIME | DEFAULT NOW() | Job creation |

**Indexes:**
- INDEX: (factory_id, status)

**Relationships:**
- Many-to-One: factory, creator

---

#### Table: reports
Generated PDF/Excel reports.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | VARCHAR(36) | PK | UUID report identifier |
| factory_id | INT | FK → factories.id, NOT NULL | Tenant isolation |
| created_by | INT | FK → users.id, NOT NULL | Report creator |
| title | VARCHAR(255) | NULL | Custom title |
| device_ids | JSON | NOT NULL | Array of device IDs included |
| date_range_start | DATETIME | NOT NULL | Report period start |
| date_range_end | DATETIME | NOT NULL | Report period end |
| format | VARCHAR(20) | NOT NULL | 'pdf', 'excel', 'json' |
| include_analytics | BOOLEAN | DEFAULT FALSE | Include ML results |
| analytics_job_id | VARCHAR(36) | NULL | Link to analytics job |
| status | VARCHAR(20) | DEFAULT 'pending' | 'pending', 'running', 'complete', 'failed' |
| file_url | VARCHAR(500) | NULL | MinIO presigned URL |
| file_size_bytes | BIGINT | NULL | File size |
| error_message | TEXT | NULL | Error details if failed |
| expires_at | DATETIME | NULL | URL expiration |
| created_at | DATETIME | DEFAULT NOW() | Report creation |

**Relationships:**
- Many-to-One: factory, creator

---

### 3.2 InfluxDB Measurement Schema

**Measurement Name:** `telemetry`

**Tags (Indexed for fast queries):**
| Tag | Type | Example | Purpose |
|-----|------|---------|---------|
| factory_id | string | "1" | Tenant isolation |
| device_id | string | "M01" | Device identifier |

**Fields (Data values):**
| Field | Type | Example | Description |
|-------|------|---------|-------------|
| *Any parameter* | float/int | voltage=231.4 | Dynamic fields based on telemetry |

**Timestamp:** Nanosecond precision Unix timestamp

**Key Characteristics:**
- Schema-less: New fields automatically created as devices send new parameters
- High cardinality: Each unique tag combination creates a series
- Optimized for time-range queries
- Retention policy: Configurable (default 30 days)

**Example Data Points:**
```
telemetry,factory_id=1,device_id=M01 voltage=231.4,current=3.2,power=745.6 1708338600000000000
telemetry,factory_id=1,device_id=M01 voltage=231.2,current=3.3,power=743.0 1708338660000000000
telemetry,factory_id=1,device_id=C02 voltage=118.5,current=2.1,power=248.9 1708338600000000000
```

**Query Patterns:**
```flux
// Get last hour of voltage for device M01
from(bucket: "factoryops")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "telemetry")
  |> filter(fn: (r) => r.factory_id == "1")
  |> filter(fn: (r) => r.device_id == "M01")
  |> filter(fn: (r) => r._field == "voltage")

// Get average power per 5 minutes
from(bucket: "factoryops")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "telemetry")
  |> filter(fn: (r) => r._field == "power")
  |> aggregateWindow(every: 5m, fn: mean)
```

---

### 3.3 Redis Usage

**Database 0 - General Cache:**

| Key Pattern | Value Type | TTL | Purpose |
|-------------|-----------|-----|---------|
| `device:{device_id}:last_seen` | String | 1 hour | Cache last telemetry time |
| `factory:{factory_id}:device_count` | String | 5 min | Cached device count |
| `kpi:{device_id}:{parameter}` | Hash | 30 sec | Cached live KPI values |

**Database 1 - Celery Broker:**

| Key Pattern | Purpose |
|-------------|---------|
| `celery` | Main task queue |
| `celery:rule_engine` | Rule evaluation tasks |
| `celery:analytics` | ML job tasks |
| `celery:reporting` | Report generation tasks |
| `celery:notifications` | Notification tasks |

**Task Message Format:**
```json
{
  "task": "evaluate_rules",
  "id": "uuid-task-id",
  "args": [1, 5, {"voltage": 231.4}, "2026-02-19T10:30:00Z"],
  "kwargs": {},
  "retries": 3
}
```

**Database 2 - Celery Result Backend:**

| Key Pattern | Value Type | Purpose |
|-------------|-----------|---------|
| `celery-task-meta-{task_id}` | JSON | Task result/status |

---

## 4. Complete Data Flows

### 4.1 Flow 1: Telemetry Ingestion Pipeline

**Scenario:** A CNC machine (M01) sends voltage, current, and power readings every 30 seconds.

```
Step-by-Step Flow:

1. DEVICE PUBLISHES TELEMETRY
   └─> Machine M01 connects to EMQX MQTT broker on port 1883
   └─> Publishes to topic: "factories/vpc/devices/M01/telemetry"
   └─> Payload (JSON):
       {
         "timestamp": "2026-02-19T10:30:00Z",
         "metrics": {
           "voltage": 231.4,
           "current": 3.2,
           "power": 745.6
         }
       }

2. MQTT BROKER RECEIVES MESSAGE
   └─> EMQX validates client connection
   └─> Routes message to subscribers
   └─> Persists message (QoS 1)

3. TELEMETRY SERVICE SUBSCRIBES
   └─> Telemetry service (aiomqtt client) receives message
   └─> Topic pattern: "factories/+/devices/+/telemetry"
   └─> Extracts: factory_slug="vpc", device_key="M01"

4. PAYLOAD VALIDATION
   └─> Validates JSON structure
   └─> Checks timestamp format (ISO8601)
   └─> Verifies metrics are numeric
   └─> If invalid: logs error, ACKs message (don't requeue)

5. DEVICE LOOKUP
   └─> Queries MySQL: SELECT id FROM devices WHERE device_key='M01' AND factory_id=1
   └─> Gets device_id=5
   └─> If device not found: logs warning, stores in dead letter queue

6. PARAMETER DISCOVERY
   └─> For each metric in payload:
       └─> INSERT INTO device_parameters 
           (factory_id, device_id, parameter_key, data_type, discovered_at)
           VALUES (1, 5, 'voltage', 'float', NOW())
           ON DUPLICATE KEY UPDATE updated_at=NOW()
   └─> Creates records for: voltage, current, power
   └─> Sets display_name = parameter_key (e.g., "voltage")
   └─> Sets is_kpi_selected = TRUE (default)

7. INFLUXDB WRITE
   └─> Converts metrics to InfluxDB line protocol:
       telemetry,factory_id=1,device_id=M01 voltage=231.4,current=3.2,power=745.6 1708338600000000000
   └─> Batches writes (100 points or 1 second)
   └─> Writes to bucket "factoryops"
   └─> If fail: retries with exponential backoff

8. DEVICE LAST_SEEN UPDATE
   └─> UPDATE devices SET last_seen='2026-02-19T10:30:00Z' WHERE id=5
   └─> Also sets Redis cache: SETEX device:5:last_seen 3600 "2026-02-19T10:30:00Z"

9. RULE EVALUATION DISPATCH
   └─> Publishes Celery task:
       Task: evaluate_rules
       Queue: rule_engine
       Args: (factory_id=1, device_id=5, metrics={...}, timestamp='2026-02-19T10:30:00Z')
   └─> Returns immediately (async processing)

10. MQTT ACK
    └─> Telemetry service ACKs MQTT message
    └─> EMQX removes from queue
    └─> Complete!

Total Latency: ~50-200ms (end-to-end)
```

**Error Handling:**
- Invalid JSON: Logged, message ACKed (don't block)
- Database unavailable: Retry 3x with backoff, then dead letter
- InfluxDB unavailable: Buffer in memory, retry with exponential backoff
- Device not found: Logged, message stored for manual review

---

### 4.2 Flow 2: User Authentication Flow

**Scenario:** Engineer logs into FactoryOps to check device status.

```
Step-by-Step Flow:

1. USER OPENS APP
   └─> Browser loads https://factoryops.example.com
   └─> Nginx serves React app (frontend:3000)
   └─> App checks localStorage for existing JWT
   └─> No token found → shows FactorySelect page

2. FACTORY SELECTION
   └─> Frontend calls: GET /api/v1/factories
   └─> No auth required (public endpoint)
   └─> API queries MySQL: SELECT id, name, slug FROM factories
   └─> Returns: [{"id": 1, "name": "Vietnam Precision Components", "slug": "vpc"}]
   └─> User selects "Vietnam Precision Components"

3. LOGIN CREDENTIALS
   └─> User enters email: "engineer@vpc.com"
   └─> User enters password: "********"
   └─> Frontend calls: POST /api/v1/auth/login
   └─> Request body:
       {
         "factory_id": 1,
         "email": "engineer@vpc.com",
         "password": "********"
       }

4. BACKEND AUTHENTICATION
   └─> API receives request
   └─> Validates request body (Pydantic)
   └─> Step 1: Verify factory exists
       └─> SELECT * FROM factories WHERE id=1
       └─> If not found: 401 Unauthorized
   
   └─> Step 2: Find user
       └─> SELECT * FROM users 
           WHERE factory_id=1 AND email='engineer@vpc.com' AND is_active=TRUE
       └─> If not found: 401 Unauthorized
   
   └─> Step 3: Verify password
       └─> bcrypt.checkpw(password, user.hashed_password)
       └─> If mismatch: 401 Unauthorized
       └─> Logs: "Login failed - invalid password"

5. JWT GENERATION
   └─> Create payload:
       {
         "sub": "42",                    # user_id
         "factory_id": 1,
         "factory_slug": "vpc",
         "role": "admin",
         "exp": 1708425000              # 24 hours from now
       }
   └─> Sign with HS256 algorithm
   └─> Secret key from environment variable
   └─> Token: "eyJhbGciOiJIUzI1NiIs..."

6. UPDATE LAST_LOGIN
   └─> UPDATE users SET last_login=NOW() WHERE id=42

7. LOGIN RESPONSE
   └─> API returns:
       {
         "access_token": "eyJhbGciOiJIUzI1NiIs...",
         "token_type": "bearer",
         "expires_in": 86400,
         "user": {
           "id": 42,
           "email": "engineer@vpc.com",
           "role": "admin",
           "permissions": {
             "create_rules": true,
             "run_analytics": true,
             "generate_reports": true
           }
         }
       }

8. FRONTEND STORES TOKEN
   └─> Zustand authStore updates:
       - token: "eyJhbGciOiJIUzI1NiIs..."
       - user: {...}
       - factory: {id: 1, name: "VPC", slug: "vpc"}
       - isAuthenticated: true
   └─> Persists to localStorage for session recovery
   └─> Redirects to /dashboard

9. SUBSEQUENT API CALLS
   └─> Frontend Axios interceptor adds header:
       Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
   
   └─> Example: GET /api/v1/devices
       Headers:
         Authorization: Bearer <token>
         X-Request-ID: uuid-request-id

10. BACKEND VALIDATES JWT
    └─> Request hits API endpoint
    └─> FastAPI dependency: get_current_user
    └─> Extracts token from Authorization header
    └─> Decodes JWT:
        - Verify signature with secret key
        - Check exp (expiration)
        - Extract claims
    └─> If invalid/expired: 401 Unauthorized
    
    └─> Sets current_user with attributes:
        - id: 42
        - factory_id: 1
        - _token_factory_id: 1 (injected from JWT)
        - role: "admin"

11. FACTORY ISOLATION CHECK
    └─> Repository queries include: WHERE factory_id=1
    └─> User CANNOT access devices from other factories
    └─> If user tries GET /api/v1/devices/999 (other factory):
        └─> Repository query: WHERE factory_id=1 AND id=999
        └─> Returns 404 Not Found (not 403 - don't reveal existence)

12. DASHBOARD DATA FETCH
    └─> Frontend calls GET /api/v1/dashboard/summary
    └─> API queries:
        - Device count: SELECT COUNT(*) FROM devices WHERE factory_id=1
        - Active alerts: SELECT COUNT(*) FROM alerts WHERE factory_id=1 AND resolved_at IS NULL
        - Latest KPIs: Query InfluxDB for last values
    └─> Returns aggregated summary
    └─> Frontend displays cards with data

Token Refresh:
└─> Before token expires, frontend calls POST /api/v1/auth/refresh
└─> Validates existing token
└─> Issues new token with fresh expiration
└─> User stays logged in seamlessly
```

---

### 4.3 Flow 3: Alert Rule Trigger Flow

**Scenario:** Spindle temperature exceeds threshold, triggering critical alert.

```
Step-by-Step Flow:

1. RULE DEFINED
   └─> Maintenance engineer creates rule via UI:
       {
         "name": "Spindle Overheat Critical",
         "severity": "critical",
         "conditions": {
           "operator": "AND",
           "conditions": [
             {"parameter": "spindle_temp", "operator": "gt", "threshold": 80},
             {"parameter": "coolant_flow", "operator": "lt", "threshold": 5}
           ]
         },
         "cooldown_minutes": 15,
         "schedule_type": "always",
         "notification_channels": {"email": true, "whatsapp": true},
         "scope": "device",
         "device_ids": [5]
       }
   └─> Stored in MySQL: rules table with id=10

2. TELEMETRY RECEIVED
   └─> Device M01 sends:
       {
         "timestamp": "2026-02-19T14:30:00Z",
         "metrics": {
           "spindle_temp": 82.5,    # > 80 threshold!
           "coolant_flow": 3.2,     # < 5 threshold!
           "voltage": 231.4,
           "current": 3.2
         }
       }
   └─> Telemetry service processes (see Flow 1)

3. RULE EVALUATION DISPATCH
   └─> Telemetry service dispatches Celery task:
       Task: evaluate_rules
       Queue: rule_engine
       Args: (
         factory_id=1,
         device_id=5,
         metrics={"spindle_temp": 82.5, "coolant_flow": 3.2, ...},
         timestamp="2026-02-19T14:30:00Z"
       )

4. RULE ENGINE PICKS UP TASK
   └─> Celery worker (rule_engine queue) receives task
   └─> Worker ID: rule_engine@worker-1
   └─> Logs: "evaluate_rules.start", factory_id=1, device_id=5

5. FETCH ACTIVE RULES
   └─> Query MySQL:
       SELECT r.* FROM rules r
       JOIN rule_devices rd ON r.id = rd.rule_id
       WHERE r.factory_id=1 
         AND r.is_active=TRUE
         AND (r.scope='global' OR rd.device_id=5)
   └─> Returns: Rule #10 "Spindle Overheat Critical"

6. CHECK SCHEDULE
   └─> Rule schedule_type = "always"
   └─> No time restrictions → proceed
   └─> If schedule_type="time_window":
       └─> Check if 14:30 is within start_time-end_time
       └─> Check if today is in allowed days[]

7. CHECK COOLDOWN
   └─> Query MySQL:
       SELECT * FROM rule_cooldowns 
       WHERE rule_id=10 AND device_id=5
   └─> Result: last_triggered = "2026-02-19T14:10:00Z" (20 min ago)
   └─> Rule cooldown_minutes = 15
   └─> Time since last alert: 20 minutes > 15 minutes → proceed
   └─> If < 15 minutes: skip alert (prevent spam)

8. EVALUATE CONDITIONS
   └─> Condition tree:
       AND
       ├─ spindle_temp > 80?  82.5 > 80 = TRUE
       └─ coolant_flow < 5?   3.2 < 5 = TRUE
   
   └─> Both conditions TRUE → AND = TRUE
   └─> If OR operator: at least one must be TRUE
   └─> Supports nested trees (AND/OR at any depth)

9. ALERT CREATED
   └─> Build alert message:
       "Spindle temperature (82.5°C) exceeded threshold (80°C) 
        AND coolant flow (3.2 L/min) below threshold (5 L/min)"
   
   └─> Insert into MySQL:
       INSERT INTO alerts (
         factory_id, rule_id, device_id, triggered_at, 
         severity, message, telemetry_snapshot
       ) VALUES (
         1, 10, 5, '2026-02-19T14:30:00Z',
         'critical', 
         'Spindle temperature (82.5°C) exceeded...',
         '{"spindle_temp": 82.5, "coolant_flow": 3.2}'
       )
   └─> Returns alert_id = 150

10. UPDATE COOLDOWN
    └─> INSERT INTO rule_cooldowns (rule_id, device_id, last_triggered)
        VALUES (10, 5, '2026-02-19T14:30:00Z')
        ON DUPLICATE KEY UPDATE last_triggered='2026-02-19T14:30:00Z'

11. DISPATCH NOTIFICATION
    └─> Rule notification_channels = {"email": true, "whatsapp": true}
    └─> Dispatch Celery task:
        Task: send_notifications
        Queue: notifications
        Args: (alert_id=150,)

12. NOTIFICATION SENT
    └─> Notification worker picks up task
    └─> Query MySQL for alert details + user contact info
    └─> Format message:
        Subject: [CRITICAL] FactoryOps Alert - Spindle Overheat Critical
        
        Rule: Spindle Overheat Critical
        Device: CNC Mill - Station A (M01)
        Severity: CRITICAL
        Time: 2026-02-19T14:30:00Z
        
        Spindle temperature (82.5°C) exceeded threshold (80°C)
        AND coolant flow (3.2 L/min) below threshold (5 L/min)
        
        Current Values:
        - spindle_temp: 82.5°C
        - coolant_flow: 3.2 L/min
    
    └─> Send email via SMTP
    └─> Send WhatsApp via Twilio API
    └─> If fails: retries 3x, then marks as failed

13. ALERT MARKED AS SENT
    └─> UPDATE alerts SET notification_sent=TRUE WHERE id=150

14. REAL-TIME UPDATE (Optional)
    └─> Frontend polling GET /api/v1/alerts every 30 seconds
    └─> Sees new alert #150
    └─> Shows notification toast: "Critical Alert: Spindle Overheat"
    └─> Updates alert badge count in UI

15. ENGINEER RESPONDS
    └─> Engineer sees alert in UI
    └─> Investigates CNC Mill M01
    └─> Finds coolant pump issue, fixes it
    └─> Clicks "Resolve Alert" in UI

16. ALERT RESOLVED
    └─> Frontend calls: PATCH /api/v1/alerts/150/resolve
    └─> API updates:
        UPDATE alerts SET resolved_at=NOW() WHERE id=150
    └─> Alert moves from "Active" to "Resolved" list

Total Time: ~2-5 seconds from telemetry to notification
```

---

### 4.4 Flow 4: Dashboard Data Loading

**Scenario:** Engineer opens dashboard to check factory overview.

```
Step-by-Step Flow:

1. USER NAVIGATES TO DASHBOARD
   └─> Clicks "Dashboard" in sidebar
   └─> React Router navigates to /dashboard
   └─> Dashboard component mounts

2. AUTHENTICATION CHECK
   └─> ProtectedRoute wrapper verifies isAuthenticated=true
   └─> Axios interceptor adds Authorization header
   └─> Request: GET /api/v1/dashboard/summary

3. BACKEND RECEIVES REQUEST
   └─> FastAPI endpoint: dashboard.get_summary()
   └─> Dependency injection: get_current_user validates JWT
   └─> Extracts factory_id=1 from token claims

4. PARALLEL DATA QUERIES
   
   Query 1: Device Count
   └─> SELECT COUNT(*) FROM devices WHERE factory_id=1 AND is_active=TRUE
   └─> Result: 47 devices
   
   Query 2: Offline Devices
   └─> SELECT COUNT(*) FROM devices 
       WHERE factory_id=1 
         AND is_active=TRUE 
         AND (last_seen < NOW() - INTERVAL 5 MINUTE OR last_seen IS NULL)
   └─> Result: 3 offline
   
   Query 3: Active Alerts
   └─> SELECT severity, COUNT(*) FROM alerts 
       WHERE factory_id=1 AND resolved_at IS NULL 
       GROUP BY severity
   └─> Result: {critical: 2, high: 5, medium: 12, low: 8}
   
   Query 4: Current Energy
   └─> InfluxDB query:
       from(bucket: "factoryops")
         |> range(start: -1m)
         |> filter(fn: (r) => r._measurement == "telemetry")
         |> filter(fn: (r) => r.factory_id == "1")
         |> filter(fn: (r) => r._field == "power")
         |> last()
   └─> Result: Sum of all devices = 125.7 kW
   
   Query 5: Energy Today
   └─> InfluxDB query:
       from(bucket: "factoryops")
         |> range(start: today())
         |> filter(fn: (r) => r._measurement == "telemetry")
         |> filter(fn: (r) => r.factory_id == "1")
         |> filter(fn: (r) => r._field == "power")
         |> integral(unit: 1h)
   └─> Result: 1,847 kWh
   
   Query 6: Health Score
   └─> Complex calculation:
       - Base score: 100
       - Subtract: 5 points per critical alert
       - Subtract: 2 points per high alert
       - Subtract: 1 point per offline device
       - Weight by device importance (if configured)
   └─> Result: 78/100

5. AGGREGATE RESPONSE
   └─> API builds response object:
       {
         "data": {
           "total_devices": 47,
           "active_devices": 44,
           "offline_devices": 3,
           "current_energy_kw": 125.7,
           "energy_today_kwh": 1847,
           "active_alerts": 27,
           "critical_alerts": 2,
           "high_alerts": 5,
           "health_score": 78
         }
       }

6. FRONTEND RECEIVES DATA
   └─> React Query caches response with 5-minute staleTime
   └─> Dashboard component re-renders with data

7. RENDER SUMMARY CARDS
   └─> Grid layout with 4 cards:
   
   ┌─────────────────┐  ┌─────────────────┐
   │ Total Devices   │  │ Active Alerts   │
   │ 47              │  │ 27              │
   │ ● 44 Online     │  │ 🔴 2 Critical   │
   │ ○ 3 Offline     │  │ 🟠 5 High       │
   └─────────────────┘  └─────────────────┘
   
   ┌─────────────────┐  ┌─────────────────┐
   │ Current Energy  │  │ Health Score    │
   │ 125.7 kW        │  │ 78/100          │
   │ 1,847 kWh today │  │ ⚠️ Needs Attention│
   └─────────────────┘  └─────────────────┘

8. BACKGROUND REFRESH
   └─> React Query refetches every 5 minutes (staleTime)
   └─> Or when window regains focus
   └─> Keeps data fresh without manual refresh

9. USER INTERACTIONS
   └─> Click "Total Devices" card → navigates to /machines
   └─> Click "Critical Alerts" → navigates to /alerts?severity=critical
   └─> Click "Health Score" → shows tooltip with breakdown

10. ERROR HANDLING
    └─> If API fails: React Query shows cached data with "stale" indicator
    └─> Retry automatically with exponential backoff
    └─> After 3 failures: Shows error toast "Failed to load dashboard"

Total Load Time: ~200-500ms (cached) to 1-2s (fresh)
```

---

## 5. API Reference

### 5.1 Authentication Endpoints

#### List Factories
**Purpose:** Get all available factories (public, for factory selection page)

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/factories |
| Auth Required | No |

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Vietnam Precision Components",
      "slug": "vpc"
    }
  ]
}
```

---

#### Login
**Purpose:** Authenticate user and get JWT token

| Attribute | Value |
|-----------|-------|
| Method | POST |
| Path | /api/v1/auth/login |
| Auth Required | No |

**Request Body:**
```json
{
  "factory_id": 1,
  "email": "engineer@vpc.com",
  "password": "********"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 42,
    "email": "engineer@vpc.com",
    "role": "admin",
    "permissions": {
      "create_rules": true,
      "run_analytics": true
    }
  }
}
```

**Errors:**
- 401: Invalid credentials (factory not found, user not found, wrong password)

---

#### Refresh Token
**Purpose:** Get new token before expiration

| Attribute | Value |
|-----------|-------|
| Method | POST |
| Path | /api/v1/auth/refresh |
| Auth Required | Yes (Bearer token) |

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

### 5.2 Device Endpoints

#### List Devices
**Purpose:** Get paginated list of devices with health metrics

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/devices |
| Auth Required | Yes |

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| page | int | No | Page number (default: 1) |
| per_page | int | No | Items per page (default: 20, max: 100) |
| search | string | No | Filter by name or device_key |
| is_active | bool | No | Filter by active status |

**Response:**
```json
{
  "data": [
    {
      "id": 5,
      "device_key": "M01",
      "name": "CNC Mill - Station A",
      "manufacturer": "Haas",
      "model": "VF-2",
      "region": "Line 3",
      "is_active": true,
      "last_seen": "2026-02-19T10:30:00Z",
      "health_score": 95,
      "current_energy_kw": 7.5,
      "active_alert_count": 0,
      "created_at": "2026-01-15T08:00:00Z",
      "updated_at": "2026-02-19T10:30:00Z"
    }
  ],
  "total": 47,
  "page": 1,
  "per_page": 20
}
```

---

#### Get Device Detail
**Purpose:** Get single device details

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/devices/{device_id} |
| Auth Required | Yes |

**Response:** Same as list item without aggregated metrics

---

#### Create Device
**Purpose:** Register new device

| Attribute | Value |
|-----------|-------|
| Method | POST |
| Path | /api/v1/devices |
| Auth Required | Yes |

**Request Body:**
```json
{
  "device_key": "M02",
  "name": "CNC Mill - Station B",
  "manufacturer": "Haas",
  "model": "VF-2",
  "region": "Line 3"
}
```

**Response:** Created device object (201)

---

#### Update Device
**Purpose:** Update device metadata

| Attribute | Value |
|-----------|-------|
| Method | PATCH |
| Path | /api/v1/devices/{device_id} |
| Auth Required | Yes |

**Request Body:** (all fields optional)
```json
{
  "name": "CNC Mill - Station B (Updated)",
  "region": "Line 4"
}
```

---

#### Delete Device
**Purpose:** Soft delete (deactivate) device

| Attribute | Value |
|-----------|-------|
| Method | DELETE |
| Path | /api/v1/devices/{device_id} |
| Auth Required | Yes |

**Response:** `{"message": "Device deactivated successfully"}`

---

### 5.3 Parameter Endpoints

#### List Parameters
**Purpose:** Get all discovered parameters for a device

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/devices/{device_id}/parameters |
| Auth Required | Yes |

**Response:**
```json
{
  "data": [
    {
      "id": 15,
      "parameter_key": "voltage",
      "display_name": "Voltage",
      "unit": "V",
      "data_type": "float",
      "is_kpi_selected": true,
      "discovered_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-02-19T08:00:00Z"
    }
  ]
}
```

---

#### Update Parameter
**Purpose:** Update parameter display name, unit, or KPI status

| Attribute | Value |
|-----------|-------|
| Method | PATCH |
| Path | /api/v1/devices/{device_id}/parameters/{param_id} |
| Auth Required | Yes |

**Request Body:**
```json
{
  "display_name": "Line Voltage",
  "unit": "Volts",
  "is_kpi_selected": true
}
```

---

### 5.4 KPI Endpoints

#### Get Live KPIs
**Purpose:** Get current values for all selected KPIs

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/devices/{device_id}/kpis/live |
| Auth Required | Yes |

**Response:**
```json
{
  "device_id": 5,
  "timestamp": "2026-02-19T10:30:00Z",
  "kpis": [
    {
      "parameter_key": "voltage",
      "display_name": "Voltage",
      "unit": "V",
      "value": 231.4,
      "is_stale": false
    },
    {
      "parameter_key": "current",
      "display_name": "Current",
      "unit": "A",
      "value": 3.2,
      "is_stale": false
    }
  ]
}
```

---

#### Get KPI History
**Purpose:** Get time-series data for charts

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/devices/{device_id}/kpis/history |
| Auth Required | Yes |

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| parameter | string | Yes | Parameter key (e.g., "voltage") |
| start | datetime | Yes | Start time (ISO8601) |
| end | datetime | Yes | End time (ISO8601) |
| interval | string | No | Aggregation: 1m, 5m, 1h, 1d |

**Response:**
```json
{
  "parameter_key": "voltage",
  "display_name": "Voltage",
  "unit": "V",
  "interval": "5m",
  "points": [
    {"timestamp": "2026-02-19T10:00:00Z", "value": 231.2},
    {"timestamp": "2026-02-19T10:05:00Z", "value": 231.4},
    {"timestamp": "2026-02-19T10:10:00Z", "value": 231.1}
  ]
}
```

---

### 5.5 Rule Endpoints

#### List Rules
**Purpose:** Get paginated list of alert rules

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/rules |
| Auth Required | Yes |

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| device_id | int | Filter by assigned device |
| is_active | bool | Filter by status |
| scope | string | 'device' or 'global' |
| page | int | Page number |
| per_page | int | Items per page |

---

#### Create Rule
**Purpose:** Create new alert rule

| Attribute | Value |
|-----------|-------|
| Method | POST |
| Path | /api/v1/rules |
| Auth Required | Yes |

**Request Body:**
```json
{
  "name": "Spindle Overheat",
  "description": "Alert when spindle temperature is too high",
  "scope": "device",
  "device_ids": [5],
  "conditions": {
    "operator": "AND",
    "conditions": [
      {"parameter": "spindle_temp", "operator": "gt", "threshold": 80}
    ]
  },
  "cooldown_minutes": 15,
  "severity": "critical",
  "schedule_type": "always",
  "notification_channels": {"email": true, "whatsapp": false}
}
```

---

#### Get Rule
**Purpose:** Get single rule details

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/rules/{rule_id} |
| Auth Required | Yes |

---

#### Update Rule
**Purpose:** Update rule configuration

| Attribute | Value |
|-----------|-------|
| Method | PATCH |
| Path | /api/v1/rules/{rule_id} |
| Auth Required | Yes |

---

#### Delete Rule
**Purpose:** Delete rule

| Attribute | Value |
|-----------|-------|
| Method | DELETE |
| Path | /api/v1/rules/{rule_id} |
| Auth Required | Yes |

---

#### Toggle Rule
**Purpose:** Enable/disable rule

| Attribute | Value |
|-----------|-------|
| Method | PATCH |
| Path | /api/v1/rules/{rule_id}/toggle |
| Auth Required | Yes |

**Response:** Updated rule with toggled is_active status

---

### 5.6 Alert Endpoints

#### List Alerts
**Purpose:** Get paginated alerts with filtering

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/alerts |
| Auth Required | Yes |

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| device_id | int | Filter by device |
| severity | string | 'low', 'medium', 'high', 'critical' |
| resolved | bool | true/false/null |
| start | datetime | Start time |
| end | datetime | End time |
| page | int | Page number |
| per_page | int | Items per page |

**Response:**
```json
{
  "data": [
    {
      "id": 150,
      "rule_id": 10,
      "rule_name": "Spindle Overheat",
      "device_id": 5,
      "device_name": "CNC Mill - Station A",
      "triggered_at": "2026-02-19T14:30:00Z",
      "resolved_at": null,
      "severity": "critical",
      "message": "Spindle temperature exceeded 80°C",
      "telemetry_snapshot": {"spindle_temp": 82.5}
    }
  ],
  "total": 27,
  "page": 1,
  "per_page": 20
}
```

---

#### Get Alert
**Purpose:** Get single alert detail

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/alerts/{alert_id} |
| Auth Required | Yes |

---

#### Resolve Alert
**Purpose:** Mark alert as resolved

| Attribute | Value |
|-----------|-------|
| Method | PATCH |
| Path | /api/v1/alerts/{alert_id}/resolve |
| Auth Required | Yes |

**Response:**
```json
{
  "id": 150,
  "resolved_at": "2026-02-19T15:00:00Z"
}
```

---

### 5.7 Analytics Endpoints

#### Create Analytics Job
**Purpose:** Start ML analysis job

| Attribute | Value |
|-----------|-------|
| Method | POST |
| Path | /api/v1/analytics/jobs |
| Auth Required | Yes |

**Request Body:**
```json
{
  "job_type": "anomaly",
  "mode": "standard",
  "device_ids": [5, 6, 7],
  "date_range_start": "2026-02-01T00:00:00Z",
  "date_range_end": "2026-02-19T00:00:00Z"
}
```

**Response:**
```json
{
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending"
  }
}
```

**Job Types:**
- `anomaly`: Isolation Forest anomaly detection
- `failure_prediction`: Random Forest failure prediction
- `energy_forecast`: Prophet energy forecasting
- `ai_copilot`: Natural language insights

---

#### List Analytics Jobs
**Purpose:** Get all jobs for factory

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/analytics/jobs |
| Auth Required | Yes |

**Query Parameters:** status, job_type, page, per_page

---

#### Get Analytics Job
**Purpose:** Check job status and results

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/analytics/jobs/{job_id} |
| Auth Required | Yes |

**Response (Complete):**
```json
{
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "complete",
    "job_type": "anomaly",
    "mode": "standard",
    "device_ids": [5, 6, 7],
    "result_url": "https://minio.factoryops.local/factoryops/anomalies/550e8400.../results.json",
    "created_at": "2026-02-19T10:00:00Z",
    "started_at": "2026-02-19T10:00:05Z",
    "completed_at": "2026-02-19T10:05:30Z"
  }
}
```

---

#### Delete Analytics Job
**Purpose:** Cancel/delete job (only pending or failed)

| Attribute | Value |
|-----------|-------|
| Method | DELETE |
| Path | /api/v1/analytics/jobs/{job_id} |
| Auth Required | Yes |

---

### 5.8 Report Endpoints

#### Create Report
**Purpose:** Generate PDF/Excel report

| Attribute | Value |
|-----------|-------|
| Method | POST |
| Path | /api/v1/reports |
| Auth Required | Yes |

**Request Body:**
```json
{
  "title": "Weekly Equipment Report",
  "device_ids": [5, 6, 7],
  "date_range_start": "2026-02-12T00:00:00Z",
  "date_range_end": "2026-02-19T00:00:00Z",
  "format": "pdf",
  "include_analytics": true,
  "analytics_job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Formats:** `pdf`, `excel`, `json`

---

#### List Reports
**Purpose:** Get all reports for factory

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/reports |
| Auth Required | Yes |

---

#### Get Report
**Purpose:** Check report status

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/reports/{report_id} |
| Auth Required | Yes |

---

#### Download Report
**Purpose:** Download generated report

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/reports/{report_id}/download |
| Auth Required | Yes |

**Response:** 302 Redirect to presigned MinIO URL

---

#### Delete Report
**Purpose:** Delete report (only pending or failed)

| Attribute | Value |
|-----------|-------|
| Method | DELETE |
| Path | /api/v1/reports/{report_id} |
| Auth Required | Yes |

---

### 5.9 User Endpoints (Super Admin Only)

#### List Users
**Purpose:** Get all users in factory

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/users |
| Auth Required | Yes (super_admin only) |

---

#### Invite User
**Purpose:** Invite new admin to factory

| Attribute | Value |
|-----------|-------|
| Method | POST |
| Path | /api/v1/users/invite |
| Auth Required | Yes (super_admin only) |

**Request Body:**
```json
{
  "email": "newengineer@vpc.com",
  "whatsapp_number": "+84901234567",
  "permissions": {
    "create_rules": true,
    "run_analytics": true,
    "generate_reports": false
  }
}
```

---

#### Accept Invite
**Purpose:** New user accepts invitation and sets password

| Attribute | Value |
|-----------|-------|
| Method | POST |
| Path | /api/v1/users/accept-invite |
| Auth Required | No |

**Request Body:**
```json
{
  "token": "invite-token-from-email",
  "password": "********"
}
```

**Response:** Same as login (access_token + user)

---

#### Update User Permissions
**Purpose:** Modify user permissions

| Attribute | Value |
|-----------|-------|
| Method | PATCH |
| Path | /api/v1/users/{user_id}/permissions |
| Auth Required | Yes (super_admin only) |

---

#### Deactivate User
**Purpose:** Deactivate user account

| Attribute | Value |
|-----------|-------|
| Method | DELETE |
| Path | /api/v1/users/{user_id} |
| Auth Required | Yes (super_admin only) |

---

### 5.10 Dashboard Endpoints

#### Get Dashboard Summary
**Purpose:** Get overview statistics for dashboard

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /api/v1/dashboard/summary |
| Auth Required | Yes |

**Response:**
```json
{
  "data": {
    "total_devices": 47,
    "active_devices": 44,
    "offline_devices": 3,
    "current_energy_kw": 125.7,
    "energy_today_kwh": 1847,
    "active_alerts": 27,
    "critical_alerts": 2,
    "high_alerts": 5,
    "health_score": 78
  }
}
```

---

### 5.11 System Endpoints

#### Health Check
**Purpose:** Check system health

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /health |
| Auth Required | No |

**Response:**
```json
{
  "status": "healthy",
  "service": "api",
  "version": "1.0.0",
  "dependencies": {
    "mysql": "ok",
    "redis": "ok",
    "influxdb": "ok",
    "minio": "ok"
  }
}
```

---

#### Metrics (Prometheus)
**Purpose:** Get Prometheus metrics for monitoring

| Attribute | Value |
|-----------|-------|
| Method | GET |
| Path | /metrics |
| Auth Required | No |

**Response:** Prometheus text format

---

## 6. Multi-Tenancy & Security

### 6.1 Factory Isolation Architecture

FactoryOps is a **multi-tenant** system where each Factory is a completely isolated tenant. This is the foundation of the security model.

**Isolation Levels:**

1. **Database Level Isolation**
   - Every table has a `factory_id` column
   - Every query includes: `WHERE factory_id = {current_factory_id}`
   - Foreign key constraints ensure referential integrity

2. **API Level Isolation**
   - JWT token includes `factory_id` claim
   - All endpoints extract factory_id from token
   - Repository layer enforces filtering

3. **Time-Series Isolation**
   - InfluxDB tags: factory_id, device_id
   - All queries filter by factory_id tag
   - Different factories cannot see each other's telemetry

4. **File Storage Isolation**
   - MinIO paths include factory_id implicitly (via device_id)
   - Presigned URLs are generated per-user per-file
   - No cross-factory file access

### 6.2 How Factory Isolation Works (Code Examples)

**Example 1: Repository Query**
```python
# device_repo.py
async def get_by_id(db: AsyncSession, factory_id: int, device_id: int) -> Optional[Device]:
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.factory_id == factory_id,  # ← ISOLATION ENFORCED
        )
    )
    return result.scalar_one_or_none()

# If user from Factory A tries to access device from Factory B:
# Query: WHERE id=999 AND factory_id=1
# Device 999 belongs to factory_id=2
# Result: None (404 Not Found)
```

**Example 2: API Endpoint**
```python
# devices.py
@router.get("/{device_id}")
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Extract factory_id from JWT token
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    # Repository enforces isolation
    device = await device_repo.get_by_id(db, factory_id, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",  # ← Doesn't reveal if exists
        )
    
    return device
```

**Example 3: InfluxDB Query**
```python
# Telemetry service writes
telemetry,factory_id=1,device_id=M01 voltage=231.4 1708338600000000000

# Query must include factory_id filter
query = f'''
from(bucket: "factoryops")
  |> range(start: -1h)
  |> filter(fn: (r) => r.factory_id == "{factory_id}")  # ← ISOLATION
  |> filter(fn: (r) => r.device_id == "{device_id}")
'''
```

### 6.3 JWT Structure and Validation

**JWT Token Payload:**
```json
{
  "sub": "42",                    # Subject: user_id
  "factory_id": 1,                # Tenant identifier
  "factory_slug": "vpc",          # Human-readable factory
  "role": "admin",                # User role
  "iat": 1708338600,              # Issued at
  "exp": 1708425000               # Expiration (24 hours)
}
```

**Token Validation Process:**
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 1. Decode token
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    
    # 2. Extract claims
    user_id = int(payload["sub"])
    factory_id = payload["factory_id"]
    factory_slug = payload["factory_slug"]
    role = payload["role"]
    
    # 3. Check expiration (handled by PyJWT)
    
    # 4. Build user object with token attributes
    user = User(
        id=user_id,
        factory_id=factory_id,
        role=role,
    )
    # Inject factory_id for repository use
    user._token_factory_id = factory_id
    
    return user
```

### 6.4 What a Malicious User CANNOT Do

**Scenario:** Attacker compromises user account in Factory A, tries to access Factory B data.

| Attack Attempt | Prevention | Why It Fails |
|----------------|-----------|--------------|
| **Access Factory B device via API** | 404 Not Found | Repository filters by factory_id from JWT. Device exists but returns None. |
| **Access Factory B telemetry** | Empty results | InfluxDB queries include factory_id tag filter. No matching series. |
| **Modify Factory B rules** | 404 Not Found | Rule lookup includes factory_id. Rule not found in Factory A. |
| **Download Factory B reports** | 404 Not Found | Report lookup includes factory_id. Report not accessible. |
| **Create device in Factory B** | Assigned to Factory A | Device creation uses factory_id from token, not request body. |
| **Tamper with JWT factory_id** | 401 Unauthorized | JWT signature verification fails. Token rejected. |
| **SQL Injection to bypass factory_id** | Parameterized queries | SQLAlchemy uses bound parameters. Injection impossible. |
| **Access via direct database connection** | Network isolation | Services run in Docker network. External access blocked. |

**Key Security Principle:**
> Always return 404 Not Found (not 403 Forbidden) when cross-factory access is attempted. This prevents information leakage about what resources exist in other factories.

---

## 7. Frontend Structure

### 7.1 Page Components

| Page | Path | Purpose | API Calls |
|------|------|---------|-----------|
| **FactorySelect** | /factory-select | Initial landing page to choose factory | GET /factories |
| **Login** | /login | User authentication | POST /auth/login |
| **Dashboard** | /dashboard | Factory overview with summary cards | GET /dashboard/summary |
| **Machines** | /machines | Device list with search/filter | GET /devices |
| **DeviceDetail** | /machines/:deviceId | Device details with KPIs and charts | GET /devices/{id}, GET /parameters, GET /kpis/live, GET /kpis/history |
| **Rules** | /rules | Alert rule listing | GET /rules |
| **RuleBuilder** | /rules/new, /rules/:ruleId | Create/edit rules with condition editor | POST /rules, GET /rules/{id}, PATCH /rules/{id} |
| **Analytics** | /analytics | ML job management | GET /analytics/jobs, POST /analytics/jobs |
| **Reports** | /reports | Report generation and download | GET /reports, POST /reports |
| **Users** | /users | User management (super_admin only) | GET /users, POST /users/invite |

### 7.2 Component Hierarchy

```
App.tsx (Root)
├── QueryClientProvider
└── Router
    ├── FactorySelect (Public)
    ├── Login (Public)
    └── ProtectedRoute
        └── MainLayout
            ├── Sidebar (Navigation)
            │   ├── Factory Info
            │   ├── User Info
            │   └── Nav Links
            └── Main Content Area
                ├── Dashboard
                │   └── Summary Cards Grid
                ├── Machines
                │   ├── Device Table
                │   └── Add Device Modal
                ├── DeviceDetail
                │   ├── Device Info Card
                │   ├── KPICardGrid
                │   │   └── KPICard (xN)
                │   └── TelemetryChart
                ├── Rules
                │   └── Rule Table
                ├── RuleBuilder
                │   ├── Rule Form
                │   ├── ConditionGroupEditor
                │   │   └── ConditionLeafEditor (recursive)
                │   └── Device Selector
                ├── Analytics
                │   ├── Job Table
                │   └── Create Job Modal
                ├── Reports
                │   ├── Report Table
                │   └── Generate Report Modal
                └── Users (SuperAdminRoute)
                    ├── User Table
                    └── Invite User Modal
```

### 7.3 State Management

**Zustand Stores:**

1. **authStore** - Authentication state
```typescript
interface AuthState {
  user: User | null;
  factory: Factory | null;
  token: string | null;
  isAuthenticated: boolean;
}

// Actions
setAuth(token, user, factory)  // Login success
logout()                       // Clear auth state
```

2. **uiStore** - UI state
```typescript
interface UIState {
  sidebarOpen: boolean;
  notifications: Notification[];
}

// Actions
toggleSidebar()
addNotification(notification)
removeNotification(id)
```

**React Query:**
- Server state management with caching
- Automatic background refetching
- Stale-while-revalidate pattern

```typescript
// Example: Device list query
const { data, isLoading } = useQuery({
  queryKey: ['devices', page, search],
  queryFn: () => devices.list({ page, search }),
  staleTime: 5 * 60 * 1000, // 5 minutes
});

// Example: Create device mutation
const createDevice = useMutation({
  mutationFn: devices.create,
  onSuccess: () => {
    queryClient.invalidateQueries(['devices']);
    showSuccessToast('Device created');
  },
});
```

### 7.4 API Integration Pattern

**Axios Client Configuration:**
```typescript
// client.ts
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// Request interceptor: Add auth header
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**Typed Endpoints:**
```typescript
// endpoints.ts
export const devices = {
  list: (params) => api.get('/devices', { params }),
  getById: (id) => api.get(`/devices/${id}`),
  create: (data) => api.post('/devices', data),
  update: (id, data) => api.patch(`/devices/${id}`, data),
  delete: (id) => api.delete(`/devices/${id}`),
};
```

---

## 8. How To Run & Debug

### 8.1 Prerequisites

**Required Software:**
- Docker 24.0+ and Docker Compose
- Git
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- mosquitto-clients (for testing MQTT)

**System Requirements:**
- RAM: 8GB minimum (16GB recommended)
- Disk: 20GB free space
- Ports: 80, 443, 3306, 6379, 8086, 9000, 9001, 1883

### 8.2 Start / Stop Commands

**Start All Services:**
```bash
# Navigate to project root
cd /Users/vedanthshetty/Desktop/Vibe-Coding/Open Code/factoryops

# Copy environment file
cp .env.example .env

# Start all services
docker compose -f docker/docker-compose.yml up -d

# Wait for services to be healthy (30-60 seconds)
docker compose -f docker/docker-compose.yml ps
```

**Stop All Services:**
```bash
docker compose -f docker/docker-compose.yml down

# To also remove volumes (WARNING: deletes all data):
docker compose -f docker/docker-compose.yml down -v
```

**View Logs:**
```bash
# All services
docker compose -f docker/docker-compose.yml logs -f

# Specific service
docker compose -f docker/docker-compose.yml logs -f api
docker compose -f docker/docker-compose.yml logs -f telemetry
docker compose -f docker/docker-compose.yml logs -f rule_engine
```

**Restart Service:**
```bash
docker compose -f docker/docker-compose.yml restart api
```

### 8.3 How to Check if Everything is Working

**1. Check Container Status:**
```bash
docker compose -f docker/docker-compose.yml ps

# Should show all services as "healthy"
NAME                STATUS          PORTS
factoryops-api-1    Up 5 minutes (healthy)   0.0.0.0:8000->8000/tcp
factoryops-mysql-1  Up 5 minutes (healthy)   0.0.0.0:3306->3306/tcp
...
```

**2. Check API Health:**
```bash
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "dependencies": {
    "mysql": "ok",
    "redis": "ok",
    "influxdb": "ok",
    "minio": "ok"
  }
}
```

**3. Check API Docs:**
- Open browser: http://localhost:8000/api/docs
- Should show Swagger UI with all endpoints

**4. Test Frontend:**
- Open browser: http://localhost
- Should show FactorySelect page

**5. Test MQTT:**
```bash
# Subscribe to topic
mosquitto_sub -h localhost -p 1883 -t "factories/vpc/devices/+/telemetry"

# In another terminal, publish test message
mosquitto_pub -h localhost -p 1883 \
  -t "factories/vpc/devices/M01/telemetry" \
  -m '{"metrics":{"voltage":231.4,"current":3.2}}'

# Should see message in subscriber
```

### 8.4 Common Errors and Fixes

**Error: "MySQL connection failed"**
```bash
# Symptoms: API health shows mysql: error
# Fix: Wait for MySQL to fully start (30s), then restart API
docker compose -f docker/docker-compose.yml restart api
```

**Error: "Port already in use"**
```bash
# Symptoms: Cannot start containers
# Fix: Find and stop process using port
lsof -i :3306  # Find MySQL port user
kill -9 <PID>  # Stop process
```

**Error: "Migration failed"**
```bash
# Symptoms: Database schema not created
# Fix: Run migrations manually
docker compose -f docker/docker-compose.yml exec api alembic upgrade head
```

**Error: "Celery worker not processing tasks"**
```bash
# Symptoms: Analytics jobs stuck in "pending"
# Fix: Check Redis connection, restart workers
docker compose -f docker/docker-compose.yml logs celery_worker
docker compose -f docker/docker-compose.yml restart rule_engine
```

**Error: "Frontend not loading"**
```bash
# Symptoms: Blank page or 404
# Fix: Check Nginx configuration, rebuild frontend
docker compose -f docker/docker-compose.yml build frontend
docker compose -f docker/docker-compose.yml up -d frontend
```

### 8.5 How to View Logs

**Structured JSON Logs:**
```bash
# View API logs with JSON formatting
docker compose -f docker/docker-compose.yml logs -f api | jq '.'

# Filter for specific log level
docker compose -f docker/docker-compose.yml logs -f api | jq 'select(.level=="error")'
```

**Log Levels:**
- `debug`: Detailed debugging info
- `info`: General operational info
- `warning`: Warning conditions
- `error`: Error conditions

**Useful Log Queries:**
```bash
# Recent errors
docker compose -f docker/docker-compose.yml logs --tail=100 api | grep error

# Telemetry processing
docker compose -f docker/docker-compose.yml logs -f telemetry | grep "telemetry.processed"

# Rule evaluations
docker compose -f docker/docker-compose.yml logs -f rule_engine | grep "rule.evaluated"
```

---

## 9. How To Extend

### 9.1 How to Add a New API Endpoint

**Example: Add device restart endpoint**

**Step 1: Add Repository Method**
```python
# backend/app/repositories/device_repo.py
async def restart_device(db: AsyncSession, factory_id: int, device_id: int) -> bool:
    """Mark device for restart (sends MQTT command)."""
    device = await get_by_id(db, factory_id, device_id)
    if not device:
        return False
    
    # Publish restart command to MQTT
    # Implementation here...
    
    return True
```

**Step 2: Add API Endpoint**
```python
# backend/app/api/v1/devices.py
@router.post("/{device_id}/restart")
async def restart_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restart device remotely."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    success = await device_repo.restart_device(db, factory_id, device_id)
    if not success:
        raise HTTPException(404, "Device not found")
    
    return {"message": "Restart command sent", "device_id": device_id}
```

**Step 3: Add Frontend Hook**
```typescript
// frontend/src/hooks/useDevices.ts
export const useRestartDevice = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (deviceId: number) => 
      api.post(`/devices/${deviceId}/restart`),
    onSuccess: () => {
      queryClient.invalidateQueries(['devices']);
      showSuccessToast('Restart command sent');
    },
  });
};
```

**Step 4: Add UI Button**
```tsx
// In DeviceDetail.tsx
const restartDevice = useRestartDevice();

<button 
  onClick={() => restartDevice.mutate(device.id)}
  disabled={restartDevice.isPending}
>
  Restart Device
</button>
```

### 9.2 How to Add a New Device Type

Device types are flexible - just send different metrics:

```json
// HVAC Unit
{
  "metrics": {
    "supply_temp": 18.5,
    "return_temp": 24.2,
    "fan_speed": 85,
    "filter_pressure": 120
  }
}

// Conveyor Belt
{
  "metrics": {
    "belt_speed": 1.2,
    "motor_current": 4.5,
    "load_weight": 150,
    "vibration": 2.1
  }
}

// All are automatically discovered as parameters
```

To customize display names:
```python
# Update parameter after discovery
await parameter_repo.update(
    db, factory_id, device_id, param_id,
    {"display_name": "Supply Air Temperature", "unit": "°C"}
)
```

### 9.3 How to Add a New Alert Type

Alert types are defined by rules. To add new alert logic:

**Option 1: New Parameter-based Rule**
- Just create a rule in UI targeting the new parameter
- No code changes needed

**Option 2: Complex Multi-device Rule**
```python
# backend/app/workers/rule_engine.py
async def evaluate_complex_rule(factory_id, device_ids, metrics):
    # Custom evaluation logic
    # e.g., Alert if 3 out of 5 devices have high temperature
    high_temp_count = sum(1 for m in metrics if m.get('temp', 0) > 80)
    if high_temp_count >= 3:
        return True
    return False
```

### 9.4 How to Add a New Frontend Page

**Step 1: Create Page Component**
```tsx
// frontend/src/pages/MaintenanceSchedule.tsx
import { useQuery } from '@tanstack/react-query';

export const MaintenanceSchedule = () => {
  const { data } = useQuery({
    queryKey: ['maintenance'],
    queryFn: () => api.get('/maintenance/schedule'),
  });
  
  return (
    <div>
      <h1>Maintenance Schedule</h1>
      {/* Page content */}
    </div>
  );
};
```

**Step 2: Add Route**
```tsx
// frontend/src/App.tsx
import MaintenanceSchedule from './pages/MaintenanceSchedule';

<Route path="maintenance" element={<MaintenanceSchedule />} />
```

**Step 3: Add Navigation Link**
```tsx
// frontend/src/components/ui/Sidebar.tsx
{to: '/maintenance', icon: WrenchIcon, label: 'Maintenance'},
```

---

## 10. Deployment

### 10.1 Local Development Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd factoryops

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env with your settings
# At minimum, change:
# - JWT_SECRET_KEY (generate random 32+ char string)
# - MYSQL_ROOT_PASSWORD
# - INFLUXDB_PASSWORD

# 4. Start services
docker compose -f docker/docker-compose.yml up -d

# 5. Run migrations
docker compose -f docker/docker-compose.yml exec api alembic upgrade head

# 6. Seed database (creates initial factory and super_admin)
docker compose -f docker/docker-compose.yml exec api python scripts/seed.py

# 7. Access application
# Frontend: http://localhost
# API Docs: http://localhost:8000/api/docs
# Default login: admin@vpc.com / Admin@123
```

### 10.2 Production Deployment Steps

**Step 1: Prepare Server**
- Provision server (4+ vCPU, 16GB RAM, 100GB SSD)
- Install Docker and Docker Compose
- Configure firewall (allow 80, 443, 22)

**Step 2: SSL Certificates**
```bash
# Using Let's Encrypt
certbot certonly --standalone -d factoryops.yourdomain.com

# Copy certs to project
cp /etc/letsencrypt/live/factoryops.yourdomain.com/fullchain.pem docker/ssl/cert.pem
cp /etc/letsencrypt/live/factoryops.yourdomain.com/privkey.pem docker/ssl/key.pem
```

**Step 3: Secrets Management**
```bash
# Create secrets directory
mkdir -p docker/secrets

# Generate secure secrets
openssl rand -base64 32 > docker/secrets/mysql_root_password.txt
openssl rand -base64 32 > docker/secrets/jwt_secret.txt
# ... etc for all secrets

chmod 600 docker/secrets/*
```

**Step 4: Production Docker Compose**
```bash
# Use production configuration
docker compose -f docker/docker-compose.prod.yml pull
docker compose -f docker/docker-compose.prod.yml up -d
```

**Step 5: Database Setup**
```bash
# Run migrations
docker compose -f docker/docker-compose.prod.yml exec api alembic upgrade head

# Seed initial data
docker compose -f docker/docker-compose.prod.yml exec api python scripts/seed.py
```

**Step 6: Verify Deployment**
```bash
# Check health
curl https://factoryops.yourdomain.com/health

# Check logs
docker compose -f docker/docker-compose.prod.yml logs -f
```

### 10.3 Environment Variables Explained

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| **APP_ENV** | Yes | development | Environment mode (development/production) |
| **APP_URL** | Yes | http://localhost | Base URL for invite links |
| **LOG_LEVEL** | Yes | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |
| **MYSQL_HOST** | Yes | mysql | MySQL service hostname |
| **MYSQL_PORT** | Yes | 3306 | MySQL port |
| **MYSQL_DATABASE** | Yes | factoryops | Database name |
| **MYSQL_USER** | Yes | factoryops | Database user |
| **MYSQL_PASSWORD** | Yes | - | Database password (CHANGE THIS!) |
| **DATABASE_URL** | Yes | - | Full SQLAlchemy connection string |
| **INFLUXDB_URL** | Yes | http://influxdb:8086 | InfluxDB endpoint |
| **INFLUXDB_TOKEN** | Yes | - | InfluxDB admin token |
| **INFLUXDB_ORG** | Yes | factoryops | InfluxDB organization |
| **INFLUXDB_BUCKET** | Yes | factoryops | InfluxDB bucket name |
| **REDIS_URL** | Yes | redis://redis:6379/0 | Redis connection |
| **CELERY_BROKER_URL** | Yes | redis://redis:6379/1 | Celery broker |
| **CELERY_RESULT_BACKEND** | Yes | redis://redis:6379/2 | Celery results |
| **MINIO_ENDPOINT** | Yes | minio:9000 | MinIO server address |
| **MINIO_ACCESS_KEY** | Yes | - | MinIO access key |
| **MINIO_SECRET_KEY** | Yes | - | MinIO secret key |
| **MINIO_BUCKET** | Yes | factoryops | MinIO bucket name |
| **MQTT_BROKER_HOST** | Yes | emqx | MQTT broker hostname |
| **MQTT_BROKER_PORT** | Yes | 1883 | MQTT broker port |
| **JWT_SECRET_KEY** | Yes | - | JWT signing key (32+ chars, random) |
| **JWT_ALGORITHM** | Yes | HS256 | JWT algorithm |
| **JWT_EXPIRY_HOURS** | Yes | 24 | Token expiration time |
| **SMTP_HOST** | No | - | SMTP server for emails |
| **SMTP_PORT** | No | 587 | SMTP port |
| **SMTP_USER** | No | - | SMTP username |
| **SMTP_PASSWORD** | No | - | SMTP password |
| **SMTP_FROM** | No | noreply@factoryops.local | From address |
| **TWILIO_ACCOUNT_SID** | No | - | Twilio account SID |
| **TWILIO_AUTH_TOKEN** | No | - | Twilio auth token |
| **TWILIO_WHATSAPP_FROM** | No | - | Twilio WhatsApp sender |

### 10.4 Backup and Maintenance

**Automated Backups:**
```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * /path/to/factoryops/scripts/backup.sh
```

**Manual Backup:**
```bash
# Database
docker compose exec -T mysql mysqldump -u factoryops -p factoryops | gzip > backup.sql.gz

# InfluxDB
docker compose exec influxdb influx backup /tmp/backup
docker cp factoryops-influxdb-1:/tmp/backup ./influxdb-backup
```

**Update Deployment:**
```bash
# Pull latest images
docker compose -f docker/docker-compose.prod.yml pull

# Rolling restart (zero downtime)
docker compose -f docker/docker-compose.prod.yml up -d --no-deps api
docker compose -f docker/docker-compose.prod.yml up -d --no-deps frontend
```

---

## Summary

FactoryOps is a comprehensive Industrial IoT platform with:

- **13 microservices** working together
- **30+ REST API endpoints**
- **Real-time telemetry processing** via MQTT
- **ML-powered analytics** for predictive maintenance
- **Multi-tenant architecture** with strict factory isolation
- **React frontend** with modern tooling
- **Production-ready** with Docker, CI/CD, and monitoring

**Key Takeaways:**
1. Every query is filtered by `factory_id` for security
2. Telemetry flows: Device → MQTT → InfluxDB + Rule Evaluation
3. Background tasks handled by Celery workers
4. JWT tokens carry user identity and factory context
5. Frontend uses React Query for efficient data fetching

**Next Steps:**
1. Review the existing codebase in detail
2. Run the application locally
3. Create a test device and send telemetry
4. Create an alert rule and trigger it
5. Explore the API documentation at `/api/docs`

---

**Document Version:** 1.0.0  
**FactoryOps Version:** 1.0.0  
**Maintained By:** Engineering Team
