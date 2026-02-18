"""Reports API routes."""
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.logging import get_logger
from app.workers.reporting_task import generate_report_task
from app.repositories import report_repo
from app.models.report import Report, ReportFormat, ReportStatus
from app.models.user import User
from app.schemas.reports import (
    ReportCreate,
    ReportResponse,
    ReportList,
    ReportDetail,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_report(
    data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new report.
    
    Returns immediately with report_id. The report is generated asynchronously.
    """
    # Validate format
    try:
        report_format = ReportFormat(data.format)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Must be one of: {[f.value for f in ReportFormat]}",
        )
    
    # Validate date range
    if data.date_range_end <= data.date_range_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_range_end must be after date_range_start",
        )
    
    # Validate device_ids not empty
    if not data.device_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one device must be selected",
        )
    
    # Generate report ID
    report_id = str(uuid.uuid4())
    
    # Create report record
    report = await report_repo.create(
        db=db,
        report_id=report_id,
        factory_id=current_user.factory_id,
        created_by=current_user.id,
        title=data.title,
        device_ids=data.device_ids,
        date_range_start=data.date_range_start,
        date_range_end=data.date_range_end,
        format=report_format,
        include_analytics=data.include_analytics,
        analytics_job_id=data.analytics_job_id,
    )
    
    # Dispatch Celery task
    generate_report_task.delay(report_id)
    
    logger.info(
        "report.dispatched",
        report_id=report_id,
        factory_id=current_user.factory_id,
        format=report_format.value,
    )
    
    return {
        "data": {
            "report_id": report_id,
            "status": ReportStatus.PENDING.value,
        }
    }


@router.get("/reports", response_model=ReportList)
async def list_reports(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List reports for the factory."""
    # Validate filter
    status_filter = None
    if status:
        try:
            status_filter = ReportStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in ReportStatus]}",
            )
    
    reports, total = await report_repo.get_all(
        db=db,
        factory_id=current_user.factory_id,
        status=status_filter,
        page=page,
        per_page=per_page,
    )
    
    return {
        "data": reports,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/reports/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get report status and details."""
    report = await report_repo.get_by_id(
        db=db,
        factory_id=current_user.factory_id,
        report_id=report_id,
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    # Build response
    response = {
        "data": {
            "report_id": report.id,
            "status": report.status.value,
            "title": report.title,
            "format": report.format.value,
            "device_ids": report.device_ids,
            "date_range_start": report.date_range_start,
            "date_range_end": report.date_range_end,
            "include_analytics": report.include_analytics,
            "analytics_job_id": report.analytics_job_id,
            "file_size_bytes": report.file_size_bytes,
            "created_at": report.created_at,
            "expires_at": report.expires_at,
        }
    }
    
    # Include file URL if report is complete
    if report.status == ReportStatus.COMPLETE:
        response["data"]["file_url"] = report.file_url
    
    # Include error if report failed
    if report.status == ReportStatus.FAILED and report.error_message:
        response["data"]["error_message"] = report.error_message
    
    return response


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download report - redirects to presigned URL."""
    report = await report_repo.get_by_id(
        db=db,
        factory_id=current_user.factory_id,
        report_id=report_id,
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    if report.status != ReportStatus.COMPLETE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not ready. Current status: {report.status.value}",
        )
    
    if not report.file_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not available",
        )
    
    logger.info(
        "report.download",
        report_id=report_id,
        factory_id=current_user.factory_id,
    )
    
    # Redirect to presigned URL
    return RedirectResponse(url=report.file_url)


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a report.
    
    Only pending or failed reports can be deleted.
    """
    report = await report_repo.get_by_id(
        db=db,
        factory_id=current_user.factory_id,
        report_id=report_id,
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    # Only allow deletion of pending or failed reports
    if report.status not in (ReportStatus.PENDING, ReportStatus.FAILED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete report with status '{report.status.value}'. Only pending or failed reports can be deleted.",
        )
    
    deleted = await report_repo.delete(
        db=db,
        factory_id=current_user.factory_id,
        report_id=report_id,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete report",
        )
    
    logger.info(
        "report.deleted",
        report_id=report_id,
        factory_id=current_user.factory_id,
    )
    
    return None
