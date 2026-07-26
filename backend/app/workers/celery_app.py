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


@celery_app.task(name="aibpo.ping")
def ping() -> str:
    """Smoke-test task to confirm the worker is wired up correctly."""
    return "pong"


# Phase 2: import task modules so the worker registers them. Runtime import
# placed after `celery_app` is defined to avoid a circular import, since
# app.workers.tasks imports `celery_app` from this module.
from app.workers import tasks  # noqa: E402,F401
