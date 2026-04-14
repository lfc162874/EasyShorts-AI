from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import UserStatus
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.db.models.rbac import User
from app.db.session import get_db
from app.services.rbac_service import collect_permissions

bearer_scheme = HTTPBearer(auto_error=False)
DBSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    request: Request,
    db: DBSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise UnauthorizedException()

    try:
        payload = decode_token(credentials.credentials)
        subject = payload.get("sub")
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise UnauthorizedException() from exc

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None or user.status != UserStatus.ACTIVE.value:
        raise UnauthorizedException(message="用户不存在或已被禁用")

    request.state.user_id = user.id
    request.state.username = user.username
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(permission_code: str):
    def dependency(current_user: CurrentUser) -> User:
        if current_user.is_superuser:
            return current_user
        permissions = collect_permissions(current_user)
        if permission_code not in permissions:
            raise ForbiddenException()
        return current_user

    return dependency
