"""Alerts API router."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.alert import AlertResponse, AlertListResponse, AlertResolveResponse
from app.repositories import alert_repo, rule_repo, device_repo
from app.core.logging import get_logger

router = APIRouter(prefix="/alerts", tags=["alerts"])
logger = get_logger(__name__)


async def _build_alert_response(db: AsyncSession, alert) -> AlertResponse:
    """Build AlertResponse with rule and device names."""
    # Get rule name
    rule = await rule_repo.get_by_id(db, alert.factory_id, alert.rule_id)
    rule_name = rule.name if rule else None
    
    # Get device name
    device = await device_repo.get_by_id(db, alert.factory_id, alert.device_id)
    device_name = device.name if device else None
    
    return AlertResponse(
        id=alert.id,
        rule_id=alert.rule_id,
        rule_name=rule_name,
        device_id=alert.device_id,
        device_name=device_name,
        triggered_at=alert.triggered_at,
        resolved_at=alert.resolved_at,
        severity=alert.severity,
        message=alert.message,
        telemetry_snapshot=alert.telemetry_snapshot,
    )


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    device_id: Optional[int] = Query(None, description="Filter by device"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    start: Optional[datetime] = Query(None, description="Start datetime (ISO8601)"),
    end: Optional[datetime] = Query(None, description="End datetime (ISO8601)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List alerts for the factory."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    alerts, total = await alert_repo.get_all(
        db, factory_id, device_id, severity, resolved, start, end, page, per_page
    )
    
    # Build responses with rule/device names
    data = []
    for alert in alerts:
        data.append(await _build_alert_response(db, alert))
    
    return AlertListResponse(data=data, total=total, page=page, per_page=per_page)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get alert detail."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    alert = await alert_repo.get_by_id(db, factory_id, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    
    return await _build_alert_response(db, alert)


@router.patch("/{alert_id}/resolve", response_model=AlertResolveResponse)
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark alert as resolved."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    alert = await alert_repo.resolve(db, factory_id, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    
    logger.info(
        "alert.resolved",
        factory_id=factory_id,
        alert_id=alert_id,
    )
    
    return AlertResolveResponse(
        id=alert.id,
        resolved_at=alert.resolved_at,
    )
