"""Main telemetry processing pipeline."""
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from datetime import datetime
from typing import Dict, Any

from redis.asyncio import Redis
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from influxdb_client.client.write_api import WriteApi
from pydantic import ValidationError
from structlog import get_logger

from telemetry.schemas import TelemetryPayload, parse_topic
from telemetry.handlers.cache import get_factory_by_slug, get_or_create_device
from telemetry.handlers.parameter_discovery import discover_parameters
from telemetry.handlers.influx_writer import build_points, write_batch
from app.models.device import Device

logger = get_logger(__name__)


async def process_telemetry(
    topic: str,
    payload: bytes,
    db: AsyncSession,
    redis: Redis,
    influx_write_api: WriteApi,
) -> None:
    """
    Main telemetry processing pipeline.
    
    MUST catch all exceptions — never raise.
    All steps are async and non-blocking where possible.
    """
    try:
        # 1. Parse topic
        try:
            factory_slug, device_key = parse_topic(str(topic))
        except ValueError as e:
            logger.warning("telemetry.invalid_topic", topic=str(topic), error=str(e))
            return

        # 2. Parse and validate payload
        try:
            data = TelemetryPayload.model_validate_json(payload)
        except ValidationError as e:
            logger.warning("telemetry.invalid_payload", topic=str(topic), error=str(e))
            return
        
        timestamp = data.timestamp or datetime.utcnow()

        # 3. Resolve factory (from cache)
        factory = await get_factory_by_slug(redis, db, factory_slug)
        if not factory:
            logger.warning("telemetry.unknown_factory", slug=factory_slug, topic=str(topic))
            return

        # 4. Get or create device (from cache)
        device = await get_or_create_device(redis, db, factory.id, device_key)

        # 5. Discover new parameters
        await discover_parameters(db, factory.id, device.id, data.metrics)

        # 6. Build and write InfluxDB points
        points = build_points(factory.id, device.id, data.metrics, timestamp)
        if points:
            await write_batch(influx_write_api, points)

        # 7. Update device last_seen (fire-and-forget, don't await failure)
        try:
            await db.execute(
                update(Device).where(Device.id == device.id).values(last_seen=timestamp)
            )
            await db.commit()
        except Exception as e:
            logger.warning("telemetry.last_seen_update_failed", device_id=device.id, error=str(e))

        # 8. Dispatch rule evaluation (non-blocking)
        try:
            from app.workers.rule_engine import evaluate_rules_task
            evaluate_rules_task.delay(
                factory_id=factory.id,
                device_id=device.id,
                metrics=data.metrics,
                timestamp=timestamp.isoformat(),
            )
        except Exception as e:
            logger.warning("telemetry.rule_dispatch_failed", factory_id=factory.id, error=str(e))

        logger.info(
            "telemetry.processed",
            factory_id=factory.id,
            device_id=device.id,
            factory_slug=factory_slug,
            device_key=device_key,
            metric_count=len(data.metrics),
        )

    except Exception as e:
        # Final safety net — log and continue, never propagate
        logger.error(
            "telemetry.unhandled_error",
            topic=str(topic),
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
