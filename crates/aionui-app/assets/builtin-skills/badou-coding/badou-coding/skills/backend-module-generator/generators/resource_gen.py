"""CRUD SQL Generators - Steps 7+8: sys_resource (菜单资源 + 按钮资源)

实际表结构 (sys_resource):
  id, parent_id, level_id, code, name, url, layer_num, priority,
  secure_type, auth_type, OPEN_TARGET_WINDOW, FLG_DELETED,
  full_path, full_name, big_Icon_Path, small_Icon_Path,
  menu_class, is_account_menu, RESOURCE_TYPE, parent_name,
  function_name, type, custom_options, remark, theme, btn_position

注意: 没有 RESOURCE_CODE, component, redirect, iz_cache, status, hidden,
      description, create_time, creator, creator_name 等列
"""

from __future__ import annotations
from common.generator_shared.models import ModuleDefinition, _to_pascal_case

STANDARD_BUTTON_RESOURCES = [
    {"code": "add",     "name": "新增", "theme": "primary", "btn_position": "top",   "priority_offset": 1},
    {"code": "edit",    "name": "修改", "theme": "warning", "btn_position": "right", "priority_offset": 2},
    {"code": "view",    "name": "查看", "theme": "primary", "btn_position": "right",  "priority_offset": 3},
    {"code": "import",  "name": "导入", "theme": "primary", "btn_position": "top",   "priority_offset": 4},
    {"code": "export",  "name": "导出", "theme": "primary", "btn_position": "top",   "priority_offset": 5},
    {"code": "delete",  "name": "删除", "theme": "danger",  "btn_position": "right", "priority_offset": 6},
]


def _parent_lookup_sql(menu) -> str:
    """生成父级菜单的子查询，嵌套物化避免 MySQL 自引用限制"""
    if menu.parent_id:
        inner = f"SELECT id FROM sys_resource WHERE id = '{menu.parent_id}' LIMIT 1"
    elif menu.parent_code:
        inner = f"SELECT id FROM sys_resource WHERE code = '{menu.parent_code}' AND RESOURCE_TYPE = 0 AND FLG_DELETED = 0 LIMIT 1"
    elif menu.parent_name:
        inner = f"SELECT id FROM sys_resource WHERE name = '{menu.parent_name}' AND RESOURCE_TYPE = 0 AND FLG_DELETED = 0 LIMIT 1"
    else:
        inner = "SELECT id FROM sys_resource WHERE code = 'FRONT-XTGL' AND RESOURCE_TYPE = 0 AND FLG_DELETED = 0 LIMIT 1"
    return f"(SELECT id FROM ({inner}) AS _p)"


def _layer_lookup_sql(menu) -> str:
    """生成 layer_num 的内联子查询，嵌套物化避免 MySQL 自引用限制"""
    where = _parent_where_clause(menu)
    inner = f"SELECT IFNULL(layer_num, 0) + 1 AS _l FROM sys_resource WHERE {where} LIMIT 1"
    return f"(SELECT _l FROM ({inner}) AS _ly)"


def _parent_name_lookup_sql(menu) -> str:
    """生成 parent_name 的内联子查询，嵌套物化避免 MySQL 自引用限制"""
    where = _parent_where_clause(menu)
    inner = f"SELECT name AS _n FROM sys_resource WHERE {where} LIMIT 1"
    return f"(SELECT _n FROM ({inner}) AS _pn)"


def _parent_where_clause(menu) -> str:
    """生成父级菜单的 WHERE 条件"""
    if menu.parent_id:
        return f"id = '{menu.parent_id}'"
    elif menu.parent_code:
        return f"code = '{menu.parent_code}' AND RESOURCE_TYPE = 0 AND FLG_DELETED = 0"
    elif menu.parent_name:
        return f"name = '{menu.parent_name}' AND RESOURCE_TYPE = 0 AND FLG_DELETED = 0"
    else:
        return "code = 'FRONT-XTGL' AND RESOURCE_TYPE = 0 AND FLG_DELETED = 0"


def _menu_resource_sql(defn: ModuleDefinition, menu_resource_id: str) -> str:
    m = defn.module
    menu = defn.menu
    code = menu.resource_code or f"SYSTEM_{_to_pascal_case(m.code).upper()}"
    # 有关联流程时使用 flow 视图 URL，否则使用 stander 视图 URL
    if defn.flow_code:
        url = f"/module/flow/list/{m.code}/placeholder"
    else:
        url = f"/module/stander/list/{m.code}/placeholder"
    full_path = menu.full_path or f"/SYSTEM/{code}"
    full_name = menu.full_name or f"系统管理/{m.name_cn}"

    parent_id_subquery = _parent_lookup_sql(menu)
    layer_subquery = _layer_lookup_sql(menu)
    parent_name_subquery = _parent_name_lookup_sql(menu)

    return f"""\
-- ========== 步骤7: 创建菜单资源 ==========
INSERT INTO sys_resource (
    id, parent_id, level_id, code, name, url, layer_num, priority,
    FLG_DELETED, full_path, full_name, menu_class, is_account_menu,
    RESOURCE_TYPE, parent_name, type
) VALUES (
    '{menu_resource_id}',
    {parent_id_subquery},
    '{menu.level_id}',
    '{code}',
    '{m.name_cn}',
    '{url}',
    {layer_subquery},
    {menu.priority},
    0,
    '{full_path}',
    '{full_name}',
    '',
    0,
    0,
    {parent_name_subquery},
    ''
);"""


def _button_resource_sql(btn: dict, defn: ModuleDefinition, menu_resource_id: str, layer_subquery: str) -> str:
    import uuid
    m = defn.module
    menu = defn.menu
    code = menu.resource_code or f"SYSTEM_{_to_pascal_case(m.code).upper()}"
    btn_level = f"{menu.level_id}.{btn['priority_offset']}"
    full_path = menu.full_path or f"/SYSTEM/{code}"
    full_name = menu.full_name or f"系统管理/{m.name_cn}"
    btn_full_path = f"{full_path}/{btn['code'].upper()}"
    btn_full_name = f"{full_name}/{btn['name']}"

    return f"""\
-- {btn['name']}按钮资源
INSERT INTO sys_resource (
    id, parent_id, level_id, code, name, url, layer_num, priority,
    FLG_DELETED, full_path, full_name, menu_class, is_account_menu,
    RESOURCE_TYPE, parent_name, function_name, type, btn_position, theme
) VALUES (
    '{uuid.uuid4().hex}',
    '{menu_resource_id}',
    '{btn_level}',
    '{btn['code']}',
    '{btn['name']}',
    '',
    {layer_subquery},
    {btn['priority_offset']},
    0,
    '{btn_full_path}',
    '{btn_full_name}',
    '',
    0,
    1,
    '{m.name_cn}',
    '',
    'button',
    '{btn['btn_position']}',
    '{btn['theme']}'
);"""


def generate_create(defn: ModuleDefinition) -> str:
    menu_resource_id = defn.reserved_ids['menu_resource_id']
    layer_subquery = _layer_lookup_sql(defn.menu)

    lines = []
    lines.append(_menu_resource_sql(defn, menu_resource_id))
    lines.append("")

    # Button resources
    lines.append("-- ========== 步骤8: 创建按钮资源 ==========")
    requested = set(defn.buttons) if defn.buttons else {"add", "edit", "view", "import", "export", "delete"}
    for btn in STANDARD_BUTTON_RESOURCES:
        if btn["code"] in requested:
            lines.append(_button_resource_sql(btn, defn, menu_resource_id, layer_subquery))
            lines.append("")

    return "\n".join(lines)


def generate_cleanup(defn: ModuleDefinition) -> str:
    menu_code = defn.menu.resource_code or "SYSTEM_" + _to_pascal_case(defn.module.code).upper()
    return (
        "-- ========== 清理: 删除资源 ==========\n"
        "-- 先删按钮资源（子级）\n"
        f"DELETE FROM sys_resource WHERE parent_id IN (\n"
        f"    SELECT id FROM (\n"
        f"        SELECT id FROM sys_resource WHERE code = '{menu_code}' AND RESOURCE_TYPE = 0 AND FLG_DELETED = 0\n"
        f"    ) AS _sys_tmp\n"
        f") AND RESOURCE_TYPE = 1;\n"
        "\n"
        "-- 再删菜单资源（父级）\n"
        f"DELETE FROM sys_resource WHERE code = '{menu_code}' AND RESOURCE_TYPE = 0;"
    )
