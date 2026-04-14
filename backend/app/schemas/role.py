from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    code: str = Field(min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    menu_ids: list[int] = Field(default_factory=list)
    is_system: bool = False


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    menu_ids: list[int] | None = None
    is_system: bool | None = None

