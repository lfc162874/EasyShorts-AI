from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.exceptions import ConflictException, NotFoundException
from app.core.response import success_response
from app.db.models.rbac import Menu, Role, User
from app.schemas.common import IDListPayload
from app.schemas.role import RoleCreate, RoleUpdate
from app.services.audit_service import record_operation_log
from app.services.rbac_service import serialize_role

router = APIRouter()


@router.get("")
def list_roles(
    _: User = Depends(require_permission("system:role:list")),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count()).select_from(Role)) or 0
    roles = db.scalars(select(Role).options(selectinload(Role.menus)).order_by(Role.id.desc())).all()
    return success_response({"items": [serialize_role(role) for role in roles], "total": total})


@router.get("/{role_id}")
def get_role(
    role_id: int,
    _: User = Depends(require_permission("system:role:list")),
    db: Session = Depends(get_db),
):
    role = db.scalar(select(Role).options(selectinload(Role.menus)).where(Role.id == role_id))
    if role is None:
        raise NotFoundException(message="角色不存在")
    return success_response(serialize_role(role))


@router.post("")
def create_role(
    payload: RoleCreate,
    request: Request,
    current_user: User = Depends(require_permission("system:role:list")),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(Role).where(Role.code == payload.code))
    if existing:
        raise ConflictException(message="角色编码已存在")
    role = Role(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        is_system=payload.is_system,
    )
    if payload.menu_ids:
        role.menus = list(db.scalars(select(Menu).where(Menu.id.in_(payload.menu_ids))).all())
    db.add(role)
    db.commit()
    db.refresh(role)
    record_operation_log(
        module="role",
        action="create",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="role",
        biz_id=str(role.id),
        message=f"创建角色 {role.code}",
    )
    return success_response(serialize_role(role), status_code=201)


@router.put("/{role_id}")
def update_role(
    role_id: int,
    payload: RoleUpdate,
    request: Request,
    current_user: User = Depends(require_permission("system:role:list")),
    db: Session = Depends(get_db),
):
    role = db.scalar(select(Role).options(selectinload(Role.menus)).where(Role.id == role_id))
    if role is None:
        raise NotFoundException(message="角色不存在")
    update_data = payload.model_dump(exclude_unset=True)
    menu_ids = update_data.pop("menu_ids", None)
    for field, value in update_data.items():
        setattr(role, field, value)
    if menu_ids is not None:
        role.menus = list(db.scalars(select(Menu).where(Menu.id.in_(menu_ids))).all())
    db.add(role)
    db.commit()
    db.refresh(role)
    record_operation_log(
        module="role",
        action="update",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="role",
        biz_id=str(role.id),
        message=f"更新角色 {role.code}",
    )
    return success_response(serialize_role(role))


@router.put("/{role_id}/menus")
def assign_role_menus(
    role_id: int,
    payload: IDListPayload,
    request: Request,
    current_user: User = Depends(require_permission("system:role:list")),
    db: Session = Depends(get_db),
):
    role = db.scalar(select(Role).options(selectinload(Role.menus)).where(Role.id == role_id))
    if role is None:
        raise NotFoundException(message="角色不存在")
    role.menus = list(db.scalars(select(Menu).where(Menu.id.in_(payload.ids))).all())
    db.add(role)
    db.commit()
    db.refresh(role)
    record_operation_log(
        module="role",
        action="assign_menus",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="role",
        biz_id=str(role.id),
        message=f"更新角色 {role.code} 的菜单权限",
    )
    return success_response(serialize_role(role))
