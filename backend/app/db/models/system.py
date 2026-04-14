from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ConfigValueType, OperationStatus, PlatformAuthStatus, TaskStatus
from app.db.models.base import Base
from app.db.models.mixins import IDMixin, ID_TYPE, TimestampMixin


class OperationLog(IDMixin, Base):
    __tablename__ = "operation_logs"
    __table_args__ = (
        Index("ix_operation_logs_module", "module"),
        Index("ix_operation_logs_operator_id", "operator_id"),
        Index("ix_operation_logs_created_at", "created_at"),
    )

    module: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    biz_type: Mapped[str | None] = mapped_column(String(64))
    biz_id: Mapped[str | None] = mapped_column(String(64))
    operator_id: Mapped[int | None] = mapped_column(ID_TYPE)
    operator_name: Mapped[str | None] = mapped_column(String(128))
    request_id: Mapped[str | None] = mapped_column(String(64))
    method: Mapped[str | None] = mapped_column(String(16))
    path: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default=OperationStatus.SUCCESS.value, nullable=False)
    message: Mapped[str | None] = mapped_column(String(255))
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class ErrorLog(IDMixin, Base):
    __tablename__ = "error_logs"
    __table_args__ = (
        Index("ix_error_logs_request_id", "request_id"),
        Index("ix_error_logs_created_at", "created_at"),
    )

    request_id: Mapped[str | None] = mapped_column(String(64))
    path: Mapped[str | None] = mapped_column(String(255))
    method: Mapped[str | None] = mapped_column(String(16))
    user_id: Mapped[int | None] = mapped_column(ID_TYPE)
    error_code: Mapped[int] = mapped_column(Integer, nullable=False)
    error_type: Mapped[str] = mapped_column(String(128), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class TaskJob(IDMixin, TimestampMixin, Base):
    __tablename__ = "task_jobs"
    __table_args__ = (
        Index("ix_task_jobs_status", "status"),
        Index("ix_task_jobs_task_name", "task_name"),
        Index("ix_task_jobs_request_id", "request_id"),
    )

    task_name: Mapped[str] = mapped_column(String(128), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    queue_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.PENDING.value, nullable=False)
    celery_task_id: Mapped[str | None] = mapped_column(String(128))
    request_id: Mapped[str | None] = mapped_column(String(64))
    triggered_by: Mapped[int | None] = mapped_column(ID_TYPE)
    payload: Mapped[dict | None] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FileAsset(IDMixin, TimestampMixin, Base):
    __tablename__ = "file_assets"
    __table_args__ = (
        Index("ix_file_assets_category", "category"),
        Index("ix_file_assets_uploaded_by", "uploaded_by"),
    )

    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    extension: Mapped[str | None] = mapped_column(String(32))
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    bucket_name: Mapped[str | None] = mapped_column(String(128))
    uploaded_by: Mapped[int | None] = mapped_column(ID_TYPE)


class PlatformAccount(IDMixin, TimestampMixin, Base):
    __tablename__ = "platform_accounts"
    __table_args__ = (
        UniqueConstraint("platform", "account_id", name="uq_platform_accounts_platform_account"),
        Index("ix_platform_accounts_platform", "platform"),
    )

    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    account_id: Mapped[str] = mapped_column(String(128), nullable=False)
    auth_status: Mapped[str] = mapped_column(
        String(32),
        default=PlatformAuthStatus.UNAUTHORIZED.value,
        nullable=False,
    )
    access_token: Mapped[str | None] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra: Mapped[dict | None] = mapped_column(JSON)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SystemConfig(IDMixin, TimestampMixin, Base):
    __tablename__ = "system_configs"
    __table_args__ = (
        UniqueConstraint("category", "config_key", name="uq_system_configs_category_key"),
        Index("ix_system_configs_category", "category"),
    )

    category: Mapped[str] = mapped_column(String(64), nullable=False)
    config_key: Mapped[str] = mapped_column(String(128), nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(
        String(32),
        default=ConfigValueType.STRING.value,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(255))
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
