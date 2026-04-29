"""
Structured logging setup using structlog.
"""
import logging
import structlog
from app.config import get_settings


def setup_logging():
    """Configure structlog with JSON output for production, pretty for dev."""
    settings = get_settings()
    is_dev = settings.app_env == "development"

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if is_dev else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """Get a named logger instance."""
    return structlog.get_logger(name or __name__)
