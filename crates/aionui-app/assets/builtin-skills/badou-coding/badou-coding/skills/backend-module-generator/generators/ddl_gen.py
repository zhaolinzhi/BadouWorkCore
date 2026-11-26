"""CRUD SQL Generators - Step 0: CREATE TABLE DDL (业务表建表语句)

根据字段定义自动生成 CREATE TABLE SQL，包含:
- 字段定义 + COMMENT
- PRIMARY KEY
- UNIQUE KEY (unique字段)
- INDEX (搜索条件字段、外键字段)
- 系统标准字段 (id, create_time, update_time, flg_deleted)
- ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

from __future__ import annotations
from common.generator_shared.models import ModuleDefinition, FieldDef, SYSTEM_FIELDS


# display_type → MySQL DDL 类型映射
DISPLAY_TYPE_DDL_MAP = {
    "varchar":  lambda f: f"varchar({f.length or 255})",
    "int":      lambda f: "int(11)",
    "tinyint":  lambda f: "tinyint(4)",
    "bigint":   lambda f: "bigint(20)",
    "decimal":  lambda f: f"decimal({f.length or 12},2)",
    "float":    lambda f: "float",
    "double":   lambda f: "double",
    "datetime": lambda f: "datetime",
    "date":     lambda f: "date",
    "text":     lambda f: "text",
}


def _field_ddl(f: FieldDef) -> str:
    """生成单个字段的 DDL 片段"""
    ddl_type_fn = DISPLAY_TYPE_DDL_MAP.get(f.display_type)
    if ddl_type_fn is None:
        ddl_type_fn = DISPLAY_TYPE_DDL_MAP["varchar"]

    mysql_type = ddl_type_fn(f)
    parts = [f"`{f.field_name}`", mysql_type]

    # Special handling for create_time / update_time
    if f.field_name == "create_time":
        parts = [f"`create_time`", "datetime", "DEFAULT CURRENT_TIMESTAMP"]
        parts.append(f"COMMENT '{f.comment or '创建时间'}'")
        return " ".join(parts)
    elif f.field_name == "update_time":
        parts = [f"`update_time`", "datetime", "DEFAULT NULL", "ON UPDATE CURRENT_TIMESTAMP"]
        parts.append(f"COMMENT '{f.comment or '更新时间'}'")
        return " ".join(parts)

    # NOT NULL / NULL
    if f.primary_key or not f.nullable:
        parts.append("NOT NULL")
    else:
        parts.append("DEFAULT NULL")

    # Default value (replace DEFAULT NULL if applicable)
    if f.default_value is not None and not f.primary_key:
        if f.nullable:
            # Replace trailing DEFAULT NULL with DEFAULT value
            parts[-1] = f"DEFAULT '{f.default_value}'"
        else:
            # After NOT NULL, add DEFAULT
            parts.append(f"DEFAULT '{f.default_value}'")

    # COMMENT
    parts.append(f"COMMENT '{f.comment or f.field_name}'")

    return " ".join(parts)


def _system_field_ddls() -> list[str]:
    """生成系统标准字段 DDL（id + create_time + update_time + flg_deleted）

    这些字段自动追加到所有 CREATE TABLE，不需要用户在 JSON 中定义。
    """
    return [
        "  `id` varchar(64) NOT NULL COMMENT '主键ID'",
        "  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'",
        "  `update_time` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'",
        "  `flg_deleted` int(11) DEFAULT 0 COMMENT '逻辑删除标识(0=未删除,1=已删除)'",
    ]


def generate_create(defn: ModuleDefinition) -> str:
    """生成 CREATE TABLE DDL"""
    m = defn.module
    lines = [
        f"-- ========== 步骤0: 创建业务表 ==========",
        f"CREATE TABLE IF NOT EXISTS `{m.db_table}` (",
    ]

    # Fields: 用户定义字段 + 系统标准字段（去重）
    field_ddls = []
    existing_names = {f.field_name.lower() for f in defn.fields}
    for f in defn.fields:
        field_ddls.append("  " + _field_ddl(f))
    # 追加系统标准字段（仅在 defn.fields 中不存在时）
    for sys_field in _system_field_ddls():
        name = sys_field.strip().split()[0].strip('`').lower()
        if name not in existing_names:
            field_ddls.append(sys_field)

    # Constraints
    constraints = []

    # PRIMARY KEY: 默认使用系统 id 字段
    constraints.append("  PRIMARY KEY (`id`)")

    # UNIQUE KEYs (非 PK 的唯一字段)
    for f in defn.fields:
        if f.unique and not f.primary_key:
            constraints.append(f"  UNIQUE KEY `uk_{f.field_name}` (`{f.field_name}`)")

    # INDEXs (searchable fields, dict fields, create_time)
    indexed = set()
    for f in defn.fields:
        if f.primary_key or f.unique:
            continue
        if f.field_name in indexed:
            continue
        should_index = False
        if f.field_name == "create_time":
            should_index = True
        elif f.form and (f.form.searchable or f.dict):
            should_index = True
        elif f.display_type == "int" and f.dict:
            should_index = True
        if should_index:
            constraints.append(f"  KEY `idx_{f.field_name}` (`{f.field_name}`)")
            indexed.add(f.field_name)

    # Combine: fields + constraints, all comma-separated
    all_items = field_ddls + constraints
    lines.append(",\n".join(all_items))

    # Close
    table_comment = m.table_name_cn or m.name_cn
    lines.append(f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{table_comment}';")

    return "\n".join(lines)


def generate_cleanup(defn: ModuleDefinition) -> str:
    """生成 DROP TABLE DDL"""
    return (
        f"-- ========== 清理: 删除业务表 ==========\n"
        f"DROP TABLE IF EXISTS `{defn.module.db_table}`;"
    )
