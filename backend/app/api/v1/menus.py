from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.core.exceptions import NotFoundException
from app.core.response import success_response
from app.db.models.rbac import Menu, User
from app.schemas.menu import MenuCreate, MenuUpdate
from app.services.audit_service import record_operation_log
from app.services.rbac_service import build_menu_tree, collect_permissions, serialize_menu

router = APIRouter()


@router.get("")
def list_menus(
    current_user: User = Depends(require_permission("system:menu:list")),
    db: Session = Depends(get_db),
):
    menus = db.scalars(select(Menu).order_by(Menu.sort_order.asc(), Menu.id.asc())).all()
    allowed_permissions = None
    if not current_user.is_superuser:
        allowed_permissions = set(collect_permissions(current_user))
    return success_response({"items": build_menu_tree(list(menus), allowed_permissions)})


@router.post("")
def create_menu(
    payload: MenuCreate,
    request: Request,
    current_user: User = Depends(require_permission("system:menu:list")),
    db: Session = Depends(get_db),
):
    menu = Menu(**payload.model_dump())
    db.add(menu)
    db.commit()
    db.refresh(menu)
    record_operation_log(
        module="menu",
        action="create",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="menu",
        biz_id=str(menu.id),
        message=f"创建菜单 {menu.name}",
    )
    return success_response(serialize_menu(menu), status_code=201)


@router.put("/{menu_id}")
def update_menu(
    menu_id: int,
    payload: MenuUpdate,
    request: Request,
    current_user: User = Depends(require_permission("system:menu:list")),
    db: Session = Depends(get_db),
):
    menu = db.get(Menu, menu_id)
    if menu is None:
        raise NotFoundException(message="菜单不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(menu, field, value)
    db.add(menu)
    db.commit()
    db.refresh(menu)
    record_operation_log(
        module="menu",
        action="update",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="menu",
        biz_id=str(menu.id),
        message=f"更新菜单 {menu.name}",
    )
    return success_response(serialize_menu(menu))
