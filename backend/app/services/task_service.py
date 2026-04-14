from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.constants import NewsFetchMode, TaskStatus
from app.db.models.system import TaskJob
from app.db.session import SessionLocal


def create_task_job(
    *,
    db: Session,
    task_name: str,
    task_type: str,
    queue_name: str,
    triggered_by: int | None,
    request_id: str | None,
    payload: dict | None = None,
) -> TaskJob:
    task_job = TaskJob(
        task_name=task_name,
        task_type=task_type,
        queue_name=queue_name,
        status=TaskStatus.PENDING.value,
        triggered_by=triggered_by,
        request_id=request_id,
        payload=payload,
    )
    db.add(task_job)
    db.commit()
    db.refresh(task_job)
    return task_job


def update_task_job(
    *,
    task_job_id: int,
    status: str,
    celery_task_id: str | None = None,
    result: dict | None = None,
    error_message: str | None = None,
    progress: int | None = None,
    retry_count: int | None = None,
) -> None:
    with SessionLocal() as db:
        task_job = db.get(TaskJob, task_job_id)
        if task_job is None:
            return
        task_job.status = status
        if celery_task_id:
            task_job.celery_task_id = celery_task_id
        if result is not None:
            task_job.result = result
        if error_message is not None:
            task_job.error_message = error_message
        if progress is not None:
            task_job.progress = progress
        if retry_count is not None:
            task_job.retry_count = retry_count

        if status == TaskStatus.RUNNING.value and task_job.started_at is None:
            task_job.started_at = datetime.now(UTC)
        if status in {TaskStatus.SUCCESS.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value}:
            task_job.finished_at = datetime.now(UTC)
        db.commit()


def dispatch_demo_task(
    *,
    db: Session,
    triggered_by: int | None,
    request_id: str | None,
    payload: dict | None,
) -> TaskJob:
    from app.tasks.demo_tasks import demo_healthcheck_task

    task_job = create_task_job(
        db=db,
        task_name="demo_healthcheck",
        task_type="system",
        queue_name="system_queue",
        triggered_by=triggered_by,
        request_id=request_id,
        payload=payload,
    )
    async_result = demo_healthcheck_task.delay(task_job.id, payload or {})
    task_job.celery_task_id = async_result.id
    db.add(task_job)
    db.commit()
    db.refresh(task_job)
    return task_job


def dispatch_news_source_sync_task(
    *,
    db: Session,
    news_source_id: int,
    triggered_by: int | None,
    request_id: str | None,
    fetch_mode: str = NewsFetchMode.MANUAL.value,
) -> TaskJob:
    from app.tasks.news_tasks import sync_news_source_task

    task_job = create_task_job(
        db=db,
        task_name="news_source_sync",
        task_type="content",
        queue_name="news_queue",
        triggered_by=triggered_by,
        request_id=request_id,
        payload={
            "news_source_id": news_source_id,
            "fetch_mode": fetch_mode,
        },
    )
    async_result = sync_news_source_task.delay(
        task_job.id,
        news_source_id,
        fetch_mode,
        triggered_by,
        request_id,
    )
    task_job.celery_task_id = async_result.id
    db.add(task_job)
    db.commit()
    db.refresh(task_job)
    return task_job


def dispatch_news_content_generation_task(
    *,
    db: Session,
    news_id: int,
    style: str,
    regenerate: bool,
    triggered_by: int | None,
    request_id: str | None,
) -> TaskJob:
    from app.tasks.news_tasks import generate_news_content_task

    task_job = create_task_job(
        db=db,
        task_name="news_content_generate",
        task_type="content",
        queue_name="content_queue",
        triggered_by=triggered_by,
        request_id=request_id,
        payload={
            "news_id": news_id,
            "style": style,
            "regenerate": regenerate,
        },
    )
    async_result = generate_news_content_task.delay(
        task_job.id,
        news_id,
        style,
        regenerate,
        triggered_by,
        request_id,
    )
    task_job.celery_task_id = async_result.id
    db.add(task_job)
    db.commit()
    db.refresh(task_job)
    return task_job
