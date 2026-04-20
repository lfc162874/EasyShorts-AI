from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.agents.digest_agent import run_digest_agent
from app.agents.runtime import build_agent_runtime
from app.agents.common import build_planned_at, infer_priority, merge_channels, recommend_channels, summarize_text
from app.core.constants import (
    AgentBizType,
    AgentRunType,
    DigestReportStatus,
    DigestReportType,
    HotTopicStatus,
    PushPlanStatus,
    PushPlanType,
    TaskStatus,
)
from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import get_logger
from app.db.models.agent import AgentRun, AgentRunArtifact, AgentRunStep, DigestReport, HotTopic, PushPlan, PushRecord
from app.db.models.system import SystemConfig
from app.services.agent_config_service import get_agent_config
from app.services.agent_run_service import create_agent_run, get_agent_run_detail, get_push_plan_detail, serialize_hot_topic, serialize_push_plan
from app.services.push_record_service import execute_push_plan_records, list_push_records, serialize_push_record, summarize_report_content

logger = get_logger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _enum_value(value: object | None, fallback: str) -> str:
    if value is None:
        return fallback
    if hasattr(value, "value"):
        return str(getattr(value, "value"))
    return str(value)


def _normalize_date(value: date | str | None, fallback: date | None = None) -> date:
    if value is None:
        if fallback is not None:
            return fallback
        return datetime.now(UTC).date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValidationException(message="简报日期格式不正确") from exc


def _serialize_digest_report(report: DigestReport) -> dict[str, object]:
    return {
        "id": report.id,
        "report_type": report.report_type,
        "report_date": report.report_date,
        "title": report.title,
        "summary": report.summary,
        "content": report.content,
        "highlights": report.highlights,
        "status": report.status,
        "topic_count": report.topic_count,
        "model_name": report.model_name,
        "prompt_version": report.prompt_version,
        "run_id": report.run_id,
        "task_job_id": report.task_job_id,
        "published_at": report.published_at,
        "extra": report.extra,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }


def list_digest_reports(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    report_type: DigestReportType | str | None = None,
    status: DigestReportStatus | str | None = None,
    keyword: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[DigestReport], int]:
    filters = []
    if report_type is not None:
        filters.append(DigestReport.report_type == _enum_value(report_type, DigestReportType.DAILY.value))
    if status is not None:
        filters.append(DigestReport.status == _enum_value(status, DigestReportStatus.DRAFT.value))
    if date_from is not None:
        filters.append(DigestReport.report_date >= date_from)
    if date_to is not None:
        filters.append(DigestReport.report_date <= date_to)
    if keyword:
        like = f"%{keyword.strip()}%"
        filters.append(
            or_(
                DigestReport.title.ilike(like),
                DigestReport.summary.ilike(like),
                DigestReport.content.ilike(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(DigestReport).where(*filters)) or 0
    items = db.scalars(
        select(DigestReport)
        .where(*filters)
        .order_by(DigestReport.report_date.desc(), DigestReport.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def get_digest_report(db: Session, report_id: int) -> DigestReport:
    report = db.get(DigestReport, report_id)
    if report is None:
        raise NotFoundException(message="简报不存在")
    return report


def _collect_report_topics(
    db: Session,
    *,
    topic_ids: list[int] | None,
    limit: int,
) -> list[HotTopic]:
    if topic_ids:
        topics = db.scalars(select(HotTopic).where(HotTopic.id.in_(topic_ids))).all()
        position = {topic_id: index for index, topic_id in enumerate(topic_ids)}
        return sorted(topics, key=lambda item: position.get(item.id, len(position)))

    topics = db.scalars(
        select(HotTopic)
        .where(HotTopic.status == HotTopicStatus.ACTIVE.value)
        .order_by(HotTopic.score.desc(), HotTopic.id.desc())
        .limit(limit)
    ).all()
    return list(topics)


def _build_topic_payload(topics: list[HotTopic]) -> list[dict[str, object]]:
    return [
        {
            "id": topic.id,
            "title": topic.title,
            "summary": topic.summary,
            "category": topic.category,
            "tags": topic.tags,
            "score": topic.score,
            "priority": topic.priority,
            "trend": topic.trend,
            "reason": topic.reason,
            "news_count": topic.news_count,
            "source_count": topic.source_count,
            "primary_news_id": topic.primary_news_id,
            "extra": topic.extra,
        }
        for topic in topics
    ]


def _build_digest_content(title: str, summary: str, highlights: list[str], topics: list[HotTopic]) -> str:
    base = summarize_report_content(title, summary, highlights)
    lines = [base, "", "## 热点明细"]
    for topic in topics:
        topic_summary = summarize_text(topic.summary or topic.title, limit=160)
        lines.append(
            f"- {topic.title}（{topic.category or '未分类'}，热度 {topic.score}，优先级 {topic.priority}）{topic_summary}"
        )
    return "\n".join(line for line in lines if line is not None).strip()


def _build_digest_input_summary(topics: list[HotTopic], report_type: str, report_date: date) -> str:
    titles = [topic.title for topic in topics[:5] if topic.title]
    return f"{report_type} | {report_date.isoformat()} | " + "；".join(titles)


def _upsert_digest_push_plan(
    db: Session,
    *,
    report: DigestReport,
    run: AgentRun,
    topics: list[HotTopic],
    channels: list[str] | None = None,
) -> PushPlan:
    priority_seed = max((topic.score for topic in topics), default=0)
    priority = infer_priority(priority_seed)
    resolved_channels = merge_channels(channels) if channels is not None else merge_channels(recommend_channels(priority))
    push_now = report.report_type == DigestReportType.TOPIC.value and priority == "HIGH"
    planned_at = build_planned_at(push_now)
    plan = db.scalar(
        select(PushPlan).where(PushPlan.biz_type == AgentBizType.DIGEST.value, PushPlan.biz_id == str(report.id))
    )
    if plan is None:
        plan = PushPlan(
            biz_type=AgentBizType.DIGEST.value,
            biz_id=str(report.id),
            run_id=run.id,
            topic_id=None,
            push_now=push_now,
            priority=priority,
            push_type=PushPlanType.DIGEST.value,
            channels=resolved_channels,
            planned_at=planned_at,
            status=PushPlanStatus.SCHEDULED.value if push_now else PushPlanStatus.PENDING.value,
            reason=report.summary or report.title,
            model_name=run.model_name,
            prompt_version=run.prompt_version,
            extra={
                "digest_report_id": report.id,
                "topic_ids": (report.extra or {}).get("topic_ids", []),
                "topic_titles": (report.extra or {}).get("topic_titles", []),
            },
        )
    else:
        plan.run_id = run.id
        plan.push_now = push_now
        plan.priority = priority
        plan.push_type = PushPlanType.DIGEST.value
        plan.channels = resolved_channels
        plan.planned_at = planned_at
        plan.status = PushPlanStatus.SCHEDULED.value if push_now else PushPlanStatus.PENDING.value
        plan.reason = report.summary or report.title
        plan.model_name = run.model_name
        plan.prompt_version = run.prompt_version
        plan.extra = {
            **(plan.extra or {}),
            "digest_report_id": report.id,
            "topic_ids": (report.extra or {}).get("topic_ids", []),
            "topic_titles": (report.extra or {}).get("topic_titles", []),
        }
    db.add(plan)
    db.flush()
    return plan


def _start_step(
    db: Session,
    *,
    run: AgentRun,
    step_code: str,
    agent_name: str,
    step_order: int,
    model_name: str,
    prompt_version: str,
    input_summary: str,
    payload: dict[str, object] | None = None,
) -> AgentRunStep:
    step = AgentRunStep(
        run_id=run.id,
        step_code=step_code,
        agent_name=agent_name,
        step_order=step_order,
        status=TaskStatus.RUNNING.value,
        model_name=model_name,
        prompt_version=prompt_version,
        input_summary=input_summary,
        payload=payload,
        started_at=_now(),
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


def _finish_step(
    db: Session,
    *,
    step: AgentRunStep,
    result: dict[str, object],
    status: str = TaskStatus.SUCCESS.value,
    error_message: str | None = None,
) -> AgentRunStep:
    finished_at = _now()
    step.status = status
    step.result = result
    step.output_summary = result.get("summary") or result.get("title") or str(result)
    step.error_message = error_message
    step.finished_at = finished_at
    if step.started_at is not None:
        started_at = step.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)
        step.duration_ms = int((finished_at - started_at).total_seconds() * 1000)
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


def _create_artifact(
    db: Session,
    *,
    run_id: int,
    step_id: int | None,
    artifact_type: str,
    artifact_key: str,
    content_json: dict[str, object] | None = None,
    content_text: str | None = None,
) -> AgentRunArtifact:
    artifact = AgentRunArtifact(
        run_id=run_id,
        step_id=step_id,
        artifact_type=artifact_type,
        artifact_key=artifact_key,
        content_json=content_json,
        content_text=content_text,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def create_agent_run_for_digest(
    db: Session,
    *,
    report_type: DigestReportType | str,
    report_date: date | str | None,
    topic_ids: list[int] | None,
    limit: int,
    model_name: str | None,
    force: bool,
    triggered_by: int | None,
    request_id: str | None,
    task_job_id: int | None = None,
    parent_run_id: int | None = None,
) -> AgentRun:
    runtime = build_agent_runtime(db, requested_model_name=model_name)
    resolved_report_type = _enum_value(report_type, DigestReportType.DAILY.value)
    resolved_report_date = _normalize_date(report_date)
    payload: dict[str, object] = {
        "report_type": resolved_report_type,
        "report_date": resolved_report_date.isoformat(),
        "topic_ids": list(topic_ids or []),
        "limit": limit,
        "model_name": runtime.model_name,
        "force": force,
    }
    run = create_agent_run(
        db,
        run_type=AgentRunType.DIGEST.value,
        biz_type=AgentBizType.DIGEST.value,
        biz_id=f"{resolved_report_type}:{resolved_report_date.isoformat()}",
        model_name=runtime.model_name,
        triggered_by=triggered_by,
        request_id=request_id,
        payload=payload,
        prompt_version=runtime.prompt_version,
        parent_run_id=parent_run_id,
        task_job_id=task_job_id,
    )
    run.input_summary = f"{resolved_report_type} | {resolved_report_date.isoformat()}"
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def execute_digest_run(db: Session, run_id: int) -> AgentRun:
    run = db.get(AgentRun, run_id)
    if run is None:
        raise NotFoundException(message="Agent 运行不存在")

    payload = dict(run.payload or {})
    report_type = _enum_value(payload.get("report_type"), DigestReportType.DAILY.value)
    report_date = _normalize_date(payload.get("report_date"))
    topic_ids = list(payload.get("topic_ids") or [])
    limit = int(payload.get("limit") or 10)
    force = bool(payload.get("force"))

    runtime = build_agent_runtime(db, requested_model_name=payload.get("model_name") or run.model_name)
    config = get_agent_config(db)
    topics = _collect_report_topics(db, topic_ids=topic_ids, limit=limit)
    if not topics and not force:
        raise ValidationException(message="当前没有可用于生成简报的热点")

    run.model_name = runtime.model_name
    run.prompt_version = runtime.prompt_version
    run.status = TaskStatus.RUNNING.value
    run.current_step = "digest"
    run.input_summary = _build_digest_input_summary(topics, report_type, report_date)
    run.started_at = run.started_at or _now()
    run.error_message = None
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        step = _start_step(
            db,
            run=run,
            step_code="digest",
            agent_name="DigestAgent",
            step_order=1,
            model_name=runtime.model_name,
            prompt_version=runtime.prompt_version,
            input_summary=run.input_summary or "",
            payload={
                "report_type": report_type,
                "report_date": report_date.isoformat(),
                "topic_ids": [topic.id for topic in topics],
                "limit": limit,
                "force": force,
            },
        )

        topic_payloads = _build_topic_payload(topics)
        agent_result = run_digest_agent(
            topic_payloads,
            model_name=runtime.model_name,
            prompt_version=runtime.prompt_version,
            report_type=report_type,
            report_date=report_date,
            runtime=runtime,
            system_prompt=config["prompts"].get("agent_digest_prompt", ""),
        )
        result = {
            **agent_result,
            "topics": topic_payloads,
        }
        safe_result = jsonable_encoder(result)
        _finish_step(db, step=step, result=safe_result)
        _create_artifact(
            db,
            run_id=run.id,
            step_id=step.id,
            artifact_type="structured_output",
            artifact_key="digest",
            content_json=safe_result,
            content_text=safe_result.get("summary") or safe_result.get("title") or "",
        )

        digest_report = db.scalar(
            select(DigestReport).where(
                DigestReport.report_type == report_type,
                DigestReport.report_date == report_date,
            )
        )
        if digest_report is None:
            digest_report = DigestReport(
                report_type=report_type,
                report_date=report_date,
                title=str(result.get("title") or "AI 热点简报"),
                summary=str(result.get("summary") or ""),
                content=_build_digest_content(
                    str(result.get("title") or "AI 热点简报"),
                    str(result.get("summary") or ""),
                    list(result.get("highlights") or []),
                    topics,
                ),
                highlights=list(result.get("highlights") or []),
                status=DigestReportStatus.GENERATED.value,
                topic_count=len(topics),
                model_name=runtime.model_name,
                prompt_version=runtime.prompt_version,
                run_id=run.id,
                task_job_id=run.task_job_id,
                published_at=None,
                extra={
                    "agent_run_id": run.id,
                    "topic_ids": [topic.id for topic in topics],
                    "topic_titles": [topic.title for topic in topics],
                    "force": force,
                },
            )
        else:
            digest_report.title = str(result.get("title") or digest_report.title)
            digest_report.summary = str(result.get("summary") or digest_report.summary or "")
            digest_report.content = _build_digest_content(
                str(result.get("title") or digest_report.title),
                str(result.get("summary") or digest_report.summary or ""),
                list(result.get("highlights") or []),
                topics,
            )
            digest_report.highlights = list(result.get("highlights") or [])
            digest_report.status = DigestReportStatus.GENERATED.value
            digest_report.topic_count = len(topics)
            digest_report.model_name = runtime.model_name
            digest_report.prompt_version = runtime.prompt_version
            digest_report.run_id = run.id
            digest_report.task_job_id = run.task_job_id
            digest_report.published_at = None
            digest_report.extra = {
                **(digest_report.extra or {}),
                "agent_run_id": run.id,
                "topic_ids": [topic.id for topic in topics],
                "topic_titles": [topic.title for topic in topics],
                "force": force,
            }
        db.add(digest_report)
        db.flush()

        plan = _upsert_digest_push_plan(
            db,
            report=digest_report,
            run=run,
            topics=topics,
            channels=None,
        )

        run.status = TaskStatus.SUCCESS.value
        run.output_summary = digest_report.summary or digest_report.title
        run.result = jsonable_encoder({
            "digest_report": _serialize_digest_report(digest_report),
            "push_plan": serialize_push_plan(plan),
            "topics": topic_payloads,
        })
        run.finished_at = _now()
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:
        logger.exception("digest run failed for run_id=%s", run_id)
        run.status = TaskStatus.FAILED.value
        run.error_message = str(exc)
        run.finished_at = _now()
        db.add(run)
        db.commit()
        db.refresh(run)
        raise


def list_digest_run_records(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    report_type: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
) -> tuple[list[DigestReport], int]:
    return list_digest_reports(
        db,
        page=page,
        page_size=page_size,
        report_type=report_type,
        status=status,
        keyword=keyword,
    )


def get_digest_report_detail(db: Session, report_id: int) -> dict[str, object]:
    report = get_digest_report(db, report_id)
    topic_ids = list((report.extra or {}).get("topic_ids") or [])
    topics = []
    if topic_ids:
        topic_map = {
            topic.id: topic
            for topic in db.scalars(select(HotTopic).where(HotTopic.id.in_(topic_ids))).all()
        }
        topics = [topic_map[topic_id] for topic_id in topic_ids if topic_id in topic_map]

    run = db.get(AgentRun, report.run_id) if report.run_id else None
    push_plan = db.scalar(
        select(PushPlan).where(PushPlan.biz_type == AgentBizType.DIGEST.value, PushPlan.biz_id == str(report.id))
    )
    push_record_rows = list_push_records(db, digest_id=report.id, page=1, page_size=200)[0]
    return {
        **_serialize_digest_report(report),
        "run": get_agent_run_detail(db, run.id) if run is not None else None,
        "topics": [serialize_hot_topic(topic) for topic in topics],
        "push_plan": get_push_plan_detail(db, push_plan.id) if push_plan is not None else None,
        "push_records": [
            serialize_push_record(record, plan=plan, digest_report=digest, topic=topic)
            for record, plan, digest, topic in push_record_rows
        ],
    }


def push_digest_report(
    db: Session,
    report_id: int,
    *,
    channels: list[str] | None = None,
    request_id: str | None = None,
    triggered_by: int | None = None,
    force: bool = False,
) -> dict[str, object]:
    report = get_digest_report(db, report_id)
    if report.status == DigestReportStatus.PUBLISHED.value and not force:
        return get_digest_report_detail(db, report.id)

    run = db.get(AgentRun, report.run_id) if report.run_id else None
    if run is None:
        raise ValidationException(message="简报缺少关联的 Agent 运行记录")

    topic_ids = list((report.extra or {}).get("topic_ids") or [])
    topics = []
    if topic_ids:
        topic_map = {
            topic.id: topic
            for topic in db.scalars(select(HotTopic).where(HotTopic.id.in_(topic_ids))).all()
        }
        topics = [topic_map[topic_id] for topic_id in topic_ids if topic_id in topic_map]

    plan = db.scalar(
        select(PushPlan).where(PushPlan.biz_type == AgentBizType.DIGEST.value, PushPlan.biz_id == str(report.id))
    )
    if plan is None:
        plan = _upsert_digest_push_plan(
            db,
            report=report,
            run=run,
            topics=topics,
            channels=channels,
        )
    elif channels is not None:
        plan.channels = list(dict.fromkeys([str(channel).strip() for channel in channels if str(channel).strip()]))
        db.add(plan)
        db.commit()
        db.refresh(plan)

    execute_push_plan_records(
        db,
        plan,
        request_id=request_id,
        triggered_by=triggered_by,
        force=force,
    )
    report.status = DigestReportStatus.PUBLISHED.value
    report.published_at = _now()
    report.extra = {
        **(report.extra or {}),
        "push_plan_id": plan.id,
        "push_channels": plan.channels,
        "published_at": report.published_at.isoformat(),
        "request_id": request_id,
        "triggered_by": triggered_by,
    }
    db.add(report)
    db.commit()
    db.refresh(report)
    return get_digest_report_detail(db, report.id)


def serialize_digest_report(report: DigestReport) -> dict[str, object]:
    return _serialize_digest_report(report)
