from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.core.exceptions import ConflictException, NotFoundException
from app.core.response import success_response
from app.db.models.rbac import User
from app.db.models.system import ErrorLog, OperationLog, PlatformAccount, SystemConfig, TaskJob
from app.schemas.system import (
    DemoTaskRequest,
    PlatformAccountCreate,
    PlatformAccountUpdate,
    SystemConfigCreate,
    SystemConfigUpdate,
)
from app.services.audit_service import record_operation_log
from app.services.task_service import dispatch_demo_task

router = APIRouter()


def serialize_config(config: SystemConfig) -> dict:
    return {
        "id": config.id,
        "category": config.category,
        "config_key": config.config_key,
        "config_value": "***" if config.is_secret else config.config_value,
        "value_type": config.value_type,
        "description": config.description,
        "is_secret": config.is_secret,
        "is_enabled": config.is_enabled,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }


def serialize_platform_account(account: PlatformAccount) -> dict:
    return {
        "id": account.id,
        "platform": account.platform,
        "display_name": account.display_name,
        "account_id": account.account_id,
        "auth_status": account.auth_status,
        "access_token": "***" if account.access_token else None,
        "refresh_token": "***" if account.refresh_token else None,
        "expires_at": account.expires_at,
        "extra": account.extra,
        "is_enabled": account.is_enabled,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
    }


@router.get("/configs")
def list_configs(
    _: User = Depends(require_permission("system:config:list")),
    db: Session = Depends(get_db),
):
    configs = db.scalars(select(SystemConfig).order_by(SystemConfig.category.asc(), SystemConfig.id.desc())).all()
    items = [serialize_config(item) for item in configs]
    return success_response({"items": items, "total": len(items)})


@router.post("/configs")
def create_config(
    payload: SystemConfigCreate,
    request: Request,
    current_user: User = Depends(require_permission("system:config:list")),
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(SystemConfig).where(
            SystemConfig.category == payload.category,
            SystemConfig.config_key == payload.config_key,
        )
    )
    if existing:
        raise ConflictException(message="配置项已存在")
    config = SystemConfig(**payload.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    record_operation_log(
        module="config",
        action="create",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="system_config",
        biz_id=str(config.id),
        message=f"创建配置 {config.category}:{config.config_key}",
    )
    return success_response(serialize_config(config), status_code=201)


@router.put("/configs/{config_id}")
def update_config(
    config_id: int,
    payload: SystemConfigUpdate,
    request: Request,
    current_user: User = Depends(require_permission("system:config:list")),
    db: Session = Depends(get_db),
):
    config = db.get(SystemConfig, config_id)
    if config is None:
        raise NotFoundException(message="配置不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    db.add(config)
    db.commit()
    db.refresh(config)
    record_operation_log(
        module="config",
        action="update",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="system_config",
        biz_id=str(config.id),
        message=f"更新配置 {config.category}:{config.config_key}",
    )
    return success_response(serialize_config(config))


@router.get("/platform-accounts")
def list_platform_accounts(
    _: User = Depends(require_permission("system:platform-account:list")),
    db: Session = Depends(get_db),
):
    accounts = db.scalars(select(PlatformAccount).order_by(PlatformAccount.id.desc())).all()
    items = [serialize_platform_account(account) for account in accounts]
    return success_response({"items": items, "total": len(items)})


@router.post("/platform-accounts")
def create_platform_account(
    payload: PlatformAccountCreate,
    request: Request,
    current_user: User = Depends(require_permission("system:platform-account:list")),
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(PlatformAccount).where(
            PlatformAccount.platform == payload.platform,
            PlatformAccount.account_id == payload.account_id,
        )
    )
    if existing:
        raise ConflictException(message="平台账号已存在")
    account = PlatformAccount(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    record_operation_log(
        module="platform_account",
        action="create",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="platform_account",
        biz_id=str(account.id),
        message=f"创建平台账号 {account.platform}:{account.account_id}",
    )
    return success_response(serialize_platform_account(account), status_code=201)


@router.put("/platform-accounts/{account_id}")
def update_platform_account(
    account_id: int,
    payload: PlatformAccountUpdate,
    request: Request,
    current_user: User = Depends(require_permission("system:platform-account:list")),
    db: Session = Depends(get_db),
):
    account = db.get(PlatformAccount, account_id)
    if account is None:
        raise NotFoundException(message="平台账号不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    db.add(account)
    db.commit()
    db.refresh(account)
    record_operation_log(
        module="platform_account",
        action="update",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="platform_account",
        biz_id=str(account.id),
        message=f"更新平台账号 {account.platform}:{account.account_id}",
    )
    return success_response(serialize_platform_account(account))


@router.get("/logs/operations")
def list_operation_logs(
    page: int = 1,
    page_size: int = 20,
    _: User = Depends(require_permission("system:log:list")),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count()).select_from(OperationLog)) or 0
    items = db.scalars(
        select(OperationLog)
        .order_by(OperationLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return success_response({"items": items, "page": page, "page_size": page_size, "total": total})


@router.get("/logs/errors")
def list_error_logs(
    page: int = 1,
    page_size: int = 20,
    _: User = Depends(require_permission("system:log:list")),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count()).select_from(ErrorLog)) or 0
    items = db.scalars(
        select(ErrorLog)
        .order_by(ErrorLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return success_response({"items": items, "page": page, "page_size": page_size, "total": total})


@router.get("/tasks")
def list_task_jobs(
    page: int = 1,
    page_size: int = 20,
    _: User = Depends(require_permission("system:task:list")),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count()).select_from(TaskJob)) or 0
    items = db.scalars(
        select(TaskJob)
        .order_by(TaskJob.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return success_response({"items": items, "page": page, "page_size": page_size, "total": total})


@router.post("/tasks/demo")
def create_demo_task(
    payload: DemoTaskRequest,
    request: Request,
    current_user: User = Depends(require_permission("system:task:list")),
    db: Session = Depends(get_db),
):
    task_job = dispatch_demo_task(
        db=db,
        triggered_by=current_user.id,
        request_id=request.state.request_id,
        payload=payload.payload,
    )
    record_operation_log(
        module="task",
        action="dispatch_demo",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="task_job",
        biz_id=str(task_job.id),
        message=f"派发演示任务 {task_job.id}",
    )
    return success_response(task_job, status_code=202)
