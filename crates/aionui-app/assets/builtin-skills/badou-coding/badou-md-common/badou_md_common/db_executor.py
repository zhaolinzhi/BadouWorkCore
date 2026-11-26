"""SQL 执行器 + PROJECT-BRAIN 解析（家族共享）。

从原 badou-md-crud-generator-skill/db_executor.py 迁入，行为不变。

D27: 新增 `db_config_resolver` shim，导出 3 层 fallback 的 resolve_db_config。
"""
import json
import os
import re
import sys

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


# D27 shim：让 badou_md_common.db_executor.resolve_db_config 同样可用
# 实现位于 badou-coding/common/db_config_resolver.py（旧 db_executor.py 直接 re-export）
def __getattr__(name: str):  # PEP 562 — 延迟导入避免循环
    if name == "resolve_db_config":
        from .db_config_resolver_shim import resolve_db_config as _rc
        return _rc
    raise AttributeError(f"module 'badou_md_common.db_executor' has no attribute {name!r}")


__all__ = [
    "parse_brain_markdown",
    "load_config",
    "split_sql_statements",
    "execute_sql_file",
    "resolve_db_config",  # D27
    "PYMYSQL_AVAILABLE",
]  # noqa


def parse_brain_markdown(brain_path: str) -> dict:
    """从 PROJECT-BRAIN.md 解析数据库连接信息（database 段）。"""
    def _extract(pattern, section, key):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip().strip("'\"`<> \t")
            if section not in config:
                config[section] = {}
            config[section][key] = val

    with open(brain_path, "r", encoding="utf-8") as f:
        text = f.read()

    config = {"database": {}}
    _extract(r"(?:IP|Host|主机)[\s：:]+(\d+\.\d+\.\d+\.\d+)", "database", "host")
    _extract(r"(?:端口|Port)[\s：:]+\s*(\d+)", "database", "port")
    _extract(r"数据库(?:名)?[\s：:]+\s*(\S+)", "database", "name")
    _extract(r"(?:账号|用户名|用户|User)[\s：:]+\s*(\S+)", "database", "user")
    _extract(r"(?:密码|Password)[\s：:]+\s*(\S+)", "database", "password")
    return config


def load_config(config_path: str) -> dict:
    """加载 crud-config.json。"""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def split_sql_statements(sql_text: str) -> list[str]:
    """状态机分割多语句 SQL，处理引号/反引号/行注释/块注释。"""
    statements = []
    current = []
    i = 0
    n = len(sql_text)
    in_single_quote = False
    in_double_quote = False
    in_backtick = False
    in_line_comment = False
    in_block_comment = False

    while i < n:
        ch = sql_text[i]

        if in_block_comment:
            current.append(ch)
            if ch == '*' and i + 1 < n and sql_text[i + 1] == '/':
                current.append('/')
                i += 2
                in_block_comment = False
                continue
            i += 1
            continue

        if in_line_comment:
            current.append(ch)
            if ch == '\n':
                in_line_comment = False
            i += 1
            continue

        if ch == "'" and not in_double_quote and not in_backtick:
            in_single_quote = not in_single_quote
            current.append(ch)
            i += 1
            continue
        if ch == '"' and not in_single_quote and not in_backtick:
            in_double_quote = not in_double_quote
            current.append(ch)
            i += 1
            continue
        if ch == '`' and not in_single_quote and not in_double_quote:
            in_backtick = not in_backtick
            current.append(ch)
            i += 1
            continue

        if in_single_quote or in_double_quote or in_backtick:
            if ch == '\\' and i + 1 < n:
                current.append(ch)
                current.append(sql_text[i + 1])
                i += 2
                continue
            current.append(ch)
            i += 1
            continue

        if ch == '-' and i + 1 < n and sql_text[i + 1] == '-':
            in_line_comment = True
            current.append(ch)
            current.append('-')
            i += 2
            continue
        if ch == '/' and i + 1 < n and sql_text[i + 1] == '*':
            in_block_comment = True
            current.append(ch)
            current.append('*')
            i += 2
            continue

        if ch == ';':
            current.append(ch)
            stmt = ''.join(current).strip()
            if stmt and stmt != ';':
                statements.append(stmt)
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    remaining = ''.join(current).strip()
    if remaining:
        statements.append(remaining)
    return statements


def execute_sql_file(sql_path: str, db_config: dict, dry_run: bool = False) -> bool:
    """单连接逐条执行 SQL，保留 MySQL 用户变量。"""
    if not PYMYSQL_AVAILABLE:
        print("❌ pymysql 未安装，请执行: pip install pymysql")
        return False

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_text = f.read()

    statements = split_sql_statements(sql_text)
    print(f"📋 共解析 {len(statements)} 条 SQL 语句")
    print(f"📁 文件: {sql_path}")

    if dry_run:
        print("\n📄 语句预览 (前10条):")
        for i, stmt in enumerate(statements[:10]):
            preview = stmt[:120].replace('\n', ' ')
            print(f"  [{i+1}] {preview}...")
        if len(statements) > 10:
            print(f"  ... 还有 {len(statements) - 10} 条")
        return True

    host = db_config.get("host", "127.0.0.1")
    port = int(db_config.get("port", 3306))
    user = db_config.get("user", "root")
    password = db_config.get("password", "")
    database = db_config.get("name", "")

    conn = None
    try:
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password,
            database=database, charset="utf8mb4", autocommit=False,
        )
        print(f"✅ 数据库连接成功: {host}:{port}/{database}")
        cursor = conn.cursor()
        executed = 0
        errors = 0
        for i, stmt in enumerate(statements, 1):
            try:
                cursor.execute(stmt)
                executed += 1
                if i % 10 == 0 or i == len(statements):
                    print(f"  ✓ 已执行 {i}/{len(statements)} 条语句")
            except pymysql.Error as e:
                if "DROP TABLE" in stmt and "doesn't exist" in str(e).lower():
                    executed += 1
                    continue
                if ("DELETE FROM" in stmt or "DROP TABLE" in stmt):
                    error_code = getattr(e, 'args', [None])[0] if hasattr(e, 'args') else None
                    if isinstance(error_code, int) and error_code in (1051, 1146):
                        print(f"  ⚠  [{i}] 跳过 (表/resource 不存在): {str(e)[:80]}")
                        executed += 1
                        continue
                errors += 1
                print(f"  ❌ [{i}] 执行失败: {str(e)[:150]}")
                print(f"     SQL: {stmt[:200]}")
        if errors > 0:
            print(f"\n⚠️  执行完成但有 {errors} 个错误，回滚中...")
            conn.rollback()
            return False
        conn.commit()
        print(f"\n✅ 全部执行成功: {executed}/{len(statements)} 条语句")
        return True
    except pymysql.Error as e:
        print(f"\n❌ 数据库连接/执行异常: {e}")
        return False
    finally:
        if conn:
            conn.close()
