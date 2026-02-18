"""Report repository for database operations."""
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report, ReportStatus, ReportFormat
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_all(
    db: AsyncSession,
    factory_id: int,
    status: Optional[ReportStatus] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Report], int]:
    """Get all reports for a factory with filtering and pagination."""
    query = select(Report).where(Report.factory_id == factory_id)
    count_query = select(func.count(Report.id)).where(Report.factory_id == factory_id)
    
    # Apply filters
    if status is not None:
        query = query.where(Report.status == status)
        count_query = count_query.where(Report.status == status)
    
    # Order by created_at desc
    query = query.order_by(Report.created_at.desc())
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    return list(reports), total


async def get_by_id(
    db: AsyncSession,
    factory_id: int,
    report_id: str,
) -> Optional[Report]:
    """Get report by ID within factory scope."""
    result = await db.execute(
        select(Report).where(
            Report.factory_id == factory_id,
            Report.id == report_id,
        )
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    report_id: str,
    factory_id: int,
    created_by: int,
    title: Optional[str],
    device_ids: List[int],
    date_range_start: datetime,
    date_range_end: datetime,
    format: ReportFormat,
    include_analytics: bool,
    analytics_job_id: Optional[str],
) -> Report:
    """Create a new report."""
    report = Report(
        id=report_id,
        factory_id=factory_id,
        created_by=created_by,
        title=title,
        device_ids=device_ids,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
        format=format,
        include_analytics=include_analytics,
        analytics_job_id=analytics_job_id,
        status=ReportStatus.PENDING,
        expires_at=datetime.utcnow() + timedelta(days=90),  # 90 day expiry
    )
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    logger.info(
        "report.created",
        report_id=report_id,
        factory_id=factory_id,
        format=format.value,
        device_count=len(device_ids),
    )
    
    return report


async def update_status(
    db: AsyncSession,
    report_id: str,
    status: ReportStatus,
    file_url: Optional[str] = None,
    file_size: Optional[int] = None,
    error_message: Optional[str] = None,
) -> Optional[Report]:
    """Update report status and optional fields."""
    report = await db.get(Report, report_id)
    if not report:
        return None
    
    report.status = status
    
    if file_url is not None:
        report.file_url = file_url
    
    if file_size is not None:
        report.file_size_bytes = file_size
    
    if error_message is not None:
        report.error_message = error_message
    
    await db.commit()
    await db.refresh(report)
    
    logger.info(
        "report.status_updated",
        report_id=report_id,
        status=status.value,
        has_file=file_url is not None,
    )
    
    return report


async def delete(
    db: AsyncSession,
    factory_id: int,
    report_id: str,
) -> bool:
    """Delete a report if it belongs to the factory.
    
    Only allows deletion of pending or failed reports.
    """
    report = await get_by_id(db, factory_id, report_id)
    if not report:
        return False
    
    if report.status not in (ReportStatus.PENDING, ReportStatus.FAILED):
        logger.warning(
            "report.delete_blocked",
            report_id=report_id,
            status=report.status.value,
        )
        return False
    
    await db.delete(report)
    await db.commit()
    
    logger.info("report.deleted", report_id=report_id, factory_id=factory_id)
    
    return True
