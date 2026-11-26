"""Schema Contract — 目标表字段约束映射

集中管理生成器涉及的所有目标表的字段约束，确保 INSERT 时不遗漏 NOT NULL 字段。

合约数据来源于实际数据库 SCHEMA（information_schema），
每次数据库结构变更后应同步更新。
"""

from __future__ import annotations

# 每个合约条目: (column_name, column_type, is_not_null, default_value, comment)
# is_not_null=True 表示该字段在数据库中是 NOT NULL 约束
# default_value = None 表示该字段无默认值，INSERT 时必须显式提供

# ──────────────────────────────────────────────
# 流程引擎表 (flw_ engine) — 实际数据库 schema
# ──────────────────────────────────────────────

FLW_FLOW_CONTRACT: list[tuple] = [
    ("id",              "varchar(64)",  True,   None,       "主键ID"),
    ("org_id",          "varchar(64)",  False,  "ROOT",     "组织ID"),
    ("code",            "varchar(64)",  False,  None,       "流程编码"),
    ("flow_name",       "varchar(100)", False,  None,       "流程名称"),
    ("busi_type",       "varchar(64)",  False,  None,       "业务类型"),
    ("memo",            "varchar(100)", False,  None,       "备注"),
    ("flg_allow_modify","int(11)",      False,  1,          "允许修改"),
    ("priority",        "int(11)",      False,  0,          "排序"),
    ("flg_deleted",     "int(11)",      False,  0,          "逻辑删除"),
]

FLW_NODE_CONTRACT: list[tuple] = [
    ("id",                  "varchar(64)",  True,   None,   "主键ID"),
    ("flow_id",             "varchar(64)",  True,   None,   "所属流程ID"),
    ("code",                "varchar(64)",  False,  None,   "节点编码"),
    ("node_name",           "varchar(100)", True,   None,   "节点名称"),
    ("handle_way",          "int(11)",      False,  None,   "处理方式"),
    ("handler",             "varchar(64)",  False,  None,   "处理人规则ID"),
    ("node_handler_type",   "int(11)",      False,  None,   "处理人类型"),
    ("view_id",             "varchar(64)",  False,  None,   "视图ID"),
    ("view_name",           "varchar(200)", False,  None,   "视图名称"),
    ("priority",            "int(11)",      True,   None,   "节点排序"),
    ("flg_head",            "int(11)",      True,   None,   "是否首环节"),
    ("flg_root",            "int(11)",      False,  0,      "是否结束环节"),
    ("flg_deleted",         "int(11)",      False,  0,      "逻辑删除"),
    ("flg_allow_delete",    "int(11)",      True,   1,      "允许删除"),
    ("flg_allow_modify",    "int(11)",      True,   1,      "允许修改"),
    ("window_type",         "int(11)",      True,   0,      "窗口类型"),
    ("submittype",          "int(11)",      False,  0,      "提交类型"),
    ("flg_submit_sync",     "int(11)",      False,  1,      "同步提交"),
    ("node_handler_scope",  "int(11)",      False,  1,      "处理人范围"),
    ("flg_prev_over",       "int(11)",      False,  1,      "前一节点结束"),
    ("automatic_terminate", "int(11)",      False,  0,      "自动提交"),
    ("flg_spread",          "int(11)",      False,  0,      "传阅属性"),
    ("flg_spread_allow",    "int(11)",      False,  1,      "允许发待阅"),
    ("timelimit_relate_yq", "int(11)",      False,  0,      "时限年季"),
    ("timelimit_relate",    "int(11)",      False,  0,      "时限月份"),
    ("timelimit_date",      "int(11)",      False,  0,      "时限日期"),
    ("timelimit_flg_apply", "int(11)",      False,  0,      "时限应用"),
    ("timellimt_house",     "int(11)",      False,  0,      "时限小时"),
    ("node_processor_value","varchar(1024)",False,  None,   "处理人值"),
    ("node_processor_text", "varchar(1024)",False,  None,   "处理人文本"),
]

FLW_ROUTE_CONTRACT: list[tuple] = [
    ("id",                      "varchar(64)",  True,   None,   "主键ID"),
    ("node_id",                 "varchar(64)",  False,  None,   "起始节点ID"),
    ("next_node_id",            "varchar(64)",  False,  None,   "目标节点ID"),
    ("menu_name",               "varchar(256)", False,  None,   "按钮显示名称"),
    ("name",                    "varchar(200)", False,  None,   "路由名称"),
    ("priority",                "int(11)",      False,  0,      "排序"),
    ("flg_attribute",           "varchar(20)",  False,  None,   "路由属性"),
    ("flg_multi_node",          "int(11)",      False,  0,      "多节点标识"),
    ("code",                    "varchar(64)",  False,  None,   "路由编码"),
    ("flg_deleted",             "int(11)",      False,  0,      "逻辑删除"),
    ("is_save",                 "int(11)",      False,  0,      "是否保存"),
    ("valid_handler",           "int(11)",      False,  0,      "验证处理器"),
    ("iz_need_opinion",         "int(1)",       False,  1,      "是否需要意见"),
    ("flow_submit_form_no_valid","int(11)",     False,  1,      "表单验证"),
]

BUSI_CONTRACT: list[tuple] = [
    ("id",                      "varchar(64)",  True,   None,   "主键ID"),
    ("code",                    "varchar(64)",  False,  None,   "业务编码"),
    ("NAME",                    "varchar(100)", False,  None,   "业务名称"),
    ("BUSI_INSTANCE_CLASS",     "varchar(500)", False,  None,   "业务实例类"),
    ("BUSI_INSTANCE_MODULE",    "varchar(500)", False,  None,   "关联模块"),
    ("FLG_BATCH",               "decimal(8,0)", False,  1,      "批量标识"),
    ("FLG_USE",                 "decimal(8,0)", False,  1,      "启用标识"),
    ("PRIORITY",                "decimal(8,0)", False,  1,      "排序"),
]

COMM_HANDLER_CONTRACT: list[tuple] = [
    ("ID",              "varchar(64)",  True,   None,   "主键ID"),
    ("DESCRIPTION",     "varchar(255)", False,  None,   "描述"),
]

COMM_HANDLER_INSTANCE_CONTRACT: list[tuple] = [
    ("ID",              "varchar(64)",  True,   None,   "主键ID"),
    ("RULE_ID",         "varchar(64)",  False,  "0",    "处理人规则ID"),
    ("HANDLER_ID",      "varchar(64)",  False,  None,   "处理人ID"),
    ("ORG_TYPE",        "varchar(64)",  False,  None,   "组织类型"),
    ("HANDLER_NAME",    "varchar(255)", False,  None,   "处理人名称"),
    ("ORG_ID",          "varchar(64)",  False,  None,   "组织ID"),
    ("PRIORITY",        "int(11)",      False,  0,      "排序"),
    ("SCALE",           "decimal(18,6)",True,   1.0,    "权重因子"),
]

FLW_VIEW_DICTIONARY_CONTRACT: list[tuple] = [
    ("id",              "varchar(64)",  True,   None,   "主键ID"),
    ("name",            "varchar(100)", False,  None,   "视图名称"),
    ("busi",            "varchar(64)",  False,  None,   "业务编码"),
    ("ways",            "varchar(10)",  False,  "1",    "处理方式"),
    ("view_url",        "varchar(500)", False,  None,   "视图URL"),
    ("preview_url",     "varchar(500)", False,  None,   "预览URL"),
    ("spread_url",      "varchar(500)", False,  None,   "传阅URL"),
    ("done_url",        "varchar(500)", False,  None,   "办结URL"),
    ("priority",        "int(11)",      False,  1,      "排序"),
    ("busi_name",       "varchar(100)", False,  None,   "业务名称"),
]

# ──────────────────────────────────────────────
# 索引: 表名 → 合约
# ──────────────────────────────────────────────
ALL_CONTRACTS: dict[str, list[tuple]] = {
    "flw_flow":             FLW_FLOW_CONTRACT,
    "flw_node":             FLW_NODE_CONTRACT,
    "flw_route":            FLW_ROUTE_CONTRACT,
    "busi":                 BUSI_CONTRACT,
    "comm_handler":         COMM_HANDLER_CONTRACT,
    "comm_handler_instance": COMM_HANDLER_INSTANCE_CONTRACT,
    "flw_view_dictionary":  FLW_VIEW_DICTIONARY_CONTRACT,
}


def get_not_null_columns(table_name: str) -> list[tuple[str, str, str]]:
    """返回目标表的所有 NOT NULL 字段约束

    Returns:
        list of (column_name, column_type, default_value_or_None)
    """
    contract = ALL_CONTRACTS.get(table_name)
    if not contract:
        return []
    return [
        (col, ctype, default)
        for col, ctype, not_null, default, _ in contract
        if not_null
    ]


def validate_insert(table_name: str, provided_columns: set[str], sql_context: str = "") -> list[str]:
    """校验 INSERT 是否覆盖了目标表的所有 NOT NULL 字段

    Args:
        table_name: 目标表名
        provided_columns: INSERT 语句中提供的字段名集合
        sql_context: 用于错误提示的上下文描述

    Returns:
        缺失的 NOT NULL 字段错误列表，空列表表示通过
    """
    not_null_cols = get_not_null_columns(table_name)
    errors = []
    for col, ctype, default in not_null_cols:
        col_upper = col.upper()
        provided_upper = {c.upper() for c in provided_columns}
        if col not in provided_columns and col_upper not in provided_upper:
            hint = f"  (建议默认值: {default})" if default is not None else "  ⚠️ 无默认值，必须提供"
            msg = f"[{table_name}] NOT NULL 字段 '{col}' ({ctype}) 未提供{hint}"
            if sql_context:
                msg = f"{sql_context}: {msg}"
            errors.append(msg)
    return errors


def format_contract(table_name: str) -> str:
    """格式化输出合约信息"""
    contract = ALL_CONTRACTS.get(table_name)
    if not contract:
        return f"⚠️ 未找到表 {table_name} 的合约定义"

    lines = [f"📋 {table_name} 字段约束:"]
    for col, ctype, not_null, default, comment in contract:
        nn = "NOT NULL" if not_null else "nullable"
        dv = f" DEFAULT {default}" if default is not None else ""
        lines.append(f"  {col:30s} {ctype:15s} {nn:10s}{dv}  -- {comment}")
    return "\n".join(lines)


def print_all_contracts() -> None:
    """打印所有已注册的合约"""
    for table_name in sorted(ALL_CONTRACTS.keys()):
        print(format_contract(table_name))
        print()


def refresh_from_database(host: str, port: int, user: str, password: str, database: str) -> None:
    """从实际数据库查询 schema 并打印合约模板

    用于数据库结构变更后更新本文件的合约数据。
    """
    import pymysql
    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
    cur = conn.cursor()

    table_names = list(ALL_CONTRACTS.keys())
    for tn in table_names:
        cur.execute("""
            SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """, (database, tn))
        rows = cur.fetchall()
        print(f"\n{tn.upper()}_CONTRACT: list[tuple] = [")
        for col, isnull, default, coltype in rows:
            not_null_str = "True" if isnull == "NO" else "False"
            default_str = repr(default) if default is not None else "None"
            comment = f'"-- TODO"  # 替换为中文注释'
            print(f'    ("{col}", "{coltype}", {not_null_str}, {default_str}),')
        print("]")

    cur.close()
    conn.close()
