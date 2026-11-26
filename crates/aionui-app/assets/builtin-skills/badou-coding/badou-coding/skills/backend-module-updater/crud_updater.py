#!/usr/bin/env python3
"""Generate safe incremental SQL for an MD module definition.

D27：显式导入 resolve_db_config 共享 resolver，为后续 --execute 路径铺路。
当前 --update 仍仅写 SQL 文件，不连接 DB；保留 import 避免未来重复实现。
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# D27: project_root 兼容：当作为库调用时由调用方计算并传入
_HERE = os.path.dirname(os.path.abspath(__file__))
_BADOU_CODING_COMMON = os.path.normpath(os.path.join(_HERE, "..", "..", "common"))
if _BADOU_CODING_COMMON not in sys.path:
    sys.path.insert(0, _BADOU_CODING_COMMON)

try:
    from db_config_resolver import resolve_db_config, ConfigNotFoundError  # noqa: F401
    _RESOLVER_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RESOLVER_AVAILABLE = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="backend-module-updater")
    parser.add_argument("--def", dest="def_path", required=True)
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--module-code", required=True)
    parser.add_argument("--mode", default="update", choices=["update", "rebuild"])
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--output", "-o", default="output")
    parser.add_argument("--snapshot", help="JSON snapshot of the previous definition")
    parser.add_argument("--confirm-delete", action="store_true")
    parser.add_argument("--line-count", action="store_true", help="仅校验时输出 SQL 行数")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--version", action="version", version="backend-module-updater 1.0.0")
    return parser.parse_args()


def load_module_def(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"ERROR: 找不到 {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"VALIDATION ERROR: invalid JSON: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("module"), dict):
        raise SystemExit("VALIDATION ERROR: missing 'module' at top level")
    if not value["module"].get("code"):
        raise SystemExit("VALIDATION ERROR: missing ['code']")
    return value


def sql_quote(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    return "'" + str(value).replace("'", "''") + "'"


def field_type(field: dict[str, Any]) -> str:
    dtype = str(field.get("display_type", "varchar")).lower()
    length = field.get("length")
    if length and dtype in {"varchar", "char", "decimal"}:
        return f"{dtype}({length})"
    return dtype


def field_sql(field: dict[str, Any]) -> str:
    nullable = "NULL" if field.get("nullable", True) else "NOT NULL"
    comment = f" COMMENT {sql_quote(field['comment'])}" if field.get("comment") else ""
    return f"{field_type(field)} {nullable}{comment}"


def diff_defs(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    old_fields = {x.get("field_name"): x for x in old.get("fields", [])}
    new_fields = {x.get("field_name"): x for x in new.get("fields", [])}
    return {"added": [new_fields[k] for k in new_fields.keys() - old_fields.keys()],
            "removed": [old_fields[k] for k in old_fields.keys() - new_fields.keys()],
            "modified": [(old_fields[k], new_fields[k]) for k in old_fields.keys() & new_fields.keys()
                          if old_fields[k] != new_fields[k]],
            "module": old.get("module", {}) != new.get("module", {}),
            "flow": old.get("module", {}).get("flow_code") != new.get("module", {}).get("flow_code"),
            "dictionaries": old.get("dictionaries", []) != new.get("dictionaries", []),
            "buttons": old.get("buttons", []) != new.get("buttons", []),
            "form": old.get("form", {}) != new.get("form", {}),
            "relations": old.get("relations", []) != new.get("relations", [])}


def _uuid_sql() -> str:
    """MySQL 内置 32 位 UUID 生成（去掉连字符）"""
    return "SUBSTR(REPLACE(UUID(), '-', ''), 1, 32)"


def _module_id_subquery(code: str) -> str:
    """通过 module.code 查 module_id（UUID）的子查询"""
    return (
        f"(SELECT id FROM md_module WHERE code={sql_quote(code)} "
        f"AND flg_deleted=0 LIMIT 1)"
    )


def _entity_name(field: dict[str, Any]) -> str:
    """从 field_name 推 camelCase（与 generator 保持一致）"""
    name = field.get("field_name", "")
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _infer_form(field: dict[str, Any]) -> dict[str, Any]:
    """复刻 generator 的 infer_form_from_metadata 逻辑（field.py:92-125）

    让 updater 输出的 md_form 与 generator 等价，不依赖 JSON 里手动写 form 配置。
    """
    form = dict(field.get("form") or {})  # 复制避免突变

    # dict 绑定字段：edit_type=select + dic_name + data_source=1 + 搜索框
    if field.get("dict"):
        if not form.get("edit_type"):
            form["edit_type"] = "select"
            form["data_source"] = 1
            form["dic_name"] = field["dict"]
        if form.get("searchable") and not form.get("search_box"):
            form["search_box"] = {
                "id": _entity_name(field) or field.get("field_name", ""),
                "name": field.get("comment") or field.get("field_name", ""),
                "defaultText": "全部",
                "queryType": "other-query",
                "selectType": 0,
            }
            form["search_data_source"] = 1
            form["search_data"] = field["dict"]

    # display_type 默认 edit_type
    dt = field.get("display_type", "varchar")
    if dt == "date" and not form.get("edit_type"):
        form["edit_type"] = "date"
    elif dt == "text" and not form.get("edit_type"):
        form["edit_type"] = "textarea"
    elif dt == "decimal":
        if not form.get("edit_type"):
            form["edit_type"] = "number"
        if not form.get("regex_rule"):
            form["regex_rule"] = "decimal"
        elif "decimal" not in form["regex_rule"]:
            form["regex_rule"] = f"{form['regex_rule']},decimal"
    elif dt == "datetime" and not form.get("edit_type"):
        form["edit_type"] = "datetime"

    # NOT NULL → 强制 required
    if not field.get("nullable", True):
        if field.get("field_name") not in {"id", "create_time", "update_time", "flg_deleted"}:
            if not form.get("regex_rule"):
                form["regex_rule"] = "required"
            elif "required" not in form["regex_rule"]:
                form["regex_rule"] = f"required,{form['regex_rule']}"

    return form


def _field_md_field_insert(field: dict[str, Any], module_code: str) -> str:
    """生成单条 md_field INSERT/UPSERT（修复 B1 + B2）

    关键修正：md_field 是 UUID 主键 + UUID 外键到 md_module，
    不能用 module_code 列（旧代码错误地引用了不存在的列）。
    """
    field_name = field.get("field_name", "")
    entity_name = _entity_name(field)
    display_type = field.get("display_type", "varchar")
    length = field.get("length")
    comment = field.get("comment", "")
    nullable = 1 if field.get("nullable", True) else 0
    is_db_field = 1 if field.get("is_db_field", True) else 0
    default_value = field.get("default_value")
    # 用 _infer_form 派生 regex_rule（与 generator 等价）
    inferred = _infer_form(field)
    regex_rule = field.get("regex_rule") or inferred.get("regex_rule")

    cols = ["ID", "module_id", "field_name", "entity_name", "comments",
            "display_type", "primary_key", "is_unique", "nullable",
            "show_in_entity", "is_db_field", "priority", "flg_deleted"]
    vals = [
        _uuid_sql(),
        _module_id_subquery(module_code),
        sql_quote(field_name),
        sql_quote(entity_name),
        sql_quote(comment),
        sql_quote(display_type),
        "0",  # primary_key
        "0",  # is_unique
        str(nullable),
        "1",  # show_in_entity
        str(is_db_field),
        str(field.get("priority") or 1),
        "0",  # flg_deleted
    ]

    if length is not None:
        cols.append("length")
        vals.append(str(length))
    if default_value is not None:
        cols.append("default_value")
        vals.append(sql_quote(default_value))
    if regex_rule:
        cols.append("validation_rule")
        vals.append(sql_quote(regex_rule))

    # 用 field_name + module_id 作为唯一性参考（MySQL 没有复合唯一约束，
    # 但 ON DUPLICATE KEY 必须基于唯一索引；这里依靠 PRI KEY 触发更新行为，
    # 真实场景下需要 DBA 维护一个 (module_id, field_name) 的唯一索引）。
    # 简化处理：先尝试 INSERT；冲突时改为 UPDATE。
    insert_sql = (
        f"INSERT INTO md_field ({', '.join(cols)})\n"
        f"VALUES ({', '.join(vals)});"
    )
    update_parts = []
    if length is not None:
        update_parts.append("length=VALUES(length)")
    if default_value is not None:
        update_parts.append("default_value=VALUES(default_value)")
    if regex_rule:
        update_parts.append("validation_rule=VALUES(validation_rule)")
    update_parts.extend([
        "display_type=VALUES(display_type)",
        "comments=VALUES(comments)",
    ])
    upsert_sql = insert_sql[:-1] + (
        f"\nON DUPLICATE KEY UPDATE {', '.join(update_parts)};"
    )
    return f"-- {field_name}\n{upsert_sql}"


def _form_md_form_inserts(fields: list[dict[str, Any]], module_code: str) -> list[str]:
    """生成 md_form 全量 INSERT。

    DELETE + INSERT 全量策略（与 form-config-change.md §1 一致）。
    每个字段输出一行 md_form，使用新 UUID。
    """
    import json as _json

    lines = []
    for f in fields:
        form = _infer_form(f)
        field_name = f.get("field_name", "")
        entity_name = _entity_name(f)
        comment = f.get("comment", "")

        cols = ["ID", "mod_id", "field_id", "display_name", "entity_name",
                "is_show_in_grid", "search_able", "is_show_in_page", "is_edit",
                "priority"]
        vals = [
            _uuid_sql(),
            _module_id_subquery(module_code),
            f"(SELECT ID FROM md_field WHERE module_id={_module_id_subquery(module_code)} "
            f"AND field_name={sql_quote(field_name)} AND flg_deleted=0 LIMIT 1)",
            sql_quote(comment),
            sql_quote(entity_name),
            "1" if form.get("show_in_grid", True) else "0",
            "1" if form.get("searchable", False) else "0",
            "1" if form.get("show_in_page", True) else "0",
            "1" if form.get("editable", True) else "0",
            str(f.get("priority") or 1),
        ]

        if form.get("show_in_grid"):
            cols.extend(["show_type", "LIST_WIDTH", "SORTABLE"])
            vals.extend([
                sql_quote(form.get("show_type", "text")),
                sql_quote(form.get("list_width", "120px")),
                "1" if form.get("sortable", True) else "0",
            ])

        # 搜索框（仅 dict + searchable 时输出，与 generator 一致）
        if form.get("searchable") and form.get("search_box"):
            sb = dict(form["search_box"])
            if not sb.get("id"):
                sb["id"] = entity_name or field_name
            if not sb.get("name"):
                sb["name"] = comment or field_name
            search_box_json = _json.dumps(
                {k: v for k, v in sb.items() if v is not None and v != ""},
                ensure_ascii=False, separators=(",", ":"),
            ).replace("'", "\\'")
            cols.append("search_box")
            vals.append(f"'{search_box_json}'")
            if form.get("search_data_source") is not None:
                cols.append("search_data_source")
                vals.append(str(form["search_data_source"]))
            if form.get("search_data"):
                cols.append("search_data")
                vals.append(sql_quote(form["search_data"]))

        is_edit_val = 1 if form.get("edit_type") == "hidden" else (1 if form.get("editable", True) else 0)
        if form.get("edit_type") and (is_edit_val == 1 or form.get("edit_type") == "hidden"):
            cols.append("edit_type")
            vals.append(sql_quote(form["edit_type"]))

        if form.get("dic_name"):
            cols.append("dic_name")
            vals.append(sql_quote(form["dic_name"]))
        if form.get("data_source") is not None:
            cols.append("data_source")
            vals.append(str(form["data_source"]))
        if form.get("regex_rule"):
            cols.append("regex_rule")
            vals.append(sql_quote(form["regex_rule"]))
        if form.get("default_value") is not None:
            cols.append("default_value")
            vals.append(sql_quote(form["default_value"]))

        lines.append(
            f"-- {field_name} form\n"
            f"INSERT INTO md_form ({', '.join(cols)})\n"
            f"VALUES ({', '.join(vals)});"
        )
    return lines


def _button_md_button_inserts(buttons: list[str], module_code: str) -> list[str]:
    """生成 md_button 全量 INSERT。

    标准 CRUD 按钮定义与 button_gen.py 保持一致。
    """
    standard = [
        {"code": "add", "name": "新增", "icon": "add", "type": "primary", "priority": 5, "right_menu": 0},
        {"code": "edit", "name": "修改", "icon": "edit", "type": "warning", "priority": 10, "right_menu": 1},
        {"code": "view", "name": "查看", "icon": "view", "type": "primary", "priority": 15, "right_menu": 1},
        {"code": "import", "name": "导入", "icon": "import", "type": "primary", "priority": 20, "right_menu": 0},
        {"code": "export", "name": "导出", "icon": "export", "type": "primary", "priority": 25, "right_menu": 0},
        {"code": "delete", "name": "删除", "icon": "delete", "type": "danger", "priority": 30, "right_menu": 1},
    ]
    requested = set(buttons) if buttons else {b["code"] for b in standard}
    lines = []
    for btn in standard:
        if btn["code"] not in requested:
            continue
        lines.append(
            f"-- 按钮 {btn['name']}\n"
            f"INSERT INTO md_button (\n"
            f"    id, module_id, code, name, function_name, icon,\n"
            f"    iz_show, type, priority, show_with_right_menu,\n"
            f"    belong_form, FLG_DELETED\n"
            f") VALUES (\n"
            f"    {_uuid_sql()}, {_module_id_subquery(module_code)},\n"
            f"    {sql_quote(btn['code'])}, {sql_quote(btn['name'])}, '', {sql_quote(btn['icon'])},\n"
            f"    1, {sql_quote(btn['type'])}, {btn['priority']}, {btn['right_menu']},\n"
            f"    'list', 0\n"
            f");"
        )
    return lines


def _comm_dictionary_upserts(dictionaries: list[dict[str, Any]],
                              creator_id: str, creator_name: str) -> list[str]:
    """生成 comm_dictionary + comm_dictionary_item 全量 UPSERT（修复 B4）

    通过 code 子查询定位 dictionary_id，避免使用 MySQL 用户变量
    （与 dictionary_gen.py 的策略一致）。
    先 DELETE 已有 items，再 INSERT，避免重复（解决重复跑 updater 导致 items 翻倍的问题）。
    """
    lines = []
    for d in dictionaries:
        type_name = d.get("type_name") or d.get("code", "")
        name = d.get("name") or type_name
        items = d.get("items") or []

        # 先清掉已有字典项（DELETE+INSERT 全量策略）
        lines.append(
            f"-- 字典项清理: {name} (code={type_name})\n"
            f"DELETE FROM comm_dictionary_item WHERE dictionary_id IN (\n"
            f"    SELECT id FROM comm_dictionary WHERE code={sql_quote(type_name)}\n"
            f");"
        )

        lines.append(
            f"-- 字典 {name} (code={type_name})\n"
            f"INSERT INTO comm_dictionary (\n"
            f"    id, type_id, type_name, code, name, value, value_type, remark,\n"
            f"    priority, create_time, creator, creator_name\n"
            f") VALUES (\n"
            f"    {_uuid_sql()}, 'OTHRE', '业务应用', {sql_quote(type_name)}, "
            f"{sql_quote(name)}, {sql_quote(d.get('value') or name)}, 1, NULL,\n"
            f"    0, NOW(), {sql_quote(creator_id)}, {sql_quote(creator_name)}\n"
            f");\n"
            f"-- 同 code 已存在则跳过（idempotent）"
        )

        if items:
            dict_lookup = (
                f"(SELECT id FROM comm_dictionary WHERE code={sql_quote(type_name)} LIMIT 1)"
            )
            item_vals = []
            for item in items:
                item_vals.append(
                    f"({_uuid_sql()}, {dict_lookup}, "
                    f"{sql_quote(item.get('code', ''))}, "
                    f"{sql_quote(str(item.get('value', '')))}, "
                    f"{sql_quote(item.get('name', ''))}, "
                    f"{int(item.get('priority', 1))}, NOW(), "
                    f"{sql_quote(creator_id)}, {sql_quote(creator_name)}, "
                    f"NULL, {int(item.get('flg_default', 0))})"
                )
            lines.append(
                f"-- 字典项 {name}\n"
                f"INSERT INTO comm_dictionary_item (\n"
                f"    id, dictionary_id, code, value, name, priority,\n"
                f"    create_time, creator, creator_name, remark, flg_default\n"
                f") VALUES\n"
                + ",\n".join(item_vals)
                + ";"
            )
    return lines


def _relation_md_module_link_insert(rel: dict[str, Any], module_code: str) -> str:
    """生成单条 md_module_link INSERT SQL

    与 generator 的 relation_gen.py 等价，但所有 UUID 改用子查询
    （避免硬编码 UUID，二次幂等时不会因 v1 的预生成 UUID 漂移而失败）。

    子查询策略：
    - module_id: 当前 module.code → md_module.id
    - related_module_id: relations[].related_module → md_module.id
    - related_table: 同步从 md_module.db_table 查
    - field_id / related_field: 从 md_field 通过 (module_id, field_name) 查
    """
    rel_type = int(rel.get("type", 0))
    if rel_type not in (1, 2):
        raise ValueError(f"unsupported relation type: {rel_type}")
    related_module = rel.get("related_module") or ""
    related_field_name = rel.get("related_field_name") or ""
    display_name = rel.get("display_name") or ""
    edit_module = int(rel.get("edit_module", 0))
    is_cascade = int(rel.get("is_cascade", 0))
    show_style = int(rel.get("show_style", 1))
    tab_name = rel.get("tab_name")
    priority = rel.get("priority", 1)
    is_edit = int(rel.get("is_edit", 1))

    # 自动推导（与 RelationDef.SHOW_TYPE/SHOW_TAB 一致）
    show_type = 0 if rel_type == 1 else 1
    show_tab = 1 if show_style in (1, 2) else 0

    # field_name / field_id 处理（与 generator 一致）
    # type=1（一对一）：field_name=用户提供的 FK 字段；field_id=该字段
    # type=2（一对多）：field_name='id'；field_id=当前模块主键
    if rel_type == 1:
        field_name_val = rel.get("field_name") or ""
        field_id_subq = (
            f"(SELECT ID FROM md_field WHERE module_id={_module_id_subquery(module_code)} "
            f"AND field_name={sql_quote(field_name_val)} AND flg_deleted=0)"
        )
    else:
        field_name_val = "id"
        field_id_subq = (
            f"(SELECT ID FROM md_field WHERE module_id={_module_id_subquery(module_code)} "
            f"AND field_name='id' AND flg_deleted=0)"
        )

    related_module_ref = (
        f"(SELECT id FROM md_module WHERE code={sql_quote(related_module)} "
        f"AND flg_deleted=0)"
    )
    related_table_ref = (
        f"(SELECT db_table FROM md_module WHERE code={sql_quote(related_module)} "
        f"AND flg_deleted=0)"
    )
    # type=1：related_field 指向关联模块的 'id'；type=2：指向 related_field_name
    if rel_type == 1:
        related_field_ref = (
            f"(SELECT ID FROM md_field WHERE module_id={related_module_ref} "
            f"AND field_name='id' AND flg_deleted=0)"
        )
    else:
        related_field_ref = (
            f"(SELECT ID FROM md_field WHERE module_id={related_module_ref} "
            f"AND field_name={sql_quote(related_field_name)} AND flg_deleted=0)"
        )

    tab_name_val = sql_quote(tab_name) if tab_name else "NULL"

    return (
        f"-- relation {display_name}（{'一对一' if rel_type == 1 else '一对多'}）\n"
        f"INSERT INTO md_module_link (id, module_id, related_module_id, field_name, field_id,\n"
        f"    related_table, related_field, related_field_name, type, is_edit, display_name,\n"
        f"    edit_module, is_cascade, priority, SHOW_TAB, SHOW_TYPE, show_style, tab_name)\n"
        f"VALUES (\n"
        f"    {_uuid_sql()},\n"
        f"    {_module_id_subquery(module_code)},\n"
        f"    {related_module_ref},\n"
        f"    {sql_quote(field_name_val)},\n"
        f"    {field_id_subq},\n"
        f"    {related_table_ref},\n"
        f"    {related_field_ref},\n"
        f"    {sql_quote(related_field_name)},\n"
        f"    {rel_type}, {is_edit}, {sql_quote(display_name)},\n"
        f"    {edit_module}, {is_cascade}, {priority},\n"
        f"    {show_tab}, {show_type}, {show_style},\n"
        f"    {tab_name_val}\n"
        f");"
    )


def _relation_md_module_link_inserts(relations: list[dict[str, Any]], module_code: str) -> list[str]:
    """逐条生成 md_module_link INSERT。子查询策略保证二次幂等可重跑。"""
    lines = []
    for rel in relations:
        lines.append(_relation_md_module_link_insert(rel, module_code))
        lines.append("")
    return lines


def generate_sql(old: dict[str, Any], new: dict[str, Any], confirm_delete: bool,
                 creator_id: str = "system", creator_name: str = "system") -> tuple[str, str, list[str]]:
    module = new["module"]
    code = module["code"]
    table = module.get("db_table", f"t_{code}")
    changes = diff_defs(old, new)
    lines = [f"-- Incremental update for {code}"]
    cleanup: list[str] = []

    for field in changes["added"]:
        lines.append(f"ALTER TABLE `{table}` ADD COLUMN `{field['field_name']}` {field_sql(field)};")
    for before, after in changes["modified"]:
        old_type, new_type = str(before.get("display_type", "varchar")), str(after.get("display_type", "varchar"))
        if before.get("length") and after.get("length") and after["length"] < before["length"]:
            raise ValueError(f"拒绝执行: 字段 {after['field_name']} length 缩小，请先手动备份")
        if (old_type, new_type) in {("varchar", "int"), ("varchar", "datetime"), ("int", "datetime")}:
            raise ValueError(f"拒绝执行: 字段 {after['field_name']} display_type 不兼容")
        lines.append(f"ALTER TABLE `{table}` MODIFY COLUMN `{after['field_name']}` {field_sql(after)};")
    if changes["removed"] and not confirm_delete:
        names = ", ".join(x["field_name"] for x in changes["removed"])
        raise ValueError(f"字段删除需 --confirm-delete: {names} (将扫描 md_form/md_button 引用)")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for field in changes["removed"]:
        backup = f"{table}__bak_{timestamp}.sql"
        cleanup.append(f"-- backup before dropping {field['field_name']}\nCREATE TABLE `{table}__bak_{timestamp}` LIKE `{table}`;\nINSERT INTO `{table}__bak_{timestamp}` SELECT * FROM `{table}`;")
        lines.append(f"ALTER TABLE `{table}` DROP COLUMN `{field['field_name']}`;")
        # 修复 B2：用 module_id 子查询代替不存在的 module_code 列
        lines.append(
            f"DELETE FROM md_form WHERE field_id IN (\n"
            f"    SELECT ID FROM md_field WHERE module_id={_module_id_subquery(code)} "
            f"AND field_name={sql_quote(field['field_name'])}\n"
            f");"
        )
        lines.append(
            f"DELETE FROM md_field WHERE module_id={_module_id_subquery(code)} "
            f"AND field_name={sql_quote(field['field_name'])};"
        )

    # md_module 元数据更新（实际列名是 name，不是 name_cn）
    lines.append(
        f"UPDATE md_module SET name={sql_quote(module.get('name_cn'))}, "
        f"remark={sql_quote(module.get('description'))}, "
        f"base_class={sql_quote(module.get('base_class'))} "
        f"WHERE code={sql_quote(code)};"
    )

    # md_field 全量 DELETE+INSERT（修复 B1：完整列集 + UUID module_id）
    # ID 是新生成的 UUID，ON DUPLICATE KEY 永不触发。改为：对 v2 列出的每个
    # field_name 先 DELETE 旧行，然后 INSERT 新行；这样 display_type / length
    # 等变更会随之刷新；系统字段(primary_key=1)不动。
    user_field_names = ", ".join(sql_quote(f["field_name"]) for f in new.get("fields", [])) or "''"
    # 1. 删 v2 中字段的旧 md_form/md_field（保留系统字段 primary_key=1）
    lines.append(
        f"DELETE FROM md_form WHERE mod_id={_module_id_subquery(code)} AND field_id IN (\n"
        f"    SELECT ID FROM md_field WHERE module_id={_module_id_subquery(code)} AND primary_key=0 AND field_name IN ({user_field_names})\n"
        f");"
    )
    lines.append(
        f"DELETE FROM md_field WHERE module_id={_module_id_subquery(code)} AND primary_key=0 AND field_name IN ({user_field_names});"
    )
    # 2. 删 v2 中删除的字段（removed）—— 已在前面处理（--confirm-delete 路径）
    # 3. INSERT 新的 v2 字段
    for field in new.get("fields", []):
        lines.append(_field_md_field_insert(field, code))

    # md_form DELETE + INSERT 全量
    if changes["form"] or changes["added"] or changes["modified"]:
        lines.append(
            f"-- md_form 全量重写（{len(new.get('fields', []))} 行）\n"
            f"DELETE FROM md_form WHERE mod_id={_module_id_subquery(code)};"
        )
        lines.extend(_form_md_form_inserts(new.get("fields", []), code))

    # md_button DELETE + INSERT 全量
    if changes["buttons"] or changes["added"]:
        lines.append(
            f"-- md_button 全量重写\n"
            f"DELETE FROM md_button WHERE module_id={_module_id_subquery(code)};"
        )
        lines.extend(_button_md_button_inserts(new.get("buttons", []), code))

    # md_module_link 全量重写（DELETE 旧行 + INSERT 新行）
    if changes["relations"]:
        lines.append(
            f"-- md_module_link 全量重写（{len(new.get('relations', []))} 条关联）\n"
            f"DELETE FROM md_module_link WHERE module_id={_module_id_subquery(code)};"
        )
        lines.extend(_relation_md_module_link_inserts(new.get("relations", []), code))

    # comm_dictionary + comm_dictionary_item UPSERT（修复 B4）
    if changes["dictionaries"]:
        lines.extend(_comm_dictionary_upserts(new.get("dictionaries", []), creator_id, creator_name))

    if changes["flow"]:
        lines.append(f"-- flow_code changed to {module.get('flow_code') or 'NULL'}")

    return "\n".join(lines) + "\n", "\n".join(cleanup) + "\n", cleanup


def main() -> None:
    args = parse_args()
    if not args.update:
        raise SystemExit("ERROR: 必须指定 --update flag 才能使用 updater 技能")
    new = load_module_def(Path(args.def_path))
    if args.validate:
        print("VALIDATION PASSED")
        if args.line_count:
            for line in new.get("fields", []):
                print(f"field {line.get('field_name')} {line.get('display_type')}({line.get('length')})")
        return
    if new["module"]["code"] != args.module_code:
        raise SystemExit("ERROR: module.code 与 --module-code 不一致")
    output = Path(args.output) / args.module_code
    output.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(Path(args.def_path).read_bytes()).hexdigest()
    hash_path = output / ".hash"
    if hash_path.exists() and hash_path.read_text().strip() == digest:
        print("0 改动")
        return
    old = json.loads(Path(args.snapshot).read_text()) if args.snapshot else {"module": {"code": args.module_code}, "fields": []}
    if old.get("module", {}).get("code") not in (None, args.module_code):
        if args.mode != "rebuild":
            raise SystemExit("ERROR: module.code rename rejected; use --mode=rebuild")
        sql = f"-- WARNING: rebuild loses business data\nDROP TABLE `{old['module'].get('db_table')}`;\n-- CREATE generated module here\n"
        (output / "update.sql").write_text(sql)
        hash_path.write_text(digest)
        print("WARNING: rebuild will lose business data")
        return
    try:
        system = new.get("system", {})
        creator_id = system.get("creator_id", "system")
        creator_name = system.get("creator_name", "system")
        sql, cleanup, _ = generate_sql(
            old, new, args.confirm_delete,
            creator_id=creator_id, creator_name=creator_name,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    (output / "update.sql").write_text(sql, encoding="utf-8")
    (output / "update_cleanup.sql").write_text(cleanup, encoding="utf-8")
    hash_path.write_text(digest, encoding="utf-8")
    print(f"generated {output / 'update.sql'} ({len(sql.splitlines())} lines)")


if __name__ == "__main__":
    main()
