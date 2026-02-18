"""Structured JSON logging configuration."""
import sys
import structlog
from structlog.typing import FilteringBoundLogger

from app.core.config import settings


def configure_logging():
    """Configure structlog for JSON logging."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]

    if settings.app_env == "development":
        # Console renderer for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # JSON renderer for production
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(__import__("logging"), settings.log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """Get a structured logger with service context."""
    logger = structlog.get_logger(name)
    return logger.bind(service="api")


# Configure on module import
configure_logging()
