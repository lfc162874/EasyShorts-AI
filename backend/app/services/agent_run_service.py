from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.agents.context import AgentExecutionContext
from app.agents.classification_agent import run_classification_agent
from app.agents.enrichment_agent import run_enrichment_agent
from app.agents.hotspot_agent import run_hotspot_agent
from app.agents.runtime import build_agent_runtime
from app.agents.push_planner_agent import run_push_planner_agent
from app.agents.summary_agent import run_summary_agent
from app.core.constants import AgentBizType, AgentRunType, HotTopicStatus, PushPlanStatus, PushPlanType, TaskStatus
from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import get_logger
from app.db.models.agent import AgentRun, AgentRunArtifact, AgentRunStep, DigestReport, HotTopic, HotTopicItem, PushPlan
from app.db.models.business import News, NewsSource
from app.db.models.system import SystemConfig
from app.services.agent_config_service import get_agent_config
from app.services.push_record_service import execute_push_plan_records, list_push_records, serialize_push_record
from app.agents.common import compute_topic_key, normalize_whitespace

logger = get_logger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _ensure_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _load_config_value(db: Session, category: str, config_key: str, default: str | None = None) -> str | None:
    config = db.scalar(
        select(SystemConfig).where(
            SystemConfig.category == category,
            SystemConfig.config_key == config_key,
            SystemConfig.is_enabled.is_(True),
        )
    )
    if config is None:
        return default
    return config.config_value


def _build_news_input_summary(news: News, model_name: str) -> str:
    parts = [
        normalize_whitespace(news.title) or "未命名内容",
        normalize_whitespace(news.source) or "未知来源",
        f"模型 {model_name}",
    ]
    return " · ".join(parts)


def _build_step_input_summary(step_code: str, context: AgentExecutionContext, outputs: dict[str, dict[str, object]]) -> str:
    news = context.news
    if step_code == "hotspot":
        return f"{news.title} | 热度 {news.hot_score} | 来源 {news.source}"
    if step_code == "classification":
        hotspot = outputs.get("hotspot", {})
        return f"hot_score={hotspot.get('score', news.hot_score)} | is_hot={hotspot.get('is_hot')}"
    if step_code == "summary":
        classification = outputs.get("classification", {})
        return f"category={classification.get('category', news.category)} | title={news.title}"
    if step_code == "enrichment":
        summary = outputs.get("summary", {})
        return f"summary={normalize_whitespace(str(summary.get('summary') or news.summary or ''))[:80]}"
    if step_code == "push_planner":
        enrichment = outputs.get("enrichment", {})
        return f"impact={normalize_whitespace(str(enrichment.get('impact') or ''))[:80]}"
    return news.title


def _build_step_output_summary(step_code: str, result: dict[str, object]) -> str:
    if step_code == "hotspot":
        return f"is_hot={result.get('is_hot')} score={result.get('score')} priority={result.get('priority')}"
    if step_code == "classification":
        return f"category={result.get('category')} tags={','.join(result.get('tags') or [])}"
    if step_code == "summary":
        return f"title={result.get('title')} summary={normalize_whitespace(str(result.get('summary') or ''))[:120]}"
    if step_code == "enrichment":
        return f"impact={normalize_whitespace(str(result.get('impact') or ''))[:120]}"
    if step_code == "push_planner":
        return f"push_now={result.get('push_now')} priority={result.get('priority')} channels={','.join(result.get('channels') or [])}"
    return jsonable_encoder(result)


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
    step.output_summary = _build_step_output_summary(step.step_code, result)
    step.error_message = error_message
    step.finished_at = finished_at
    started_at = _ensure_aware(step.started_at)
    if started_at is not None:
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


def _serialize_step(step: AgentRunStep) -> dict[str, object]:
    return {
        "id": step.id,
        "run_id": step.run_id,
        "step_code": step.step_code,
        "agent_name": step.agent_name,
        "step_order": step.step_order,
        "status": step.status,
        "model_name": step.model_name,
        "prompt_version": step.prompt_version,
        "input_summary": step.input_summary,
        "output_summary": step.output_summary,
        "payload": step.payload,
        "result": step.result,
        "error_message": step.error_message,
        "started_at": step.started_at,
        "finished_at": step.finished_at,
        "duration_ms": step.duration_ms,
        "created_at": step.created_at,
        "updated_at": step.updated_at,
    }


def _serialize_artifact(artifact: AgentRunArtifact) -> dict[str, object]:
    return {
        "id": artifact.id,
        "run_id": artifact.run_id,
        "step_id": artifact.step_id,
        "artifact_type": artifact.artifact_type,
        "artifact_key": artifact.artifact_key,
        "content_json": artifact.content_json,
        "content_text": artifact.content_text,
        "created_at": artifact.created_at,
        "updated_at": artifact.updated_at,
    }


def _serialize_run(run: AgentRun) -> dict[str, object]:
    return {
        "id": run.id,
        "parent_run_id": run.parent_run_id,
        "task_job_id": run.task_job_id,
        "run_type": run.run_type,
        "biz_type": run.biz_type,
        "biz_id": run.biz_id,
        "status": run.status,
        "current_step": run.current_step,
        "model_name": run.model_name,
        "prompt_version": run.prompt_version,
        "input_summary": run.input_summary,
        "output_summary": run.output_summary,
        "payload": run.payload,
        "result": run.result,
        "triggered_by": run.triggered_by,
        "request_id": run.request_id,
        "error_message": run.error_message,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
    }


def _serialize_news_item(news: News, source_name: str | None = None) -> dict[str, object]:
    return {
        "id": news.id,
        "title": news.title,
        "source_name": source_name,
        "source_id": news.source_id,
        "url": news.url,
        "publish_time": news.publish_time,
        "category": news.category,
        "hot_score": news.hot_score,
        "summary": news.summary,
        "translated_title": news.translated_title,
        "translated_content": news.translated_content,
        "script": news.script,
        "tags": news.tags,
    }


def _serialize_hot_topic_item(item: HotTopicItem, news: News, source_name: str | None = None) -> dict[str, object]:
    return {
        "id": item.id,
        "news_id": item.news_id,
        "source_id": item.source_id,
        "source_name": source_name,
        "title": news.title,
        "url": news.url,
        "weight": item.weight,
        "is_primary": item.is_primary,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _serialize_hot_topic(topic: HotTopic) -> dict[str, object]:
    return {
        "id": topic.id,
        "topic_key": topic.topic_key,
        "title": topic.title,
        "summary": topic.summary,
        "category": topic.category,
        "tags": topic.tags,
        "score": topic.score,
        "priority": topic.priority,
        "reason": topic.reason,
        "trend": topic.trend,
        "status": topic.status,
        "model_name": topic.model_name,
        "prompt_version": topic.prompt_version,
        "news_count": topic.news_count,
        "source_count": topic.source_count,
        "primary_news_id": topic.primary_news_id,
        "extra": topic.extra,
        "created_at": topic.created_at,
        "updated_at": topic.updated_at,
    }


def _serialize_push_plan(plan: PushPlan) -> dict[str, object]:
    return {
        "id": plan.id,
        "biz_type": plan.biz_type,
        "biz_id": plan.biz_id,
        "run_id": plan.run_id,
        "topic_id": plan.topic_id,
        "push_now": plan.push_now,
        "priority": plan.priority,
        "push_type": plan.push_type,
        "channels": plan.channels,
        "planned_at": plan.planned_at,
        "status": plan.status,
        "reason": plan.reason,
        "model_name": plan.model_name,
        "prompt_version": plan.prompt_version,
        "executed_at": plan.executed_at,
        "extra": plan.extra,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
    }


def create_agent_run(
    db: Session,
    *,
    run_type: str,
    biz_type: str,
    biz_id: str,
    model_name: str,
    triggered_by: int | None,
    request_id: str | None,
    payload: dict[str, object] | None,
    prompt_version: str,
    parent_run_id: int | None = None,
    task_job_id: int | None = None,
) -> AgentRun:
    run = AgentRun(
        parent_run_id=parent_run_id,
        task_job_id=task_job_id,
        run_type=run_type,
        biz_type=biz_type,
        biz_id=biz_id,
        status=TaskStatus.PENDING.value,
        current_step="hotspot",
        model_name=model_name,
        prompt_version=prompt_version,
        input_summary=None,
        output_summary=None,
        payload=payload or {},
        result=None,
        triggered_by=triggered_by,
        request_id=request_id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def list_agent_runs(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    run_type: str | None = None,
    biz_type: str | None = None,
    model_name: str | None = None,
    keyword: str | None = None,
) -> tuple[list[AgentRun], int]:
    filters = []
    if status:
        filters.append(AgentRun.status == status)
    if run_type:
        filters.append(AgentRun.run_type == run_type)
    if biz_type:
        filters.append(AgentRun.biz_type == biz_type)
    if model_name:
        filters.append(AgentRun.model_name == model_name)
    if keyword:
        like = f"%{keyword.strip()}%"
        filters.append(
            or_(
                AgentRun.input_summary.ilike(like),
                AgentRun.output_summary.ilike(like),
                AgentRun.biz_id.ilike(like),
                AgentRun.model_name.ilike(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(AgentRun).where(*filters)) or 0
    items = db.scalars(
        select(AgentRun)
        .where(*filters)
        .order_by(AgentRun.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def get_agent_run(db: Session, run_id: int) -> AgentRun:
    run = db.get(AgentRun, run_id)
    if run is None:
        raise NotFoundException(message="Agent 运行不存在")
    return run


def get_agent_run_detail(db: Session, run_id: int) -> dict[str, object]:
    run = get_agent_run(db, run_id)
    steps = db.scalars(select(AgentRunStep).where(AgentRunStep.run_id == run.id).order_by(AgentRunStep.step_order.asc(), AgentRunStep.id.asc())).all()
    artifacts = db.scalars(select(AgentRunArtifact).where(AgentRunArtifact.run_id == run.id).order_by(AgentRunArtifact.id.asc())).all()
    return {
        **_serialize_run(run),
        "steps": [_serialize_step(step) for step in steps],
        "artifacts": [_serialize_artifact(artifact) for artifact in artifacts],
    }


def list_hot_topics(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    category: str | None = None,
    keyword: str | None = None,
) -> tuple[list[HotTopic], int]:
    filters = []
    if status:
        filters.append(HotTopic.status == status)
    if category:
        filters.append(HotTopic.category == category)
    if keyword:
        like = f"%{keyword.strip()}%"
        filters.append(
            or_(
                HotTopic.title.ilike(like),
                HotTopic.summary.ilike(like),
                HotTopic.reason.ilike(like),
                HotTopic.category.ilike(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(HotTopic).where(*filters)) or 0
    items = db.scalars(
        select(HotTopic)
        .where(*filters)
        .order_by(HotTopic.score.desc(), HotTopic.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def get_hot_topic(db: Session, topic_id: int) -> HotTopic:
    topic = db.get(HotTopic, topic_id)
    if topic is None:
        raise NotFoundException(message="热点不存在")
    return topic


def get_hot_topic_detail(db: Session, topic_id: int) -> dict[str, object]:
    topic = get_hot_topic(db, topic_id)
    items = db.scalars(
        select(HotTopicItem).where(HotTopicItem.topic_id == topic.id).order_by(HotTopicItem.is_primary.desc(), HotTopicItem.weight.desc(), HotTopicItem.id.asc())
    ).all()
    news_ids = [item.news_id for item in items]
    news_map = {
        news.id: news
        for news in db.scalars(select(News).where(News.id.in_(news_ids))).all()
    }
    source_map = {
        source.id: source.name
        for source in db.scalars(select(NewsSource).where(NewsSource.id.in_([item.source_id for item in items if item.source_id is not None]))).all()
    }
    return {
        **_serialize_hot_topic(topic),
        "items": [
            _serialize_hot_topic_item(
                item,
                news=news_map[item.news_id],
                source_name=source_map.get(item.source_id) if item.source_id is not None else None,
            )
            for item in items
            if item.news_id in news_map
        ],
    }


def list_push_plans(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    biz_type: str | None = None,
    keyword: str | None = None,
) -> tuple[list[PushPlan], int]:
    filters = []
    if status:
        filters.append(PushPlan.status == status)
    if biz_type:
        filters.append(PushPlan.biz_type == biz_type)
    if keyword:
        like = f"%{keyword.strip()}%"
        filters.append(
            or_(
                PushPlan.reason.ilike(like),
                PushPlan.biz_id.ilike(like),
                PushPlan.model_name.ilike(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(PushPlan).where(*filters)) or 0
    items = db.scalars(
        select(PushPlan)
        .where(*filters)
        .order_by(PushPlan.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def get_push_plan(db: Session, plan_id: int) -> PushPlan:
    plan = db.get(PushPlan, plan_id)
    if plan is None:
        raise NotFoundException(message="推送计划不存在")
    return plan


def get_push_plan_detail(db: Session, plan_id: int) -> dict[str, object]:
    plan = get_push_plan(db, plan_id)
    topic = db.get(HotTopic, plan.topic_id) if plan.topic_id else None
    run = db.get(AgentRun, plan.run_id) if plan.run_id else None
    digest_report = None
    if plan.biz_type == AgentBizType.DIGEST.value:
        try:
            digest_id = int(plan.biz_id)
        except (TypeError, ValueError):
            digest_id = None
        if digest_id is not None:
            digest_report = db.get(DigestReport, digest_id)
    push_record_rows = list_push_records(db, plan_id=plan.id, page=1, page_size=200)[0]
    payload = _serialize_push_plan(plan)
    payload["topic"] = _serialize_hot_topic(topic) if topic else None
    payload["run"] = _serialize_run(run) if run else None
    payload["digest_report"] = (
        {
            "id": digest_report.id,
            "report_type": digest_report.report_type,
            "report_date": digest_report.report_date,
            "title": digest_report.title,
            "summary": digest_report.summary,
            "content": digest_report.content,
            "highlights": digest_report.highlights,
            "status": digest_report.status,
            "topic_count": digest_report.topic_count,
            "model_name": digest_report.model_name,
            "prompt_version": digest_report.prompt_version,
            "run_id": digest_report.run_id,
            "task_job_id": digest_report.task_job_id,
            "published_at": digest_report.published_at,
            "extra": digest_report.extra,
            "created_at": digest_report.created_at,
            "updated_at": digest_report.updated_at,
        }
        if digest_report is not None
        else None
    )
    payload["push_records"] = [
        serialize_push_record(record, plan=record_plan, digest_report=record_digest, topic=record_topic)
        for record, record_plan, record_digest, record_topic in push_record_rows
    ]
    return payload


def _upsert_hot_topic(
    db: Session,
    *,
    run: AgentRun,
    news: News,
    hotspot_result: dict[str, object],
    classification_result: dict[str, object],
    summary_result: dict[str, object],
) -> HotTopic:
    topic_title = str(summary_result.get("title") or news.title).strip() or news.title
    category = str(classification_result.get("category") or news.category or "行业动态")
    topic_key = compute_topic_key(topic_title, category)
    topic = db.scalar(select(HotTopic).where(HotTopic.topic_key == topic_key))
    score = int(hotspot_result.get("score") or news.hot_score or 0)
    priority = str(hotspot_result.get("priority") or "MEDIUM")
    reason = str(hotspot_result.get("reason") or "")
    trend = str(hotspot_result.get("trend") or "STABLE")
    tags = list(classification_result.get("tags") or news.tags or [])

    if topic is None:
        topic = HotTopic(
            topic_key=topic_key,
            title=topic_title,
            summary=str(summary_result.get("summary") or news.summary or topic_title),
            category=category,
            tags=tags[:5],
            score=score,
            priority=priority,
            reason=reason,
            trend=trend,
            status=HotTopicStatus.ACTIVE.value,
            model_name=run.model_name,
            prompt_version=run.prompt_version,
            news_count=1,
            source_count=1 if news.source_id is not None else 0,
            primary_news_id=news.id,
            extra={
                "agent_run_id": run.id,
                "news_id": news.id,
                "source_name": news.source,
            },
        )
        db.add(topic)
        db.flush()
    else:
        topic.title = topic_title
        topic.summary = str(summary_result.get("summary") or topic.summary or news.summary or topic_title)
        topic.category = category
        topic.tags = tags[:5]
        topic.score = max(topic.score or 0, score)
        topic.priority = priority
        topic.reason = reason
        topic.trend = trend
        topic.status = HotTopicStatus.ACTIVE.value
        topic.model_name = run.model_name
        topic.prompt_version = run.prompt_version
        topic.news_count = (topic.news_count or 0) + 1
        if news.source_id is not None:
            topic.source_count = (topic.source_count or 0) + 1
        if topic.primary_news_id is None or score >= topic.score:
            topic.primary_news_id = news.id
        topic.extra = {
            **(topic.extra or {}),
            "agent_run_id": run.id,
            "latest_news_id": news.id,
            "latest_source_name": news.source,
        }
        db.add(topic)
        db.flush()

    existing_item = db.scalar(
        select(HotTopicItem).where(HotTopicItem.topic_id == topic.id, HotTopicItem.news_id == news.id)
    )
    if existing_item is None:
        item = HotTopicItem(
            topic_id=topic.id,
            news_id=news.id,
            source_id=news.source_id,
            weight=score,
            is_primary=topic.primary_news_id == news.id,
        )
        db.add(item)
        db.flush()
    else:
        existing_item.weight = score
        existing_item.is_primary = topic.primary_news_id == news.id
        db.add(existing_item)
        db.flush()

    return topic


def _create_push_plan(
    db: Session,
    *,
    run: AgentRun,
    topic: HotTopic,
    push_plan_result: dict[str, object],
) -> PushPlan:
    planned_at_value = push_plan_result.get("planned_at")
    planned_at = datetime.fromisoformat(str(planned_at_value)) if planned_at_value else _now()
    push_type = str(push_plan_result.get("push_type") or PushPlanType.SCHEDULED.value)
    status = PushPlanStatus.SCHEDULED.value if bool(push_plan_result.get("push_now")) else PushPlanStatus.PENDING.value
    plan = db.scalar(select(PushPlan).where(PushPlan.run_id == run.id, PushPlan.topic_id == topic.id))
    channels = list(push_plan_result.get("channels") or [])
    if plan is None:
        plan = PushPlan(
            biz_type=AgentBizType.HOT_TOPIC.value,
            biz_id=str(topic.id),
            run_id=run.id,
            topic_id=topic.id,
            push_now=bool(push_plan_result.get("push_now")),
            priority=str(push_plan_result.get("priority") or "LOW"),
            push_type=push_type,
            channels=channels,
            planned_at=planned_at,
            status=status,
            reason=str(push_plan_result.get("reason") or ""),
            model_name=run.model_name,
            prompt_version=run.prompt_version,
            extra={
                "agent_run_id": run.id,
                "topic_title": topic.title,
                "title": push_plan_result.get("title"),
            },
        )
        db.add(plan)
        db.flush()
    else:
        plan.push_now = bool(push_plan_result.get("push_now"))
        plan.priority = str(push_plan_result.get("priority") or "LOW")
        plan.push_type = push_type
        plan.channels = channels
        plan.planned_at = planned_at
        plan.status = status
        plan.reason = str(push_plan_result.get("reason") or "")
        plan.model_name = run.model_name
        plan.prompt_version = run.prompt_version
        plan.extra = {
            **(plan.extra or {}),
            "agent_run_id": run.id,
            "topic_title": topic.title,
            "title": push_plan_result.get("title"),
        }
        db.add(plan)
        db.flush()
    return plan


def execute_agent_run(db: Session, run_id: int) -> AgentRun:
    run = get_agent_run(db, run_id)
    payload = dict(run.payload or {})
    news_id = payload.get("news_id")
    if news_id is None:
        raise ValidationException(message="Agent 运行缺少新闻内容编号")

    news = db.get(News, int(news_id))
    if news is None:
        raise NotFoundException(message="关联内容不存在")

    runtime = build_agent_runtime(db, requested_model_name=payload.get("model_name") or run.model_name)
    config = get_agent_config(db)
    run.model_name = runtime.model_name
    run.prompt_version = runtime.prompt_version
    run.status = TaskStatus.RUNNING.value
    run.current_step = "hotspot"
    run.input_summary = _build_news_input_summary(news, runtime.model_name)
    run.started_at = run.started_at or _now()
    run.error_message = None
    db.add(run)
    db.commit()
    db.refresh(run)

    context = AgentExecutionContext(
        news=news,
        model_name=runtime.model_name,
        prompt_version=runtime.prompt_version,
        prompt_bundle=runtime.prompt_bundle,
        config=config,
        runtime=runtime,
        force=bool(payload.get("force")),
    )
    outputs: dict[str, dict[str, object]] = dict(payload.get("seed_step_outputs") or {})
    start_from_step_order = int(payload.get("start_from_step_order") or 1)
    step_definitions = [
        ("hotspot", "HotspotAgent", 1),
        ("classification", "ClassificationAgent", 2),
        ("summary", "SummaryAgent", 3),
        ("enrichment", "EnrichmentAgent", 4),
        ("push_planner", "PushPlannerAgent", 5),
    ]

    workflow_result: dict[str, object] = {}

    try:
        for step_code, agent_name, step_order in step_definitions:
            if step_order < start_from_step_order:
                if step_code in outputs:
                    workflow_result[step_code] = outputs[step_code]
                continue

            input_summary = _build_step_input_summary(step_code, context, outputs)
            step = _start_step(
                db,
                run=run,
                step_code=step_code,
                agent_name=agent_name,
                step_order=step_order,
                model_name=runtime.model_name,
                prompt_version=runtime.prompt_version,
                input_summary=input_summary,
                payload={
                    "news_id": news.id,
                    "request_id": run.request_id,
                    "triggered_by": run.triggered_by,
                    "force": context.force,
                },
            )

            if step_code == "hotspot":
                result = run_hotspot_agent(context)
            elif step_code == "classification":
                if "hotspot" not in outputs:
                    raise ValidationException(message="分类步骤缺少热点分析结果")
                result = run_classification_agent(context, outputs["hotspot"])
            elif step_code == "summary":
                if "hotspot" not in outputs or "classification" not in outputs:
                    raise ValidationException(message="摘要步骤缺少上游分析结果")
                result = run_summary_agent(context, outputs["hotspot"], outputs["classification"])
            elif step_code == "enrichment":
                if "classification" not in outputs or "summary" not in outputs:
                    raise ValidationException(message="内容扩展步骤缺少上游分析结果")
                result = run_enrichment_agent(context, outputs["classification"], outputs["summary"])
            elif step_code == "push_planner":
                if "hotspot" not in outputs or "classification" not in outputs or "summary" not in outputs:
                    raise ValidationException(message="推送决策步骤缺少上游分析结果")
                result = run_push_planner_agent(context, outputs["hotspot"], outputs["classification"], outputs["summary"])
            else:  # pragma: no cover - defensive branch
                result = {}

            _finish_step(db, step=step, result=result)
            _create_artifact(
                db,
                run_id=run.id,
                step_id=step.id,
                artifact_type="structured_output",
                artifact_key=step_code,
                content_json=result,
                content_text=_build_step_output_summary(step_code, result),
            )
            outputs[step_code] = result
            workflow_result[step_code] = result
            run.current_step = step_code
            db.add(run)
            db.commit()
            db.refresh(run)

            if step_code == "hotspot" and not bool(result.get("is_hot")):
                run.status = TaskStatus.SUCCESS.value
                run.output_summary = str(result.get("reason") or "")
                run.result = jsonable_encoder(workflow_result)
                run.finished_at = _now()
                db.add(run)
                db.commit()
                db.refresh(run)
                news.raw_metadata = {
                    **(news.raw_metadata or {}),
                    "agent_processing": {
                        "run_id": run.id,
                        "model_name": run.model_name,
                        "prompt_version": run.prompt_version,
                        "hotspot": result,
                        "status": "NON_HOT",
                    },
                }
                db.add(news)
                db.commit()
                return run

        hotspot_result = outputs["hotspot"]
        classification_result = outputs["classification"]
        summary_result = outputs["summary"]
        enrichment_result = outputs["enrichment"]
        push_plan_result = outputs["push_planner"]

        topic = _upsert_hot_topic(
            db,
            run=run,
            news=news,
            hotspot_result=hotspot_result,
            classification_result=classification_result,
            summary_result=summary_result,
        )
        push_plan = _create_push_plan(
            db,
            run=run,
            topic=topic,
            push_plan_result=push_plan_result,
        )

        workflow_result.update(
            {
                "hot_topic": jsonable_encoder(_serialize_hot_topic(topic)),
                "push_plan": jsonable_encoder(_serialize_push_plan(push_plan)),
            }
        )
        run.status = TaskStatus.SUCCESS.value
        run.output_summary = str(summary_result.get("summary") or topic.summary or news.summary or topic.title)
        run.result = jsonable_encoder(workflow_result)
        run.finished_at = _now()
        db.add(run)
        news.raw_metadata = {
            **(news.raw_metadata or {}),
            "agent_processing": {
                "run_id": run.id,
                "model_name": run.model_name,
                "prompt_version": run.prompt_version,
                "hot_topic_id": topic.id,
                "push_plan_id": push_plan.id,
                "hotspot": hotspot_result,
                "classification": classification_result,
                "summary": summary_result,
                "enrichment": enrichment_result,
                "push_planner": push_plan_result,
            },
        }
        db.add(news)
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:
        logger.exception("agent run failed for run_id=%s", run_id)
        run.status = TaskStatus.FAILED.value
        run.error_message = str(exc)
        run.finished_at = _now()
        db.add(run)
        db.commit()
        db.refresh(run)
        raise


def create_agent_run_for_news(
    db: Session,
    *,
    news_id: int,
    model_name: str | None,
    force: bool,
    triggered_by: int | None,
    request_id: str | None,
    task_job_id: int | None = None,
    parent_run_id: int | None = None,
    start_from_step_order: int = 1,
    seed_step_outputs: dict[str, dict[str, object]] | None = None,
) -> AgentRun:
    news = db.get(News, news_id)
    if news is None:
        raise NotFoundException(message="内容不存在")
    runtime = build_agent_runtime(db, requested_model_name=model_name)
    payload: dict[str, object] = {
        "news_id": news.id,
        "force": force,
        "model_name": runtime.model_name,
        "start_from_step_order": start_from_step_order,
    }
    if seed_step_outputs:
        payload["seed_step_outputs"] = seed_step_outputs
    run = create_agent_run(
        db,
        run_type=AgentRunType.SINGLE_ARTICLE.value,
        biz_type=AgentBizType.NEWS.value,
        biz_id=str(news.id),
        model_name=runtime.model_name,
        triggered_by=triggered_by,
        request_id=request_id,
        payload=payload,
        prompt_version=runtime.prompt_version,
        parent_run_id=parent_run_id,
        task_job_id=task_job_id,
    )
    run.input_summary = _build_news_input_summary(news, runtime.model_name)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def retry_agent_run(
    db: Session,
    *,
    run_id: int,
    model_name: str | None = None,
) -> AgentRun:
    origin = get_agent_run(db, run_id)
    payload = dict(origin.payload or {})
    payload.pop("seed_step_outputs", None)
    payload["model_name"] = model_name or origin.model_name
    news_id = int(payload.get("news_id"))
    return create_agent_run_for_news(
        db,
        news_id=news_id,
        model_name=payload.get("model_name") or origin.model_name,
        force=bool(payload.get("force")),
        triggered_by=origin.triggered_by,
        request_id=origin.request_id,
        parent_run_id=origin.id,
        start_from_step_order=1,
    )


def retry_agent_run_step(
    db: Session,
    *,
    run_id: int,
    step_id: int,
    model_name: str | None = None,
) -> AgentRun:
    origin = get_agent_run(db, run_id)
    step = db.get(AgentRunStep, step_id)
    if step is None or step.run_id != origin.id:
        raise NotFoundException(message="Agent 步骤不存在")
    prior_steps = db.scalars(
        select(AgentRunStep)
        .where(AgentRunStep.run_id == origin.id, AgentRunStep.step_order < step.step_order)
        .order_by(AgentRunStep.step_order.asc())
    ).all()
    seed_outputs = {
        prior_step.step_code: dict(prior_step.result or {})
        for prior_step in prior_steps
        if prior_step.result is not None
    }
    payload = dict(origin.payload or {})
    payload["seed_step_outputs"] = seed_outputs
    payload["start_from_step_order"] = step.step_order
    payload["model_name"] = model_name or origin.model_name
    news_id = int(payload.get("news_id"))
    return create_agent_run_for_news(
        db,
        news_id=news_id,
        model_name=payload.get("model_name") or origin.model_name,
        force=bool(payload.get("force")),
        triggered_by=origin.triggered_by,
        request_id=origin.request_id,
        parent_run_id=origin.id,
        start_from_step_order=step.step_order,
        seed_step_outputs=seed_outputs,
    )


def execute_push_plan(db: Session, plan_id: int) -> PushPlan:
    plan = get_push_plan(db, plan_id)
    execute_push_plan_records(db, plan)
    db.refresh(plan)
    return plan


def serialize_agent_run(run: AgentRun) -> dict[str, object]:
    return _serialize_run(run)


def serialize_agent_run_step(step: AgentRunStep) -> dict[str, object]:
    return _serialize_step(step)


def serialize_agent_run_artifact(artifact: AgentRunArtifact) -> dict[str, object]:
    return _serialize_artifact(artifact)


def serialize_hot_topic(topic: HotTopic) -> dict[str, object]:
    return _serialize_hot_topic(topic)


def serialize_push_plan(plan: PushPlan) -> dict[str, object]:
    return _serialize_push_plan(plan)


def serialize_agent_model_options(db: Session) -> dict[str, object]:
    config = get_agent_config(db)
    options = [
        {
            "value": model_name,
            "label": model_name,
            "is_default": model_name == config["default_model_name"],
        }
        for model_name in config["supported_models"]
    ]
    return {
        "default_model_name": config["default_model_name"],
        "supported_models": config["supported_models"],
        "default_provider": config["default_provider"],
        "prompt_version": config["prompt_version"],
        "push_channels": config["push_channels"],
        "hot_threshold": config["hot_threshold"],
        "options": options,
    }
