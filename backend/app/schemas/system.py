from datetime import datetime

from pydantic import BaseModel, Field


class SystemConfigCreate(BaseModel):
    category: str = Field(min_length=2, max_length=64)
    config_key: str = Field(min_length=2, max_length=128)
    config_value: str
    value_type: str = "STRING"
    description: str | None = Field(default=None, max_length=255)
    is_secret: bool = False
    is_enabled: bool = True


class SystemConfigUpdate(BaseModel):
    config_value: str | None = None
    value_type: str | None = None
    description: str | None = Field(default=None, max_length=255)
    is_secret: bool | None = None
    is_enabled: bool | None = None


class PlatformAccountCreate(BaseModel):
    platform: str = Field(min_length=2, max_length=64)
    display_name: str = Field(min_length=2, max_length=128)
    account_id: str = Field(min_length=2, max_length=128)
    auth_status: str = "UNAUTHORIZED"
    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: datetime | None = None
    extra: dict | None = None
    is_enabled: bool = True


class PlatformAccountUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=128)
    auth_status: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: datetime | None = None
    extra: dict | None = None
    is_enabled: bool | None = None


class DemoTaskRequest(BaseModel):
    payload: dict | None = None

