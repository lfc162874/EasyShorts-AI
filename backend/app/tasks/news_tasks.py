from __future__ import annotations

from app.core.celery_app import celery_app
from app.core.constants import NewsFetchMode, TaskStatus
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.services.content_pipeline_service import process_existing_news_item
from app.services.news_service import generate_news_content, list_due_news_sources, sync_news_source
from app.services.task_service import update_task_job
from app.schemas.news import NewsGenerateRequest

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.news_tasks.sync_news_source_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def sync_news_source_task(
    self,
    task_job_id: int,
    news_source_id: int,
    fetch_mode: str = NewsFetchMode.MANUAL.value,
    triggered_by: int | None = None,
    request_id: str | None = None,
) -> dict:
    try:
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.RUNNING.value,
            celery_task_id=self.request.id,
            progress=10,
        )
        with SessionLocal() as db:
            result = sync_news_source(
                db=db,
                source_id=news_source_id,
                fetch_mode=NewsFetchMode(fetch_mode),
                task_job_id=task_job_id,
                request_id=request_id,
                triggered_by=triggered_by,
            )
        task_result = {
            "source_id": result["source"]["id"],
            "fetch_record_id": result["fetch_record"]["id"],
            "total_count": result["total_count"],
            "new_count": result["new_count"],
            "duplicate_count": result["duplicate_count"],
            "merged_count": result.get("merged_count", 0),
            "filtered_count": result["filtered_count"],
            "rejected_count": result["rejected_count"],
            "promoted_count": result.get("promoted_count", 0),
        }
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.SUCCESS.value,
            result=task_result,
            progress=100,
        )
        return task_result
    except Exception as exc:
        logger.exception("news source sync task failed")
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.FAILED.value,
            error_message=str(exc),
            retry_count=self.request.retries,
        )
        raise


@celery_app.task(
    bind=True,
    name="app.tasks.news_tasks.generate_news_content_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_news_content_task(
    self,
    task_job_id: int,
    news_id: int,
    style: str = "professional",
    regenerate: bool = False,
    triggered_by: int | None = None,
    request_id: str | None = None,
) -> dict:
    try:
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.RUNNING.value,
            celery_task_id=self.request.id,
            progress=10,
        )
        with SessionLocal() as db:
            result = generate_news_content(
                db=db,
                news_id=news_id,
                payload=NewsGenerateRequest(style=style, regenerate=regenerate),
                task_job_id=task_job_id,
                request_id=request_id,
                triggered_by=triggered_by,
            )
        task_result = {
            "news_id": result["news"]["id"],
            "style": style,
            "regenerate": regenerate,
            "status": result["news"]["status"],
        }
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.SUCCESS.value,
            result=task_result,
            progress=100,
        )
        return task_result
    except Exception as exc:
        logger.exception("news content generation task failed")
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.FAILED.value,
            error_message=str(exc),
            retry_count=self.request.retries,
        )
        raise


@celery_app.task(
    bind=False,
    name="app.tasks.news_tasks.sync_due_news_sources_task",
)
def sync_due_news_sources_task() -> dict:
    processed: list[dict] = []
    with SessionLocal() as db:
        due_sources = list_due_news_sources(db)
        for source in due_sources:
            try:
                result = sync_news_source(
                    db=db,
                    source_id=source.id,
                    fetch_mode=NewsFetchMode.SCHEDULED,
                    triggered_by=None,
                )
                processed.append(
                    {
                        "source_id": result["source"]["id"],
                        "fetch_record_id": result["fetch_record"]["id"],
                        "total_count": result["total_count"],
                        "new_count": result["new_count"],
                    }
                )
            except Exception:  # pragma: no cover - scheduler should continue processing other sources
                logger.exception("scheduled sync failed for source %s", source.id)
    return {
        "processed_count": len(processed),
        "sources": processed,
    }


@celery_app.task(
    bind=True,
    name="app.tasks.news_tasks.process_news_content_task",
)
def process_news_content_task(
    self,
    task_job_id: int,
    news_id: int,
    style: str = "professional",
    force: bool = False,
    triggered_by: int | None = None,
    request_id: str | None = None,
) -> dict:
    try:
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.RUNNING.value,
            celery_task_id=self.request.id,
            progress=10,
        )
        with SessionLocal() as db:
            from app.services.news_service import get_news

            news = get_news(db, news_id)
            processed = process_existing_news_item(
                db,
                news=news,
                style=style,
                force=force,
                request_id=request_id,
                task_job_id=task_job_id,
                triggered_by=triggered_by,
            )
        task_result = {
            "news_id": processed.id,
            "style": style,
            "force": force,
            "status": processed.status,
        }
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.SUCCESS.value,
            result=task_result,
            progress=100,
        )
        return task_result
    except Exception as exc:
        logger.exception("news content processing task failed")
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.FAILED.value,
            error_message=str(exc),
            retry_count=self.request.retries,
        )
        raise
