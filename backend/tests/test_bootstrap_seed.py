from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.business import NewsSource
from app.db.models.rbac import Menu, Role, User
from app.db.models.system import PlatformAccount, SystemConfig
from app.services.bootstrap_service import bootstrap_default_data


def make_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)()


def test_bootstrap_default_data_is_idempotent():
    with make_session() as db:
        bootstrap_default_data(db)
        initial_counts = {
            "menus": db.scalar(select(func.count()).select_from(Menu)) or 0,
            "roles": db.scalar(select(func.count()).select_from(Role)) or 0,
            "users": db.scalar(select(func.count()).select_from(User)) or 0,
            "configs": db.scalar(select(func.count()).select_from(SystemConfig)) or 0,
            "news_sources": db.scalar(select(func.count()).select_from(NewsSource)) or 0,
            "platform_accounts": db.scalar(select(func.count()).select_from(PlatformAccount)) or 0,
        }

        bootstrap_default_data(db)
        repeated_counts = {
            "menus": db.scalar(select(func.count()).select_from(Menu)) or 0,
            "roles": db.scalar(select(func.count()).select_from(Role)) or 0,
            "users": db.scalar(select(func.count()).select_from(User)) or 0,
            "configs": db.scalar(select(func.count()).select_from(SystemConfig)) or 0,
            "news_sources": db.scalar(select(func.count()).select_from(NewsSource)) or 0,
            "platform_accounts": db.scalar(select(func.count()).select_from(PlatformAccount)) or 0,
        }

        assert initial_counts == repeated_counts
        assert repeated_counts["menus"] >= 20
        assert repeated_counts["roles"] == 2
        assert repeated_counts["users"] == 2
        assert repeated_counts["configs"] >= 9
        assert repeated_counts["news_sources"] == 2
        assert repeated_counts["platform_accounts"] == 1

        admin = db.scalar(select(User).where(User.username == "admin"))
        assert admin is not None
        permissions = {
            menu.permission_code
            for role in admin.roles
            for menu in role.menus
            if menu.permission_code
        }
        assert "system:menu:list" in permissions
        assert "system:user:list" in permissions
        assert "system:platform-account:list" in permissions
        assert "news:list" in permissions
        assert "news:generate" in permissions
