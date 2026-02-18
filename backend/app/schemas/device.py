"""Device Pydantic schemas."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class DeviceCreate(BaseModel):
    """Schema for creating a new device."""
    device_key: str
    name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    region: Optional[str] = None


class DeviceUpdate(BaseModel):
    """Schema for updating device metadata."""
    name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    region: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceResponse(BaseModel):
    """Schema for device detail response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    device_key: str
    name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    region: Optional[str] = None
    is_active: bool
    last_seen: Optional[datetime] = None
    api_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DeviceListItem(BaseModel):
    """Schema for device list item with computed fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    device_key: str
    name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    region: Optional[str] = None
    is_active: bool
    last_seen: Optional[datetime] = None
    health_score: int
    current_energy_kw: float
    active_alert_count: int


class DeviceListResponse(BaseModel):
    """Schema for paginated device list."""
    data: List[DeviceListItem]
    total: int
    page: int
    per_page: int


class DeviceDetailResponse(BaseModel):
    """Schema for device detail with parameters."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    device_key: str
    name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    region: Optional[str] = None
    is_active: bool
    last_seen: Optional[datetime] = None
    health_score: int
    parameters: List[dict]  # Will be populated from ParameterResponse
