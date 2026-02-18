"""Celery application configuration."""
from celery import Celery

from app.core.config import settings


celery_app = Celery("factoryops")

celery_app.config_from_object({
    "broker_url": settings.celery_broker_url,
    "result_backend": settings.celery_result_backend,
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "task_routes": {
        "evaluate_rules": {"queue": "rule_engine"},
        "run_analytics_job": {"queue": "analytics"},
        "generate_report": {"queue": "reporting"},
        "send_notifications": {"queue": "notifications"},
    },
    "task_acks_late": True,
    "task_reject_on_worker_lost": True,
    "worker_prefetch_multiplier": 1,  # Process one task at a time
})
