"""Telemetry/KPI API router."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.parameter import ParameterListResponse, ParameterResponse, ParameterUpdate
from app.schemas.kpi import KPILiveResponse, KPIHistoryResponse
from app.repositories import parameter_repo
from app.services import kpi_service
from app.core.logging import get_logger

router = APIRouter(tags=["telemetry"])
logger = get_logger(__name__)


@router.get("/devices/{device_id}/parameters", response_model=ParameterListResponse)
async def list_parameters(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all parameters for a device."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    # Verify device belongs to factory
    from app.repositories import device_repo
    device = await device_repo.get_by_id(db, factory_id, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    parameters = await parameter_repo.get_all(db, factory_id, device_id)
    
    return ParameterListResponse(data=[
        ParameterResponse.model_validate(p) for p in parameters
    ])


@router.patch("/devices/{device_id}/parameters/{param_id}", response_model=ParameterResponse)
async def update_parameter(
    device_id: int,
    param_id: int,
    data: ParameterUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update parameter display name, unit, or KPI selection."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    # Verify device belongs to factory
    from app.repositories import device_repo
    device = await device_repo.get_by_id(db, factory_id, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    param = await parameter_repo.update(
        db, factory_id, device_id, param_id, data.model_dump(exclude_unset=True)
    )
    if not param:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parameter not found",
        )
    
    return ParameterResponse.model_validate(param)


@router.get("/devices/{device_id}/kpis/live", response_model=KPILiveResponse)
async def get_live_kpis(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get latest values for all selected KPIs."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    # Verify device belongs to factory
    from app.repositories import device_repo
    device = await device_repo.get_by_id(db, factory_id, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    # Get selected parameter keys
    selected_params = await parameter_repo.get_selected_keys(db, factory_id, device_id)
    
    # Get live KPI values
    kpis = await kpi_service.get_live_kpis(factory_id, device_id, selected_params, db)
    
    return KPILiveResponse(
        device_id=device_id,
        timestamp=datetime.utcnow(),
        kpis=kpis,
    )


@router.get("/devices/{device_id}/kpis/history", response_model=KPIHistoryResponse)
async def get_kpi_history(
    device_id: int,
    parameter: str = Query(..., description="Parameter key"),
    start: datetime = Query(..., description="Start datetime (ISO8601)"),
    end: datetime = Query(..., description="End datetime (ISO8601)"),
    interval: Optional[str] = Query(None, description="Aggregation interval (1m, 5m, 1h, 1d)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get historical trend data for a single parameter."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    # Verify device belongs to factory
    from app.repositories import device_repo
    device = await device_repo.get_by_id(db, factory_id, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    # Get parameter metadata for display name
    params = await parameter_repo.get_all(db, factory_id, device_id)
    param_meta = next((p for p in params if p.parameter_key == parameter), None)
    
    # Get history data
    points = await kpi_service.get_kpi_history(
        factory_id, device_id, parameter, start, end, interval
    )
    
    return KPIHistoryResponse(
        parameter_key=parameter,
        display_name=param_meta.display_name if param_meta else parameter,
        unit=param_meta.unit if param_meta else None,
        interval=interval or "auto",
        points=points,
    )
