#!/usr/bin/env python3
"""DB Executor - 薄 shim，re-export badou-md-common 实现。

保留此文件以兼容现有文档（CLAUDE.md / SKILL.md）中对
.claude/skills/backend-module-generator/db_executor.py 的引用。
实际逻辑见 badou_md_common.db_executor。

D27：main() 改用 resolve_db_config() 的 3 层 fallback 链；--config-from-brain 路径行为不变。
"""
import os
import sys
import argparse

_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "badou-md-common")
_BADOU_CODING_COMMON = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common")
)
for p in (_COMMON, _BADOU_CODING_COMMON):
    if p not in sys.path:
        sys.path.insert(0, p)

from badou_md_common.db_executor import (  # noqa: E401
    split_sql_statements,
    execute_sql_file,
    parse_brain_markdown,
    load_config,
)
from badou_md_common.db_executor import resolve_db_config  # D27 — type: ignore[attr-defined]
from badou_md_common.db_config_resolver_shim import ConfigNotFoundError  # D27

# 保留 CLI 入口（行为与原 db_executor.py main() 一致，新增 D27 fallback）
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PyMySQL 多语句 SQL 执行器")
    parser.add_argument("sql_file", help="SQL 文件路径")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--db")
    parser.add_argument("--user")
    parser.add_argument("--password")
    parser.add_argument("--config", "-c")
    parser.add_argument("--config-from-brain")
    parser.add_argument("--project-root", default=".",
                        help="D27: 项目根目录（含 .trellis/ 或 backend/），供 fallback 使用")
    parser.add_argument("--no-interactive", action="store_true",
                        help="D27: 关闭 input() 询问 fallback")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not os.path.isfile(args.sql_file):
        print(f"❌ SQL 文件不存在: {args.sql_file}")
        sys.exit(1)

    # D27：解析 DB 配置 — 4 步 fallback
    try:
        resolved = resolve_db_config(
            project_root=args.project_root,
            explicit_config=args.config_from_brain or args.config,
            interactive=not args.no_interactive,
        )
    except ConfigNotFoundError as exc:
        print(f"❌ {exc}")
        sys.exit(1)
    db_config: dict = dict(resolved.get("database", {}))
    source = resolved.get("source", "?")
    print(f"✅ DB 配置已解析（source={source}）")

    # CLI 显式参数仍然覆盖任何 fallback 结果（向后兼容）
    if args.host:
        db_config["host"] = args.host
    if args.port:
        db_config["port"] = str(args.port)
    if args.db:
        db_config["name"] = args.db
    if args.user:
        db_config["user"] = args.user
    if args.password:
        db_config["password"] = args.password

    if not db_config.get("host"):
        print("❌ 未提供数据库连接信息")
        sys.exit(1)
    sys.exit(0 if execute_sql_file(args.sql_file, db_config, dry_run=args.dry_run) else 1)
