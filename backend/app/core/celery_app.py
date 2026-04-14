from celery import Celery
from datetime import timedelta

from app.core.config import settings

celery_app = Celery("easy_shorts", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_default_queue="system_queue",
    task_routes={
        "app.tasks.demo_tasks.*": {"queue": "system_queue"},
        "app.tasks.news_tasks.sync_news_source_task": {"queue": "news_queue"},
        "app.tasks.news_tasks.sync_due_news_sources_task": {"queue": "news_queue"},
        "app.tasks.news_tasks.generate_news_content_task": {"queue": "content_queue"},
    },
    beat_schedule={
        "sync-due-news-sources-every-10-minutes": {
            "task": "app.tasks.news_tasks.sync_due_news_sources_task",
            "schedule": timedelta(minutes=10),
        },
    },
)
celery_app.autodiscover_tasks(["app.tasks"])
