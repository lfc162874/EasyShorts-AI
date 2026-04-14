from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.exceptions import UnauthorizedException
from app.core.config import settings
from app.core.response import success_response
from app.core.security import create_access_token, verify_password
from app.db.models.rbac import User
from app.db.session import get_db
from app.schemas.auth import LoginRequest
from app.services.audit_service import record_operation_log
from app.services.rbac_service import serialize_user

router = APIRouter()


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedException(message="用户名或密码错误")
    if user.status != "ACTIVE":
        raise UnauthorizedException(message="当前账号已禁用")

    user.last_login_at = datetime.now(UTC)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    record_operation_log(
        module="auth",
        action="login",
        operator_id=user.id,
        operator_name=user.username,
        request=request,
        message="用户登录成功",
    )
    return success_response(
        {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": serialize_user(user),
        }
    )


@router.post("/logout")
def logout(current_user: CurrentUser, request: Request):
    record_operation_log(
        module="auth",
        action="logout",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        message="用户退出登录",
    )
    return success_response({"success": True})


@router.get("/me")
def get_current_profile(current_user: CurrentUser):
    return success_response(serialize_user(current_user))
