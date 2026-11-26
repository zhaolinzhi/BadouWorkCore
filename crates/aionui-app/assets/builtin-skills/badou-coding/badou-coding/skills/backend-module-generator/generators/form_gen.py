"""CRUD SQL Generators - Step 3: md_form"""

from __future__ import annotations
import json
from common.generator_shared.models import ModuleDefinition, FieldDef, FormConfig, SearchBox


def _form_sql(f: FieldDef, module_id: str, field_id: str) -> str:
    """生成单个字段的 md_form INSERT SQL"""
    form = f.form
    if form is None:
        form = FormConfig()

    # Base columns
    cols = ["ID", "mod_id", "field_id", "display_name", "entity_name"]
    vals = [
        f"'{_new_uuid_hex()}'",
        f"'{module_id}'",
        f"'{field_id}'",
        f"'{f.comment}'",
        f"'{f.entity_name}'",
    ]

    # Grid display
    cols.append("is_show_in_grid")
    vals.append("1" if form.show_in_grid else "0")

    if form.show_in_grid:
        cols.extend(["show_type", "LIST_WIDTH", "SORTABLE"])
        vals.extend([
            f"'{form.show_type}'",
            f"'{form.list_width}'",
            "1" if form.sortable else "0",
        ])

    # Search
    cols.append("search_able")
    vals.append("1" if form.searchable else "0")

    if form.searchable and form.search_box:
        # Deep-copy search_box to avoid mutating shared references
        sb = form.search_box.model_copy(deep=True)
        # Auto-fill id if empty
        if not sb.id:
            sb.id = f.entity_name or f.field_name
        if not sb.name:
            sb.name = f.comment or f.field_name

        search_box_json = json.dumps(
            {k: v for k, v in sb.model_dump().items() if v is not None and v != ""},
            ensure_ascii=False,
            separators=(",", ":"),
        ).replace("'", "\\'")
        cols.append("search_box")
        vals.append(f"'{search_box_json}'")

        # Only add data source fields when search_data_source is set (dropdown search)
        if form.search_data_source is not None:
            cols.append("search_data_source")
            vals.append(str(form.search_data_source))
        if form.search_data:
            cols.append("search_data")
            vals.append(f"'{form.search_data}'")
        # value_field_id/value_field_text only for dict-backed search
        if form.search_data_source and form.value_field_id:
            cols.append("value_field_id")
            vals.append(f"'{form.value_field_id}'")
        if form.search_data_source and form.value_field_text:
            cols.append("value_field_text")
            vals.append(f"'{form.value_field_text}'")

    # Edit page
    cols.append("is_show_in_page")
    vals.append("1" if form.show_in_page else "0")

    # ⚠️ 强制规则：edit_type=hidden 时 is_edit 必须为 1（模型配置工具需要写入权限）
    is_edit_val = 1 if form.edit_type == "hidden" else (1 if form.editable else 0)
    cols.append("is_edit")
    vals.append(str(is_edit_val))

    if form.edit_type and (is_edit_val == 1 or form.edit_type == "hidden"):
        cols.append("edit_type")
        vals.append(f"'{form.edit_type}'")
        if form.edit_tip:
            cols.append("edit_tip")
            vals.append(f"'{form.edit_tip}'")

    # View page (查看页)
    if form.show_in_page and form.view_type:
        cols.append("view_type")
        vals.append(f"'{form.view_type}'")
    if form.view_drill_url:
        cols.append("view_drill_url")
        vals.append(f"'{form.view_drill_url}'")
    if form.view_drill_open_type is not None:
        cols.append("view_drill_open_type")
        vals.append(str(form.view_drill_open_type))
    if form.view_drill_page_title:
        cols.append("view_drill_page_title")
        vals.append(f"'{form.view_drill_page_title}'")

    # Layout (布局)
    if form.is_full_line is not None:
        cols.append("is_full_line")
        vals.append("1" if form.is_full_line else "0")

    # regex_rule 独立于 edit_type 输出（不依赖显式编辑类型）
    if form.regex_rule:
        cols.append("regex_rule")
        vals.append(f"'{form.regex_rule}'")

    # Data source (for select fields with dictionary)
    if form.data_source is not None:
        cols.append("data_source")
        vals.append(str(form.data_source))
    if form.dic_name:
        cols.append("dic_name")
        vals.append(f"'{form.dic_name}'")

    # Import / Export
    if form.is_import is not None:
        cols.append("is_import")
        vals.append("1" if form.is_import else "0")
    if form.is_export is not None:
        cols.append("is_export")
        vals.append("1" if form.is_export else "0")

    # Default value
    if form.default_value is not None:
        cols.append("default_value")
        vals.append(f"'{form.default_value}'")

    # Priority
    cols.append("priority")
    vals.append(str(f.priority or 1))

    # 分组配置 (group_name)
    if form.group:
        cols.append("group_name")
        vals.append(f"'{form.group}'")

    return (
        f"-- {f.comment} ({f.field_name})\n"
        f"INSERT INTO md_form ({', '.join(cols)})\n"
        f"VALUES ({', '.join(vals)});"
    )


def _new_uuid_hex() -> str:
    import uuid
    return uuid.uuid4().hex


def generate_create(defn: ModuleDefinition) -> str:
    module_id = defn.reserved_ids['module_id']
    lines = ["-- ========== 步骤3: 配置表单 =========="]
    for f in defn.fields:
        field_id = defn.reserved_ids['field_ids'][f.field_name]
        lines.append(_form_sql(f, module_id, field_id))
        lines.append("")
    return "\n".join(lines)


def generate_cleanup(defn: ModuleDefinition) -> str:
    code = defn.module.code
    return f"-- ========== 清理: 删除表单 ==========\nDELETE FROM md_form WHERE mod_id IN (SELECT id FROM md_module WHERE code = '{code}');"
