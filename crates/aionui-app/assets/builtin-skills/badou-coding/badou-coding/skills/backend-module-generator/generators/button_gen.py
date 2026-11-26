"""CRUD SQL Generators - Step 4: md_button"""

from __future__ import annotations
from common.generator_shared.models import ModuleDefinition

# Standard CRUD 6 buttons
STANDARD_BUTTONS = [
    {"code": "add",     "name": "新增", "icon": "add",     "type": "primary", "priority": 5,  "right_menu": 0},
    {"code": "edit",    "name": "修改", "icon": "edit",    "type": "warning", "priority": 10, "right_menu": 1},
    {"code": "view",    "name": "查看", "icon": "view",    "type": "primary", "priority": 15, "right_menu": 1},
    {"code": "import",  "name": "导入", "icon": "import",  "type": "primary", "priority": 20, "right_menu": 0},
    {"code": "export",  "name": "导出", "icon": "export",  "type": "primary", "priority": 25, "right_menu": 0},
    {"code": "delete",  "name": "删除", "icon": "delete",  "type": "danger",  "priority": 30, "right_menu": 1},
]


def _button_sql(btn: dict, module_id: str) -> str:
    import uuid
    return f"""\
INSERT INTO md_button (
    id, module_id, code, name, function_name, icon,
    iz_show, type, priority, show_with_right_menu,
    belong_form, FLG_DELETED
) VALUES (
    '{uuid.uuid4().hex}', '{module_id}',
    '{btn['code']}', '{btn['name']}', '', '{btn['icon']}',
    1, '{btn['type']}', {btn['priority']}, {btn['right_menu']},
    'list', 0
);"""


def generate_create(defn: ModuleDefinition) -> str:
    module_id = defn.reserved_ids['module_id']
    lines = ["-- ========== 步骤4: 配置按钮 =========="]
    requested = set(defn.buttons) if defn.buttons else {"add", "edit", "view", "import", "export", "delete"}
    for btn in STANDARD_BUTTONS:
        if btn["code"] in requested:
            lines.append(f"-- {btn['name']}按钮（{'行操作' if btn['right_menu'] else '工具栏'}）")
            lines.append(_button_sql(btn, module_id))
            lines.append("")
    return "\n".join(lines)


def generate_cleanup(defn: ModuleDefinition) -> str:
    code = defn.module.code
    return f"-- ========== 清理: 删除按钮 ==========\nDELETE FROM md_button WHERE module_id IN (SELECT id FROM md_module WHERE code = '{code}');"
