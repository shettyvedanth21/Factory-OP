"""Reporting Celery task for generating PDF/Excel reports."""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional

from asgiref.sync import async_to_sync
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.minio_client import get_minio_client
from app.core.logging import get_logger
from app.workers.celery_app import celery_app
from app.workers.reporting import generate_pdf, generate_excel
from app.services.report_data import get_report_data
from app.models.report import Report, ReportStatus, ReportFormat

logger = get_logger(__name__)

# Create sync engine for Celery task
sync_engine = create_engine(
    settings.database_url.replace("+aiomysql", "+pymysql"),
    pool_pre_ping=True,
)
SyncSessionLocal = sessionmaker(bind=sync_engine)


def get_report_sync(report_id: str) -> Optional[Report]:
    """Get report by ID using sync session."""
    with SyncSessionLocal() as session:
        return session.get(Report, report_id)


def get_analytics_results_sync(job_id: str) -> Optional[dict]:
    """Get analytics job results from MinIO if available."""
    try:
        from app.models.analytics_job import AnalyticsJob
        job = SyncSessionLocal().get(AnalyticsJob, job_id)
        if job and job.status.value == "complete" and job.result_url:
            # Fetch results from MinIO
            import requests
            response = requests.get(job.result_url, timeout=30)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.warning("report.analytics_fetch_failed", job_id=job_id, error=str(e))
    return None


def update_report_status_sync(
    report_id: str,
    status: ReportStatus,
    file_url: Optional[str] = None,
    file_size: Optional[int] = None,
    error_message: Optional[str] = None,
) -> None:
    """Update report status using sync session."""
    with SyncSessionLocal() as session:
        report = session.get(Report, report_id)
        if not report:
            logger.error("report.not_found", report_id=report_id)
            return
        
        report.status = status
        
        if file_url is not None:
            report.file_url = file_url
        
        if file_size is not None:
            report.file_size_bytes = file_size
        
        if error_message is not None:
            report.error_message = error_message
        
        session.commit()
        
        logger.info(
            "report.status_updated",
            report_id=report_id,
            status=status.value,
            has_file=file_url is not None,
        )


@celery_app.task(name="generate_report", bind=True, max_retries=1, queue="reporting")
def generate_report_task(self, report_id: str):
    """Celery task to generate PDF/Excel report.
    
    Args:
        report_id: UUID of the report to generate
    """
    logger.info("report.generating", report_id=report_id)
    
    # Update status to running
    update_report_status_sync(report_id, ReportStatus.RUNNING)
    
    try:
        # Get report details
        report = get_report_sync(report_id)
        if not report:
            raise ValueError(f"Report not found: {report_id}")
        
        logger.info(
            "report.fetching_data",
            report_id=report_id,
            factory_id=report.factory_id,
            format=report.format.value,
            device_count=len(report.device_ids),
        )
        
        # Fetch report data (run async function in sync context with db session)
        from app.core.database import AsyncSessionLocal
        
        async def fetch_data():
            async with AsyncSessionLocal() as db:
                return await get_report_data(
                    db=db,
                    factory_id=report.factory_id,
                    device_ids=report.device_ids,
                    start=report.date_range_start,
                    end=report.date_range_end,
                )
        
        data = async_to_sync(fetch_data)()
        
        # Get analytics results if included
        analytics = None
        if report.include_analytics and report.analytics_job_id:
            analytics = get_analytics_results_sync(report.analytics_job_id)
            logger.info(
                "report.analytics_included",
                report_id=report_id,
                has_analytics=analytics is not None,
            )
        
        # Build report config
        report_config = {
            "title": report.title or f"Report {report_id[:8]}",
            "include_analytics": report.include_analytics,
        }
        
        # Generate file based on format
        if report.format == ReportFormat.PDF:
            file_bytes = generate_pdf(report_config, data, analytics)
            content_type = "application/pdf"
            ext = "pdf"
        elif report.format == ReportFormat.EXCEL:
            file_bytes = generate_excel(report_config, data, analytics)
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
        else:  # JSON
            output_data = {**data, "analytics": analytics}
            file_bytes = json.dumps(output_data, indent=2, default=str).encode("utf-8")
            content_type = "application/json"
            ext = "json"
        
        logger.info(
            "report.generated",
            report_id=report_id,
            format=report.format.value,
            size_bytes=len(file_bytes),
        )
        
        # Upload to MinIO
        minio_client = get_minio_client()
        key = f"{report.factory_id}/reports/{report_id}.{ext}"
        
        minio_client.s3_client.put_object(
            Bucket=minio_client.bucket,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
        
        # Generate presigned URL (24 hour expiry)
        file_url = minio_client.generate_presigned_url(key, expiry=86400)
        
        # Update report as complete
        update_report_status_sync(
            report_id,
            ReportStatus.COMPLETE,
            file_url=file_url,
            file_size=len(file_bytes),
        )
        
        logger.info(
            "report.complete",
            report_id=report_id,
            file_url=file_url,
        )
        
    except Exception as e:
        logger.error(
            "report.failed",
            report_id=report_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        
        update_report_status_sync(
            report_id,
            ReportStatus.FAILED,
            error_message=str(e),
        )
        
        # Retry once after 60 seconds
        raise self.retry(exc=e, countdown=60)
