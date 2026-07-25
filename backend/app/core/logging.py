"""Structured logging setup. Import `logger` anywhere in the app."""
import sys

from loguru import logger

from app.core.config import get_settings

settings = get_settings()

logger.remove()
logger.add(
    sys.stdout,
    level="DEBUG" if settings.environment == "development" else "INFO",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    ),
    serialize=settings.environment == "production",
)

__all__ = ["logger"]
