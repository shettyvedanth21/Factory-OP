"""Rule engine condition evaluator and task."""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from celery import shared_task
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from asgiref.sync import async_to_sync

from app.workers.celery_app import celery_app
from app.core.logging import get_logger
from app.core.database import AsyncSessionLocal
from app.repositories import rule_repo, alert_repo, user_repo
from app.models.rule import Rule
from app.models.alert import Alert, RuleCooldown

logger = get_logger(__name__)

# Operator functions
OPERATORS = {
    "gt": lambda a, b: a > b,
    "lt": lambda a, b: a < b,
    "gte": lambda a, b: a >= b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
    "neq": lambda a, b: a != b,
}


def evaluate_conditions(condition_tree: dict, metrics: dict) -> bool:
    """
    Recursively evaluates condition tree against metrics.
    Returns False (not exception) on any invalid input.
    """
    try:
        op = condition_tree.get("operator", "AND").upper()
        conditions = condition_tree.get("conditions", [])
        
        if not conditions:
            return False
        
        results = []
        for cond in conditions:
            if "conditions" in cond:
                # Nested condition tree
                results.append(evaluate_conditions(cond, metrics))
            else:
                # Leaf condition
                param = cond.get("parameter")
                if param not in metrics:
                    results.append(False)
                    continue
                
                fn = OPERATORS.get(cond.get("operator"))
                if not fn:
                    results.append(False)
                    continue
                
                try:
                    result = fn(float(metrics[param]), float(cond["value"]))
                    results.append(result)
                except (ValueError, TypeError):
                    results.append(False)
        
        if op == "AND":
            return all(results)
        if op == "OR":
            return any(results)
        return False
        
    except Exception:
        return False


def is_rule_scheduled(rule: Dict[str, Any], now: datetime) -> bool:
    """Check if rule should be evaluated based on schedule."""
    schedule_type = rule.get("schedule_type", "always")
    
    if schedule_type == "always":
        return True
    
    config = rule.get("schedule_config") or {}
    
    if schedule_type == "time_window":
        try:
            start_t = datetime.strptime(config["start_time"], "%H:%M").time()
            end_t = datetime.strptime(config["end_time"], "%H:%M").time()
            day_ok = now.isoweekday() in config.get("days", list(range(1, 8)))
            time_ok = start_t <= now.time() <= end_t
            return day_ok and time_ok
        except (KeyError, ValueError):
            return True  # On parse error, allow evaluation
    
    if schedule_type == "date_range":
        try:
            start_d = datetime.fromisoformat(config["start_date"]).date()
            end_d = datetime.fromisoformat(config["end_date"]).date()
            return start_d <= now.date() <= end_d
        except (KeyError, ValueError):
            return True  # On parse error, allow evaluation
    
    return True


async def is_in_cooldown(
    db: AsyncSession,
    rule_id: int,
    device_id: int,
    cooldown_minutes: int
) -> bool:
    """Check if rule is in cooldown period for this device."""
    cooldown = await alert_repo.get_cooldown(db, rule_id, device_id)
    if not cooldown:
        return False
    
    elapsed = (datetime.utcnow() - cooldown.last_triggered).total_seconds()
    return elapsed < cooldown_minutes * 60


def build_alert_message(rule_name: str, conditions: dict, metrics: dict) -> str:
    """Build human readable alert message."""
    parts = []
    
    def process_condition(cond):
        if "conditions" in cond:
            # Nested condition - recurse
            op = cond.get("operator", "AND")
            sub_parts = [process_condition(c) for c in cond.get("conditions", [])]
            return f"({f' {op} '.join(sub_parts)})"
        else:
            # Leaf condition
            param = cond.get("parameter", "?")
            actual = metrics.get(param, "?")
            operator = cond.get("operator", "?")
            value = cond.get("value", "?")
            return f"{param} ({actual}) {operator} {value}"
    
    for cond in conditions.get("conditions", []):
        parts.append(process_condition(cond))
    
    return f"[{rule_name}] " + " AND ".join(parts)


# Synchronous wrappers for DB operations
def get_active_rules_for_device_sync(factory_id: int, device_id: int) -> list:
    """Synchronous wrapper to get active rules."""
    async def _fetch():
        async with AsyncSessionLocal() as db:
            return await rule_repo.get_active_for_device(db, factory_id, device_id)
    return async_to_sync(_fetch)()


def is_in_cooldown_sync(rule_id: int, device_id: int, cooldown_minutes: int) -> bool:
    """Synchronous wrapper for cooldown check."""
    async def _check():
        async with AsyncSessionLocal() as db:
            return await is_in_cooldown(db, rule_id, device_id, cooldown_minutes)
    return async_to_sync(_check)()


def create_alert_sync(
    factory_id: int,
    rule_id: int,
    device_id: int,
    triggered_at: datetime,
    severity: str,
    message: str,
    snapshot: dict,
) -> int:
    """Synchronous wrapper to create alert."""
    async def _create():
        async with AsyncSessionLocal() as db:
            alert = await alert_repo.create_alert(
                db, factory_id, rule_id, device_id,
                triggered_at, severity, message, snapshot
            )
            return alert.id
    return async_to_sync(_create)()


def upsert_cooldown_sync(rule_id: int, device_id: int, timestamp: datetime) -> None:
    """Synchronous wrapper to upsert cooldown."""
    async def _upsert():
        async with AsyncSessionLocal() as db:
            await alert_repo.upsert_cooldown(db, rule_id, device_id, timestamp)
    async_to_sync(_upsert)()


@celery_app.task(
    name="evaluate_rules",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def evaluate_rules_task(
    self,
    factory_id: int,
    device_id: int,
    metrics: dict,
    timestamp: str,
):
    """
    Evaluate all active rules for a device against current telemetry.
    Called asynchronously after every telemetry write.
    """
    try:
        rules = get_active_rules_for_device_sync(factory_id, device_id)
        ts = datetime.fromisoformat(timestamp)
        
        for rule in rules:
            try:
                # Convert rule to dict for processing
                rule_dict = {
                    "id": rule.id,
                    "name": rule.name,
                    "conditions": rule.conditions,
                    "cooldown_minutes": rule.cooldown_minutes,
                    "severity": rule.severity.value if hasattr(rule.severity, 'value') else rule.severity,
                    "schedule_type": rule.schedule_type.value if hasattr(rule.schedule_type, 'value') else rule.schedule_type,
                    "schedule_config": rule.schedule_config,
                    "notification_channels": rule.notification_channels,
                }
                
                # Check schedule
                if not is_rule_scheduled(rule_dict, ts):
                    continue
                
                # Check cooldown
                if is_in_cooldown_sync(rule["id"], device_id, rule["cooldown_minutes"]):
                    continue
                
                # Evaluate conditions
                if evaluate_conditions(rule["conditions"], metrics):
                    # Trigger alert
                    alert_id = create_alert_sync(
                        factory_id=factory_id,
                        rule_id=rule["id"],
                        device_id=device_id,
                        triggered_at=ts,
                        severity=rule["severity"],
                        message=build_alert_message(rule["name"], rule["conditions"], metrics),
                        snapshot=metrics,
                    )
                    
                    # Update cooldown
                    upsert_cooldown_sync(rule["id"], device_id, ts)
                    
                    # Dispatch notification task
                    from app.workers.notifications import send_notifications_task
                    send_notifications_task.delay(
                        alert_id=alert_id,
                        channels=rule["notification_channels"],
                    )
                    
                    logger.info(
                        "alert.triggered",
                        factory_id=factory_id,
                        device_id=device_id,
                        rule_id=rule["id"],
                        alert_id=alert_id,
                    )
                    
            except Exception as e:
                logger.error(
                    "rule.evaluation_error",
                    factory_id=factory_id,
                    device_id=device_id,
                    rule_id=getattr(rule, 'id', 'unknown'),
                    error=str(e),
                )
                # Continue to next rule — one failure must not affect others
                
    except Exception as exc:
        logger.error(
            "evaluate_rules_task.failed",
            factory_id=factory_id,
            device_id=device_id,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
