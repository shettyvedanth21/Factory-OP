# SENSOR_ONBOARDING.md

Complete guide for onboarding physical sensors and devices to the FactoryOps platform.

**Version**: 1.0  
**Last Updated**: 2026-02-19  
**Codebase Commit**: Based on telemetry service v1, backend API v1

---

## PART A: FOR ME (Platform Owner)

### A1. Pre-Onboarding Checklist

**Information to collect from firmware team BEFORE starting:**

```
=== FIRMWARE TEAM QUESTIONNAIRE ===

Factory Information:
- Factory name: ___________________________
- Proposed factory slug (lowercase, no spaces): ___________________________
- Factory timezone (IANA format, e.g., "Asia/Kolkata"): ___________________________

Device Inventory:
- Number of devices to connect: ___________________________
- Device types/machines (e.g., "Compressor", "Pump", "Motor"): ___________________________
- Proposed device keys for each (e.g., "COMP_01", "PUMP_A", "MOTOR_B1"): ___________________________

Technical Details:
- Can devices connect to MQTT broker over port 1883? [ ] Yes [ ] No
- Network restrictions (firewalls, proxies): ___________________________
- Supported TLS version (if encryption required): ___________________________
- Data collection frequency: ___________________________
- Metrics each device will send (list parameter names): ___________________________

MQTT Client Capabilities:
- MQTT client library being used: ___________________________
- Supports QoS 1? [ ] Yes [ ] No
- Can send ISO8601 timestamps? [ ] Yes [ ] No [ ] Will use server time
- Maximum payload size: ___________________________

Contact:
- Firmware team lead email: ___________________________
- Emergency contact: ___________________________
```

**Check before proceeding:**
- [ ] Factory slug is URL-safe (lowercase, alphanumeric + hyphens only)
- [ ] Device keys are unique and follow naming convention (see B6)
- [ ] Firmware team can access MQTT port 1883 (or appropriate port)
- [ ] You have admin access to FactoryOps platform

---

### A2. Register a New Factory

**Exact curl command to create factory via API:**

```bash
curl -X POST http://localhost:8000/api/v1/factories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer [YOUR_ADMIN_TOKEN]" \
  -d '{
    "name": "ABC Manufacturing",
    "slug": "abc-manufacturing",
    "timezone": "Asia/Kolkata"
  }'
```

**Slug Naming Rules (from `backend/app/models/factory.py` lines 14-15):**
- Maximum 100 characters
- Must be URL-safe: lowercase letters, numbers, hyphens only
- Must be unique across all factories
- No spaces, no special characters except hyphen
- Examples: `vpc`, `abc-manufacturing`, `plant-1-mumbai`

**Docker command to verify creation in MySQL:**

```bash
docker compose -f docker/docker-compose.yml exec mysql mysql -u factoryops -p \
  -e "SELECT id, name, slug, timezone, created_at FROM factories WHERE slug='abc-manufacturing';"
```

Expected output:
```
+----+-----------------+-----------------+---------------------+---------------------+
| id | name            | slug            | timezone            | created_at          |
+----+-----------------+-----------------+---------------------+---------------------+
|  3 | ABC Manufacturing| abc-manufacturing | Asia/Kolkata        | 2026-02-19 08:30:00 |
+----+-----------------+-----------------+---------------------+---------------------+
```

---

### A3. How Device Auto-Registration Works

**What triggers auto-registration:**

Function: `get_or_create_device()`  
File: `telemetry/handlers/cache.py` lines 121-187

When a message arrives on topic `factories/{slug}/devices/{key}/telemetry`:

1. Telemetry service parses the topic (line 43 in `telemetry/handlers/ingestion.py`)
2. Resolves factory by slug from cache/DB
3. Calls `get_or_create_device()` which:
   - Checks Redis cache first (line 142-150)
   - Queries MySQL for existing device (line 153-159)
   - If not found, auto-creates device (line 161-177):
     ```python
     device = Device(
         factory_id=factory_id,
         device_key=device_key,
         is_active=True,  # Auto-activated
     )
     ```
   - Logs: `device.auto_registered` with factory_id, device_id, device_key

**What you will see after first message arrives:**

1. **In telemetry service logs:**
   ```
   device.auto_registered factory_id=3 device_id=15 device_key="COMP_01"
   parameter.discovered factory_id=3 device_id=15 parameter="voltage" data_type="float"
   telemetry.processed factory_id=3 device_id=15 metric_count=4
   ```

2. **In UI (http://localhost):**
   - New device appears in device list
   - Device shows "Offline" initially, switches to "Online" when receiving data
   - Discovered parameters appear in device detail page

3. **In MySQL:**
   ```sql
   SELECT id, factory_id, device_key, name, is_active, last_seen 
   FROM devices WHERE device_key='COMP_01';
   ```

**Exact curl command to verify device appeared:**

```bash
# List all devices (requires auth token)
curl -H "Authorization: Bearer [TOKEN]" \
  http://localhost:8000/api/v1/devices | jq '.data[] | {id, device_key, name, is_active}'

# Get specific device details
curl -H "Authorization: Bearer [TOKEN]" \
  http://localhost:8000/api/v1/devices/15

# View discovered parameters
curl -H "Authorization: Bearer [TOKEN]" \
  http://localhost:8000/api/v1/devices/15/parameters | jq '.data[] | {parameter_key, display_name, data_type}'
```

---

### A4. Configure KPIs After Device Appears

**Step 1: View discovered parameters**

```bash
curl -H "Authorization: Bearer [TOKEN]" \
  http://localhost:8000/api/v1/devices/15/parameters
```

Response example:
```json
{
  "data": [
    {
      "id": 47,
      "parameter_key": "voltage",
      "display_name": "Voltage",
      "data_type": "float",
      "unit": null,
      "is_kpi_selected": true
    },
    {
      "id": 48,
      "parameter_key": "current",
      "display_name": "Current",
      "data_type": "float",
      "unit": null,
      "is_kpi_selected": true
    }
  ]
}
```

**Step 2: Update parameter units and display names**

```bash
# Update voltage parameter (id=47) with unit
curl -X PATCH \
  http://localhost:8000/api/v1/devices/15/parameters/47 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer [TOKEN]" \
  -d '{
    "display_name": "Line Voltage L1",
    "unit": "V",
    "is_kpi_selected": true
  }'

# Update current parameter (id=48)
curl -X PATCH \
  http://localhost:8000/api/v1/devices/15/parameters/48 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer [TOKEN]" \
  -d '{
    "display_name": "Line Current L1",
    "unit": "A",
    "is_kpi_selected": true
  }'
```

**Step 3: Create an alert rule**

```bash
# Create rule for high voltage alert
curl -X POST http://localhost:8000/api/v1/rules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer [TOKEN]" \
  -d '{
    "name": "High Voltage Alert",
    "description": "Alert when voltage exceeds 250V",
    "scope": "device",
    "device_ids": [15],
    "conditions": {
      "operator": "AND",
      "conditions": [
        {
          "parameter": "voltage",
          "operator": "gt",
          "value": 250
        }
      ]
    },
    "cooldown_minutes": 5,
    "severity": "warning",
    "schedule_type": "always",
    "notification_channels": ["email"]
  }'
```

Supported operators in conditions (from `backend/app/workers/rule_engine.py` lines 20-27):
- `gt` - greater than (>)
- `lt` - less than (<)
- `gte` - greater than or equal (>=)
- `lte` - less than or equal (<=)
- `eq` - equal (==)
- `neq` - not equal (!=)

**Step 4: View KPI dashboard**

```bash
# Get live KPI values for device
curl -H "Authorization: Bearer [TOKEN]" \
  http://localhost:8000/api/v1/devices/15/kpis/live

# Get historical data
curl -H "Authorization: Bearer [TOKEN]" \
  "http://localhost:8000/api/v1/devices/15/kpis/history?parameter=voltage&start=2026-02-19T00:00:00Z&end=2026-02-19T23:59:59Z&interval=5m"
```

**UI Steps for KPI Dashboard:**
1. Navigate to http://localhost/devices
2. Click on the device name
3. Go to "Parameters" tab
4. Toggle "Show in Dashboard" for desired parameters
5. Go to "Dashboard" to see live values
6. Click on any metric to view historical trends

---

### A5. End-to-End Verification Commands

**1. Watch MQTT broker receive messages (live):**

```bash
# Subscribe to all telemetry topics
mosquitto_sub -h localhost -p 1883 -t "factories/+/devices/+/telemetry" -v

# Or subscribe to specific factory only
mosquitto_sub -h localhost -p 1883 -t "factories/abc-manufacturing/devices/+/telemetry" -v
```

Expected output when device publishes:
```
factories/abc-manufacturing/devices/COMP_01/telemetry {"timestamp":"2026-02-19T08:30:00Z","metrics":{"voltage":231.4,"current":3.2}}
```

**2. Check telemetry service logs:**

```bash
# Follow logs in real-time
docker compose -f docker/docker-compose.yml logs -f telemetry

# Check for successful processing (look for these log lines):
docker compose -f docker/docker-compose.yml logs telemetry | grep "telemetry.processed"
```

✅ **Success indicators in logs:**
```json
{"event": "telemetry.processed", "factory_id": 3, "device_id": 15, "metric_count": 4}
{"event": "device.auto_registered", "factory_id": 3, "device_id": 15, "device_key": "COMP_01"}
{"event": "parameter.discovered", "factory_id": 3, "device_id": 15, "parameter": "voltage"}
```

❌ **Error indicators:**
```json
{"event": "telemetry.invalid_topic", "error": "Invalid topic format"}
{"event": "telemetry.invalid_payload", "error": "metrics cannot be empty"}
{"event": "telemetry.unknown_factory", "slug": "invalid-factory"}
```

**3. Query InfluxDB directly:**

```bash
# Enter InfluxDB container
docker compose -f docker/docker-compose.yml exec influxdb influx query '
from(bucket: "factoryops")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "device_metrics")
  |> filter(fn: (r) => r.factory_id == "3")
  |> filter(fn: (r) => r.device_id == "15")
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 10)
'
```

**4. Check MySQL for device + parameters:**

```bash
docker compose -f docker/docker-compose.yml exec mysql mysql -u factoryops -p factoryops -e "
SELECT d.id, d.device_key, d.name, d.last_seen, d.is_active,
       COUNT(DISTINCT p.id) as param_count
FROM devices d
LEFT JOIN device_parameters p ON d.id = p.device_id
WHERE d.factory_id = 3
GROUP BY d.id;
"
```

**5. Hit live KPI endpoint:**

```bash
# Get live KPI values (requires device ID from step 4)
curl -s -H "Authorization: Bearer [TOKEN]" \
  http://localhost:8000/api/v1/devices/15/kpis/live | jq
```

Expected response:
```json
{
  "device_id": 15,
  "timestamp": "2026-02-19T08:35:22.123456",
  "kpis": [
    {
      "parameter_key": "voltage",
      "display_name": "Line Voltage L1",
      "unit": "V",
      "value": 231.4,
      "is_stale": false
    },
    {
      "parameter_key": "current",
      "display_name": "Line Current L1",
      "unit": "A",
      "value": 3.2,
      "is_stale": false
    }
  ]
}
```

---

### A6. My Troubleshooting Guide

| Symptom | What to Check | Exact Command | Fix |
|---------|--------------|---------------|-----|
| **Device not appearing in UI** | Check telemetry logs for auto-registration | `docker compose logs telemetry \| grep auto_registered` | Verify topic format matches `factories/{slug}/devices/{key}/telemetry` |
| **Device not appearing** | Check if factory slug exists | `docker compose exec mysql mysql -e "SELECT slug FROM factories;"` | Create factory first via API |
| **Data in InfluxDB but not API** | Check parameter is_kpi_selected flag | `docker compose exec mysql mysql -e "SELECT parameter_key, is_kpi_selected FROM device_parameters WHERE device_id=15;"` | Set `is_kpi_selected=true` via PATCH API |
| **Parameters missing** | Check parameter discovery logs | `docker compose logs telemetry \| grep parameter.discovered` | Send message with all metric keys; they auto-discover on first message |
| **is_stale showing true** | Check last_seen timestamp vs current time | `docker compose exec mysql mysql -e "SELECT device_key, last_seen FROM devices WHERE id=15;"` | Device hasn't sent data in >10 minutes; check device connectivity |
| **MQTT not connecting** | Check EMQX is running | `docker compose ps emqx` | Start EMQX: `docker compose up -d emqx` |
| **MQTT not connecting** | Check port 1883 is accessible | `telnet localhost 1883` | Open firewall for port 1883 |
| **Invalid topic errors** | Check exact topic format | `mosquitto_sub -h localhost -p 1883 -t '#' -v` | Must be exactly 5 segments: `factories/{slug}/devices/{key}/telemetry` |
| **Invalid payload errors** | Check JSON format | `echo '{"metrics":{}}' \| jq .` | Metrics object must not be empty; values must be numbers (int or float) |
| **No alerts triggered** | Check rule is active and device assigned | `curl -H "Authorization: Bearer [TOKEN]" http://localhost:8000/api/v1/rules` | Ensure rule has `is_active=true` and device_id is in `device_ids` array |
| **High latency** | Check Redis cache hits | `docker compose logs telemetry \| grep cache_hit` | Cache miss is normal for first message; should hit on subsequent messages |
| **Memory issues** | Check InfluxDB write failures | `docker compose logs telemetry \| grep influx.write_failed` | May indicate InfluxDB disk full or connection issues |

**Quick diagnostic script:**

```bash
#!/bin/bash
echo "=== FactoryOps Diagnostic ==="
echo ""
echo "1. Container status:"
docker compose -f docker/docker-compose.yml ps

echo ""
echo "2. Factory list:"
docker compose -f docker/docker-compose.yml exec mysql mysql -u factoryops -p${MYSQL_PASSWORD} factoryops -e "SELECT id, slug, name FROM factories;" 2>/dev/null

echo ""
echo "3. Recent devices:"
docker compose -f docker/docker-compose.yml exec mysql mysql -u factoryops -p${MYSQL_PASSWORD} factoryops -e "SELECT device_key, name, last_seen FROM devices ORDER BY id DESC LIMIT 5;" 2>/dev/null

echo ""
echo "4. Telemetry log (last 20 lines):"
docker compose -f docker/docker-compose.yml logs --tail=20 telemetry 2>/dev/null

echo ""
echo "5. MQTT test:"
mosquitto_pub -h localhost -p 1883 -t "factories/vpc/devices/test/telemetry" -m '{"metrics":{"test":1}}' && echo "✓ MQTT publish successful" || echo "✗ MQTT publish failed"
```

---

## PART B: FOR FIRMWARE TEAM (Technical Specification)

### B1. Plain English Summary

**What you need to do:** Connect your device to our MQTT broker and publish JSON messages containing sensor readings to a specific topic. The platform will automatically create your device record, discover all parameters you're sending, and start showing live dashboards.

**What you do NOT need to do:** You don't need to pre-register devices, create API accounts, manage database entries, or handle authentication tokens. The MQTT connection is your only integration point.

**Key benefit:** Send one test message with your data, and you'll immediately see your device and metrics appear in the web dashboard at http://[factoryops-host]/devices.

---

### B2. MQTT Connection Details

| Setting | Value | Notes |
|---------|-------|-------|
| **Broker Host** | `emqx` (Docker internal) / `[PROD_IP]` (production) | For local dev use `localhost`. Production IP provided separately |
| **Port** | `1883` | Standard MQTT port (non-TLS). TLS port 8883 available on request |
| **Username** | *(empty)* | No authentication required in development |
| **Password** | *(empty)* | Production credentials provided separately |
| **Protocol Version** | MQTT v3.1.1 or v5.0 | Both supported by EMQX broker |
| **QoS Recommendation** | `1` | At-least-once delivery. QoS 0 acceptable for non-critical data |
| **Keep-Alive** | `60` seconds | Standard keep-alive interval |
| **Clean Session** | `true` | Start fresh session on reconnect |
| **Client ID** | Any unique string | Suggest: `{factory_slug}_{device_key}_{random}` |

**Connection string examples:**

```python
# Python (paho-mqtt)
client = mqtt.Client(client_id="abc_mfg_comp01_001")
client.connect("localhost", 1883, keepalive=60)

# mosquitto_pub CLI
mosquitto_pub -h localhost -p 1883 -t "factories/abc-manufacturing/devices/COMP_01/telemetry" -m '{...}'

# Node.js (mqtt)
const client = mqtt.connect('mqtt://localhost:1883', { keepalive: 60 });
```

---

### B3. Topic Format — Critical

**Exact format (from `telemetry/schemas.py` lines 26-50):**

```
factories/{factory_slug}/devices/{device_key}/telemetry
```

**Topic parsing logic (from code):**
```python
def parse_topic(topic: str) -> tuple[str, str]:
    parts = topic.split("/")
    
    if len(parts) != 5:
        raise ValueError(f"Invalid topic format: expected 5 segments, got {len(parts)}")
    
    if parts[0] != "factories":
        raise ValueError(f"Invalid topic format: expected 'factories' prefix")
    
    if parts[2] != "devices":
        raise ValueError(f"Invalid topic format: expected 'devices' segment")
    
    if parts[4] != "telemetry":
        raise ValueError(f"Invalid topic format: expected 'telemetry' suffix")
    
    return parts[1], parts[3]  # (factory_slug, device_key)
```

**Variable definitions:**

| Variable | What it is | Who provides it | Character Rules |
|----------|-----------|-----------------|-----------------|
| `factory_slug` | Factory identifier in URL format | Platform owner gives this to you | Max 100 chars, lowercase, alphanumeric + hyphens only |
| `device_key` | Unique device identifier | You create this following naming convention (see B6) | Max 100 chars, unique per factory, URL-safe characters |

**✅ Valid topic examples:**

```
factories/vpc/devices/M01/telemetry
factories/abc-manufacturing/devices/COMP_01/telemetry
factories/plant-1-mumbai/devices/PUMP_A_LINE_1/telemetry
factories/demo-factory/devices/motor_bearing_temp/telemetry
factories/test-facility/devices/SENSOR_001/telemetry
```

**❌ Invalid topic examples:**

```
factories/vpc/devices/M01                # Missing /telemetry suffix
factories/vpc/M01/telemetry              # Missing /devices segment
factory/vpc/devices/M01/telemetry        # Wrong prefix (factory vs factories)
vpc/devices/M01/telemetry                # Missing factories/ prefix
factories/vpc/devices/M01/extra/telemetry # Too many segments (6)
factories/vpc/devices/M 01/telemetry      # Space in device_key not recommended
factories/ABC-MANUFACTURING/devices/D1/telemetry  # Uppercase in slug (works but not best practice)
factories/vpc/devices/M01/TELEMETRY      # Wrong case (TELEMETRY vs telemetry) - CASE SENSITIVE
```

⚠️ **CRITICAL:** Topic parsing is case-sensitive. Use lowercase `telemetry`, not `TELEMETRY`.

---

### B4. JSON Payload — Exact Schema

**Schema definition (from `telemetry/schemas.py` lines 8-23):**

```python
class TelemetryPayload(BaseModel):
    timestamp: Optional[datetime] = None  # ISO8601 format
    metrics: Dict[str, Union[float, int]]  # Required, cannot be empty
```

**Field-by-field rules:**

| Field | Type | Required | Format | Notes |
|-------|------|----------|--------|-------|
| `timestamp` | string | No | ISO8601 with timezone | Example: `"2026-02-19T08:30:00Z"` or `"2026-02-19T08:30:00+05:30"`. If omitted, server uses current UTC time |
| `metrics` | object | **Yes** | Key-value pairs | Object with string keys and numeric values. Cannot be empty. Min 1 metric, max practical limit ~100 |

**Metric value rules:**
- Keys: String, alphanumeric + underscores recommended
- Values: Must be `integer` or `float` (JSON number type)
- ❌ NO strings: `"voltage": "231.4"` is INVALID
- ❌ NO booleans: `"status": true` is INVALID
- ❌ NO nulls: `"reading": null` is INVALID
- ✅ Numbers only: `"voltage": 231.4` is VALID

**Parameter discovery (from `telemetry/handlers/parameter_discovery.py` lines 11-64):**

Every metric key in your payload automatically becomes a parameter:
- Display name auto-generated: `voltage_l1` → `"Voltage L1"`
- Data type auto-detected: integer values → `"int"`, float values → `"float"`
- Marked as KPI by default: `is_kpi_selected = true`
- Only new keys trigger discovery; existing keys just update timestamp

**4 Complete Payload Examples:**

**Example 1: Power meter (voltage, current, power, frequency, power_factor)**
```json
{
  "timestamp": "2026-02-19T08:30:00Z",
  "metrics": {
    "voltage_l1": 231.4,
    "voltage_l2": 232.1,
    "voltage_l3": 230.8,
    "current_l1": 3.2,
    "current_l2": 3.1,
    "current_l3": 3.3,
    "power_total": 2205.6,
    "frequency": 50.01,
    "power_factor": 0.94
  }
}
```

**Example 2: Temperature and pressure sensor**
```json
{
  "timestamp": "2026-02-19T08:30:00+05:30",
  "metrics": {
    "temperature_inlet": 45.2,
    "temperature_outlet": 67.8,
    "pressure_suction": 2.4,
    "pressure_discharge": 8.7,
    "differential_pressure": 6.3
  }
}
```

**Example 3: Motor/pump (rpm, torque, vibration axes)**
```json
{
  "timestamp": "2026-02-19T08:30:00.123Z",
  "metrics": {
    "motor_rpm": 1750,
    "motor_torque": 124.5,
    "vibration_x": 2.3,
    "vibration_y": 1.8,
    "vibration_z": 4.1,
    "bearing_temp_drive": 58.2,
    "bearing_temp_nondrive": 55.1
  }
}
```

**Example 4: Minimal single-metric payload**
```json
{
  "metrics": {
    "sensor_reading": 42.0
  }
}
```
⚠️ Note: Without timestamp, server uses current UTC time.

---

### B5. Sending Frequency

**Recommended intervals by sensor type:**

| Sensor Type | Recommended Interval | Max Interval Before `is_stale=true` | Notes |
|-------------|---------------------|-------------------------------------|-------|
| Critical safety sensors | 100ms - 1s | 10 min | High-speed machinery protection |
| Process variables (temperature, pressure) | 5s - 30s | 10 min | Standard industrial monitoring |
| Energy meters | 1s - 5s | 10 min | Power quality monitoring |
| Vibration sensors | 1s - 10s | 10 min | Predictive maintenance |
| Environmental (humidity, ambient temp) | 1min - 5min | 10 min | HVAC, comfort monitoring |
| Status/indicators | On change only | 10 min | Binary state changes |

**One message per publish rule:**

⚠️ **CRITICAL:** Send exactly one JSON payload per MQTT publish. Do NOT batch multiple readings into arrays:

```json
// ❌ WRONG - Array of readings
{
  "readings": [
    {"timestamp": "2026-02-19T08:30:00Z", "voltage": 231.4},
    {"timestamp": "2026-02-19T08:30:01Z", "voltage": 231.5}
  ]
}

// ✅ CORRECT - One reading per publish
{"timestamp": "2026-02-19T08:30:00Z", "metrics": {"voltage": 231.4}}
{"timestamp": "2026-02-19T08:30:01Z", "metrics": {"voltage": 231.5}}
```

**Rate limiting:**

Currently, there is no explicit rate limiting. However:
- InfluxDB write batching happens automatically
- Database connection pooling may throttle very high rates (>1000 msg/sec)
- Recommended max: 100 messages/second per device
- If sending faster, consider local aggregation

---

### B6. Device Key Naming Convention

**Format:** `{MACHINE_TYPE}_{IDENTIFIER}`

| Machine Type | Key Format | Example |
|--------------|------------|---------|
| **Compressor** | `COMP_{number/line}` | `COMP_01`, `COMP_LINE_A` |
| **Pump** | `PUMP_{location/number}` | `PUMP_01`, `PUMP_CIRC_1` |
| **Motor** | `MOTOR_{location}` | `MOTOR_B1`, `MOTOR_CONVEYOR_1` |
| **Generator** | `GEN_{number}` | `GEN_01`, `GEN_BACKUP_A` |
| **Heat Exchanger** | `HX_{service}` | `HX_COOLING_1`, `HX_OIL` |
| **Sensor** | `SENSOR_{location}` | `SENSOR_ZONE_A_TEMP`, `SENSOR_AMBIENT_1` |

**Device key rules (from `backend/app/models/device.py` line 17):**
- Maximum 100 characters
- Must be unique within the factory
- URL-safe characters: alphanumeric, hyphens, underscores
- Case-sensitive: `COMP_01` ≠ `comp_01`
- Suggestion: Use uppercase for consistency

⚠️ **WARNING: Never change device key after data starts flowing**

**Why:** The device key is part of the MQTT topic and is used to identify the device record in the database. Changing it will:
1. Create a NEW device record (orphaning old data)
2. Break historical continuity
3. Require reconfiguration of all rules and alerts
4. Split your data across two device IDs in InfluxDB

If you must rename, deactivate the old device and create a new one with proper naming.

---

### B7. What Happens Automatically

When you send your first message, the platform automatically:

✅ **Device Auto-Registration:**
- Device record created in MySQL with `is_active=true`
- Device appears in web UI immediately
- `last_seen` timestamp updated on every message

✅ **Parameter Discovery:**
- Each unique metric key creates a parameter record
- Display name auto-generated from key (snake_case → Title Case)
- Data type detected (int vs float)
- Parameter marked as KPI (`is_kpi_selected=true`)
- All parameters appear in device detail page

✅ **Data Storage:**
- Every metric written to InfluxDB time-series database
- Data retention: Configurable (default unlimited)
- Compression: Automatic per InfluxDB

✅ **Live Dashboard:**
- KPI dashboard auto-populates with discovered parameters
- Real-time values update as messages arrive
- Historical charts available immediately

✅ **Health Monitoring:**
- Device marked "Online" when receiving data within 10 minutes
- Device marked "Offline" when no data for 10+ minutes
- Health score calculated based on online status and alerts

✅ **Rule Evaluation:**
- Every message triggers rule engine evaluation
- Alerts created automatically when conditions match
- Notifications sent via configured channels

---

### B8. Test Script — Python

**Complete working Python script to verify connection:**

```python
#!/usr/bin/env python3
"""
FactoryOps MQTT Connection Test Script
Tests connectivity and publishes sample telemetry data.
"""

import json
import time
import sys
import random
from datetime import datetime, timezone

# Install paho-mqtt: pip install paho-mqtt
import paho.mqtt.client as mqtt

# === CONFIGURATION (Fill these in) ===
MQTT_BROKER = "localhost"  # Change to production IP when provided
MQTT_PORT = 1883
FACTORY_SLUG = "abc-manufacturing"  # Replace with your factory slug
DEVICE_KEY = "COMP_01"  # Replace with your device key
# =====================================

TOPIC = f"factories/{FACTORY_SLUG}/devices/{DEVICE_KEY}/telemetry"

# Connection state
connected = False
connection_error = None

def on_connect(client, userdata, flags, rc):
    """Callback for when client receives CONNACK from broker."""
    global connected, connection_error
    
    if rc == 0:
        connected = True
        print(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        print(f"   Client ID: {client._client_id.decode()}")
    else:
        connection_error = f"Connection failed with code {rc}"
        print(f"❌ Connection failed with code {rc}")
        # Error codes: 1=incorrect protocol, 2=invalid client ID, 3=server unavailable, 
        # 4=bad credentials, 5=not authorized

def on_disconnect(client, userdata, rc):
    """Callback for when client disconnects from broker."""
    global connected
    connected = False
    if rc != 0:
        print(f"⚠️ Unexpected disconnection (code {rc})")

def on_publish(client, userdata, mid):
    """Callback for when message is published."""
    print(f"✅ Message {mid} published successfully")

def create_payload():
    """Create a sample telemetry payload."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "voltage": round(220 + random.uniform(-10, 15), 1),
            "current": round(5 + random.uniform(-1, 2), 2),
            "power": round(1100 + random.uniform(-100, 200), 1),
            "temperature": round(45 + random.uniform(-5, 10), 1)
        }
    }

def main():
    print("=" * 60)
    print("FactoryOps MQTT Connection Test")
    print("=" * 60)
    print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Topic: {TOPIC}")
    print("=" * 60)
    
    # Create client with unique ID
    client_id = f"{FACTORY_SLUG}_{DEVICE_KEY}_test_{int(time.time())}"
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    
    # Enable logging for debugging
    # client.enable_logger()
    
    try:
        # Connect with 60s keepalive
        print(f"\n📡 Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        
        # Start network loop
        client.loop_start()
        
        # Wait for connection (max 10 seconds)
        timeout = 10
        while not connected and timeout > 0 and not connection_error:
            time.sleep(0.5)
            timeout -= 0.5
        
        if not connected:
            print("❌ Connection timeout")
            return 1
        
        if connection_error:
            print(f"❌ {connection_error}")
            return 1
        
        # Publish test messages
        print(f"\n📤 Publishing to topic: {TOPIC}")
        print("-" * 60)
        
        for i in range(3):
            payload = create_payload()
            payload_json = json.dumps(payload)
            
            print(f"\nMessage {i+1}:")
            print(f"  Payload: {payload_json}")
            
            # Publish with QoS 1 (at-least-once delivery)
            result = client.publish(TOPIC, payload_json, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"  Status: Queued for delivery (mid={result.mid})")
            else:
                print(f"  Status: Failed to queue (code={result.rc})")
            
            time.sleep(2)  # Wait between messages
        
        # Wait for publishes to complete
        time.sleep(2)
        
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print("=" * 60)
        print(f"\nNext steps:")
        print(f"1. Check web UI: http://[factoryops-host]/devices")
        print(f"2. Look for device: {DEVICE_KEY}")
        print(f"3. Verify parameters: voltage, current, power, temperature")
        print(f"4. Report back to platform owner with:")
        print(f"   - Device key used: {DEVICE_KEY}")
        print(f"   - Messages sent: 3")
        print(f"   - Any errors seen: None")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    finally:
        client.loop_stop()
        client.disconnect()
        print("\n🔌 Disconnected")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**Installation:**
```bash
# Install required library
pip install paho-mqtt

# Run the test
python3 mqtt_test.py
```

**Expected output on success:**
```
============================================================
FactoryOps MQTT Connection Test
============================================================
Broker: localhost:1883
Topic: factories/abc-manufacturing/devices/COMP_01/telemetry
============================================================

📡 Connecting to localhost:1883...
✅ Connected to MQTT broker at localhost:1883
   Client ID: abc-manufacturing_COMP_01_test_1708341234

📤 Publishing to topic: factories/abc-manufacturing/devices/COMP_01/telemetry
------------------------------------------------------------

Message 1:
  Payload: {"timestamp": "2026-02-19T08:30:00+00:00", "metrics": {"voltage": 231.4, ...}}
  Status: Queued for delivery (mid=1)
✅ Message 1 published successfully

...

============================================================
✅ Test completed successfully!
============================================================
```

---

### B9. Common Mistakes Table

| ❌ Wrong | ✅ Correct | Why it fails |
|----------|-----------|--------------|
| `factories/vpc/devices/M01/data` | `factories/vpc/devices/M01/telemetry` | Topic must end with `telemetry`, not `data` |
| `"voltage": "231.4"` (string) | `"voltage": 231.4` (number) | Values must be numeric; strings rejected by schema validation |
| `TELEMETRY` (uppercase) | `telemetry` (lowercase) | Topic parsing is case-sensitive |
| Batch array: `{"readings": [{...}, {...}]}` | One message per reading | Schema expects flat metrics object, not arrays |
| `"temperature_celsius"` | `"temperature"` | Don't put units in metric names; use parameter `unit` field instead |
| `"2026-02-19 08:30:00"` (no timezone) | `"2026-02-19T08:30:00Z"` or `"2026-02-19T08:30:00+05:30"` | Use ISO8601 format with explicit timezone. Server assumes UTC if omitted |
| Empty metrics: `{"metrics": {}}` | At least one metric: `{"metrics": {"status": 1}}` | Metrics object cannot be empty - will fail validation |
| `5 segments` vs `4 segments` | Must be exactly 5 segments with `/` separator | Parser strictly checks segment count |
| `device key` with spaces: `M 01` | URL-safe: `M01` or `M_01` | Spaces may cause topic parsing issues |
| `null` values: `"reading": null` | Omit the key or use `0` | Null values fail numeric validation |
| Changing device key after start | Keep same key forever | Creates new device record, splits historical data |

---

### B10. Checklist of What I Will Give Them

Before firmware team can connect, provide them with:

**Network Configuration:**
- [ ] MQTT broker IP address (production)
- [ ] Port number (1883 or 8883 for TLS)
- [ ] Network requirements (VPN, firewall rules)
- [ ] TLS certificate (if using TLS)

**Factory Details:**
- [ ] Factory slug (exact string, e.g., `abc-manufacturing`)
- [ ] Factory timezone (IANA format, e.g., `Asia/Kolkata`)

**Authentication (if enabled):**
- [ ] MQTT username
- [ ] MQTT password
- [ ] Client ID prefix (optional)

**Device Assignment:**
- [ ] List of approved device keys
- [ ] Machine type for each device
- [ ] Expected metrics/parameters per device

**Testing:**
- [ ] Test topic to use (format example)
- [ ] Platform owner contact for troubleshooting
- [ ] Web UI URL for verification

**Documentation:**
- [ ] This SENSOR_ONBOARDING.md document
- [ ] Network diagram (if complex)
- [ ] Emergency escalation contacts

---

## PART C: EMAIL TEMPLATE

**Subject:** FactoryOps MQTT Integration - Technical Specification for [FACTORY_NAME]

---

Dear Firmware Team,

I am setting up our factory equipment monitoring on FactoryOps, an industrial IoT platform that provides real-time dashboards, automated alerting, and predictive analytics for factory equipment.

**What you need to implement:**

1. Connect your device to our MQTT broker and publish sensor readings
2. Use the exact topic format and JSON payload structure specified below
3. Run the provided Python test script to verify connectivity
4. Report back confirmation that data is appearing in the dashboard

**You do NOT need to:**
- Create any API accounts or manage authentication tokens
- Pre-register devices in any system
- Handle database operations
- Build any UI components

---

**MQTT Connection Details:**

```
Broker Host: [BROKER_IP_PLACEHOLDER]
Port: 1883 (or 8883 for TLS)
Protocol: MQTT v3.1.1 or v5.0
QoS: 1 (recommended)
Keep-Alive: 60 seconds
Clean Session: true
```

⚠️ **Note:** Username/password authentication: [AUTH_DETAILS_PLACEHOLDER]

---

**Exact Topic Format:**

```
factories/[FACTORY_SLUG_PLACEHOLDER]/devices/{device_key}/telemetry
```

Replace `{device_key}` with your assigned device identifier following the naming convention provided separately.

**Your factory slug is:** `[FACTORY_SLUG_PLACEHOLDER]`

**Example topic for device "COMP_01":**
```
factories/[FACTORY_SLUG_PLACEHOLDER]/devices/COMP_01/telemetry
```

---

**JSON Payload Format:**

```json
{
  "timestamp": "2026-02-19T08:30:00Z",
  "metrics": {
    "voltage_l1": 231.4,
    "current_l1": 3.2,
    "power_total": 745.6,
    "frequency": 50.01
  }
}
```

**Field requirements:**
- `timestamp`: ISO8601 format with timezone (optional, server uses UTC if omitted)
- `metrics`: Object containing numeric values only (required, cannot be empty)
- Metric names: Use snake_case (e.g., `motor_temperature` not `Motor Temperature`)
- Values: Must be numbers (int or float), NOT strings

---

**Python Test Script:**

Save this as `test_mqtt.py`, update the configuration section, and run it:

```python
#!/usr/bin/env python3
import json
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

# CONFIGURATION
MQTT_BROKER = "[BROKER_IP_PLACEHOLDER]"
MQTT_PORT = 1883
FACTORY_SLUG = "[FACTORY_SLUG_PLACEHOLDER]"
DEVICE_KEY = "[YOUR_DEVICE_KEY_PLACEHOLDER]"
TOPIC = f"factories/{FACTORY_SLUG}/devices/{DEVICE_KEY}/telemetry"

client = mqtt.Client(client_id=f"{DEVICE_KEY}_test")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

payload = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "metrics": {
        "voltage": 231.4,
        "current": 3.2,
        "test_metric": 42.0
    }
}

print(f"Publishing to: {TOPIC}")
print(f"Payload: {json.dumps(payload)}")
client.publish(TOPIC, json.dumps(payload), qos=1)
print("Message sent!")
client.disconnect()
```

**Install dependency:** `pip install paho-mqtt`

---

**What to report back:**

After running the test script, please confirm:

1. Did the script complete without errors? (Yes/No)
2. What device key did you use for testing?
3. What metrics did you include in the test payload?
4. Did you see the device appear in the dashboard at [UI_URL_PLACEHOLDER]?
5. Any error messages or issues encountered?

**Timeline:**

Please complete testing and report back by [DATE_PLACEHOLDER].

---

**Questions or Issues:**

Contact me directly:
- Email: [YOUR_EMAIL_PLACEHOLDER]
- Phone: [YOUR_PHONE_PLACEHOLDER]
- Slack/Teams: [YOUR_HANDLE_PLACEHOLDER]

For technical troubleshooting, include:
- Error messages (copy-paste)
- Screenshot of terminal output
- Device type and firmware version
- Network configuration details

---

Best regards,

[YOUR_NAME_PLACEHOLDER]  
[YOUR_TITLE_PLACEHOLDER]  
[COMPANY_NAME_PLACEHOLDER]

---

**Attachments:**
- SENSOR_ONBOARDING.md (complete technical specification)
- Network diagram (if applicable)
- TLS certificates (if using encrypted connection)

---

*This integration will enable real-time monitoring of your equipment, automated alerts for anomalies, and historical trend analysis for predictive maintenance.*
