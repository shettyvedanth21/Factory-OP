"""Device service with business logic."""
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import device_repo, parameter_repo, alert_repo
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceListItem, DeviceResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

# Health calculation constants
ONLINE_THRESHOLD_MINUTES = 10
HEALTH_BASE_SCORE = 100
HEALTH_PENALTY_PER_ALERT = 10


def _is_device_online(last_seen: Optional[datetime]) -> bool:
    """Check if device is considered online (last seen within threshold)."""
    if not last_seen:
        return False
    
    # Handle timezone-aware vs naive datetimes
    now = datetime.utcnow()
    if last_seen.tzinfo:
        now = datetime.now(last_seen.tzinfo)
    
    threshold = now - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
    return last_seen > threshold


def _calculate_health_score(is_online: bool, active_alert_count: int) -> int:
    """Calculate device health score."""
    if not is_online:
        return 0
    
    score = HEALTH_BASE_SCORE - (active_alert_count * HEALTH_PENALTY_PER_ALERT)
    return max(0, score)


async def list_devices(
    db: AsyncSession,
    factory_id: int,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Tuple[List[DeviceListItem], int]:
    """
    List devices with computed fields.
    
    Returns:
        Tuple of (device list items, total count)
    """
    devices, total = await device_repo.get_all(
        db, factory_id, page, per_page, search, is_active
    )
    
    device_items = []
    for device in devices:
        # Get active alert count
        alert_count = await alert_repo.get_active_count_by_device(
            db, factory_id, device.id
        )
        
        # Calculate health score
        is_online = _is_device_online(device.last_seen)
        health_score = _calculate_health_score(is_online, alert_count)
        
        # TODO: Calculate current_energy_kw from InfluxDB
        current_energy_kw = 0.0  # Placeholder
        
        device_items.append(DeviceListItem(
            id=device.id,
            device_key=device.device_key,
            name=device.name,
            manufacturer=device.manufacturer,
            model=device.model,
            region=device.region,
            is_active=device.is_active,
            last_seen=device.last_seen,
            health_score=health_score,
            current_energy_kw=current_energy_kw,
            active_alert_count=alert_count,
        ))
    
    return device_items, total


async def get_device(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
) -> Optional[DeviceResponse]:
    """Get device detail with parameters."""
    device = await device_repo.get_by_id(db, factory_id, device_id)
    if not device:
        return None
    
    # Get parameters
    parameters = await parameter_repo.get_all(db, factory_id, device_id)
    
    # Convert to response
    return DeviceResponse(
        id=device.id,
        device_key=device.device_key,
        name=device.name,
        manufacturer=device.manufacturer,
        model=device.model,
        region=device.region,
        is_active=device.is_active,
        last_seen=device.last_seen,
        api_key=device.api_key,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


async def create_device(
    db: AsyncSession,
    factory_id: int,
    data: DeviceCreate,
) -> DeviceResponse:
    """Create a new device with generated API key."""
    # Generate API key
    api_key = secrets.token_urlsafe(32)
    
    # Create device data dict
    device_data = data.model_dump()
    device_data["api_key"] = api_key
    
    device = await device_repo.create(db, factory_id, device_data)
    
    return DeviceResponse(
        id=device.id,
        device_key=device.device_key,
        name=device.name,
        manufacturer=device.manufacturer,
        model=device.model,
        region=device.region,
        is_active=device.is_active,
        last_seen=device.last_seen,
        api_key=device.api_key,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


async def update_device(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
    data: DeviceUpdate,
) -> Optional[DeviceResponse]:
    """Update device metadata."""
    device = await device_repo.update(db, factory_id, device_id, data.model_dump(exclude_unset=True))
    if not device:
        return None
    
    return DeviceResponse(
        id=device.id,
        device_key=device.device_key,
        name=device.name,
        manufacturer=device.manufacturer,
        model=device.model,
        region=device.region,
        is_active=device.is_active,
        last_seen=device.last_seen,
        api_key=device.api_key,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


async def delete_device(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
) -> bool:
    """Soft delete device (set is_active=False)."""
    device = await device_repo.soft_delete(db, factory_id, device_id)
    return device is not None
