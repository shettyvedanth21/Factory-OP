"""Alert Pydantic schemas."""
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    """Schema for alert response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    rule_id: int
    rule_name: Optional[str] = None
    device_id: int
    device_name: Optional[str] = None
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    severity: str
    message: Optional[str] = None
    telemetry_snapshot: Optional[Dict[str, Any]] = None


class AlertListResponse(BaseModel):
    """Schema for paginated alert list."""
    data: List[AlertResponse]
    total: int
    page: int
    per_page: int


class AlertResolveResponse(BaseModel):
    """Schema for alert resolution response."""
    id: int
    resolved_at: datetime
