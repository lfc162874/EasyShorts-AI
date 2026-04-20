from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.constants import DigestReportStatus, DigestReportType, PushRecordStatus
from app.schemas.common import ORMModel, PaginationQuery


class AgentConfigUpdateRequest(BaseModel):
    default_model_name: str | None = Field(default=None, max_length=128)
    supported_models: list[str] | None = None
    default_provider: str | None = Field(default=None, max_length=64)
    prompt_version: str | None = Field(default=None, max_length=32)
    push_channels: list[str] | None = None


class AgentRunRequest(BaseModel):
    model_name: str | None = Field(default=None, max_length=128)
    force: bool = False


class AgentRunRetryRequest(AgentRunRequest):
    pass


class AgentModelItem(BaseModel):
    value: str
    label: str
    is_default: bool = False


class AgentConfigItem(BaseModel):
    default_model_name: str
    supported_models: list[str]
    default_provider: str
    prompt_version: str
    push_channels: list[str]
    hot_threshold: int
    prompts: dict[str, str]


class AgentRunQuery(PaginationQuery):
    status: str | None = Field(default=None, max_length=32)
    run_type: str | None = Field(default=None, max_length=32)
    biz_type: str | None = Field(default=None, max_length=64)
    model_name: str | None = Field(default=None, max_length=128)
    keyword: str | None = Field(default=None, max_length=255)


class AgentRunStepItem(ORMModel):
    id: int
    run_id: int
    step_code: str
    agent_name: str
    step_order: int
    status: str
    model_name: str
    prompt_version: str
    input_summary: str | None
    output_summary: str | None
    payload: dict | None
    result: dict | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    created_at: datetime
    updated_at: datetime


class AgentRunArtifactItem(ORMModel):
    id: int
    run_id: int
    step_id: int | None
    artifact_type: str
    artifact_key: str
    content_json: dict | None
    content_text: str | None
    created_at: datetime
    updated_at: datetime


class AgentRunItem(ORMModel):
    id: int
    parent_run_id: int | None
    task_job_id: int | None
    run_type: str
    biz_type: str
    biz_id: str
    status: str
    current_step: str | None
    model_name: str
    prompt_version: str
    input_summary: str | None
    output_summary: str | None
    payload: dict | None
    result: dict | None
    triggered_by: int | None
    request_id: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AgentRunDetailItem(AgentRunItem):
    steps: list[AgentRunStepItem] = Field(default_factory=list)
    artifacts: list[AgentRunArtifactItem] = Field(default_factory=list)


class HotTopicNewsItem(ORMModel):
    id: int
    news_id: int
    source_id: int | None
    source_name: str | None = None
    title: str
    url: str
    weight: int
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class HotTopicItem(ORMModel):
    id: int
    topic_key: str
    title: str
    summary: str | None
    category: str | None
    tags: list[str] | None
    score: int
    priority: str
    reason: str | None
    trend: str | None
    status: str
    model_name: str
    prompt_version: str
    news_count: int
    source_count: int
    primary_news_id: int | None
    extra: dict | None
    created_at: datetime
    updated_at: datetime


class HotTopicDetailItem(HotTopicItem):
    items: list[HotTopicNewsItem] = Field(default_factory=list)


class PushPlanItem(ORMModel):
    id: int
    biz_type: str
    biz_id: str
    run_id: int | None
    topic_id: int | None
    push_now: bool
    priority: str
    push_type: str
    channels: list[str] | None
    planned_at: datetime | None
    status: str
    reason: str | None
    model_name: str
    prompt_version: str
    executed_at: datetime | None
    extra: dict | None
    created_at: datetime
    updated_at: datetime


class PushPlanDetailItem(PushPlanItem):
    topic: HotTopicItem | None = None
    run: AgentRunItem | None = None


class DigestRunRequest(BaseModel):
    report_type: DigestReportType = DigestReportType.DAILY
    report_date: date | None = None
    topic_ids: list[int] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=50)
    model_name: str | None = Field(default=None, max_length=128)
    force: bool = False


class DigestPushRequest(BaseModel):
    channels: list[str] | None = None
    force: bool = False


class DigestReportQuery(PaginationQuery):
    report_type: DigestReportType | None = None
    status: DigestReportStatus | None = None
    keyword: str | None = Field(default=None, max_length=255)
    date_from: date | None = None
    date_to: date | None = None


class PushRecordItem(ORMModel):
    id: int
    plan_id: int | None
    digest_id: int | None
    topic_id: int | None
    channel: str
    status: str
    request_id: str | None
    payload: dict | None
    result: dict | None
    error_message: str | None
    pushed_at: datetime | None
    extra: dict | None
    created_at: datetime
    updated_at: datetime


class PushRecordQuery(PaginationQuery):
    plan_id: int | None = None
    digest_id: int | None = None
    topic_id: int | None = None
    channel: str | None = Field(default=None, max_length=64)
    status: PushRecordStatus | None = None
    keyword: str | None = Field(default=None, max_length=255)


class DigestReportItem(ORMModel):
    id: int
    report_type: str
    report_date: date
    title: str
    summary: str | None
    content: str | None
    highlights: list[str] | None
    status: str
    topic_count: int
    model_name: str
    prompt_version: str
    run_id: int | None
    task_job_id: int | None
    published_at: datetime | None
    extra: dict | None
    created_at: datetime
    updated_at: datetime


class DigestReportDetailItem(DigestReportItem):
    run: AgentRunDetailItem | None = None
    topics: list[HotTopicItem] = Field(default_factory=list)
    push_plan: PushPlanDetailItem | None = None
    push_records: list[PushRecordItem] = Field(default_factory=list)
