"""Reports schemas."""
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    """Request to create a report."""
    title: Optional[str] = Field(None, max_length=255)
    device_ids: List[int] = Field(..., min_length=1)
    date_range_start: datetime
    date_range_end: datetime
    format: Literal["pdf", "excel", "json"]
    include_analytics: bool = False
    analytics_job_id: Optional[str] = None


class ReportResponse(BaseModel):
    """Response after creating a report."""
    class ReportInfo(BaseModel):
        report_id: str
        status: str
    
    data: ReportInfo


class ReportItem(BaseModel):
    """Single report item."""
    id: str
    title: Optional[str]
    format: str
    status: str
    device_ids: List[int]
    date_range_start: datetime
    date_range_end: datetime
    include_analytics: bool
    file_size_bytes: Optional[int] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class ReportList(BaseModel):
    """List of reports."""
    data: List[ReportItem]
    total: int
    page: int
    per_page: int


class ReportDetailData(BaseModel):
    """Report detail data."""
    report_id: str
    status: str
    title: Optional[str]
    format: str
    device_ids: List[int]
    date_range_start: datetime
    date_range_end: datetime
    include_analytics: bool
    analytics_job_id: Optional[str] = None
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class ReportDetail(BaseModel):
    """Report detail response."""
    data: ReportDetailData
