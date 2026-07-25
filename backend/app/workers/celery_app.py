"""Celery application. Task modules (ingestion, ML inference, report generation)
are added in later phases and imported here so the worker discovers them."""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "aibpo",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Phase 2+ will add: celery_app.autodiscover_tasks(["app.workers"])


@celery_app.task(name="aibpo.ping")
def ping() -> str:
    """Smoke-test task to confirm the worker is wired up correctly."""
    return "pong"
