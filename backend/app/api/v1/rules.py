"""Rules API router."""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.rule import RuleCreate, RuleUpdate, RuleResponse, RuleListResponse
from app.repositories import rule_repo, device_repo
from app.core.logging import get_logger

router = APIRouter(prefix="/rules", tags=["rules"])
logger = get_logger(__name__)


def _build_rule_response(rule, device_ids: List[int]) -> RuleResponse:
    """Build RuleResponse from Rule model."""
    return RuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        scope=rule.scope.value if hasattr(rule.scope, 'value') else rule.scope,
        is_active=rule.is_active,
        conditions=rule.conditions,
        cooldown_minutes=rule.cooldown_minutes,
        severity=rule.severity.value if hasattr(rule.severity, 'value') else rule.severity,
        schedule_type=rule.schedule_type.value if hasattr(rule.schedule_type, 'value') else rule.schedule_type,
        schedule_config=rule.schedule_config,
        notification_channels=rule.notification_channels,
        device_ids=device_ids,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.get("", response_model=RuleListResponse)
async def list_rules(
    device_id: Optional[int] = Query(None, description="Filter by device"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    scope: Optional[str] = Query(None, description="Filter by scope (device/global)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List rules for the factory."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    rules, total = await rule_repo.get_all(
        db, factory_id, device_id, is_active, scope, page, per_page
    )
    
    # Build responses with device IDs
    data = []
    for rule in rules:
        device_ids = await rule_repo.get_device_ids_for_rule(db, rule.id)
        data.append(_build_rule_response(rule, device_ids))
    
    return RuleListResponse(data=data, total=total, page=page, per_page=per_page)


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: RuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new rule."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    # Validate device IDs exist in factory
    if data.scope == "device" and data.device_ids:
        for device_id in data.device_ids:
            device = await device_repo.get_by_id(db, factory_id, device_id)
            if not device:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Device {device_id} not found",
                )
    
    rule = await rule_repo.create(db, factory_id, current_user.id, data.model_dump())
    device_ids = await rule_repo.get_device_ids_for_rule(db, rule.id)
    
    logger.info(
        "rule.api_created",
        factory_id=factory_id,
        rule_id=rule.id,
        rule_name=rule.name,
    )
    
    return _build_rule_response(rule, device_ids)


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get rule detail."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    rule = await rule_repo.get_by_id(db, factory_id, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    
    device_ids = await rule_repo.get_device_ids_for_rule(db, rule.id)
    return _build_rule_response(rule, device_ids)


@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    data: RuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update rule."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    rule = await rule_repo.update(db, factory_id, rule_id, data.model_dump(exclude_unset=True))
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    
    device_ids = await rule_repo.get_device_ids_for_rule(db, rule.id)
    return _build_rule_response(rule, device_ids)


@router.delete("/{rule_id}", status_code=status.HTTP_200_OK)
async def delete_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete rule."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    success = await rule_repo.delete(db, factory_id, rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    
    return {"message": "Rule deleted successfully"}


@router.patch("/{rule_id}/toggle", response_model=RuleResponse)
async def toggle_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable/disable rule."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    rule = await rule_repo.toggle(db, factory_id, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    
    device_ids = await rule_repo.get_device_ids_for_rule(db, rule.id)
    return _build_rule_response(rule, device_ids)
