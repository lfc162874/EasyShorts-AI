from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import MenuType, UserStatus
from app.db.models.base import Base
from app.db.models.mixins import IDMixin, ID_TYPE, TimestampMixin

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ID_TYPE, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ID_TYPE, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_menus = Table(
    "role_menus",
    Base.metadata,
    Column("role_id", ID_TYPE, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("menu_id", ID_TYPE, ForeignKey("menus.id", ondelete="CASCADE"), primary_key=True),
)


class User(IDMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_status", "status"),
    )

    username: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))
    nickname: Mapped[str | None] = mapped_column(String(128))
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=UserStatus.ACTIVE.value, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    roles: Mapped[list["Role"]] = relationship(
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )


class Role(IDMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("code", name="uq_roles_code"),
        Index("ix_roles_code", "code"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    users: Mapped[list[User]] = relationship(
        secondary=user_roles,
        back_populates="roles",
        lazy="selectin",
    )
    menus: Mapped[list["Menu"]] = relationship(
        secondary=role_menus,
        back_populates="roles",
        lazy="selectin",
    )


class Menu(IDMixin, TimestampMixin, Base):
    __tablename__ = "menus"
    __table_args__ = (
        Index("ix_menus_parent_id", "parent_id"),
        UniqueConstraint("name", "parent_id", name="uq_menus_name_parent"),
    )

    parent_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("menus.id", ondelete="SET NULL"),
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    path: Mapped[str | None] = mapped_column(String(255))
    component: Mapped[str | None] = mapped_column(String(255))
    icon: Mapped[str | None] = mapped_column(String(64))
    permission_code: Mapped[str | None] = mapped_column(String(128))
    menu_type: Mapped[str] = mapped_column(String(32), default=MenuType.MENU.value, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    parent: Mapped["Menu | None"] = relationship(remote_side="Menu.id", backref="children")
    roles: Mapped[list[Role]] = relationship(
        secondary=role_menus,
        back_populates="menus",
        lazy="selectin",
    )
