"""Parameter repository for database operations."""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_parameter import DeviceParameter
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_all(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
) -> List[DeviceParameter]:
    """Get all parameters for a device within factory scope."""
    result = await db.execute(
        select(DeviceParameter).where(
            DeviceParameter.factory_id == factory_id,
            DeviceParameter.device_id == device_id,
        )
    )
    return list(result.scalars().all())


async def get_selected_keys(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
) -> List[str]:
    """Get keys of selected KPI parameters for a device."""
    result = await db.execute(
        select(DeviceParameter.parameter_key).where(
            DeviceParameter.factory_id == factory_id,
            DeviceParameter.device_id == device_id,
            DeviceParameter.is_kpi_selected == True,
        )
    )
    return [row[0] for row in result.all()]


async def get_by_id(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
    param_id: int,
) -> Optional[DeviceParameter]:
    """Get parameter by ID within factory and device scope."""
    result = await db.execute(
        select(DeviceParameter).where(
            DeviceParameter.factory_id == factory_id,
            DeviceParameter.device_id == device_id,
            DeviceParameter.id == param_id,
        )
    )
    return result.scalar_one_or_none()


async def update(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
    param_id: int,
    data: dict,
) -> Optional[DeviceParameter]:
    """Update parameter display name, unit, or KPI selection."""
    param = await get_by_id(db, factory_id, device_id, param_id)
    if not param:
        return None
    
    # Update fields
    for field in ["display_name", "unit", "is_kpi_selected"]:
        if field in data:
            setattr(param, field, data[field])
    
    await db.commit()
    await db.refresh(param)
    
    logger.info(
        "parameter.updated",
        factory_id=factory_id,
        device_id=device_id,
        param_id=param_id,
        param_key=param.parameter_key,
    )
    
    return param
