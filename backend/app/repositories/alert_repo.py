"""Alert repository for database operations."""
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, RuleCooldown


async def create_alert(
    db: AsyncSession,
    factory_id: int,
    rule_id: int,
    device_id: int,
    triggered_at: datetime,
    severity: str,
    message: str,
    telemetry_snapshot: Optional[dict],
) -> Alert:
    """Create a new alert."""
    alert = Alert(
        factory_id=factory_id,
        rule_id=rule_id,
        device_id=device_id,
        triggered_at=triggered_at,
        severity=severity,
        message=message,
        telemetry_snapshot=telemetry_snapshot,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


async def get_all(
    db: AsyncSession,
    factory_id: int,
    device_id: Optional[int] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Alert], int]:
    """Get all alerts for a factory with filtering and pagination."""
    query = select(Alert).where(Alert.factory_id == factory_id)
    count_query = select(func.count(Alert.id)).where(Alert.factory_id == factory_id)
    
    if device_id is not None:
        query = query.where(Alert.device_id == device_id)
        count_query = count_query.where(Alert.device_id == device_id)
    
    if severity is not None:
        query = query.where(Alert.severity == severity)
        count_query = count_query.where(Alert.severity == severity)
    
    if resolved is not None:
        if resolved:
            query = query.where(Alert.resolved_at.isnot(None))
            count_query = count_query.where(Alert.resolved_at.isnot(None))
        else:
            query = query.where(Alert.resolved_at.is_(None))
            count_query = count_query.where(Alert.resolved_at.is_(None))
    
    if start is not None:
        query = query.where(Alert.triggered_at >= start)
        count_query = count_query.where(Alert.triggered_at >= start)
    
    if end is not None:
        query = query.where(Alert.triggered_at <= end)
        count_query = count_query.where(Alert.triggered_at <= end)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.order_by(Alert.triggered_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_by_id(
    db: AsyncSession,
    factory_id: int,
    alert_id: int,
) -> Optional[Alert]:
    """Get alert by ID within factory scope."""
    result = await db.execute(
        select(Alert).where(
            Alert.factory_id == factory_id,
            Alert.id == alert_id,
        )
    )
    return result.scalar_one_or_none()


async def resolve(
    db: AsyncSession,
    factory_id: int,
    alert_id: int,
) -> Optional[Alert]:
    """Mark alert as resolved."""
    alert = await get_by_id(db, factory_id, alert_id)
    if not alert:
        return None
    
    alert.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alert)
    return alert


async def get_cooldown(
    db: AsyncSession,
    rule_id: int,
    device_id: int,
) -> Optional[RuleCooldown]:
    """Get cooldown record for rule-device pair."""
    result = await db.execute(
        select(RuleCooldown).where(
            RuleCooldown.rule_id == rule_id,
            RuleCooldown.device_id == device_id,
        )
    )
    return result.scalar_one_or_none()


async def upsert_cooldown(
    db: AsyncSession,
    rule_id: int,
    device_id: int,
    last_triggered: datetime,
) -> None:
    """Insert or update cooldown record."""
    cooldown = await get_cooldown(db, rule_id, device_id)
    if cooldown:
        cooldown.last_triggered = last_triggered
    else:
        cooldown = RuleCooldown(
            rule_id=rule_id,
            device_id=device_id,
            last_triggered=last_triggered,
        )
        db.add(cooldown)
    await db.commit()


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
