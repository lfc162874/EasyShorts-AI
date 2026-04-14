from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.exceptions import ConflictException, NotFoundException
from app.core.response import success_response
from app.core.security import get_password_hash
from app.db.models.rbac import Role, User
from app.schemas.user import UserCreate, UserUpdate
from app.services.audit_service import record_operation_log
from app.services.rbac_service import serialize_user

router = APIRouter()


@router.get("")
def list_users(
    page: int = 1,
    page_size: int = 20,
    _: User = Depends(require_permission("system:user:list")),
    db: Session = Depends(get_db),
):
    query = select(User).options(selectinload(User.roles)).order_by(User.id.desc())
    total = db.scalar(select(func.count()).select_from(User)) or 0
    items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return success_response(
        {
            "items": [serialize_user(user) for user in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/{user_id}")
def get_user(
    user_id: int,
    _: User = Depends(require_permission("system:user:list")),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    if user is None:
        raise NotFoundException(message="用户不存在")
    return success_response(serialize_user(user))


@router.post("")
def create_user(
    payload: UserCreate,
    request: Request,
    current_user: User = Depends(require_permission("system:user:list")),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(User).where(User.username == payload.username))
    if existing:
        raise ConflictException(message="用户名已存在")
    if payload.email:
        email_taken = db.scalar(select(User).where(User.email == payload.email))
        if email_taken:
            raise ConflictException(message="邮箱已存在")

    roles = []
    if payload.role_ids:
        roles = db.scalars(select(Role).where(Role.id.in_(payload.role_ids))).all()

    user = User(
        username=payload.username,
        email=payload.email,
        phone=payload.phone,
        nickname=payload.nickname,
        hashed_password=get_password_hash(payload.password),
        status=payload.status,
        is_superuser=payload.is_superuser,
    )
    user.roles = list(roles)
    db.add(user)
    db.commit()
    db.refresh(user)

    record_operation_log(
        module="user",
        action="create",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="user",
        biz_id=str(user.id),
        message=f"创建用户 {user.username}",
    )
    return success_response(serialize_user(user), status_code=201)


@router.put("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    current_user: User = Depends(require_permission("system:user:list")),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    if user is None:
        raise NotFoundException(message="用户不存在")

    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        user.hashed_password = get_password_hash(update_data.pop("password"))
    if "role_ids" in update_data and update_data["role_ids"] is not None:
        roles = db.scalars(select(Role).where(Role.id.in_(update_data.pop("role_ids")))).all()
        user.roles = list(roles)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)

    record_operation_log(
        module="user",
        action="update",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="user",
        biz_id=str(user.id),
        message=f"更新用户 {user.username}",
    )
    return success_response(serialize_user(user))
