"""Application settings using pydantic-settings."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_url: str = "http://localhost"
    log_level: str = "INFO"

    # MySQL
    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_database: str = "factoryops"
    mysql_user: str = "factoryops"
    mysql_password: str = "factoryops_dev"
    database_url: str = "mysql+aiomysql://factoryops:factoryops_dev@mysql:3306/factoryops"

    # InfluxDB
    influxdb_url: str = "http://influxdb:8086"
    influxdb_token: str = "factoryops-dev-token"
    influxdb_org: str = "factoryops"
    influxdb_bucket: str = "factoryops"
    influxdb_username: str = "admin"
    influxdb_password: str = "admin12345"

    # Redis
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "factoryops"
    minio_secure: bool = False

    # MQTT
    mqtt_broker_host: str = "emqx"
    mqtt_broker_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None

    # JWT
    jwt_secret_key: str = "change-this-in-production-min-32-characters-long"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # SMTP (optional)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: str = "noreply@factoryops.local"

    # Twilio (optional)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_from: Optional[str] = None


settings = Settings()
