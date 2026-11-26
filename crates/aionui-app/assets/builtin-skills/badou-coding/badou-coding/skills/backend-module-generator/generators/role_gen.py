"""CRUD SQL Generators - Step 9: sys_role_resource (授权)


实际表结构 (sys_role_resource):
  id, resource_id, role_id, creator, creator_name, create_date

注意:
  - 时间列是 create_date 不是 create_time
  - 超级管理员角色ID固定为 ROOT，直接使用即可，无需查询 sys_role 表
"""
from __future__ import annotations
from common.generator_shared.models import ModuleDefinition, _to_pascal_case
from generators.resource_gen import STANDARD_BUTTON_RESOURCES


def generate_create(defn: ModuleDefinition) -> str:
    import uuid
    m = defn.module
    role = defn.role
    role_code = role.role_code or "ROOT"
    menu_resource_id = defn.reserved_ids['menu_resource_id']

    lines = [
        "-- ========== 步骤9: 给超级管理员授权 ==========",
        f"-- 超级管理员角色ID固定为 ROOT（直接使用，不查询sys_role表）",
        "",
        "-- 授权菜单资源",
        "INSERT INTO sys_role_resource (id, role_id, resource_id, creator, creator_name, create_date)",
        f"VALUES ('{uuid.uuid4().hex}', '{role_code}', '{menu_resource_id}', '{defn.creator.id}', '{defn.creator.name}', NOW());",
        "",
        "-- 授权按钮资源",
    ]

    requested = set(defn.buttons) if defn.buttons else {"add", "edit", "view", "import", "export", "delete"}
    for btn in STANDARD_BUTTON_RESOURCES:
        if btn["code"] in requested:
            lines.append(f"-- 授权{btn['name']}按钮")
            lines.append(
                f"INSERT INTO sys_role_resource (id, role_id, resource_id, creator, creator_name, create_date)\n"
                f"SELECT '{uuid.uuid4().hex}', '{role_code}', id, '{defn.creator.id}', '{defn.creator.name}', NOW()\n"
                f"FROM sys_resource WHERE parent_id = '{menu_resource_id}' AND code = '{btn['code']}' AND FLG_DELETED = 0;"
            )

    return "\n".join(lines)


def generate_cleanup(defn: ModuleDefinition) -> str:
    menu_code = defn.menu.resource_code or "SYSTEM_" + _to_pascal_case(defn.module.code).upper()
    return (
        "-- ========== 清理: 删除授权 ==========\n"
        "DELETE FROM sys_role_resource WHERE resource_id IN (\n"
        f"    SELECT id FROM sys_resource WHERE code = '{menu_code}' OR parent_id IN (\n"
        f"        SELECT id FROM sys_resource WHERE code = '{menu_code}'\n"
        "    )\n"
        ");"
    )
