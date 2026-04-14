from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import NewsFetchMode, NewsSourceType, NewsStatus, PublishStatus, TaskStatus, VideoStatus
from app.db.models.base import Base
from app.db.models.mixins import IDMixin, ID_TYPE, TimestampMixin


class News(IDMixin, TimestampMixin, Base):
    __tablename__ = "news"
    __table_args__ = (
        UniqueConstraint("url", name="uq_news_url"),
        Index("ix_news_status", "status"),
        Index("ix_news_publish_time", "publish_time"),
        Index("ix_news_source_id", "source_id"),
        Index("ix_news_category", "category"),
        Index("ix_news_dedup_hash", "dedup_hash"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("news_sources.id", ondelete="SET NULL"),
    )
    source_url: Mapped[str | None] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    publish_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default=NewsStatus.NEW.value, nullable=False)
    dedup_hash: Mapped[str | None] = mapped_column(String(128))
    category: Mapped[str | None] = mapped_column(String(64))
    hot_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    translated_title: Mapped[str | None] = mapped_column(String(500))
    translated_content: Mapped[str | None] = mapped_column(Text)
    script: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    filter_reason: Mapped[str | None] = mapped_column(Text)
    raw_metadata: Mapped[dict | None] = mapped_column(JSON)


class NewsSource(IDMixin, TimestampMixin, Base):
    __tablename__ = "news_sources"
    __table_args__ = (
        UniqueConstraint("source_key", name="uq_news_sources_source_key"),
        Index("ix_news_sources_source_type", "source_type"),
        Index("ix_news_sources_is_enabled", "is_enabled"),
    )

    source_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(32),
        default=NewsSourceType.RSS.value,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64))
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, default=360, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_message: Mapped[str | None] = mapped_column(Text)
    extra: Mapped[dict | None] = mapped_column(JSON)


class NewsFetchRecord(IDMixin, TimestampMixin, Base):
    __tablename__ = "news_fetch_records"
    __table_args__ = (
        Index("ix_news_fetch_records_source_id", "source_id"),
        Index("ix_news_fetch_records_status", "status"),
        Index("ix_news_fetch_records_request_id", "request_id"),
    )

    source_id: Mapped[int] = mapped_column(
        ID_TYPE,
        ForeignKey("news_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_job_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("task_jobs.id", ondelete="SET NULL"),
    )
    request_id: Mapped[str | None] = mapped_column(String(64))
    fetch_mode: Mapped[str] = mapped_column(
        String(32),
        default=NewsFetchMode.MANUAL.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.PENDING.value, nullable=False)
    total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    filtered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra: Mapped[dict | None] = mapped_column(JSON)


class Video(IDMixin, TimestampMixin, Base):
    __tablename__ = "video"
    __table_args__ = (Index("ix_video_status", "status"),)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    script: Mapped[str | None] = mapped_column(Text)
    video_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(32), default=VideoStatus.INIT.value, nullable=False)
    news_id: Mapped[int | None] = mapped_column(ID_TYPE)


class PublishRecord(IDMixin, TimestampMixin, Base):
    __tablename__ = "publish_record"
    __table_args__ = (
        Index("ix_publish_record_status", "status"),
        Index("ix_publish_record_platform", "platform"),
    )

    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    video_id: Mapped[int] = mapped_column(ID_TYPE, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=PublishStatus.PENDING.value, nullable=False)
    publish_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    platform_result: Mapped[str | None] = mapped_column(Text)
