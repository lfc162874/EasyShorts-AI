from __future__ import annotations

from datetime import UTC, datetime

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.agents.common import merge_channels, normalize_whitespace, recommend_channels
from app.core.constants import AgentBizType, PushPlanStatus, PushPlanType, PushRecordStatus
from app.core.logging import get_logger
from app.db.models.agent import DigestReport, HotTopic, PushPlan, PushRecord
from app.services.push_delivery_service import PushDeliveryResult, deliver_push_channel, load_push_delivery_config
from app.services.agent_config_service import get_agent_config

logger = get_logger(__name__)

SUPPORTED_PUSH_CHANNELS = {
    "email",
    "feishu",
    "wechat_work",
    "webhook",
    "dingding",
    "dingtalk",
    "slack",
    "telegram",
}


def _now() -> datetime:
    return datetime.now(UTC)


def _serialize_hot_topic(topic: HotTopic | None) -> dict[str, object] | None:
    if topic is None:
        return None
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


def _serialize_digest_report(report: DigestReport | None) -> dict[str, object] | None:
    if report is None:
        return None
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


def _serialize_push_plan(plan: PushPlan | None) -> dict[str, object] | None:
    if plan is None:
        return None
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


def serialize_push_record(
    record: PushRecord,
    *,
    plan: PushPlan | None = None,
    digest_report: DigestReport | None = None,
    topic: HotTopic | None = None,
) -> dict[str, object]:
    payload = {
        "id": record.id,
        "plan_id": record.plan_id,
        "digest_id": record.digest_id,
        "topic_id": record.topic_id,
        "channel": record.channel,
        "status": record.status,
        "request_id": record.request_id,
        "payload": record.payload,
        "result": record.result,
        "error_message": record.error_message,
        "pushed_at": record.pushed_at,
        "extra": record.extra,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
    payload["plan"] = _serialize_push_plan(plan)
    payload["digest_report"] = _serialize_digest_report(digest_report)
    payload["topic"] = _serialize_hot_topic(topic)
    return payload


def list_push_records(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    plan_id: int | None = None,
    digest_id: int | None = None,
    topic_id: int | None = None,
    channel: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
) -> tuple[list[tuple[PushRecord, PushPlan | None, DigestReport | None, HotTopic | None]], int]:
    filters = []
    if plan_id is not None:
        filters.append(PushRecord.plan_id == plan_id)
    if digest_id is not None:
        filters.append(PushRecord.digest_id == digest_id)
    if topic_id is not None:
        filters.append(PushRecord.topic_id == topic_id)
    if channel:
        filters.append(PushRecord.channel == channel)
    if status:
        filters.append(PushRecord.status == status)
    if keyword:
        like = f"%{keyword.strip()}%"
        filters.append(
            or_(
                PushRecord.channel.ilike(like),
                PushRecord.error_message.ilike(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(PushRecord).where(*filters)) or 0
    records = db.scalars(
        select(PushRecord)
        .where(*filters)
        .order_by(PushRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    plan_ids = {record.plan_id for record in records if record.plan_id is not None}
    digest_ids = {record.digest_id for record in records if record.digest_id is not None}
    topic_ids = {record.topic_id for record in records if record.topic_id is not None}

    plans = {
        plan.id: plan
        for plan in db.scalars(select(PushPlan).where(PushPlan.id.in_(plan_ids))).all()
    }
    digests = {
        digest.id: digest
        for digest in db.scalars(select(DigestReport).where(DigestReport.id.in_(digest_ids))).all()
    }
    topics = {
        topic.id: topic
        for topic in db.scalars(select(HotTopic).where(HotTopic.id.in_(topic_ids))).all()
    }
    return [
        (
            record,
            plans.get(record.plan_id) if record.plan_id is not None else None,
            digests.get(record.digest_id) if record.digest_id is not None else None,
            topics.get(record.topic_id) if record.topic_id is not None else None,
        )
        for record in records
    ], total


def get_push_record(db: Session, record_id: int) -> PushRecord:
    record = db.get(PushRecord, record_id)
    if record is None:
        from app.core.exceptions import NotFoundException

        raise NotFoundException(message="推送记录不存在")
    return record


def get_push_record_detail(db: Session, record_id: int) -> dict[str, object]:
    record = get_push_record(db, record_id)
    plan = db.get(PushPlan, record.plan_id) if record.plan_id else None
    digest_report = db.get(DigestReport, record.digest_id) if record.digest_id else None
    topic = db.get(HotTopic, record.topic_id) if record.topic_id else None
    return _serialize_push_record(record, plan=plan, digest_report=digest_report, topic=topic)


def _resolve_push_channels(plan: PushPlan, db: Session) -> list[str]:
    channels = [str(channel).strip() for channel in (plan.channels or []) if str(channel).strip()]
    if channels:
        return merge_channels(channels)

    config = get_agent_config(db)
    default_channels = [str(channel).strip() for channel in config.get("push_channels") or [] if str(channel).strip()]
    if default_channels:
        return merge_channels(default_channels)

    priority = str(plan.priority or "LOW")
    return recommend_channels(priority)


def _build_push_delivery_context(
    *,
    plan: PushPlan,
    digest_report: DigestReport | None,
    topic: HotTopic | None,
    request_id: str | None,
    triggered_by: int | None,
) -> dict[str, object]:
    if digest_report is not None:
        title = normalize_whitespace(digest_report.title or plan.reason or "AI 热点简报")
        summary = normalize_whitespace(digest_report.summary or digest_report.content or plan.reason or title)
        highlights = [normalize_whitespace(str(item)) for item in (digest_report.highlights or []) if normalize_whitespace(str(item))]
        if not highlights and topic is not None:
            highlights = [normalize_whitespace(topic.summary or topic.reason or topic.title)]
        message_text = summarize_report_content(title, summary, highlights)
    else:
        title = normalize_whitespace((plan.extra or {}).get("title") if isinstance(plan.extra, dict) else None) or (
            normalize_whitespace(topic.title) if topic is not None else normalize_whitespace(plan.reason or "AI 热点推送")
        )
        summary = normalize_whitespace((topic.summary if topic is not None else None) or plan.reason or title)
        highlights = []
        if topic is not None:
            if topic.reason:
                highlights.append(normalize_whitespace(topic.reason))
            if topic.category:
                highlights.append(f"分类：{normalize_whitespace(topic.category)}")
            if topic.tags:
                joined_tags = "、".join(
                    normalize_whitespace(str(tag))
                    for tag in topic.tags[:5]
                    if normalize_whitespace(str(tag))
                )
                if joined_tags:
                    highlights.append(f"标签：{joined_tags}")
            if topic.score is not None:
                highlights.append(f"热度：{topic.score}")
        message_lines = [f"# {title}", ""]
        if summary:
            message_lines.extend(["## 摘要", summary, ""])
        if highlights:
            message_lines.extend(["## 要点"])
            for item in highlights:
                cleaned = normalize_whitespace(item)
                if cleaned:
                    message_lines.append(f"- {cleaned}")
            message_lines.append("")
        if topic is not None:
            message_lines.extend(
                [
                    "## 热点信息",
                    f"- 分类：{normalize_whitespace(topic.category or '未分类')}",
                    f"- 优先级：{normalize_whitespace(topic.priority or '未知')}",
                    f"- 评分：{topic.score}",
                    f"- 趋势：{normalize_whitespace(topic.trend or '未知')}",
                ]
            )
        message_text = "\n".join(line for line in message_lines if line is not None).strip()

    return {
        "title": title,
        "summary": summary,
        "highlights": highlights,
        "message_text": message_text,
        "payload": {
            "plan": _serialize_push_plan(plan),
            "digest_report": _serialize_digest_report(digest_report),
            "topic": _serialize_hot_topic(topic),
            "title": title,
            "summary": summary,
            "highlights": highlights,
            "message_text": message_text,
            "request_id": request_id,
            "triggered_by": triggered_by,
        },
    }


def execute_push_plan_records(
    db: Session,
    plan: PushPlan,
    *,
    request_id: str | None = None,
    triggered_by: int | None = None,
    force: bool = False,
) -> list[PushRecord]:
    existing_records = db.scalars(
        select(PushRecord).where(PushRecord.plan_id == plan.id).order_by(PushRecord.id.asc())
    ).all()
    if existing_records and plan.status == PushPlanStatus.EXECUTED.value and not force:
        return list(existing_records)

    channels = _resolve_push_channels(plan, db)
    now = _now()
    record_ids: list[int] = []
    channel_results: list[dict[str, object]] = []
    created_records: list[PushRecord] = []
    delivery_outcomes: list[PushDeliveryResult] = []
    delivery_config = load_push_delivery_config(db)

    digest_id = None
    if plan.biz_type == AgentBizType.DIGEST.value:
        try:
            digest_id = int(plan.biz_id)
        except (TypeError, ValueError):
            digest_id = None

    digest_report = db.get(DigestReport, digest_id) if digest_id is not None else None
    topic = db.get(HotTopic, plan.topic_id) if plan.topic_id is not None else None
    delivery_context = _build_push_delivery_context(
        plan=plan,
        digest_report=digest_report,
        topic=topic,
        request_id=request_id,
        triggered_by=triggered_by,
    )

    for channel in channels or ["email"]:
        normalized_channel = channel.strip().lower()
        if normalized_channel not in SUPPORTED_PUSH_CHANNELS:
            outcome = PushDeliveryResult(
                channel=normalized_channel,
                success=False,
                simulated=False,
                delivery_mode="real",
                message=f"不支持的推送渠道：{normalized_channel}",
                attempts=0,
                error_message=f"不支持的推送渠道：{normalized_channel}",
            )
        else:
            outcome = deliver_push_channel(
                channel=normalized_channel,
                context=delivery_context,
                config=delivery_config,
            )

        record_payload = {
            **(delivery_context.get("payload") or {}),
            "channel": normalized_channel,
            "request_id": request_id,
            "triggered_by": triggered_by,
        }
        record_payload = jsonable_encoder(record_payload)
        record = PushRecord(
            plan_id=plan.id,
            digest_id=digest_id,
            topic_id=plan.topic_id,
            channel=normalized_channel,
            status=PushRecordStatus.SENT.value if outcome.success else PushRecordStatus.FAILED.value,
            request_id=request_id,
            payload=record_payload,
            result=jsonable_encoder(outcome.as_dict()),
            error_message=None if outcome.success else outcome.error_message or outcome.message,
            pushed_at=now if outcome.success else None,
            extra=jsonable_encoder({
                "simulated": outcome.simulated,
                "delivery_mode": outcome.delivery_mode,
                "attempts": outcome.attempts,
                "endpoint": outcome.endpoint,
                "response_status": outcome.response_status,
                "triggered_by": triggered_by,
                "plan_type": plan.push_type,
            }),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        created_records.append(record)
        record_ids.append(record.id)
        delivery_outcomes.append(outcome)
        channel_results.append(
            {
                "record_id": record.id,
                "channel": normalized_channel,
                "status": record.status,
                "message": outcome.message,
                "simulated": outcome.simulated,
                "delivery_mode": outcome.delivery_mode,
                "attempts": outcome.attempts,
                "endpoint": outcome.endpoint,
                "response_status": outcome.response_status,
            }
        )

    success_count = sum(1 for result in channel_results if result["status"] == PushRecordStatus.SENT.value)
    failure_count = len(channel_results) - success_count
    real_success_count = sum(1 for outcome in delivery_outcomes if outcome.success and not outcome.simulated)
    simulated_success_count = sum(1 for outcome in delivery_outcomes if outcome.success and outcome.simulated)
    if success_count == 0:
        delivery_mode = "failed"
    elif failure_count == 0:
        if real_success_count and simulated_success_count:
            delivery_mode = "mixed"
        elif real_success_count:
            delivery_mode = "real"
        else:
            delivery_mode = "simulated"
    else:
        delivery_mode = "mixed"

    plan.status = PushPlanStatus.EXECUTED.value if success_count else PushPlanStatus.FAILED.value
    plan.executed_at = now
    plan.extra = {
        **(plan.extra or {}),
        "executed_at": now.isoformat(),
        "execution_result": delivery_mode,
        "delivery_mode": delivery_mode,
        "push_record_ids": record_ids,
        "channel_results": channel_results,
        "success_count": success_count,
        "failure_count": failure_count,
        "real_success_count": real_success_count,
        "simulated_success_count": simulated_success_count,
    }
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return created_records


def summarize_report_content(title: str, summary: str | None, highlights: list[str] | None) -> str:
    summary_text = normalize_whitespace(summary or "")
    lines = [f"# {title}", ""]
    if summary_text:
        lines.extend(["## 摘要", summary_text, ""])
    if highlights:
        lines.extend(["## 要点"])
        for item in highlights:
            cleaned = normalize_whitespace(item)
            if cleaned:
                lines.append(f"- {cleaned}")
        lines.append("")
    return "\n".join(line for line in lines if line is not None).strip()
