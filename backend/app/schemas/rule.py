"""Rule Pydantic schemas."""
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class ConditionLeaf(BaseModel):
    """A single condition (leaf node)."""
    parameter: str = Field(..., description="Parameter key to check")
    operator: Literal["gt", "lt", "gte", "lte", "eq", "neq"] = Field(..., description="Comparison operator")
    value: float = Field(..., description="Threshold value")


class ConditionTree(BaseModel):
    """Nested condition tree (branch node)."""
    operator: Literal["AND", "OR"] = Field(..., description="Logical operator")
    conditions: List[Union["ConditionTree", ConditionLeaf]] = Field(
        ..., description="List of conditions (can be nested)"
    )


class ScheduleConfig(BaseModel):
    """Schedule configuration for time-based rules."""
    start_time: Optional[str] = None  # HH:MM format
    end_time: Optional[str] = None    # HH:MM format
    days: Optional[List[int]] = None  # 1=Monday, 7=Sunday
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None    # YYYY-MM-DD


class NotificationChannels(BaseModel):
    """Notification channel configuration."""
    email: bool = False
    whatsapp: bool = False


class RuleCreate(BaseModel):
    """Schema for creating a new rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scope: Literal["device", "global"] = "device"
    device_ids: List[int] = Field(default_factory=list)
    conditions: ConditionTree
    cooldown_minutes: int = Field(default=15, ge=0)
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    schedule_type: Literal["always", "time_window", "date_range"] = "always"
    schedule_config: Optional[ScheduleConfig] = None
    notification_channels: NotificationChannels = Field(default_factory=NotificationChannels)


class RuleUpdate(BaseModel):
    """Schema for updating a rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scope: Optional[Literal["device", "global"]] = None
    device_ids: Optional[List[int]] = None
    conditions: Optional[ConditionTree] = None
    cooldown_minutes: Optional[int] = Field(None, ge=0)
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    schedule_type: Optional[Literal["always", "time_window", "date_range"]] = None
    schedule_config: Optional[ScheduleConfig] = None
    notification_channels: Optional[NotificationChannels] = None
    is_active: Optional[bool] = None


class RuleResponse(BaseModel):
    """Schema for rule response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    scope: str
    is_active: bool
    conditions: Dict[str, Any]
    cooldown_minutes: int
    severity: str
    schedule_type: str
    schedule_config: Optional[Dict[str, Any]] = None
    notification_channels: Optional[Dict[str, Any]] = None
    device_ids: List[int]
    created_at: datetime
    updated_at: datetime


class RuleListResponse(BaseModel):
    """Schema for paginated rule list."""
    data: List[RuleResponse]
    total: int
    page: int
    per_page: int
