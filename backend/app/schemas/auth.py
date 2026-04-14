from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class UserProfile(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    email: EmailStr | None = None
    is_superuser: bool
    status: str
    roles: list[dict] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)

