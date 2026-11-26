"""CRUD SQL Generators - md_module_link relation generator"""

from __future__ import annotations
from common.generator_shared.models import ModuleDefinition, RelationDef


def _relation_insert_sql(rel: RelationDef, idx: int, defn: ModuleDefinition) -> str:
    """生成单条 md_module_link INSERT SQL

    使用子查询查找关联模块的 module_id（code-based），
    当前模块的 module_id 和 field_id 使用预生成 UUID。
    """
    ids = defn.reserved_ids
    link_uuid = ids['link_uuids'][idx]
    module_id = ids['module_id']

    # 自动推导字段
    show_type = rel.SHOW_TYPE
    show_tab = rel.SHOW_TAB

    # field_name / field_id 处理
    # type=1（一对一）：使用用户提供的 field_name（外键字段）
    # type=2（一对多）：使用当前模块的 'id' 字段（关联模块的外键指向它）
    if rel.type == 1:
        field_name_val = rel.field_name or ""
        field_id_ref = f"'{ids['field_ids'][rel.field_name]}'" if rel.field_name else "''"
    else:
        field_name_val = "id"
        field_id_ref = f"'{ids['field_ids']['id']}'"

    # tab_name 处理
    tab_name_val = f"'{rel.tab_name}'" if rel.tab_name else "NULL"

    # 关联模块的 module_id（通过子查询查找）
    related_module_ref = f"(SELECT id FROM md_module WHERE code = '{rel.related_module}' AND flg_deleted = 0)"

    # 关联模块的 related_table（通过子查询查找）
    related_table_ref = f"(SELECT db_table FROM md_module WHERE code = '{rel.related_module}' AND flg_deleted = 0)"

    # ⚠️ 关联字段的 field_id（自动推导，不依赖 Agent 判断）
    # type=1（一对一）：关联字段 = 关联模块的主键 id（外键引用的目标）
    # type=2（一对多）：关联字段 = 关联模块中外键字段（related_field_name）
    if rel.type == 1:
        # type=1: related_field 指向关联模块的主键 id
        related_field_ref = (
            f"(SELECT ID FROM md_field WHERE module_id = {related_module_ref} "
            f"AND field_name = 'id' AND flg_deleted = 0)"
        )
    else:
        # type=2: related_field 指向关联模块中的外键字段（related_field_name）
        related_field_ref = (
            f"(SELECT ID FROM md_field WHERE module_id = {related_module_ref} "
            f"AND field_name = '{rel.related_field_name}' AND flg_deleted = 0)"
        )

    relation_type = "一对一" if rel.type == 1 else "一对多"

    return (
        f"-- relation {idx+1}: {rel.display_name}（{relation_type}）\n"
        f"INSERT INTO md_module_link (id, module_id, related_module_id, field_name, field_id,\n"
        f"    related_table, related_field, related_field_name, type, is_edit, display_name,\n"
        f"    edit_module, is_cascade, priority, SHOW_TAB, SHOW_TYPE, show_style, tab_name)\n"
        f"VALUES (\n"
        f"    '{link_uuid}',\n"
        f"    '{module_id}',\n"
        f"    {related_module_ref},\n"
        f"    '{field_name_val}',\n"
        f"    {field_id_ref},\n"
        f"    {related_table_ref},\n"
        f"    {related_field_ref},\n"
        f"    '{rel.related_field_name}',\n"
        f"    {rel.type}, {rel.is_edit}, '{rel.display_name}',\n"
        f"    {rel.edit_module}, {rel.is_cascade}, {rel.priority},\n"
        f"    {show_tab}, {show_type}, {rel.show_style},\n"
        f"    {tab_name_val}\n"
        f");"
    )


def generate_create(defn: ModuleDefinition) -> str:
    """生成 md_module_link INSERT SQL"""
    if not defn.relations:
        return ""

    lines = ["-- ========== 步骤: 创建模块关联 (md_module_link) =========="]
    for i, rel in enumerate(defn.relations):
        lines.append(_relation_insert_sql(rel, i, defn))
        lines.append("")
    return "\n".join(lines)


def _relation_cleanup_sql(rel: RelationDef, idx: int, defn: ModuleDefinition) -> str:
    """生成单条 md_module_link 清理 SQL"""
    link_uuid = defn.reserved_ids['link_uuids'][idx]
    return (
        f"-- 删除关联: {rel.display_name}\n"
        f"DELETE FROM md_module_link WHERE id = '{link_uuid}';\n"
    )


def generate_cleanup(defn: ModuleDefinition) -> str:
    """生成 md_module_link DELETE SQL（倒序）"""
    if not defn.relations:
        return ""

    lines = ["-- ========== 清理模块关联 =========="]
    for i in range(len(defn.relations) - 1, -1, -1):
        lines.append(_relation_cleanup_sql(defn.relations[i], i, defn))
        lines.append("")
    return "\n".join(lines)
