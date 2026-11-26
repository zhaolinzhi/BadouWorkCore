#!/usr/bin/env python3
"""流程引擎生成器 - 从 flow.json 生成流程 8 表 SQL（busi/flw_flow/flw_node/flw_route/flw_view_dictionary/comm_handler(_instance)）。

用法:
    python flow_generator.py --flow-only flow.json                 # 打印 SQL
    python flow_generator.py --flow-only flow.json --flow-execute  # 生成并执行
    python flow_generator.py --flow-only flow.json --flow-clean    # 仅清理
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "badou-md-common")
if _COMMON not in sys.path:
    sys.path.insert(0, _COMMON)

from models.flow_model import FlowDefinition, BusiDef, NodeDef, RouteDef, HandlerDef
from generators.flow_engine import generate_create, generate_cleanup, resolve_flow_handlers
from badou_md_common.config_loader import load_dotreillis_db_config


def _build_handler(h: dict | None) -> HandlerDef | None:
    if not h:
        return None
    return HandlerDef(type=h["type"], value=h.get("value", ""), text=h.get("text", ""))


def _build_route(r: dict) -> RouteDef:
    return RouteDef(
        code=r["code"], menu_name=r["menu_name"], name=r.get("name"),
        flg_attribute=r.get("flg_attribute", "GOAHEAD"),
        target_node=r["target_node"], priority=r.get("priority", 0),
        flg_multi_node=r.get("flg_multi_node", 0),
        iz_need_opinion=r.get("iz_need_opinion", 1))


def _build_node(n: dict) -> NodeDef:
    flg_head = n.get("flg_head", 0)
    raw_handler = n.get("handler")
    if flg_head == 1 and not raw_handler:
        raw_handler = {"type": 1, "value": "1!@!拟稿人/填报人!@!3", "text": "拟稿人/填报人"}
    return NodeDef(
        code=n["code"], node_name=n["node_name"], flg_head=flg_head,
        handle_way=n.get("handle_way", 1),
        handler=_build_handler(raw_handler),
        routes=[_build_route(r) for r in n.get("routes", [])])


def build_flow(data: dict) -> FlowDefinition:
    """从 dict 构建 FlowDefinition（递归构建嵌套模型）。"""
    return FlowDefinition(
        code=data["code"], flow_name=data["flow_name"], memo=data.get("memo", ""),
        busi=BusiDef(**data["busi"]),
        nodes=[_build_node(n) for n in data["nodes"]],
        org_id=data.get("org_id", "ROOT"),
    )


def generate_flow(def_file: str, execute: bool = False, clean_only: bool = False):
    """从 JSON 文件生成流程引擎 SQL。"""
    with open(def_file) as f:
        data = json.load(f)
    flow = build_flow(data)

    db_config = load_dotreillis_db_config(os.path.dirname(os.path.abspath(__file__))) if execute else None
    if db_config:
        print(f"🔍 正在查询数据库处理人数据...", file=sys.stderr)
        flow = resolve_flow_handlers(flow, db_config)
        for nd in flow.nodes:
            if nd.handler:
                print(f"  {nd.node_name}: type={nd.handler.type}, value={nd.handler.value}", file=sys.stderr)

    sql_parts = [generate_cleanup(flow)]
    if not clean_only:
        try:
            sql_parts.append(generate_create(flow))
        except ValueError as e:
            print(f"❌ 流程引擎 INSERT 完整性校验失败:", file=sys.stderr)
            for line in str(e).split("\n  "):
                print(f"  {line}", file=sys.stderr)
            print(f"\n💡 提示: 请检查 JSON 配置是否完整")
            sys.exit(1)
    sql = "\n".join(sql_parts)

    if execute:
        if not db_config:
            print("❌ 未找到 .trellis/.db-config.json", file=sys.stderr)
            sys.exit(1)
        cmd = f"mysql -h {db_config['host']} -P {db_config['port']}"
        cmd += f" -u {db_config['user']} -p'{db_config['password']}' {db_config['database']}"
        p = subprocess.run(cmd, input=sql, capture_output=True, text=True, shell=True, timeout=30)
        if p.returncode != 0:
            print(f"❌ 执行失败: {p.stderr}", file=sys.stderr)
            sys.exit(1)
        action = "清理" if clean_only else "部署"
        print(f"\n✅ 流程 {flow.code} 已{action}完成", file=sys.stderr)
    else:
        print(sql)


def main():
    parser = argparse.ArgumentParser(description="流程引擎 SQL 生成器")
    parser.add_argument("--flow-only", default=None, metavar="FLOW_JSON",
                        help="流程引擎独立生成：从 JSON 文件生成流程 SQL")
    parser.add_argument("--flow-execute", action="store_true",
                        help="与 --flow-only 配合：生成并执行到数据库")
    parser.add_argument("--flow-clean", action="store_true",
                        help="与 --flow-only 配合：只清理不创建")
    args = parser.parse_args()

    if not args.flow_only:
        parser.error("--flow-only <FLOW_JSON> 是必需的")
    generate_flow(args.flow_only, execute=args.flow_execute, clean_only=args.flow_clean)


if __name__ == "__main__":
    main()
