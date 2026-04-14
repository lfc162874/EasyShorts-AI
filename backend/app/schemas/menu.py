from pydantic import BaseModel, Field


class MenuCreate(BaseModel):
    parent_id: int | None = None
    name: str = Field(min_length=2, max_length=128)
    title: str = Field(min_length=2, max_length=128)
    path: str | None = Field(default=None, max_length=255)
    component: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=64)
    permission_code: str | None = Field(default=None, max_length=128)
    menu_type: str = "MENU"
    sort_order: int = 0
    hidden: bool = False


class MenuUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=128)
    path: str | None = Field(default=None, max_length=255)
    component: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=64)
    permission_code: str | None = Field(default=None, max_length=128)
    menu_type: str | None = None
    sort_order: int | None = None
    hidden: bool | None = None
    parent_id: int | None = None

