"""CRUD SQL Generators - Step 2: md_field"""

from __future__ import annotations
from common.generator_shared.models import ModuleDefinition, FieldDef


def _field_sql(f: FieldDef, priority: int, module_id: str, field_id: str) -> str:
    """生成单个字段的 INSERT SQL"""
    nullable_val = 1 if f.nullable else 0
    unique_val = 1 if f.unique else 0
    pk_val = 1 if f.primary_key else 0

    # Determine column list and values
    cols = [
        "ID", "module_id", "field_name", "entity_name", "comments",
        "display_type", "primary_key", "is_unique", "nullable",
        "show_in_entity", "is_db_field", "priority", "flg_deleted",
    ]
    vals = [
        f"'{field_id}'",
        f"'{module_id}'",
        f"'{f.field_name}'",
        f"'{f.entity_name}'",
        f"'{f.comment}'",
        f"'{f.display_type}'",
        str(pk_val),
        str(unique_val),
        str(nullable_val),
        "1",
        "1" if f.is_db_field else "0",
        str(priority),
        "0",
    ]

    # Optional fields
    if f.length is not None:
        cols.append("length")
        vals.append(str(f.length))
    if f.default_value is not None:
        cols.append("default_value")
        vals.append(f"'{f.default_value}'")
    if f.form and f.form.regex_rule:
        cols.append("validation_rule")
        vals.append(f"'{f.form.regex_rule}'")

    return (
        f"-- {f.comment} ({f.field_name})\n"
        f"INSERT INTO md_field ({', '.join(cols)})\n"
        f"VALUES ({', '.join(vals)});"
    )


def generate_create(defn: ModuleDefinition) -> str:
    module_id = defn.reserved_ids['module_id']
    lines = ["-- ========== 步骤2: 创建字段 =========="]
    for i, f in enumerate(defn.fields, start=1):
        field_id = defn.reserved_ids['field_ids'][f.field_name]
        lines.append(_field_sql(f, f.priority or i, module_id, field_id))
        lines.append("")
    return "\n".join(lines)


def generate_cleanup(defn: ModuleDefinition) -> str:
    code = defn.module.code
    return f"-- ========== 清理: 删除字段 ==========\nDELETE FROM md_field WHERE module_id IN (SELECT id FROM md_module WHERE code = '{code}');"
