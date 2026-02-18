"""MQTT subscriber for telemetry ingestion."""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiomqtt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from structlog import get_logger

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import configure_logging, get_logger as app_get_logger
from telemetry.handlers.ingestion import process_telemetry

# Configure logging
configure_logging()
logger = app_get_logger(__name__)


@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def redis_client() -> AsyncGenerator[Redis, None]:
    """Async context manager for Redis client."""
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.close()


@asynccontextmanager
async def influx_write_api() -> AsyncGenerator:
    """Async context manager for InfluxDB write API."""
    client = InfluxDBClientAsync(
        url=settings.influxdb_url,
        token=settings.influxdb_token,
        org=settings.influxdb_org,
    )
    try:
        write_api = client.write_api()
        yield write_api
    finally:
        await client.close()


async def start():
    """Start the MQTT subscriber with reconnection logic."""
    retry_delay = 1
    
    while True:
        try:
            async with aiomqtt.Client(
                hostname=settings.mqtt_broker_host,
                port=settings.mqtt_broker_port,
                username=settings.mqtt_username or None,
                password=settings.mqtt_password or None,
            ) as client:
                retry_delay = 1  # Reset on successful connection
                logger.info(
                    "mqtt.connected",
                    host=settings.mqtt_broker_host,
                    port=settings.mqtt_broker_port,
                )
                
                await client.subscribe("factories/+/devices/+/telemetry")
                logger.info(
                    "mqtt.subscribed",
                    topic="factories/+/devices/+/telemetry",
                )

                async with db_session() as db, redis_client() as redis:
                    async with influx_write_api() as write_api:
                        async for message in client.messages:
                            await process_telemetry(
                                topic=message.topic,
                                payload=message.payload,
                                db=db,
                                redis=redis,
                                influx_write_api=write_api,
                            )

        except aiomqtt.MqttError as e:
            logger.error(
                "mqtt.disconnected",
                error=str(e),
                error_type=type(e).__name__,
                retry_in=retry_delay,
            )
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)  # Exponential backoff, max 60s

        except Exception as e:
            logger.error(
                "mqtt.unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
                retry_in=retry_delay,
            )
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)
