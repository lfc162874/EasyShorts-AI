import time
from datetime import UTC, datetime

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.services.task_service import update_task_job

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.demo_tasks.demo_healthcheck_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def demo_healthcheck_task(self, task_job_id: int, payload: dict) -> dict:
    try:
        update_task_job(
            task_job_id=task_job_id,
            status="RUNNING",
            celery_task_id=self.request.id,
            progress=10,
        )
        time.sleep(1)
        result = {
            "echo": payload,
            "checked_at": datetime.now(UTC).isoformat(),
            "worker": "celery",
        }
        update_task_job(
            task_job_id=task_job_id,
            status="SUCCESS",
            result=result,
            progress=100,
        )
        return result
    except Exception as exc:
        logger.exception("demo task failed")
        update_task_job(
            task_job_id=task_job_id,
            status="FAILED",
            error_message=str(exc),
            retry_count=self.request.retries,
        )
        raise

