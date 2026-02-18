"""Celery workers package."""
from app.workers.celery_app import celery_app
from app.workers.analytics import (
    run_anomaly_detection,
    run_energy_forecast,
    run_failure_prediction,
    run_ai_copilot,
)
from app.workers.analytics_task import run_analytics_job

__all__ = [
    "celery_app",
    "run_anomaly_detection",
    "run_energy_forecast",
    "run_failure_prediction",
    "run_ai_copilot",
    "run_analytics_job",
]
