from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources.types import NoDecode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="EasyShorts AI Backend", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    api_prefix: str = Field(default="/easy-shorts", alias="API_PREFIX")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(
        default=720,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    algorithm: str = "HS256"

    database_url: str = Field(
        default="sqlite:///./data/easy_shorts.db",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    dashscope_api_key: str | None = Field(default=None, alias="DASHSCOPE_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")

    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    local_storage_root: str = Field(default="storage/uploads", alias="LOCAL_STORAGE_ROOT")
    local_storage_public_prefix: str = Field(
        default="/easy-shorts/assets",
        alias="LOCAL_STORAGE_PUBLIC_PREFIX",
    )
    max_upload_size_mb: int = Field(default=200, alias="MAX_UPLOAD_SIZE_MB")

    auto_create_tables: bool = Field(default=True, alias="AUTO_CREATE_TABLES")

    bootstrap_admin_on_startup: bool = Field(
        default=True,
        alias="BOOTSTRAP_ADMIN_ON_STARTUP",
    )
    bootstrap_admin_username: str = Field(default="admin", alias="BOOTSTRAP_ADMIN_USERNAME")
    bootstrap_admin_password: str = Field(
        default="Admin@123456",
        alias="BOOTSTRAP_ADMIN_PASSWORD",
    )
    bootstrap_admin_nickname: str = Field(
        default="System Admin",
        alias="BOOTSTRAP_ADMIN_NICKNAME",
    )
    bootstrap_admin_email: str = Field(
        default="admin@easyshorts.local",
        alias="BOOTSTRAP_ADMIN_EMAIL",
    )

    agent_default_model_name: str = Field(
        default="qwen3.5-plus",
        alias="AGENT_DEFAULT_MODEL_NAME",
    )
    agent_supported_models: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["qwen3.5-plus", "qwen-max", "deepseek-v3"],
        alias="AGENT_SUPPORTED_MODELS",
    )
    agent_prompt_version: str = Field(default="v1", alias="AGENT_PROMPT_VERSION")
    agent_default_provider: str = Field(default="dashscope", alias="AGENT_DEFAULT_PROVIDER")

    backend_cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"],
        alias="BACKEND_CORS_ORIGINS",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        if value.startswith("[") and value.endswith("]"):
            import json

            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in value.split(",") if item.strip()]

    @field_validator("agent_supported_models", mode="before")
    @classmethod
    def parse_agent_supported_models(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return [item.strip() for item in value if str(item).strip()]
        if not value:
            return []
        if value.startswith("[") and value.endswith("]"):
            import json

            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def backend_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def local_storage_path(self) -> Path:
        root = Path(self.local_storage_root)
        if root.is_absolute():
            return root
        return self.backend_root / root

    @property
    def sqlite_data_path(self) -> Path | None:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            return None
        raw_path = self.database_url.removeprefix(prefix)
        path = Path(raw_path)
        if path.is_absolute():
            return path
        return self.backend_root / raw_path

    @property
    def resolved_database_url(self) -> str:
        sqlite_path = self.sqlite_data_path
        if sqlite_path is None:
            return self.database_url
        return f"sqlite:///{sqlite_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
