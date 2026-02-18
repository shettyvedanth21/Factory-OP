"""Device API router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceListResponse,
)
from app.services import device_service
from app.core.logging import get_logger

router = APIRouter(prefix="/devices", tags=["devices"])
logger = get_logger(__name__)


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all devices for the factory."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    devices, total = await device_service.list_devices(
        db, factory_id, page, per_page, search, is_active
    )
    
    return DeviceListResponse(
        data=devices,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get device detail."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    device = await device_service.get_device(db, factory_id, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    return device


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    data: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new device."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    device = await device_service.create_device(db, factory_id, data)
    
    logger.info(
        "device.api_created",
        factory_id=factory_id,
        device_id=device.id,
        device_key=device.device_key,
    )
    
    return device


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    data: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update device metadata."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    device = await device_service.update_device(db, factory_id, device_id, data)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    return device


@router.delete("/{device_id}", status_code=status.HTTP_200_OK)
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate device (soft delete)."""
    factory_id = getattr(current_user, '_token_factory_id', None)
    
    success = await device_service.delete_device(db, factory_id, device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    return {"message": "Device deactivated successfully"}
