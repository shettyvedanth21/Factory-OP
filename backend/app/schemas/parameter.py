"""Parameter Pydantic schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ParameterResponse(BaseModel):
    """Schema for device parameter response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    parameter_key: str
    display_name: Optional[str] = None
    unit: Optional[str] = None
    data_type: str
    is_kpi_selected: bool
    discovered_at: datetime
    updated_at: datetime


class ParameterUpdate(BaseModel):
    """Schema for updating parameter."""
    display_name: Optional[str] = None
    unit: Optional[str] = None
    is_kpi_selected: Optional[bool] = None


class ParameterListResponse(BaseModel):
    """Schema for parameter list response."""
    data: list[ParameterResponse]
