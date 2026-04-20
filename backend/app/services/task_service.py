from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.constants import NewsFetchMode, TaskStatus
from app.core.logging import get_logger
from app.db.models.system import TaskJob
from app.db.session import SessionLocal

logger = get_logger(__name__)


def _sync_task_job(
    *,
    db: Session,
    task_job: TaskJob,
    status: str,
    celery_task_id: str | None = None,
    result: dict | None = None,
    error_message: str | None = None,
    progress: int | None = None,
    retry_count: int | None = None,
) -> TaskJob:
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

    db.add(task_job)
    db.commit()
    db.refresh(task_job)
    return task_job


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
        _sync_task_job(
            db=db,
            task_job=task_job,
            status=status,
            celery_task_id=celery_task_id,
            result=result,
            error_message=error_message,
            progress=progress,
            retry_count=retry_count,
        )


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
    try:
        async_result = demo_healthcheck_task.delay(task_job.id, payload or {})
    except Exception as exc:
        logger.warning("celery unavailable, running demo task inline: %s", exc)
        _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.RUNNING.value,
            celery_task_id=f"inline-{task_job.id}",
            progress=10,
        )
        result = {
            "echo": payload or {},
            "checked_at": datetime.now(UTC).isoformat(),
            "worker": "inline",
        }
        return _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.SUCCESS.value,
            result=result,
            progress=100,
        )

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
    from app.services.news_service import sync_news_source

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
    try:
        async_result = sync_news_source_task.delay(
            task_job.id,
            news_source_id,
            fetch_mode,
            triggered_by,
            request_id,
        )
    except Exception as exc:
        logger.warning("celery unavailable, running news sync inline for source %s: %s", news_source_id, exc)
        _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.RUNNING.value,
            celery_task_id=f"inline-{task_job.id}",
            progress=10,
        )
        with SessionLocal() as inline_db:
            result = sync_news_source(
                db=inline_db,
                source_id=news_source_id,
                fetch_mode=NewsFetchMode(fetch_mode),
                task_job_id=task_job.id,
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
        return _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.SUCCESS.value,
            result=task_result,
            progress=100,
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
    from app.schemas.news import NewsGenerateRequest
    from app.services.news_service import generate_news_content

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
    try:
        async_result = generate_news_content_task.delay(
            task_job.id,
            news_id,
            style,
            regenerate,
            triggered_by,
            request_id,
        )
    except Exception as exc:
        logger.warning("celery unavailable, running news content generation inline for news %s: %s", news_id, exc)
        _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.RUNNING.value,
            celery_task_id=f"inline-{task_job.id}",
            progress=10,
        )
        with SessionLocal() as inline_db:
            result = generate_news_content(
                db=inline_db,
                news_id=news_id,
                payload=NewsGenerateRequest(style=style, regenerate=regenerate),
                task_job_id=task_job.id,
                request_id=request_id,
                triggered_by=triggered_by,
            )
        task_result = {
            "news_id": result["news"]["id"],
            "style": style,
            "regenerate": regenerate,
            "status": result["news"]["status"],
        }
        return _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.SUCCESS.value,
            result=task_result,
            progress=100,
        )

    task_job.celery_task_id = async_result.id
    db.add(task_job)
    db.commit()
    db.refresh(task_job)
    return task_job


def dispatch_news_content_processing_task(
    *,
    db: Session,
    news_id: int,
    style: str,
    force: bool,
    triggered_by: int | None,
    request_id: str | None,
) -> TaskJob:
    from app.tasks.news_tasks import process_news_content_task
    from app.services.content_pipeline_service import process_existing_news_item
    from app.services.news_service import get_news

    task_job = create_task_job(
        db=db,
        task_name="news_content_process",
        task_type="content",
        queue_name="content_queue",
        triggered_by=triggered_by,
        request_id=request_id,
        payload={
            "news_id": news_id,
            "style": style,
            "force": force,
        },
    )
    try:
        async_result = process_news_content_task.delay(
            task_job.id,
            news_id,
            style,
            force,
            triggered_by,
            request_id,
        )
    except Exception as exc:
        logger.warning("celery unavailable, running news content processing inline for news %s: %s", news_id, exc)
        _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.RUNNING.value,
            celery_task_id=f"inline-{task_job.id}",
            progress=10,
        )
        with SessionLocal() as inline_db:
            news = get_news(inline_db, news_id)
            processed = process_existing_news_item(
                inline_db,
                news=news,
                style=style,
                force=force,
                request_id=request_id,
                task_job_id=task_job.id,
                triggered_by=triggered_by,
            )
        task_result = {
            "news_id": processed.id,
            "style": style,
            "force": force,
            "status": processed.status,
        }
        return _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.SUCCESS.value,
            result=task_result,
            progress=100,
        )

    task_job.celery_task_id = async_result.id
    db.add(task_job)
    db.commit()
    db.refresh(task_job)
    return task_job


def dispatch_agent_news_run_task(
    *,
    db: Session,
    news_id: int,
    triggered_by: int | None,
    request_id: str | None,
    model_name: str | None = None,
    force: bool = False,
    parent_run_id: int | None = None,
    start_from_step_order: int = 1,
    seed_step_outputs: dict | None = None,
) -> TaskJob:
    from app.services.agent_run_service import create_agent_run_for_news, execute_agent_run
    from app.tasks.agent_tasks import run_agent_news_task

    agent_run = create_agent_run_for_news(
        db,
        news_id=news_id,
        model_name=model_name,
        force=force,
        triggered_by=triggered_by,
        request_id=request_id,
        parent_run_id=parent_run_id,
        start_from_step_order=start_from_step_order,
        seed_step_outputs=seed_step_outputs,
    )

    task_job = create_task_job(
        db=db,
        task_name="agent_news_run",
        task_type="agent",
        queue_name="content_queue",
        triggered_by=triggered_by,
        request_id=request_id,
        payload={
            "news_id": news_id,
            "agent_run_id": agent_run.id,
            "model_name": agent_run.model_name,
            "force": force,
            "parent_run_id": parent_run_id,
            "start_from_step_order": start_from_step_order,
        },
    )
    agent_run.task_job_id = task_job.id
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    try:
        async_result = run_agent_news_task.delay(task_job.id, agent_run.id)
    except Exception as exc:
        logger.warning("celery unavailable, running agent news task inline for news %s: %s", news_id, exc)
        _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.RUNNING.value,
            celery_task_id=f"inline-{task_job.id}",
            progress=10,
        )
        with SessionLocal() as inline_db:
            run = execute_agent_run(inline_db, agent_run.id)
        task_result = {
            "agent_run_id": run.id,
            "status": run.status,
            "model_name": run.model_name,
            "current_step": run.current_step,
        }
        return _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.SUCCESS.value,
            result=task_result,
            progress=100,
        )

    task_job.celery_task_id = async_result.id
    db.add(task_job)
    db.commit()
    db.refresh(task_job)
    return task_job


def dispatch_agent_digest_task(
    *,
    db: Session,
    report_type: str,
    report_date: date,
    topic_ids: list[int] | None,
    limit: int,
    model_name: str | None,
    force: bool,
    triggered_by: int | None,
    request_id: str | None,
    parent_run_id: int | None = None,
) -> TaskJob:
    from app.services.digest_service import create_agent_run_for_digest, execute_digest_run
    from app.tasks.agent_tasks import run_agent_digest_task

    agent_run = create_agent_run_for_digest(
        db,
        report_type=report_type,
        report_date=report_date,
        topic_ids=topic_ids,
        limit=limit,
        model_name=model_name,
        force=force,
        triggered_by=triggered_by,
        request_id=request_id,
        parent_run_id=parent_run_id,
    )

    task_job = create_task_job(
        db=db,
        task_name="agent_digest_run",
        task_type="agent",
        queue_name="content_queue",
        triggered_by=triggered_by,
        request_id=request_id,
        payload={
            "report_type": report_type,
            "report_date": report_date.isoformat() if hasattr(report_date, "isoformat") else report_date,
            "topic_ids": list(topic_ids or []),
            "limit": limit,
            "agent_run_id": agent_run.id,
            "model_name": agent_run.model_name,
            "force": force,
            "parent_run_id": parent_run_id,
        },
    )
    agent_run.task_job_id = task_job.id
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    try:
        async_result = run_agent_digest_task.delay(task_job.id, agent_run.id)
    except Exception as exc:
        logger.warning("celery unavailable, running agent digest task inline: %s", exc)
        _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.RUNNING.value,
            celery_task_id=f"inline-{task_job.id}",
            progress=10,
        )
        with SessionLocal() as inline_db:
            run = execute_digest_run(inline_db, agent_run.id)
        task_result = {
            "agent_run_id": run.id,
            "status": run.status,
            "model_name": run.model_name,
            "current_step": run.current_step,
        }
        return _sync_task_job(
            db=db,
            task_job=task_job,
            status=TaskStatus.SUCCESS.value,
            result=task_result,
            progress=100,
        )

    task_job.celery_task_id = async_result.id
    db.add(task_job)
    db.commit()
    db.refresh(task_job)
    return task_job
