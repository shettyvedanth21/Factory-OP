"""Analytics schemas."""
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class AnalyticsJobCreate(BaseModel):
    """Request to create an analytics job."""
    job_type: Literal["anomaly", "failure_prediction", "energy_forecast", "ai_copilot"]
    mode: Optional[Literal["standard", "ai_copilot"]] = "standard"
    device_ids: List[int] = Field(..., min_length=1)
    date_range_start: datetime
    date_range_end: datetime


class AnalyticsJobResponse(BaseModel):
    """Response after creating analytics job."""
    class JobInfo(BaseModel):
        job_id: str
        status: str
    
    data: JobInfo


class AnalyticsJobItem(BaseModel):
    """Single analytics job item."""
    id: str
    job_type: str
    mode: str
    status: str
    device_ids: List[int]
    date_range_start: datetime
    date_range_end: datetime
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class AnalyticsJobList(BaseModel):
    """List of analytics jobs."""
    data: List[AnalyticsJobItem]
    total: int
    page: int
    per_page: int


class AnalyticsJobDetailData(BaseModel):
    """Analytics job detail data."""
    job_id: str
    status: str
    job_type: str
    mode: str
    device_ids: List[int]
    date_range_start: datetime
    date_range_end: datetime
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class AnalyticsJobDetail(BaseModel):
    """Analytics job detail response."""
    data: AnalyticsJobDetailData
