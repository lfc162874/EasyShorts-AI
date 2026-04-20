from fastapi import APIRouter, Depends, Request
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.core.response import success_response
from app.db.models.agent import AgentRun, AgentRunStep, HotTopic, HotTopicItem
from app.db.models.rbac import User
from app.schemas.agent import (
    AgentConfigUpdateRequest,
    AgentRunRequest,
    DigestPushRequest,
    DigestReportQuery,
    DigestRunRequest,
    PushRecordQuery,
)
from app.services.agent_config_service import get_agent_config, get_agent_model_options, update_agent_config
from app.services.agent_run_service import (
    execute_push_plan,
    get_agent_run,
    get_agent_run_detail,
    get_hot_topic_detail,
    get_push_plan_detail,
    list_agent_runs,
    list_hot_topics,
    list_push_plans,
    serialize_hot_topic,
    serialize_push_plan,
)
from app.services.audit_service import record_operation_log
from app.services.digest_service import (
    get_digest_report_detail,
    list_digest_run_records,
    push_digest_report,
    serialize_digest_report,
)
from app.services.push_record_service import list_push_records, serialize_push_record
from app.services.task_service import dispatch_agent_news_run_task
from app.services.task_service import dispatch_agent_digest_task

router = APIRouter()


@router.get("/config")
def get_config(
    _: User = Depends(require_permission("agent:config:list")),
    db: Session = Depends(get_db),
):
    return success_response(get_agent_config(db))


@router.put("/config")
def save_config(
    payload: AgentConfigUpdateRequest,
    request: Request,
    current_user: User = Depends(require_permission("agent:config:update")),
    db: Session = Depends(get_db),
):
    config = update_agent_config(db, payload.model_dump(exclude_unset=True))
    record_operation_log(
        module="agent",
        action="update_config",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="agent_config",
        biz_id="default",
        message="更新 Agent 配置",
    )
    return success_response(config)


@router.get("/models")
def get_models(
    _: User = Depends(require_permission("agent:model:list")),
    db: Session = Depends(get_db),
):
    return success_response(get_agent_model_options(db))


@router.post("/runs/news/{news_id}")
def run_news_agent(
    news_id: int,
    request: Request,
    payload: AgentRunRequest | None = None,
    current_user: User = Depends(require_permission("agent:run:create")),
    db: Session = Depends(get_db),
):
    payload = payload or AgentRunRequest()
    task_job = dispatch_agent_news_run_task(
        db=db,
        news_id=news_id,
        triggered_by=current_user.id,
        request_id=request.state.request_id,
        model_name=payload.model_name,
        force=payload.force,
    )
    record_operation_log(
        module="agent",
        action="run_news",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="news",
        biz_id=str(news_id),
        message=f"触发内容智能处理 {news_id}",
    )
    return success_response(task_job, status_code=202)


@router.post("/runs/digest")
def run_digest_agent(
    request: Request,
    payload: DigestRunRequest | None = None,
    current_user: User = Depends(require_permission("agent:run:digest:create")),
    db: Session = Depends(get_db),
):
    payload = payload or DigestRunRequest()
    report_date = payload.report_date or date.today()
    task_job = dispatch_agent_digest_task(
        db=db,
        report_type=payload.report_type.value if hasattr(payload.report_type, "value") else str(payload.report_type),
        report_date=report_date,
        topic_ids=payload.topic_ids,
        limit=payload.limit,
        model_name=payload.model_name,
        force=payload.force,
        triggered_by=current_user.id,
        request_id=request.state.request_id,
    )
    record_operation_log(
        module="agent",
        action="run_digest",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="digest",
        biz_id=f"{payload.report_type.value if hasattr(payload.report_type, 'value') else str(payload.report_type)}:{report_date.isoformat()}",
        message=f"触发简报生成 {report_date.isoformat()}",
    )
    return success_response(task_job, status_code=202)


@router.get("/runs")
def list_runs(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    run_type: str | None = None,
    biz_type: str | None = None,
    model_name: str | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("agent:run:list")),
    db: Session = Depends(get_db),
):
    items, total = list_agent_runs(
        db,
        page=page,
        page_size=page_size,
        status=status,
        run_type=run_type,
        biz_type=biz_type,
        model_name=model_name,
        keyword=keyword,
    )
    return success_response(
        {
            "items": [get_agent_run_detail(db, item.id) for item in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/runs/{run_id}")
def get_run(
    run_id: int,
    _: User = Depends(require_permission("agent:run:list")),
    db: Session = Depends(get_db),
):
    return success_response(get_agent_run_detail(db, run_id))


@router.post("/runs/{run_id}/retry")
def retry_run(
    run_id: int,
    request: Request,
    payload: AgentRunRequest | None = None,
    current_user: User = Depends(require_permission("agent:run:retry")),
    db: Session = Depends(get_db),
):
    origin = get_agent_run(db, run_id)
    retry_payload = payload or AgentRunRequest()
    task_job = dispatch_agent_news_run_task(
        db=db,
        news_id=int(origin.biz_id),
        triggered_by=current_user.id,
        request_id=request.state.request_id,
        model_name=retry_payload.model_name or origin.model_name,
        force=retry_payload.force or bool((origin.payload or {}).get("force")),
        parent_run_id=origin.id,
        start_from_step_order=1,
    )
    record_operation_log(
        module="agent",
        action="retry_run",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="agent_run",
        biz_id=str(run_id),
        message=f"重试 Agent 运行 {run_id}",
    )
    return success_response(task_job, status_code=202)


@router.post("/runs/{run_id}/steps/{step_id}/retry")
def retry_step(
    run_id: int,
    step_id: int,
    request: Request,
    payload: AgentRunRequest | None = None,
    current_user: User = Depends(require_permission("agent:run:step:retry")),
    db: Session = Depends(get_db),
):
    origin = get_agent_run(db, run_id)
    step = db.get(AgentRunStep, step_id)
    if step is None or step.run_id != origin.id:
        from app.core.exceptions import NotFoundException

        raise NotFoundException(message="Agent 步骤不存在")

    prior_steps = db.scalars(
        select(AgentRunStep)
        .where(AgentRunStep.run_id == origin.id, AgentRunStep.step_order < step.step_order)
        .order_by(AgentRunStep.step_order.asc())
    ).all()
    seed_step_outputs = {
        prior_step.step_code: dict(prior_step.result or {})
        for prior_step in prior_steps
        if prior_step.result is not None
    }
    retry_payload = payload or AgentRunRequest()
    task_job = dispatch_agent_news_run_task(
        db=db,
        news_id=int(origin.biz_id),
        triggered_by=current_user.id,
        request_id=request.state.request_id,
        model_name=retry_payload.model_name or origin.model_name,
        force=retry_payload.force or bool((origin.payload or {}).get("force")),
        parent_run_id=origin.id,
        start_from_step_order=step.step_order,
        seed_step_outputs=seed_step_outputs,
    )
    record_operation_log(
        module="agent",
        action="retry_step",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="agent_run",
        biz_id=f"{run_id}:{step_id}",
        message=f"重试 Agent 步骤 {step_id}",
    )
    return success_response(task_job, status_code=202)


@router.post("/hot-topics/{topic_id}/reprocess")
def reprocess_hot_topic(
    topic_id: int,
    request: Request,
    payload: AgentRunRequest | None = None,
    current_user: User = Depends(require_permission("agent:hot-topic:reprocess")),
    db: Session = Depends(get_db),
):
    payload = payload or AgentRunRequest(force=True)
    topic = db.get(HotTopic, topic_id)
    if topic is None:
        from app.core.exceptions import NotFoundException

        raise NotFoundException(message="热点不存在")

    news_id = topic.primary_news_id
    if news_id is None:
        primary_item = db.scalar(
            select(HotTopicItem)
            .where(HotTopicItem.topic_id == topic.id)
            .order_by(HotTopicItem.is_primary.desc(), HotTopicItem.weight.desc(), HotTopicItem.id.asc())
        )
        if primary_item is not None:
            news_id = primary_item.news_id
    if news_id is None:
        from app.core.exceptions import ValidationException

        raise ValidationException(message="热点缺少可重处理的原始内容")

    task_job = dispatch_agent_news_run_task(
        db=db,
        news_id=news_id,
        triggered_by=current_user.id,
        request_id=request.state.request_id,
        model_name=payload.model_name,
        force=True,
        parent_run_id=None,
        start_from_step_order=1,
    )
    record_operation_log(
        module="agent",
        action="reprocess_hot_topic",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="hot_topic",
        biz_id=str(topic.id),
        message=f"重处理热点 {topic.id}",
    )
    return success_response(task_job, status_code=202)


@router.get("/hot-topics")
def list_topics(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    category: str | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("agent:hot-topic:list")),
    db: Session = Depends(get_db),
):
    items, total = list_hot_topics(
        db,
        page=page,
        page_size=page_size,
        status=status,
        category=category,
        keyword=keyword,
    )
    return success_response(
        {
            "items": [serialize_hot_topic(item) for item in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/hot-topics/{topic_id}")
def get_topic(
    topic_id: int,
    _: User = Depends(require_permission("agent:hot-topic:list")),
    db: Session = Depends(get_db),
):
    return success_response(get_hot_topic_detail(db, topic_id))


@router.get("/push-plans")
def list_plans(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    biz_type: str | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("agent:push-plan:list")),
    db: Session = Depends(get_db),
):
    items, total = list_push_plans(
        db,
        page=page,
        page_size=page_size,
        status=status,
        biz_type=biz_type,
        keyword=keyword,
    )
    return success_response(
        {
            "items": [serialize_push_plan(item) for item in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/push-plans/{plan_id}")
def get_plan(
    plan_id: int,
    _: User = Depends(require_permission("agent:push-plan:list")),
    db: Session = Depends(get_db),
):
    return success_response(get_push_plan_detail(db, plan_id))


@router.post("/push-plans/{plan_id}/execute")
def execute_plan(
    plan_id: int,
    request: Request,
    current_user: User = Depends(require_permission("agent:push-plan:execute")),
    db: Session = Depends(get_db),
):
    plan = execute_push_plan(db, plan_id)
    record_operation_log(
        module="agent",
        action="execute_push_plan",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="push_plan",
        biz_id=str(plan.id),
        message=f"执行推送计划 {plan.id}",
    )
    return success_response(serialize_push_plan(plan))


@router.get("/digests")
def list_digests(
    page: int = 1,
    page_size: int = 20,
    report_type: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("agent:digest:list")),
    db: Session = Depends(get_db),
):
    items, total = list_digest_run_records(
        db,
        page=page,
        page_size=page_size,
        report_type=report_type,
        status=status,
        keyword=keyword,
    )
    return success_response(
        {
            "items": [serialize_digest_report(item) for item in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/digests/{digest_id}")
def get_digest(
    digest_id: int,
    _: User = Depends(require_permission("agent:digest:list")),
    db: Session = Depends(get_db),
):
    return success_response(get_digest_report_detail(db, digest_id))


@router.post("/digests/{digest_id}/push")
def push_digest(
    digest_id: int,
    request: Request,
    payload: DigestPushRequest | None = None,
    current_user: User = Depends(require_permission("agent:digest:push")),
    db: Session = Depends(get_db),
):
    payload = payload or DigestPushRequest()
    result = push_digest_report(
        db,
        digest_id,
        channels=payload.channels,
        request_id=request.state.request_id,
        triggered_by=current_user.id,
        force=payload.force,
    )
    record_operation_log(
        module="agent",
        action="push_digest",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="digest",
        biz_id=str(digest_id),
        message=f"执行简报推送 {digest_id}",
    )
    return success_response(result)


@router.get("/push-records")
def list_push_records_api(
    page: int = 1,
    page_size: int = 20,
    plan_id: int | None = None,
    digest_id: int | None = None,
    topic_id: int | None = None,
    channel: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("agent:push-record:list")),
    db: Session = Depends(get_db),
):
    items, total = list_push_records(
        db,
        page=page,
        page_size=page_size,
        plan_id=plan_id,
        digest_id=digest_id,
        topic_id=topic_id,
        channel=channel,
        status=status,
        keyword=keyword,
    )
    return success_response(
        {
            "items": [
                serialize_push_record(record, plan=plan, digest_report=digest, topic=topic)
                for record, plan, digest, topic in items
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/push-records/{record_id}")
def get_push_record_api(
    record_id: int,
    _: User = Depends(require_permission("agent:push-record:list")),
    db: Session = Depends(get_db),
):
    from app.services.push_record_service import get_push_record_detail

    return success_response(get_push_record_detail(db, record_id))
