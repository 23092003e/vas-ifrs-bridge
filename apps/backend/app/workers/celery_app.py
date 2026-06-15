"""Celery application instance."""

from __future__ import annotations

from celery import Celery

from app.settings import settings

celery_app = Celery(
    "vas_ifrs",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.ingestion_tasks",
        "app.workers.gl_tasks",
        "app.workers.report_tasks",
    ],
)

celery_app.conf.update(task_serializer="json", result_serializer="json")
