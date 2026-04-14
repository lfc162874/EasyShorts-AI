from app.db.models.rbac import Menu, Role, User


def collect_permissions(user: User) -> list[str]:
    permissions: set[str] = set()
    for role in user.roles:
        for menu in role.menus:
            if menu.permission_code:
                permissions.add(menu.permission_code)
    return sorted(permissions)


def serialize_role(role: Role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "is_system": role.is_system,
        "menu_ids": [menu.id for menu in role.menus],
    }


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "nickname": user.nickname,
        "status": user.status,
        "is_superuser": user.is_superuser,
        "roles": [serialize_role(role) for role in user.roles],
        "permissions": collect_permissions(user),
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def serialize_menu(menu: Menu) -> dict:
    return {
        "id": menu.id,
        "parent_id": menu.parent_id,
        "name": menu.name,
        "title": menu.title,
        "path": menu.path,
        "component": menu.component,
        "icon": menu.icon,
        "permission_code": menu.permission_code,
        "menu_type": menu.menu_type,
        "sort_order": menu.sort_order,
        "hidden": menu.hidden,
        "created_at": menu.created_at,
        "updated_at": menu.updated_at,
    }


def build_menu_tree(
    menus: list[Menu],
    allowed_permissions: set[str] | None = None,
) -> list[dict]:
    grouped: dict[int | None, list[Menu]] = {}
    for menu in sorted(menus, key=lambda item: (item.sort_order, item.id)):
        grouped.setdefault(menu.parent_id, []).append(menu)

    def build(parent_id: int | None) -> list[dict]:
        result: list[dict] = []
        for menu in grouped.get(parent_id, []):
            item = serialize_menu(menu)
            item["children"] = build(menu.id)
            if allowed_permissions is None:
                result.append(item)
                continue

            if menu.permission_code is None or menu.permission_code in allowed_permissions or item["children"]:
                result.append(item)
        return result

    return build(None)
