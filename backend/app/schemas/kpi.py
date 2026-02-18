"""KPI Pydantic schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class KPIValue(BaseModel):
    """Schema for a single KPI value."""
    parameter_key: str
    display_name: Optional[str] = None
    unit: Optional[str] = None
    value: float
    is_stale: bool


class KPILiveResponse(BaseModel):
    """Schema for live KPI response."""
    device_id: int
    timestamp: datetime
    kpis: List[KPIValue]


class DataPoint(BaseModel):
    """Schema for a single data point in history."""
    timestamp: datetime
    value: float


class KPIHistoryResponse(BaseModel):
    """Schema for KPI history response."""
    parameter_key: str
    display_name: Optional[str] = None
    unit: Optional[str] = None
    interval: str
    points: List[DataPoint]
