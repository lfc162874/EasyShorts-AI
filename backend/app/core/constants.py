from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class MenuType(StrEnum):
    DIRECTORY = "DIRECTORY"
    MENU = "MENU"
    BUTTON = "BUTTON"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class PlatformAuthStatus(StrEnum):
    UNAUTHORIZED = "UNAUTHORIZED"
    AUTHORIZED = "AUTHORIZED"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"


class NewsSourceType(StrEnum):
    RSS = "RSS"
    ATOM = "ATOM"
    WEB = "WEB"
    MANUAL = "MANUAL"


class NewsFetchMode(StrEnum):
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"


class NewsStatus(StrEnum):
    NEW = "NEW"
    DEDUPED = "DEDUPED"
    FILTERED = "FILTERED"
    REJECTED = "REJECTED"
    SCRIPT_READY = "SCRIPT_READY"
    ARCHIVED = "ARCHIVED"


class AgentRunType(StrEnum):
    SINGLE_ARTICLE = "single_article"
    DIGEST = "digest"
    PUSH_PLAN = "push_plan"


class AgentBizType(StrEnum):
    NEWS = "news"
    HOT_TOPIC = "hot_topic"
    DIGEST = "digest"


class HotTopicStatus(StrEnum):
    ACTIVE = "ACTIVE"
    IGNORED = "IGNORED"
    ARCHIVED = "ARCHIVED"


class DigestReportType(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    TOPIC = "TOPIC"


class DigestReportStatus(StrEnum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class PushPlanStatus(StrEnum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PushPlanType(StrEnum):
    IMMEDIATE = "IMMEDIATE"
    DIGEST = "DIGEST"
    SCHEDULED = "SCHEDULED"


class PushRecordStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class VideoStatus(StrEnum):
    INIT = "INIT"
    SCRIPT_GENERATED = "SCRIPT_GENERATED"
    AUDIO_READY = "AUDIO_READY"
    SUBTITLE_READY = "SUBTITLE_READY"
    RENDERING = "RENDERING"
    RENDER_SUCCESS = "RENDER_SUCCESS"
    RENDER_FAILED = "RENDER_FAILED"
    COMPLIANCE_PENDING = "COMPLIANCE_PENDING"
    COMPLIANCE_REJECTED = "COMPLIANCE_REJECTED"
    PUBLISH_READY = "PUBLISH_READY"
    PUBLISHED = "PUBLISHED"


class PublishStatus(StrEnum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    SUBMITTING = "SUBMITTING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class ConfigValueType(StrEnum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    SECRET = "SECRET"


class FileCategory(StrEnum):
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    OTHER = "OTHER"


class OperationStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
