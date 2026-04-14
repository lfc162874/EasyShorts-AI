from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import NewsFetchMode, NewsSourceType, NewsStatus
from app.schemas.common import ORMModel, PaginationQuery


class NewsSourceCreate(BaseModel):
    source_key: str = Field(min_length=2, max_length=128)
    name: str = Field(min_length=2, max_length=128)
    source_type: NewsSourceType = NewsSourceType.RSS
    url: str = Field(min_length=8, max_length=500)
    category: str | None = Field(default=None, max_length=64)
    language: str = Field(default="en", max_length=16)
    fetch_interval_minutes: int = Field(default=360, ge=5, le=10080)
    is_enabled: bool = True
    extra: dict | None = None


class NewsSourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=128)
    source_type: NewsSourceType | None = None
    url: str | None = Field(default=None, min_length=8, max_length=500)
    category: str | None = Field(default=None, max_length=64)
    language: str | None = Field(default=None, max_length=16)
    fetch_interval_minutes: int | None = Field(default=None, ge=5, le=10080)
    is_enabled: bool | None = None
    extra: dict | None = None


class NewsSourceItem(ORMModel):
    id: int
    source_key: str
    name: str
    source_type: str
    url: str
    category: str | None
    language: str
    fetch_interval_minutes: int
    is_enabled: bool
    last_fetched_at: datetime | None
    last_success_at: datetime | None
    last_error_message: str | None
    extra: dict | None
    created_at: datetime
    updated_at: datetime


class NewsListQuery(PaginationQuery):
    keyword: str | None = Field(default=None, max_length=255)
    status: NewsStatus | None = None
    source_id: int | None = None
    category: str | None = Field(default=None, max_length=64)


class NewsGenerateRequest(BaseModel):
    style: str = Field(default="professional", max_length=64)
    regenerate: bool = False


class NewsSyncRequest(BaseModel):
    fetch_mode: NewsFetchMode = NewsFetchMode.MANUAL


class NewsItem(ORMModel):
    id: int
    title: str
    content: str | None
    source: str
    source_id: int | None
    source_url: str | None
    url: str
    publish_time: datetime | None
    status: str
    dedup_hash: str | None
    category: str | None
    hot_score: int
    language: str
    summary: str | None
    translated_title: str | None
    translated_content: str | None
    script: str | None
    tags: list[str] | None
    filter_reason: str | None
    raw_metadata: dict | None
    created_at: datetime
    updated_at: datetime


class NewsFetchRecordItem(ORMModel):
    id: int
    source_id: int
    source_name: str | None = None
    task_job_id: int | None
    request_id: str | None
    fetch_mode: str
    status: str
    total_count: int
    new_count: int
    duplicate_count: int
    filtered_count: int
    error_count: int
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    extra: dict | None
    created_at: datetime
    updated_at: datetime


class NewsDetailItem(NewsItem):
    source_detail: NewsSourceItem | None = None
    fetch_records: list[NewsFetchRecordItem] = Field(default_factory=list)

