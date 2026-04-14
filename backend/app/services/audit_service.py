import traceback

from fastapi import Request

from app.core.constants import OperationStatus
from app.core.logging import get_logger
from app.db.models.system import ErrorLog, OperationLog
from app.db.session import SessionLocal

logger = get_logger(__name__)


def record_operation_log(
    *,
    module: str,
    action: str,
    operator_id: int | None = None,
    operator_name: str | None = None,
    request: Request | None = None,
    status: str = OperationStatus.SUCCESS.value,
    message: str | None = None,
    biz_type: str | None = None,
    biz_id: str | None = None,
    details: dict | None = None,
) -> None:
    with SessionLocal() as db:
        log = OperationLog(
            module=module,
            action=action,
            biz_type=biz_type,
            biz_id=biz_id,
            operator_id=operator_id,
            operator_name=operator_name,
            request_id=getattr(request.state, "request_id", None) if request else None,
            method=request.method if request else None,
            path=request.url.path if request else None,
            ip_address=request.client.host if request and request.client else None,
            status=status,
            message=message,
            details=details,
        )
        db.add(log)
        db.commit()


def record_error_log(
    *,
    request: Request | None,
    error_code: int,
    error_type: str,
    error_message: str,
    exc: Exception | None = None,
) -> None:
    stack_trace = traceback.format_exc() if exc else None
    try:
        with SessionLocal() as db:
            log = ErrorLog(
                request_id=getattr(request.state, "request_id", None) if request else None,
                path=request.url.path if request else None,
                method=request.method if request else None,
                user_id=getattr(request.state, "user_id", None) if request else None,
                error_code=error_code,
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack_trace,
            )
            db.add(log)
            db.commit()
    except Exception:  # pragma: no cover - secondary logging must not block requests
        logger.exception("failed to persist error log")

