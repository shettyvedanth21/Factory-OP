"""Telemetry service configuration."""
import os
from typing import Optional


# Database
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "factoryops")
MYSQL_USER = os.getenv("MYSQL_USER", "factoryops")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "factoryops_dev")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

# InfluxDB
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "factoryops-dev-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "factoryops")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "factoryops")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# MQTT
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "emqx")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME") or None
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD") or None

# Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")

# App
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
