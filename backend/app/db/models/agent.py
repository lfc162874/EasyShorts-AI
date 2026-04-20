from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import (
    DigestReportStatus,
    DigestReportType,
    HotTopicStatus,
    PushPlanStatus,
    PushPlanType,
    PushRecordStatus,
    TaskStatus,
)
from app.db.models.base import Base
from app.db.models.mixins import IDMixin, ID_TYPE, TimestampMixin


class AgentRun(IDMixin, TimestampMixin, Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_status", "status"),
        Index("ix_agent_runs_run_type", "run_type"),
        Index("ix_agent_runs_biz_type", "biz_type"),
        Index("ix_agent_runs_biz_id", "biz_id"),
        Index("ix_agent_runs_request_id", "request_id"),
    )

    parent_run_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
    )
    task_job_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("task_jobs.id", ondelete="SET NULL"),
    )
    run_type: Mapped[str] = mapped_column(String(32), nullable=False)
    biz_type: Mapped[str] = mapped_column(String(64), nullable=False)
    biz_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.PENDING.value, nullable=False)
    current_step: Mapped[str | None] = mapped_column(String(64))
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    input_summary: Mapped[str | None] = mapped_column(Text)
    output_summary: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON)
    triggered_by: Mapped[int | None] = mapped_column(ID_TYPE)
    request_id: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AgentRunStep(IDMixin, TimestampMixin, Base):
    __tablename__ = "agent_run_steps"
    __table_args__ = (
        Index("ix_agent_run_steps_run_id", "run_id"),
        Index("ix_agent_run_steps_status", "status"),
        Index("ix_agent_run_steps_step_code", "step_code"),
        UniqueConstraint("run_id", "step_code", name="uq_agent_run_steps_run_step_code"),
    )

    run_id: Mapped[int] = mapped_column(
        ID_TYPE,
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_code: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.PENDING.value, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    input_summary: Mapped[str | None] = mapped_column(Text)
    output_summary: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)


class AgentRunArtifact(IDMixin, TimestampMixin, Base):
    __tablename__ = "agent_run_artifacts"
    __table_args__ = (
        Index("ix_agent_run_artifacts_run_id", "run_id"),
        Index("ix_agent_run_artifacts_step_id", "step_id"),
        Index("ix_agent_run_artifacts_artifact_type", "artifact_type"),
        UniqueConstraint("run_id", "step_id", "artifact_key", name="uq_agent_run_artifacts_key"),
    )

    run_id: Mapped[int] = mapped_column(
        ID_TYPE,
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("agent_run_steps.id", ondelete="CASCADE"),
    )
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_key: Mapped[str] = mapped_column(String(128), nullable=False)
    content_json: Mapped[dict | None] = mapped_column(JSON)
    content_text: Mapped[str | None] = mapped_column(Text)


class HotTopic(IDMixin, TimestampMixin, Base):
    __tablename__ = "hot_topics"
    __table_args__ = (
        UniqueConstraint("topic_key", name="uq_hot_topics_topic_key"),
        Index("ix_hot_topics_status", "status"),
        Index("ix_hot_topics_category", "category"),
        Index("ix_hot_topics_score", "score"),
    )

    topic_key: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(64))
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    trend: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default=HotTopicStatus.ACTIVE.value, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    news_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    primary_news_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("news.id", ondelete="SET NULL"),
    )
    extra: Mapped[dict | None] = mapped_column(JSON)


class HotTopicItem(IDMixin, TimestampMixin, Base):
    __tablename__ = "hot_topic_items"
    __table_args__ = (
        UniqueConstraint("topic_id", "news_id", name="uq_hot_topic_items_topic_news"),
        Index("ix_hot_topic_items_topic_id", "topic_id"),
        Index("ix_hot_topic_items_news_id", "news_id"),
        Index("ix_hot_topic_items_source_id", "source_id"),
    )

    topic_id: Mapped[int] = mapped_column(
        ID_TYPE,
        ForeignKey("hot_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    news_id: Mapped[int] = mapped_column(
        ID_TYPE,
        ForeignKey("news.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("news_sources.id", ondelete="SET NULL"),
    )
    weight: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class PushPlan(IDMixin, TimestampMixin, Base):
    __tablename__ = "push_plans"
    __table_args__ = (
        Index("ix_push_plans_status", "status"),
        Index("ix_push_plans_priority", "priority"),
        Index("ix_push_plans_biz_type", "biz_type"),
        Index("ix_push_plans_biz_id", "biz_id"),
    )

    biz_type: Mapped[str] = mapped_column(String(64), nullable=False)
    biz_id: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
    )
    topic_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("hot_topics.id", ondelete="SET NULL"),
    )
    push_now: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default="LOW", nullable=False)
    push_type: Mapped[str] = mapped_column(String(32), default=PushPlanType.SCHEDULED.value, nullable=False)
    channels: Mapped[list[str] | None] = mapped_column(JSON)
    planned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default=PushPlanStatus.PENDING.value, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra: Mapped[dict | None] = mapped_column(JSON)


class DigestReport(IDMixin, TimestampMixin, Base):
    __tablename__ = "digest_reports"
    __table_args__ = (
        UniqueConstraint("report_type", "report_date", name="uq_digest_reports_type_date"),
        Index("ix_digest_reports_status", "status"),
        Index("ix_digest_reports_report_type", "report_type"),
        Index("ix_digest_reports_report_date", "report_date"),
        Index("ix_digest_reports_run_id", "run_id"),
    )

    report_type: Mapped[str] = mapped_column(String(32), nullable=False, default=DigestReportType.DAILY.value)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    highlights: Mapped[list[str] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(32),
        default=DigestReportStatus.DRAFT.value,
        nullable=False,
    )
    topic_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    run_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
    )
    task_job_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("task_jobs.id", ondelete="SET NULL"),
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra: Mapped[dict | None] = mapped_column(JSON)


class PushRecord(IDMixin, TimestampMixin, Base):
    __tablename__ = "push_records"
    __table_args__ = (
        Index("ix_push_records_status", "status"),
        Index("ix_push_records_channel", "channel"),
        Index("ix_push_records_plan_id", "plan_id"),
        Index("ix_push_records_digest_id", "digest_id"),
        Index("ix_push_records_topic_id", "topic_id"),
        Index("ix_push_records_request_id", "request_id"),
    )

    plan_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("push_plans.id", ondelete="SET NULL"),
    )
    digest_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("digest_reports.id", ondelete="SET NULL"),
    )
    topic_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("hot_topics.id", ondelete="SET NULL"),
    )
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=PushRecordStatus.PENDING.value,
        nullable=False,
    )
    request_id: Mapped[str | None] = mapped_column(String(64))
    payload: Mapped[dict | None] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra: Mapped[dict | None] = mapped_column(JSON)
