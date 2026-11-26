"""CRUD SQL Generators - Step 5: comm_dictionary (数据字典)

业务字典规则（v5.7）：
  - type_id 固定为 'OTHRE'
  - type_name 固定为 '业务应用'
  - code 为字典唯一标识，用于查询和清理
  - 不能自定义 type_code/type_name
  - 清理时通过 code 精确匹配

表结构 (comm_dictionary):
  id, type_id, type_name, name, code, value, value_type, remark,
  priority, create_time, creator, creator_name, updator, updator_name,
  update_time, flg_deleted, campus

表结构 (comm_dictionary_item):
  id, dictionary_id, value, name, priority, create_time, creator,
  creator_name, remark, flg_default, code
"""

from __future__ import annotations
from common.generator_shared.models import ModuleDefinition, DictionaryDef


def _dict_create_sql(d: DictionaryDef, creator_id: str, creator_name: str) -> str:
    """生成一个字典类型及其所有字典项的创建 SQL

    使用子查询引用 comm_dictionary.id 而非 MySQL 用户变量（@dict_xxx），
    避免 type_name 含特殊字符（连字符、空格等）时变量名被 MySQL 误解析导致 NULL。
    """
    # 用于子查询的字典类型查找条件
    dict_lookup = f"SELECT id FROM comm_dictionary WHERE code = '{d.type_name}' LIMIT 1"

    lines = [
        f"-- ---------- 字典: {d.name} (code={d.type_name}) ----------",
        f"INSERT INTO comm_dictionary (id, type_id, type_name, code, name, value, value_type, remark, priority, create_time, creator, creator_name)",
        f"VALUES (SUBSTR(UUID(),1,32), 'OTHRE', '业务应用', '{d.type_name}', '{d.name}', '{d.value or d.name}', 1, NULL, 0, NOW(), '{creator_id}', '{creator_name}');",
    ]

    if d.items:
        lines.append("")
        lines.append(
            f"INSERT INTO comm_dictionary_item "
            f"(id, dictionary_id, code, value, name, priority, create_time, creator, creator_name, remark, flg_default)"
            f" VALUES"
        )
        item_vals = []
        for item in d.items:
            item_vals.append(
                f"(SUBSTR(UUID(),1,32), ({dict_lookup}), "
                f"'{item.code}', '{item.value}', '{item.name}', {item.priority}, "
                f"NOW(), '{creator_id}', '{creator_name}', NULL, {item.flg_default})"
            )
        lines.append(",\n".join(item_vals) + ";")

    return "\n".join(lines)


def _dict_cleanup_sql(d: DictionaryDef) -> str:
    """生成一个字典的清理 SQL（通过 code 精确匹配）"""
    return (
        f"-- 清理字典: {d.name} (code={d.type_name})\n"
        f"DELETE FROM comm_dictionary_item WHERE dictionary_id IN (\n"
        f"    SELECT id FROM comm_dictionary WHERE code = '{d.type_name}'\n"
        f");\n"
        f"DELETE FROM comm_dictionary WHERE code = '{d.type_name}';"
    )


def generate_create(defn: ModuleDefinition) -> str:
    if not defn.dictionaries:
        return "-- ========== 步骤5: 创建数据字典（无字典需要创建）=========="
    lines = ["-- ========== 步骤5: 创建数据字典 =========="]
    for d in defn.dictionaries:
        lines.append(_dict_create_sql(d, defn.creator.id, defn.creator.name))
        lines.append("")
    return "\n".join(lines)


def generate_cleanup(defn: ModuleDefinition) -> str:
    if not defn.dictionaries:
        return "-- ========== 清理: 无数据字典需要清理 =========="
    lines = ["-- ========== 清理: 删除数据字典 =========="]
    for d in defn.dictionaries:
        lines.append(_dict_cleanup_sql(d))
        lines.append("")
    return "\n".join(lines)
