"""Dashboard API router."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories import device_repo, alert_repo
from app.core.logging import get_logger

router = APIRouter(tags=["dashboard"])
logger = get_logger(__name__)


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get factory-level operational summary."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    # Get device counts
    devices, total_devices = await device_repo.get_all(db, factory_id, per_page=1000)
    active_devices = sum(1 for d in devices if d.is_active)
    
    # Calculate online devices (last_seen within 10 minutes)
    from datetime import datetime, timedelta
    threshold = datetime.utcnow() - timedelta(minutes=10)
    online_devices = sum(
        1 for d in devices 
        if d.is_active and d.last_seen and d.last_seen > threshold
    )
    
    # Get alert counts
    active_alerts = await alert_repo.get_active_count_by_factory(db, factory_id)
    critical_alerts = await alert_repo.get_critical_count_by_factory(db, factory_id)
    
    # Calculate health score (average of device health scores)
    # Simple calculation: (online_devices / total_active) * 100 - penalties for alerts
    if active_devices > 0:
        base_health = int((online_devices / active_devices) * 100)
        health_penalty = min(active_alerts * 2, 30)  # Max 30 point penalty
        health_score = max(0, base_health - health_penalty)
    else:
        health_score = 0
    
    # TODO: Get energy metrics from InfluxDB
    # For now, return placeholder values
    
    return {
        "data": {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "offline_devices": active_devices - online_devices,
            "current_energy_kw": 0.0,  # Placeholder
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
            "health_score": health_score,
            "energy_today_kwh": 0.0,  # Placeholder
            "energy_this_month_kwh": 0.0,  # Placeholder
        }
    }
