from fastapi import APIRouter

from app.core.config import settings
from app.core.response import success_response

router = APIRouter()


@router.get("/health")
def healthcheck():
    return success_response(
        {
            "service": settings.app_name,
            "environment": settings.app_env,
            "api_prefix": settings.api_prefix,
        }
    )

