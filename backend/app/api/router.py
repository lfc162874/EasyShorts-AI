from fastapi import APIRouter

from app.api.v1 import auth, health, menus, news, roles, system, uploads, users
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_prefix)
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/system/users", tags=["users"])
api_router.include_router(roles.router, prefix="/system/roles", tags=["roles"])
api_router.include_router(menus.router, prefix="/system/menus", tags=["menus"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
