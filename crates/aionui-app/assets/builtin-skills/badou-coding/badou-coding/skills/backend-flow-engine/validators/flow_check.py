#!/usr/bin/env python3
"""流程引擎一致性校验：busi/flw_flow/flw_node/flw_route/comm_handler(_instance)/flw_view_dictionary。

使用: python3 validators/flow_check.py <flow.json>
退出码: 0=通过, 1=有失败
"""
import sys, json, os

_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_COMMON = os.path.join(_SKILL_DIR, "..", "badou-md-common")
if _COMMON not in sys.path:
    sys.path.insert(0, _COMMON)

from badou_md_common.validator_core import DB, CheckResult, TTY_CYAN, TTY_RED, TTY_RESET
from datetime import datetime


class FlowChecker:
    """流程引擎一致性校验器。"""

    def __init__(self, def_path: str):
        with open(def_path) as f:
            self.data = json.load(f)
        self.db = DB(_SKILL_DIR)
        self.result = CheckResult()

    def check_flow(self):
        """验证流程 8 表数据一致性（从原 idempotent_check.check_flow 迁入）。"""
        flow_code = self.data.get("code", "")
        busi = self.data.get("busi", {})
        if not flow_code:
            return self.result.skip("JSON 非流程定义，跳过流程引擎校验")

        busi_rows = self.db.query(f"SELECT id, code, NAME FROM busi WHERE code = '{busi.get('code', '')}'")
        if not busi_rows:
            self.result.fail(f"busi '{busi.get('code')}' 未找到")
            return
        self.result.ok(f"busi '{busi_rows[0]['code']}' ({busi_rows[0]['NAME']}) 存在")

        flows = self.db.query(f"SELECT id, code, flow_name FROM flw_flow WHERE code = '{flow_code}' AND flg_deleted = 0")
        if not flows:
            self.result.fail(f"flw_flow '{flow_code}' 未找到")
            return
        flow_id = flows[0]["id"]
        self.result.ok(f"flw_flow '{flow_code}' ({flows[0]['flow_name']}) 存在")

        nodes = self.db.query(
            f"SELECT code, node_name, priority, flg_head, flg_root, flg_deleted "
            f"FROM flw_node WHERE flow_id = '{flow_id}' ORDER BY priority")
        expected_nodes = {n["code"] for n in self.data.get("nodes", [])}
        actual_nodes = {n["code"] for n in nodes}
        missing_nodes = expected_nodes - actual_nodes
        extra_nodes = actual_nodes - expected_nodes
        if missing_nodes:
            self.result.fail(f"流程缺少节点: {missing_nodes}")
        if extra_nodes:
            self.result.fail(f"流程多余节点: {extra_nodes}")
        if not missing_nodes and not extra_nodes:
            self.result.ok(f"流程节点 {len(nodes)} 个: {', '.join(n['code'] for n in nodes)}")

        heads = [n for n in nodes if n["flg_head"] == 1]
        roots = [n for n in nodes if n["flg_root"] == 1]
        if len(heads) != 1:
            self.result.fail(f"首环节数量: {len(heads)}（期望 1 个）")
        else:
            self.result.ok(f"首环节: {heads[0]['code']}({heads[0]['node_name']})")
        if len(roots) != 1:
            self.result.fail(f"结束环节数量: {len(roots)}（期望 1 个）")
        else:
            self.result.ok(f"结束环节: {roots[0]['code']}({roots[0]['node_name']})")

        routes = self.db.query(
            f"SELECT r.code, r.menu_name, r.flg_attribute, r.priority "
            f"FROM flw_route r JOIN flw_node n ON r.node_id = n.id "
            f"WHERE n.flow_id = '{flow_id}' ORDER BY r.priority")
        if routes:
            self.result.ok(f"路由 {len(routes)} 条")
        else:
            self.result.fail("无路由数据")

        handler_count = self.db.query(
            f"SELECT COUNT(*) AS cnt FROM comm_handler "
            f"WHERE id IN (SELECT handler FROM flw_node WHERE flow_id = '{flow_id}')")
        instance_count = self.db.query(
            f"SELECT COUNT(*) AS cnt FROM comm_handler_instance "
            f"WHERE HANDLER_ID IN (SELECT id FROM comm_handler WHERE id IN "
            f"(SELECT handler FROM flw_node WHERE flow_id = '{flow_id}'))")
        if handler_count and handler_count[0]["cnt"] == len(nodes):
            self.result.ok(f"comm_handler {handler_count[0]['cnt']} 条（应与节点数一致）")
        else:
            self.result.fail(f"comm_handler 数量 {handler_count[0]['cnt'] if handler_count else 0}，期望 {len(nodes)}")
        if instance_count and instance_count[0]["cnt"] == len(nodes):
            self.result.ok(f"comm_handler_instance {instance_count[0]['cnt']} 条（应与节点数一致）")
        else:
            self.result.fail(f"comm_handler_instance 数量 {instance_count[0]['cnt'] if instance_count else 0}，期望 {len(nodes)}")

        views = self.db.query(f"SELECT id, name, busi FROM flw_view_dictionary WHERE busi = '{busi.get('code', '')}'")
        if len(views) == 2:
            self.result.ok(f"flw_view_dictionary 2 条（编辑+审批）")
        else:
            self.result.fail(f"flw_view_dictionary 数量 {len(views)}，期望 2")

    def run_all(self) -> CheckResult:
        print(f"\n{TTY_CYAN}═══ 流程引擎一致性校验 ══════════════════════{TTY_RESET}")
        print(f"  数据库: {self.db.database}@{self.db.host}")
        print(f"  校验时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{TTY_CYAN}────────────────────────────────────────────────{TTY_RESET}")
        self.check_flow()
        print(f"\n  {self.result.summary()}")
        return self.result


def main():
    if len(sys.argv) < 2:
        print(f"用法: python3 validators/flow_check.py <flow.json>")
        sys.exit(1)
    def_path = sys.argv[1]
    if not os.path.exists(def_path):
        print(f"{TTY_RED}❌ 定义文件不存在: {def_path}{TTY_RESET}", file=sys.stderr)
        sys.exit(1)
    checker = FlowChecker(def_path)
    result = checker.run_all()
    sys.exit(0 if result.is_pass() else 1)


if __name__ == "__main__":
    main()
