"""Flow Engine - SQL Generator

独立生成流程引擎配置数据的 SQL，包含：
1. busi — 业务定义
2. flw_view_dictionary — 流程视图（按 busi 动态生成）
3. flw_flow — 流程定义
4. comm_handler + comm_handler_instance — 处理人规则
5. flw_node — 流程环节（handler 字段引用 comm_handler.ID）
6. flw_route — 环节路由
"""

from __future__ import annotations
from typing import Optional
from models.flow_model import FlowDefinition, NodeDef, RouteDef, HandlerDef
from generators.schema_contract import validate_insert

# ── 数据库查询：根据 handler type 查找真实数据 ──

HANDLER_TABLE_SQL = {
    1: "SELECT ID, NAME FROM comm_handler_rule WHERE ID = %s",
    20: """
        SELECT u.id, c.name FROM sys_user u
        LEFT JOIN sys_user_comminfo c ON u.user_info_id = c.id
        WHERE u.id = %s AND c.name IS NOT NULL
        """,
    0: "SELECT id, name FROM sys_org WHERE id = %s AND flg_deleted = 0",
    40: "SELECT id, name FROM sys_role WHERE id = %s",
}

HANDLER_FALLBACK = HandlerDef(
    type=20,
    value="20!@!超级管理员!@!U00001",
    text="超级管理员",
)

# 默认引用 ID 映射（当 DB 不可用时）
HANDLER_DEFAULT_REF = {
    1: "3",           # comm_handler_rule ID=3 (拟稿人/填报人)
    20: "U00001",     # 超级管理员
}


def resolve_handler(handler: HandlerDef, db_config: Optional[dict] = None) -> HandlerDef:
    """解析环节处理人：从数据库查询真实数据构建 processor_value

    参数:
        handler: HandlerDef (含 type, 以及 value 的最后一段用作 ref_id / 或从 text 查找)
        db_config: 数据库连接配置 {host, port, user, password, database}
                   None 表示跳过 DB 查询，直接返回 fallback 或原始值

    返回:
        解析后的 HandlerDef
    """
    if db_config is None:
        # DB 不可用 → type=20 超级管理员 作为保底
        return HANDLER_FALLBACK

    ref_id = _extract_ref_id(handler)
    sql = HANDLER_TABLE_SQL.get(handler.type)
    if sql is None or not ref_id:
        return HANDLER_FALLBACK

    try:
        import pymysql
        conn = pymysql.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
            connect_timeout=5,
        )
        cur = conn.cursor()
        cur.execute(sql, (ref_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            db_id, db_name = row
            return HandlerDef(
                type=handler.type,
                value=f"{handler.type}!@!{db_name}!@!{db_id}",
                text=db_name,
            )
    except Exception as e:
        print(f"  ⚠️  DB 查询失败 ({handler.type=}, {ref_id=}): {e}")

    return HANDLER_FALLBACK


def _extract_ref_id(handler: HandlerDef) -> str:
    """从 handler 提取引用 ID (用于数据库查询)"""
    parts = handler.value.split("!@!")
    if len(parts) == 3 and parts[2]:
        ref = parts[2].strip()
        # ⚠️ 抽象处理人（type=1）第三段为 '0' 是典型幻觉——Agent 误以为 0 是占位符
        if handler.type == 1 and ref == '0':
            default_id = HANDLER_DEFAULT_REF.get(1, "3")
            print(
                f"\033[93m⚠️  [_extract_ref_id 自动修复] type=1 第三段为 '0'（典型幻觉），"
                f"自动使用默认 ID='{default_id}'。\033[0m",
                file=sys.stderr
            )
            return default_id
        return ref
    # 如果 type=1 且未指定，用默认的 handler_rule ID
    return HANDLER_DEFAULT_REF.get(handler.type, "")


def resolve_flow_handlers(flow: FlowDefinition, db_config: Optional[dict] = None) -> FlowDefinition:
    """批量解析流程中所有节点的处理人"""
    import copy
    resolved = copy.deepcopy(flow)
    for node in resolved.nodes:
        if node.handler and not _is_end_node(node):
            node.handler = resolve_handler(node.handler, db_config)
    return resolved


# ── SQL 生成 ──


def generate_busi_insert(flow: FlowDefinition, ids: dict) -> str:
    """生成 busi INSERT"""
    busi = flow.busi
    busi_id = ids["busi_id"]
    return (
        f"-- busi: {busi.name} ({busi.code})\n"
        f"INSERT INTO busi (id, code, NAME, BUSI_INSTANCE_CLASS, "
        f"BUSI_INSTANCE_MODULE, FLG_BATCH, FLG_USE, PRIORITY)\n"
        f"VALUES ('{busi_id}', '{busi.code}', '{busi.name}',\n"
        f"    '{busi.instance_class}', '{busi.module_code or ''}',\n"
        f"    1, 1, 1);"
    )


def _view_urls(view_type: str) -> tuple:
    """返回 (view_url, preview_url, spread_url, done_url)"""
    if view_type == "edit":
        url = "/module/flow/workEdit/${id}"
        preview = "/module/flow/view/${id}"
        return (url, preview, preview, preview)
    else:  # approve
        url = "/module/flow/tableView/${id}/1"
        return (url, url, url, url)


def generate_view_inserts(flow: FlowDefinition, ids: dict) -> str:
    """生成 flw_view_dictionary INSERT（2条/流程）

    规则：name 使用"业务名称-视图类型"格式，如"请假-编辑"、"请假-审批"
    """
    busi_code = flow.busi.code
    busi_name = flow.busi.name

    edit_url, edit_prev, edit_sprd, edit_done = _view_urls("edit")
    app_url, app_prev, app_sprd, app_done = _view_urls("approve")

    return (
        f"-- flw_view_dictionary: {busi_name} - 编辑\n"
        f"INSERT INTO flw_view_dictionary (id, name, busi, ways, view_url,\n"
        f"    preview_url, spread_url, done_url, priority, busi_name)\n"
        f"VALUES ('{ids['view_edit_id']}', '{busi_name}-编辑', '{busi_code}', '1',\n"
        f"    '{edit_url}', '{edit_prev}',\n"
        f"    '{edit_sprd}', '{edit_done}', 1, '{busi_name}');\n\n"
        f"-- flw_view_dictionary: {busi_name} - 审批\n"
        f"INSERT INTO flw_view_dictionary (id, name, busi, ways, view_url,\n"
        f"    preview_url, spread_url, done_url, priority, busi_name)\n"
        f"VALUES ('{ids['view_approve_id']}', '{busi_name}-审批', '{busi_code}', '1',\n"
        f"    '{app_url}', '{app_prev}',\n"
        f"    '{app_sprd}', '{app_done}', 1, '{busi_name}');"
    )


def generate_flow_insert(flow: FlowDefinition, ids: dict) -> tuple:
    """生成 flw_flow INSERT（返回元组列表，用于 join）"""
    memo = flow.memo or ""
    return (
        f"-- flw_flow: {flow.flow_name} ({flow.code})",
        f"INSERT INTO flw_flow (id, org_id, code, flow_name, busi_type, memo,",
        f"    flg_allow_modify, priority, flg_deleted)",
        f"VALUES ('{ids['flow_id']}', '{flow.org_id}', '{flow.code}',",
        f"    '{flow.flow_name}', '{ids['busi_id']}', '{memo}',",
        f"    {flow.flg_allow_modify}, {flow.priority or 0}, 0);",
    )


def _is_end_node(node: NodeDef) -> bool:
    return node.code == "end"


_HANDLER_FALLBACK_TYPE = 20
_HANDLER_FALLBACK_VALUE = "20!@!超级管理员!@!U00001"
_HANDLER_FALLBACK_TEXT = "超级管理员"


# 安全助手：Python 的 `x or default` 当 x=0 时会错误地走 default 分支
# 而 0 是一个有效值（如 handle_way=0, priority=0）
def _safe_val(val, default: str = 'NULL'):
    """安全取值：0 / False 等有效值不会被覆盖为默认值"""
    return str(val) if val is not None else default


def _handler_type(h: Optional[HandlerDef]) -> int:
    """获取处理人类型，无 handler 时默认 20"""
    return h.type if h else _HANDLER_FALLBACK_TYPE


def _processor_value(h: Optional[HandlerDef]) -> str:
    """获取 processor_value，无 handler 时使用超级管理员保底"""
    return h.value if (h and h.value) else _HANDLER_FALLBACK_VALUE


def _processor_text(h: Optional[HandlerDef]) -> str:
    """获取 processor_text，无 handler 时使用超级管理员保底"""
    return h.text if (h and h.text) else _HANDLER_FALLBACK_TEXT


def _processor_ref(h: Optional[HandlerDef]) -> str:
    """获取 processor_value 的第三段（引用ID）"""
    val = _processor_value(h)
    parts = val.split("!@!")
    return parts[2] if len(parts) == 3 else ""


def _processor_value_parts(h: Optional[HandlerDef]) -> list:
    """将 processor_value 拆分为三段 [type, name, ref_id]"""
    val = _processor_value(h)
    parts = val.split("!@!")
    if len(parts) != 3:
        return ["20", "超级管理员", "U00001"]
    return parts


def generate_comm_handler_insert(node: NodeDef, flow: FlowDefinition, ids: dict) -> str:
    """生成 comm_handler INSERT（每个节点一条）"""
    handler_id = ids[f"handler_{node.code}_id"]
    return (
        f"-- comm_handler: {node.node_name} ({node.code})\n"
        f"INSERT INTO comm_handler (ID, DESCRIPTION)\n"
        f"VALUES ('{handler_id}', NULL);"
    )


def generate_comm_handler_instance_insert(node: NodeDef, flow: FlowDefinition, ids: dict) -> str:
    """生成 comm_handler_instance INSERT（每个节点一条）

    字段规则：
    - ID: 新 UUID
    - HANDLER_ID: 引用 comm_handler.ID
    - RULE_ID: 默认为 0（环节处理人），对应 comm_handler_rule.ID
    - ORG_TYPE / HANDLER_NAME / ORG_ID: 从 node_processor_value 的三段解析
      ⚠️ 抽象处理人（type=1）时 ORG_TYPE 强制为 100
    - PRIORITY: 默认为 0
    - SCALE: 默认为 1.000000
    """
    instance_id = ids[f"handler_instance_{node.code}_id"]
    handler_id = ids[f"handler_{node.code}_id"]
    parts = _processor_value_parts(node.handler)
    handler_type = _handler_type(node.handler)
    # 抽象处理人（type=1）时 ORG_TYPE 强制为 100，RULE_ID 取 comm_handler_rule.ID
    org_type = '100' if handler_type == 1 else parts[0]
    handler_name, org_id = parts[1], parts[2]
    # ⚠️ type=1 第三段为 '0' 是 Agent 典型幻觉，自动纠正为默认规则 ID
    if handler_type == 1 and org_id == '0':
        org_id = '3'  # comm_handler_rule ID=3 (拟稿人/填报人)
    rule_id = org_id if handler_type == 1 else '0'
    return (
        f"-- comm_handler_instance: {node.node_name} ({node.code})\n"
        f"INSERT INTO comm_handler_instance "
        f"(ID, RULE_ID, HANDLER_ID, ORG_TYPE, HANDLER_NAME, ORG_ID, PRIORITY, SCALE)\n"
        f"VALUES ("
        f"'{instance_id}', {rule_id}, '{handler_id}',"
        f" {org_type}, '{handler_name}', '{org_id}',"
        f" 0, 1.000000"
        f");"
    )


def generate_node_insert(node: NodeDef, flow: FlowDefinition, ids: dict) -> tuple:
    """生成单条 flw_node INSERT（返回元组列表）"""
    node_id = ids[f"node_{node.code}_id"]

    if _is_end_node(node):
        handler_id = ids[f"handler_{node.code}_id"]
        return (
            f"-- flw_node: 结束 ({node.code})",
            f"INSERT INTO flw_node (id, flow_id, code, node_name, priority,",
            f"    flg_head, flg_root,",
            f"    flg_deleted, flg_allow_delete, flg_allow_modify, flg_prev_over,",
            f"    window_type, submittype, flg_submit_sync, node_handler_scope,",
            f"    node_handler_type, node_processor_value, node_processor_text,",
            f"    handler,",
            f"    automatic_terminate, flg_spread,",
            f"    flg_spread_allow,",
            f"    timelimit_relate_yq, timelimit_relate, timelimit_date,",
            f"    timelimit_flg_apply, timellimt_house)",
            f"VALUES ('{node_id}', '{ids['flow_id']}', '{node.code}', '{node.node_name}',",
            f"    999999, 0, 1,",
            f"    0, 1, 1, 1, 0, 0, 1, 1,",
            f"    {_handler_type(None)}, '{_processor_value(None)}', '{_processor_text(None)}',",
            f"    '{handler_id}',",
            f"    {node.automatic_terminate}, {node.flg_spread},",
            f"    {node.flg_spread_allow},",
            f"    {node.timelimit_relate_yq}, {node.timelimit_relate}, {node.timelimit_date},",
            f"    {node.timelimit_flg_apply}, {node.timellimt_house});",
        )

    view_id = ids["view_edit_id"] if node.flg_head == 1 else ids["view_approve_id"]
    view_name = f"{flow.busi.name}-编辑" if node.flg_head == 1 else f"{flow.busi.name}-审批"
    h = node.handler
    handler_id = ids[f"handler_{node.code}_id"]
    return (
        f"-- flw_node: {node.node_name} ({node.code})",
        f"INSERT INTO flw_node (id, flow_id, code, node_name, handle_way,",
        f"    node_handler_type, node_processor_value, node_processor_text,",
        f"    handler,",
        f"    view_id, view_name, priority, flg_head, flg_root,",
        f"    flg_deleted, flg_allow_delete, flg_allow_modify, window_type,",
        f"    submittype, flg_submit_sync, node_handler_scope, flg_prev_over,",
        f"    automatic_terminate, flg_spread,",
        f"    flg_spread_allow,",
        f"    timelimit_relate_yq, timelimit_relate, timelimit_date,",
        f"    timelimit_flg_apply, timellimt_house)",
        f"VALUES (",
        f"    '{node_id}', '{ids['flow_id']}', '{node.code}', '{node.node_name}',",
        f"    {_safe_val(node.handle_way)},",
        f"    {_handler_type(h)}, '{_processor_value(h)}', '{_processor_text(h)}',",
        f"    '{handler_id}',",
        f"    '{view_id}', '{view_name}',",
        f"    {node.priority or 0}, {node.flg_head}, {node.flg_root},",
        f"    0, 1, 1, 0, 0, 1, 1, 1,",
        f"    {node.automatic_terminate}, {node.flg_spread},",
        f"    {node.flg_spread_allow},",
        f"    {node.timelimit_relate_yq}, {node.timelimit_relate}, {node.timelimit_date},",
        f"    {node.timelimit_flg_apply}, {node.timellimt_house}",
        f");",
    )


def generate_route_insert(route: RouteDef, node: NodeDef, ids: dict) -> tuple:
    """生成单条 flw_route INSERT（返回元组列表）"""
    route_id = ids[f"route_{node.code}_{route.target_node}_{route.code}_id"]
    target_id = ids[f"node_{route.target_node}_id"]

    return (
        f"-- flw_route: {node.code} → {route.target_node} ({route.menu_name})",
        f"INSERT INTO flw_route (id, node_id, next_node_id, menu_name, name,",
        f"    priority, flg_attribute, flg_multi_node, code, flg_deleted,",
        f"    is_save, valid_handler, iz_need_opinion, flow_submit_form_no_valid)",
        f"VALUES (",
        f"    '{route_id}', '{ids[f'node_{node.code}_id']}', '{target_id}',",
        f"    '{route.menu_name}', '{route.name}',",
        f"    {route.priority}, '{route.flg_attribute}', {route.flg_multi_node},",
        f"    '{route.code}', 0, 0, 0, {route.iz_need_opinion}, {route.flow_submit_form_no_valid}",
        f");",
    )


def validate_flow_inserts(flow: FlowDefinition) -> list[str]:
    """校验流程引擎 INSERT 是否覆盖所有 NOT NULL 字段"""
    errors = []

    # busi
    errors.extend(validate_insert("busi", {"id", "code", "NAME", "BUSI_INSTANCE_CLASS",
        "BUSI_INSTANCE_MODULE", "FLG_BATCH", "FLG_USE", "PRIORITY"},
        "busi INSERT"))

    # flw_view_dictionary (每条 2 个 NOT NULL 字段: id)
    errors.extend(validate_insert("flw_view_dictionary", {"id", "name", "busi", "ways",
        "view_url", "preview_url", "spread_url", "done_url", "priority", "busi_name"},
        "flw_view_dictionary INSERT"))

    # flw_flow
    errors.extend(validate_insert("flw_flow", {"id", "org_id", "code", "flow_name",
        "busi_type", "memo", "flg_allow_modify", "priority", "flg_deleted"},
        "flw_flow INSERT"))

    # comm_handler
    errors.extend(validate_insert("comm_handler", {"ID", "DESCRIPTION"},
        "comm_handler INSERT"))

    # comm_handler_instance
    errors.extend(validate_insert("comm_handler_instance", {"ID", "RULE_ID", "HANDLER_ID",
        "ORG_TYPE", "HANDLER_NAME", "ORG_ID", "PRIORITY", "SCALE"},
        "comm_handler_instance INSERT"))

    # flw_node (通用字段 + 每个节点)
    node_common_cols = {"id", "flow_id", "code", "node_name", "handle_way",
        "handler", "node_handler_type", "node_processor_value", "node_processor_text",
        "priority", "flg_head", "flg_root",
        "flg_deleted", "flg_allow_delete", "flg_allow_modify", "window_type",
        "submittype", "flg_submit_sync", "node_handler_scope", "flg_prev_over",
        "automatic_terminate", "flg_spread", "flg_spread_allow",
        "timelimit_relate_yq", "timelimit_relate", "timelimit_date",
        "timelimit_flg_apply", "timellimt_house",
        "view_id", "view_name"}
    for node in flow.nodes:
        node_cols = node_common_cols.copy()
        if flow.is_end_node(node.code):
            # 结束节点简化：无 view_id, view_name, handle_way
            node_cols.discard("view_id")
            node_cols.discard("view_name")
            node_cols.discard("handle_way")
        errors.extend(validate_insert("flw_node", node_cols, f"flw_node INSERT (node={node.code})"))

    # flw_route (每个路由)
    route_common_cols = {"id", "node_id", "next_node_id", "menu_name", "name",
        "priority", "flg_attribute", "flg_multi_node", "code", "flg_deleted",
        "is_save", "valid_handler", "iz_need_opinion", "flow_submit_form_no_valid"}
    for node in flow.nodes:
        for route in node.routes:
            errors.extend(validate_insert("flw_route", route_common_cols,
                f"flw_route INSERT (node={node.code}, route={route.code})"))

    return errors


def generate_create(flow: FlowDefinition) -> str:
    """主入口：生成完整的流程引擎 SQL"""
    # 先做 NOT NULL 字段完整性校验
    errors = validate_flow_inserts(flow)
    if errors:
        raise ValueError(
            "流程引擎 INSERT 完整性校验失败:\n  " + "\n  ".join(errors)
        )
    ids = _generate_ids(flow)
    now = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "-- ============================================================",
        f"-- Flow Engine SQL: {flow.flow_name} ({flow.code})",
        f"-- Generated: {now}",
        "-- ============================================================",
        "",
        generate_busi_insert(flow, ids),
        "",
        generate_view_inserts(flow, ids),
        "",
    ]

    lines.extend(list(generate_flow_insert(flow, ids)))
    lines.append("")

    for node in flow.nodes:
        # comm_handler + comm_handler_instance（每个节点一条）
        lines.append(generate_comm_handler_insert(node, flow, ids))
        lines.append(generate_comm_handler_instance_insert(node, flow, ids))
        lines.append("")

    for node in flow.nodes:
        # flw_node
        lines.extend(list(generate_node_insert(node, flow, ids)))
        lines.append("")

    for node in flow.nodes:
        if _is_end_node(node):
            continue
        for route in node.routes:
            lines.extend(list(generate_route_insert(route, node, ids)))
            lines.append("")

    return "\n".join(lines)


def generate_cleanup(flow: FlowDefinition) -> str:
    """生成清理 SQL（含 comm_handler/comm_handler_instance）"""
    lines = [
        "-- ============================================================",
        f"-- Flow Engine Cleanup: {flow.flow_name} ({flow.code})",
        "-- ============================================================",
        "",
    ]

    rev_nodes = list(reversed([n.code for n in flow.nodes]))

    # 1. 清理 comm_handler_instance（子表先删）
    for nc in rev_nodes:
        lines.append(
            f"DELETE FROM comm_handler_instance WHERE HANDLER_ID IN ("
            f"SELECT id FROM comm_handler WHERE id IN ("
            f"SELECT handler FROM flw_node WHERE code = '{nc}' "
            f"AND flow_id IN (SELECT id FROM flw_flow WHERE code = '{flow.code}' AND flg_deleted = 0)"
            f"));"
        )
    lines.append("")

    # 2. 清理 comm_handler
    for nc in rev_nodes:
        lines.append(
            f"DELETE FROM comm_handler WHERE id IN ("
            f"SELECT handler FROM flw_node WHERE code = '{nc}' "
            f"AND flow_id IN (SELECT id FROM flw_flow WHERE code = '{flow.code}' AND flg_deleted = 0)"
            f");"
        )
    lines.append("")

    # 3. 清理 flw_route
    for nc in rev_nodes:
        node = flow.get_node(nc)
        if node and not _is_end_node(node):
            for route in node.routes:
                lines.append(
                    f"DELETE FROM flw_route WHERE code = '{route.code}' "
                    f"AND node_id IN (SELECT id FROM flw_node WHERE code = '{nc}' "
                    f"AND flow_id IN (SELECT id FROM flw_flow WHERE code = '{flow.code}' "
                    f"AND flg_deleted = 0));"
                )
    lines.append("")

    # 4. 清理 flw_node
    for nc in rev_nodes:
        lines.append(
            f"DELETE FROM flw_node WHERE code = '{nc}' "
            f"AND flow_id IN (SELECT id FROM flw_flow WHERE code = '{flow.code}' "
            f"AND flg_deleted = 0);"
        )
    lines.append("")

    # 5. 清理 flw_flow
    lines.append(f"DELETE FROM flw_flow WHERE code = '{flow.code}' AND flg_deleted = 0;\n")

    # 6. 清理 flw_view_dictionary
    lines.append(f"DELETE FROM flw_view_dictionary WHERE busi = '{flow.busi.code}';\n")

    # 7. 清理 busi
    lines.append(f"DELETE FROM busi WHERE code = '{flow.busi.code}';")

    return "\n".join(lines)


def _generate_ids(flow: FlowDefinition) -> dict:
    """生成所有预分配 ID"""
    from models.flow_model import FlowDefinition as FD
    ids = {
        "busi_id": FD.gen_uuid(),
        "view_edit_id": FD.gen_uuid(),
        "view_approve_id": FD.gen_uuid(),
        "flow_id": FD.gen_uuid(),
    }
    for node in flow.nodes:
        ids[f"node_{node.code}_id"] = FD.gen_uuid()
        ids[f"handler_{node.code}_id"] = FD.gen_uuid()
        ids[f"handler_instance_{node.code}_id"] = FD.gen_uuid()
        for route in node.routes:
            ids[f"route_{node.code}_{route.target_node}_{route.code}_id"] = FD.gen_uuid()
    return ids
