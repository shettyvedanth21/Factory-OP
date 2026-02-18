"""Alert repository for database operations."""
from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert


async def get_active_count_by_device(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
) -> int:
    """Get count of active (unresolved) alerts for a device."""
    result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.factory_id == factory_id,
            Alert.device_id == device_id,
            Alert.resolved_at.is_(None),
        )
    )
    return result.scalar() or 0


async def get_active_count_by_factory(
    db: AsyncSession,
    factory_id: int,
) -> int:
    """Get count of active alerts for a factory."""
    result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.factory_id == factory_id,
            Alert.resolved_at.is_(None),
        )
    )
    return result.scalar() or 0


async def get_critical_count_by_factory(
    db: AsyncSession,
    factory_id: int,
) -> int:
    """Get count of critical active alerts for a factory."""
    result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.factory_id == factory_id,
            Alert.resolved_at.is_(None),
            Alert.severity == "critical",
        )
    )
    return result.scalar() or 0


async def get_recent_alerts(
    db: AsyncSession,
    factory_id: int,
    limit: int = 5,
) -> List[Alert]:
    """Get recent alerts for a factory."""
    result = await db.execute(
        select(Alert)
        .where(Alert.factory_id == factory_id)
        .order_by(Alert.triggered_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
