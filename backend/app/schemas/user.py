from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    nickname: str | None = Field(default=None, max_length=128)
    role_ids: list[int] = Field(default_factory=list)
    is_superuser: bool = False
    status: str = "ACTIVE"


class UserUpdate(BaseModel):
    password: str | None = Field(default=None, min_length=6, max_length=128)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    nickname: str | None = Field(default=None, max_length=128)
    role_ids: list[int] | None = None
    is_superuser: bool | None = None
    status: str | None = None

