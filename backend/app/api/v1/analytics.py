"""Analytics API routes."""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.logging import get_logger
from app.workers.analytics_task import run_analytics_job
from app.repositories import analytics_job_repo
from app.models.analytics_job import AnalyticsJob, JobType, JobStatus, JobMode
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsJobCreate,
    AnalyticsJobResponse,
    AnalyticsJobList,
    AnalyticsJobDetail,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/jobs", response_model=AnalyticsJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_analytics_job(
    data: AnalyticsJobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new analytics job.
    
    Returns immediately with job_id. The job runs asynchronously.
    """
    # Validate job type
    try:
        job_type = JobType(data.job_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job_type. Must be one of: {[t.value for t in JobType]}",
        )
    
    # Validate date range
    if data.date_range_end <= data.date_range_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_range_end must be after date_range_start",
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job record
    job = await analytics_job_repo.create(
        db=db,
        job_id=job_id,
        factory_id=current_user.factory_id,
        created_by=current_user.id,
        job_type=job_type,
        mode=data.mode or JobMode.STANDARD,
        device_ids=data.device_ids,
        date_range_start=data.date_range_start,
        date_range_end=data.date_range_end,
    )
    
    # Dispatch Celery task
    run_analytics_job.delay(job_id)
    
    logger.info(
        "analytics_job.dispatched",
        job_id=job_id,
        factory_id=current_user.factory_id,
        job_type=job_type.value,
    )
    
    return {
        "data": {
            "job_id": job_id,
            "status": JobStatus.PENDING.value,
        }
    }


@router.get("/jobs", response_model=AnalyticsJobList)
async def list_analytics_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List analytics jobs for the factory."""
    # Validate filters
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in JobStatus]}",
            )
    
    type_filter = None
    if job_type:
        try:
            type_filter = JobType(job_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job_type. Must be one of: {[t.value for t in JobType]}",
            )
    
    jobs, total = await analytics_job_repo.get_all(
        db=db,
        factory_id=current_user.factory_id,
        status=status_filter,
        job_type=type_filter,
        page=page,
        per_page=per_page,
    )
    
    return {
        "data": jobs,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/jobs/{job_id}", response_model=AnalyticsJobDetail)
async def get_analytics_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics job status and results."""
    job = await analytics_job_repo.get_by_id(
        db=db,
        factory_id=current_user.factory_id,
        job_id=job_id,
    )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    
    # Build response
    response = {
        "data": {
            "job_id": job.id,
            "status": job.status.value,
            "job_type": job.job_type.value,
            "mode": job.mode.value,
            "device_ids": job.device_ids,
            "date_range_start": job.date_range_start,
            "date_range_end": job.date_range_end,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }
    }
    
    # Include results if job is complete
    if job.status == JobStatus.COMPLETE:
        response["data"]["result_url"] = job.result_url
    
    # Include error if job failed
    if job.status == JobStatus.FAILED and job.error_message:
        response["data"]["error_message"] = job.error_message
    
    return response


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_analytics_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel/delete an analytics job.
    
    Only pending or failed jobs can be deleted.
    """
    job = await analytics_job_repo.get_by_id(
        db=db,
        factory_id=current_user.factory_id,
        job_id=job_id,
    )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    
    # Only allow deletion of pending or failed jobs
    if job.status not in (JobStatus.PENDING, JobStatus.FAILED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete job with status '{job.status.value}'. Only pending or failed jobs can be deleted.",
        )
    
    deleted = await analytics_job_repo.delete(
        db=db,
        factory_id=current_user.factory_id,
        job_id=job_id,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete job",
        )
    
    logger.info(
        "analytics_job.cancelled",
        job_id=job_id,
        factory_id=current_user.factory_id,
    )
    
    return None
