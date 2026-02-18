"""Analytics Celery task for running ML jobs."""
import asyncio
import uuid
from datetime import datetime
from typing import Optional

from asgiref.sync import async_to_sync
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.minio_client import get_minio_client
from app.core.logging import get_logger
from app.workers.celery_app import celery_app
from app.workers.analytics import (
    run_anomaly_detection,
    run_energy_forecast,
    run_failure_prediction,
    run_ai_copilot,
)
from app.services.telemetry_fetcher import fetch_as_dataframe
from app.models.analytics_job import AnalyticsJob, JobStatus, JobType

logger = get_logger(__name__)

# Create sync engine for Celery task (Celery runs sync code)
sync_engine = create_engine(
    settings.database_url.replace("+aiomysql", "+pymysql"),
    pool_pre_ping=True,
)
SyncSessionLocal = sessionmaker(bind=sync_engine)


def get_job_sync(job_id: str) -> Optional[AnalyticsJob]:
    """Get job by ID using sync session."""
    with SyncSessionLocal() as session:
        return session.get(AnalyticsJob, job_id)


def update_job_status_sync(
    job_id: str,
    status: JobStatus,
    result_url: Optional[str] = None,
    error_message: Optional[str] = None,
    results: Optional[dict] = None,
) -> None:
    """Update job status using sync session."""
    with SyncSessionLocal() as session:
        job = session.get(AnalyticsJob, job_id)
        if not job:
            logger.error("analytics_job.not_found", job_id=job_id)
            return
        
        job.status = status
        
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.utcnow()
        
        if status in (JobStatus.COMPLETE, JobStatus.FAILED):
            job.completed_at = datetime.utcnow()
        
        if result_url is not None:
            job.result_url = result_url
        
        if error_message is not None:
            job.error_message = error_message
        
        session.commit()
        
        logger.info(
            "analytics_job.status_updated",
            job_id=job_id,
            status=status.value,
            has_result=result_url is not None,
        )


@celery_app.task(name="run_analytics_job", bind=True, max_retries=1, queue="analytics")
def run_analytics_job(self, job_id: str):
    """Celery task to run analytics job.
    
    Args:
        job_id: UUID of the analytics job to run
    """
    logger.info("analytics_job.starting", job_id=job_id)
    
    # Update status to running
    update_job_status_sync(job_id, JobStatus.RUNNING)
    
    try:
        # Get job details
        job = get_job_sync(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        logger.info(
            "analytics_job.fetching_data",
            job_id=job_id,
            factory_id=job.factory_id,
            job_type=job.job_type.value,
            device_count=len(job.device_ids),
        )
        
        # Fetch telemetry data (run async function in sync context)
        df = async_to_sync(fetch_as_dataframe)(
            factory_id=job.factory_id,
            device_ids=job.device_ids,
            start=job.date_range_start,
            end=job.date_range_end,
        )
        
        logger.info(
            "analytics_job.data_fetched",
            job_id=job_id,
            rows=len(df),
            columns=list(df.columns) if not df.empty else [],
        )
        
        # Dispatch to appropriate model
        dispatch = {
            JobType.ANOMALY: run_anomaly_detection,
            JobType.FAILURE_PREDICTION: run_failure_prediction,
            JobType.ENERGY_FORECAST: run_energy_forecast,
            JobType.AI_COPILOT: run_ai_copilot,
        }
        
        fn = dispatch.get(job.job_type)
        if not fn:
            raise ValueError(f"Unknown job type: {job.job_type}")
        
        # Run the analysis
        results = fn(df)
        
        # Check for errors in results
        if "error" in results and len(results) == 1:
            # Only error key present, treat as failure
            logger.error("analytics_job.analysis_error", job_id=job_id, error=results["error"])
            update_job_status_sync(
                job_id,
                JobStatus.FAILED,
                error_message=results["error"],
            )
            return
        
        logger.info("analytics_job.analysis_complete", job_id=job_id, result_keys=list(results.keys()))
        
        # Upload results to MinIO
        minio_client = get_minio_client()
        result_url = minio_client.upload_json(
            factory_id=job.factory_id,
            job_id=job_id,
            data=results,
        )
        
        # Update job as complete
        update_job_status_sync(
            job_id,
            JobStatus.COMPLETE,
            result_url=result_url,
            results=results,
        )
        
        logger.info(
            "analytics_job.complete",
            job_id=job_id,
            result_url=result_url,
        )
        
    except Exception as e:
        logger.error(
            "analytics_job.failed",
            job_id=job_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        
        update_job_status_sync(
            job_id,
            JobStatus.FAILED,
            error_message=str(e),
        )
        
        # Retry once after 60 seconds
        raise self.retry(exc=e, countdown=60)
