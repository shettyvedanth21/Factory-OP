"""Rule repository for database operations."""
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule, rule_devices
from app.models.device import Device
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_all(
    db: AsyncSession,
    factory_id: int,
    device_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    scope: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Rule], int]:
    """Get all rules for a factory with filtering and pagination."""
    query = select(Rule).where(Rule.factory_id == factory_id)
    count_query = select(func.count(Rule.id)).where(Rule.factory_id == factory_id)
    
    # Apply filters
    if device_id is not None:
        # Get rules that are either global or assigned to this device
        query = query.outerjoin(
            rule_devices, Rule.id == rule_devices.c.rule_id
        ).where(
            or_(
                Rule.scope == "global",
                rule_devices.c.device_id == device_id
            )
        )
    
    if is_active is not None:
        query = query.where(Rule.is_active == is_active)
        count_query = count_query.where(Rule.is_active == is_active)
    
    if scope is not None:
        query = query.where(Rule.scope == scope)
        count_query = count_query.where(Rule.scope == scope)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    result = await db.execute(query)
    rules = result.scalars().unique().all()
    
    return list(rules), total


async def get_by_id(
    db: AsyncSession,
    factory_id: int,
    rule_id: int,
) -> Optional[Rule]:
    """Get rule by ID within factory scope."""
    result = await db.execute(
        select(Rule).where(
            Rule.factory_id == factory_id,
            Rule.id == rule_id,
        )
    )
    return result.scalar_one_or_none()


async def get_active_for_device(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
) -> List[Rule]:
    """
    Get all active rules applicable to a device.
    Returns global rules + device-specific rules for this device.
    """
    query = select(Rule).where(
        Rule.factory_id == factory_id,
        Rule.is_active == True,
    ).outerjoin(
        rule_devices, Rule.id == rule_devices.c.rule_id
    ).where(
        or_(
            Rule.scope == "global",
            rule_devices.c.device_id == device_id
        )
    )
    
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def create(
    db: AsyncSession,
    factory_id: int,
    user_id: int,
    data: dict,
) -> Rule:
    """Create a new rule."""
    from app.models.rule import RuleScope, Severity, ScheduleType
    
    rule = Rule(
        factory_id=factory_id,
        name=data["name"],
        description=data.get("description"),
        scope=data.get("scope", "device"),
        conditions=data["conditions"],
        cooldown_minutes=data.get("cooldown_minutes", 15),
        is_active=True,
        schedule_type=data.get("schedule_type", "always"),
        schedule_config=data.get("schedule_config"),
        severity=data.get("severity", "medium"),
        notification_channels=data.get("notification_channels", {}),
        created_by=user_id,
    )
    
    db.add(rule)
    await db.flush()  # Get the rule ID
    
    # Associate devices if device scope
    if rule.scope == "device" and data.get("device_ids"):
        for device_id in data["device_ids"]:
            await db.execute(
                rule_devices.insert().values(
                    rule_id=rule.id,
                    device_id=device_id,
                )
            )
    
    await db.commit()
    await db.refresh(rule)
    
    logger.info(
        "rule.created",
        factory_id=factory_id,
        rule_id=rule.id,
        rule_name=rule.name,
    )
    
    return rule


async def update(
    db: AsyncSession,
    factory_id: int,
    rule_id: int,
    data: dict,
) -> Optional[Rule]:
    """Update rule."""
    rule = await get_by_id(db, factory_id, rule_id)
    if not rule:
        return None
    
    # Update fields
    updatable_fields = [
        "name", "description", "scope", "conditions", "cooldown_minutes",
        "is_active", "schedule_type", "schedule_config", "severity",
        "notification_channels"
    ]
    
    for field in updatable_fields:
        if field in data:
            setattr(rule, field, data[field])
    
    # Update device associations if scope is device
    if "device_ids" in data and rule.scope == "device":
        # Clear existing associations
        await db.execute(
            rule_devices.delete().where(rule_devices.c.rule_id == rule_id)
        )
        # Add new associations
        for device_id in data["device_ids"]:
            await db.execute(
                rule_devices.insert().values(
                    rule_id=rule.id,
                    device_id=device_id,
                )
            )
    
    await db.commit()
    await db.refresh(rule)
    
    logger.info(
        "rule.updated",
        factory_id=factory_id,
        rule_id=rule_id,
    )
    
    return rule


async def delete(
    db: AsyncSession,
    factory_id: int,
    rule_id: int,
) -> bool:
    """Delete rule (hard delete)."""
    rule = await get_by_id(db, factory_id, rule_id)
    if not rule:
        return False
    
    await db.delete(rule)
    await db.commit()
    
    logger.info(
        "rule.deleted",
        factory_id=factory_id,
        rule_id=rule_id,
    )
    
    return True


async def toggle(
    db: AsyncSession,
    factory_id: int,
    rule_id: int,
) -> Optional[Rule]:
    """Toggle rule active state."""
    rule = await get_by_id(db, factory_id, rule_id)
    if not rule:
        return None
    
    rule.is_active = not rule.is_active
    await db.commit()
    await db.refresh(rule)
    
    logger.info(
        "rule.toggled",
        factory_id=factory_id,
        rule_id=rule_id,
        is_active=rule.is_active,
    )
    
    return rule


async def get_device_ids_for_rule(
    db: AsyncSession,
    rule_id: int,
) -> List[int]:
    """Get list of device IDs associated with a rule."""
    result = await db.execute(
        select(rule_devices.c.device_id).where(rule_devices.c.rule_id == rule_id)
    )
    return [row[0] for row in result.all()]
