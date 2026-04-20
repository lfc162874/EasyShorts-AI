from __future__ import annotations

from app.core.celery_app import celery_app
from app.core.constants import TaskStatus
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.services.digest_service import execute_digest_run
from app.services.agent_run_service import execute_agent_run
from app.services.task_service import update_task_job

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.agent_tasks.run_agent_news_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_agent_news_task(self, task_job_id: int, agent_run_id: int) -> dict:
    try:
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.RUNNING.value,
            celery_task_id=self.request.id,
            progress=10,
        )
        with SessionLocal() as db:
            run = execute_agent_run(db, agent_run_id)
        task_result = {
            "agent_run_id": run.id,
            "status": run.status,
            "model_name": run.model_name,
            "current_step": run.current_step,
        }
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.SUCCESS.value,
            result=task_result,
            progress=100,
        )
        return task_result
    except Exception as exc:
        logger.exception("agent news run task failed")
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.FAILED.value,
            error_message=str(exc),
            retry_count=self.request.retries,
        )
        raise


@celery_app.task(
    bind=True,
    name="app.tasks.agent_tasks.run_agent_digest_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_agent_digest_task(self, task_job_id: int, agent_run_id: int) -> dict:
    try:
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.RUNNING.value,
            celery_task_id=self.request.id,
            progress=10,
        )
        with SessionLocal() as db:
            run = execute_digest_run(db, agent_run_id)
        task_result = {
            "agent_run_id": run.id,
            "status": run.status,
            "model_name": run.model_name,
            "current_step": run.current_step,
        }
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.SUCCESS.value,
            result=task_result,
            progress=100,
        )
        return task_result
    except Exception as exc:
        logger.exception("agent digest task failed")
        update_task_job(
            task_job_id=task_job_id,
            status=TaskStatus.FAILED.value,
            error_message=str(exc),
            retry_count=self.request.retries,
        )
        raise
