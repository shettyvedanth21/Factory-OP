"""Device repository for database operations."""
from typing import List, Optional, Tuple

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_all(
    db: AsyncSession,
    factory_id: int,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Tuple[List[Device], int]:
    """
    Get all devices for a factory with pagination.
    
    Returns:
        Tuple of (devices list, total count)
    """
    # Build base query with factory filter
    query = select(Device).where(Device.factory_id == factory_id)
    count_query = select(func.count(Device.id)).where(Device.factory_id == factory_id)
    
    # Apply filters
    if search:
        search_filter = Device.device_key.ilike(f"%{search}%") | Device.name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    if is_active is not None:
        query = query.where(Device.is_active == is_active)
        count_query = count_query.where(Device.is_active == is_active)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
    return list(devices), total


async def get_by_id(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
) -> Optional[Device]:
    """Get device by ID within factory scope."""
    result = await db.execute(
        select(Device).where(
            Device.factory_id == factory_id,
            Device.id == device_id,
        )
    )
    return result.scalar_one_or_none()


async def get_by_key(
    db: AsyncSession,
    factory_id: int,
    device_key: str,
) -> Optional[Device]:
    """Get device by device_key within factory scope."""
    result = await db.execute(
        select(Device).where(
            Device.factory_id == factory_id,
            Device.device_key == device_key,
        )
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    factory_id: int,
    data: dict,
) -> Device:
    """Create a new device."""
    device = Device(
        factory_id=factory_id,
        device_key=data["device_key"],
        name=data.get("name"),
        manufacturer=data.get("manufacturer"),
        model=data.get("model"),
        region=data.get("region"),
        is_active=True,
    )
    
    db.add(device)
    await db.commit()
    await db.refresh(device)
    
    logger.info(
        "device.created",
        factory_id=factory_id,
        device_id=device.id,
        device_key=device.device_key,
    )
    
    return device


async def update(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
    data: dict,
) -> Optional[Device]:
    """Update device metadata."""
    device = await get_by_id(db, factory_id, device_id)
    if not device:
        return None
    
    # Update fields
    for field in ["name", "manufacturer", "model", "region", "is_active"]:
        if field in data:
            setattr(device, field, data[field])
    
    await db.commit()
    await db.refresh(device)
    
    logger.info(
        "device.updated",
        factory_id=factory_id,
        device_id=device_id,
    )
    
    return device


async def update_last_seen(
    db: AsyncSession,
    device_id: int,
    timestamp,
) -> None:
    """Update device last_seen timestamp."""
    await db.execute(
        update(Device)
        .where(Device.id == device_id)
        .values(last_seen=timestamp)
    )
    await db.commit()


async def soft_delete(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
) -> Optional[Device]:
    """Soft delete device by setting is_active=False."""
    device = await get_by_id(db, factory_id, device_id)
    if not device:
        return None
    
    device.is_active = False
    await db.commit()
    await db.refresh(device)
    
    logger.info(
        "device.deactivated",
        factory_id=factory_id,
        device_id=device_id,
    )
    
    return device
