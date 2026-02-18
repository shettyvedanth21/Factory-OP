"""Cache layer for factory and device lookups."""
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import json
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.models.factory import Factory
from app.models.device import Device

logger = get_logger(__name__)

CACHE_TTL_SECONDS = 60


def factory_to_dict(factory: Factory) -> dict:
    """Convert Factory model to dict for caching."""
    return {
        "id": factory.id,
        "name": factory.name,
        "slug": factory.slug,
        "timezone": factory.timezone,
    }


def device_to_dict(device: Device) -> dict:
    """Convert Device model to dict for caching."""
    return {
        "id": device.id,
        "factory_id": device.factory_id,
        "device_key": device.device_key,
        "name": device.name,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "region": device.region,
        "is_active": device.is_active,
    }


def dict_to_factory(data: dict) -> Factory:
    """Convert dict to Factory model."""
    factory = Factory(
        id=data["id"],
        name=data["name"],
        slug=data["slug"],
        timezone=data.get("timezone", "UTC"),
    )
    return factory


def dict_to_device(data: dict) -> Device:
    """Convert dict to Device model."""
    device = Device(
        id=data["id"],
        factory_id=data["factory_id"],
        device_key=data["device_key"],
        name=data.get("name"),
        manufacturer=data.get("manufacturer"),
        model=data.get("model"),
        region=data.get("region"),
        is_active=data.get("is_active", True),
    )
    return device


async def get_factory_by_slug(
    redis: Redis,
    db: AsyncSession,
    slug: str
) -> Optional[Factory]:
    """
    Get factory by slug with Redis caching.
    
    Args:
        redis: Redis client
        db: Database session
        slug: Factory slug
    
    Returns:
        Factory or None if not found
    """
    cache_key = f"factory:slug:{slug}"
    
    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        try:
            data = json.loads(cached)
            logger.debug("factory.cache_hit", slug=slug)
            return dict_to_factory(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("factory.cache_decode_failed", slug=slug, error=str(e))
            await redis.delete(cache_key)
    
    # Query database
    result = await db.execute(select(Factory).where(Factory.slug == slug))
    factory = result.scalar_one_or_none()
    
    if factory:
        # Cache the result
        await redis.setex(
            cache_key,
            CACHE_TTL_SECONDS,
            json.dumps(factory_to_dict(factory))
        )
        logger.debug("factory.cache_set", slug=slug, factory_id=factory.id)
    else:
        logger.warning("factory.not_found", slug=slug)
    
    return factory


async def get_or_create_device(
    redis: Redis,
    db: AsyncSession,
    factory_id: int,
    device_key: str
) -> Device:
    """
    Get existing device or auto-register new one.
    
    Args:
        redis: Redis client
        db: Database session
        factory_id: Factory ID
        device_key: Device key from MQTT topic
    
    Returns:
        Device (existing or newly created)
    """
    cache_key = f"device:{factory_id}:{device_key}"
    
    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        try:
            data = json.loads(cached)
            logger.debug("device.cache_hit", factory_id=factory_id, device_key=device_key)
            return dict_to_device(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("device.cache_decode_failed", factory_id=factory_id, device_key=device_key, error=str(e))
            await redis.delete(cache_key)
    
    # Query database
    result = await db.execute(
        select(Device).where(
            Device.factory_id == factory_id,
            Device.device_key == device_key
        )
    )
    device = result.scalar_one_or_none()
    
    if not device:
        # Auto-register new device
        device = Device(
            factory_id=factory_id,
            device_key=device_key,
            is_active=True,
        )
        db.add(device)
        await db.commit()
        await db.refresh(device)
        
        logger.info(
            "device.auto_registered",
            factory_id=factory_id,
            device_id=device.id,
            device_key=device_key,
        )
    
    # Cache the device
    await redis.setex(
        cache_key,
        CACHE_TTL_SECONDS,
        json.dumps(device_to_dict(device))
    )
    logger.debug("device.cache_set", factory_id=factory_id, device_id=device.id, device_key=device_key)
    
    return device
