"""Analytics job repository for database operations."""
from typing import List, Optional, Tuple
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics_job import AnalyticsJob, JobStatus, JobType
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_all(
    db: AsyncSession,
    factory_id: int,
    status: Optional[JobStatus] = None,
    job_type: Optional[JobType] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[AnalyticsJob], int]:
    """Get all analytics jobs for a factory with filtering and pagination."""
    query = select(AnalyticsJob).where(AnalyticsJob.factory_id == factory_id)
    count_query = select(func.count(AnalyticsJob.id)).where(AnalyticsJob.factory_id == factory_id)
    
    # Apply filters
    if status is not None:
        query = query.where(AnalyticsJob.status == status)
        count_query = count_query.where(AnalyticsJob.status == status)
    
    if job_type is not None:
        query = query.where(AnalyticsJob.job_type == job_type)
        count_query = count_query.where(AnalyticsJob.job_type == job_type)
    
    # Order by created_at desc
    query = query.order_by(AnalyticsJob.created_at.desc())
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return list(jobs), total


async def get_by_id(
    db: AsyncSession,
    factory_id: int,
    job_id: str,
) -> Optional[AnalyticsJob]:
    """Get analytics job by ID within factory scope."""
    result = await db.execute(
        select(AnalyticsJob).where(
            AnalyticsJob.factory_id == factory_id,
            AnalyticsJob.id == job_id,
        )
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    job_id: str,
    factory_id: int,
    created_by: int,
    job_type: JobType,
    mode: str,
    device_ids: List[int],
    date_range_start: datetime,
    date_range_end: datetime,
) -> AnalyticsJob:
    """Create a new analytics job."""
    job = AnalyticsJob(
        id=job_id,
        factory_id=factory_id,
        created_by=created_by,
        job_type=job_type,
        mode=mode,
        device_ids=device_ids,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
        status=JobStatus.PENDING,
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    logger.info(
        "analytics_job.created",
        job_id=job_id,
        factory_id=factory_id,
        job_type=job_type.value,
        device_count=len(device_ids),
    )
    
    return job


async def update_status(
    db: AsyncSession,
    job_id: str,
    status: JobStatus,
    result_url: Optional[str] = None,
    error_message: Optional[str] = None,
    results: Optional[dict] = None,
) -> Optional[AnalyticsJob]:
    """Update job status and optional fields."""
    job = await db.get(AnalyticsJob, job_id)
    if not job:
        return None
    
    job.status = status
    
    if status == JobStatus.RUNNING and not job.started_at:
        job.started_at = datetime.utcnow()
    
    if status in (JobStatus.COMPLETE, JobStatus.FAILED):
        job.completed_at = datetime.utcnow()
    
    if result_url is not None:
        job.result_url = result_url
    
    if error_message is not None:
        job.error_message = error_message
    
    await db.commit()
    await db.refresh(job)
    
    logger.info(
        "analytics_job.status_updated",
        job_id=job_id,
        status=status.value,
        has_result=result_url is not None,
    )
    
    return job


async def delete(
    db: AsyncSession,
    factory_id: int,
    job_id: str,
) -> bool:
    """Delete an analytics job if it belongs to the factory.
    
    Only allows deletion of pending or failed jobs.
    """
    job = await get_by_id(db, factory_id, job_id)
    if not job:
        return False
    
    if job.status not in (JobStatus.PENDING, JobStatus.FAILED):
        logger.warning(
            "analytics_job.delete_blocked",
            job_id=job_id,
            status=job.status.value,
        )
        return False
    
    await db.delete(job)
    await db.commit()
    
    logger.info("analytics_job.deleted", job_id=job_id, factory_id=factory_id)
    
    return True
