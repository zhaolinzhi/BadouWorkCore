"""校验器骨架（家族共享）：DB 访问 + 结果收集。"""
import json
import os
import sys

TTY_RED = "\033[91m"
TTY_GREEN = "\033[92m"
TTY_YELLOW = "\033[93m"
TTY_CYAN = "\033[96m"
TTY_RESET = "\033[0m"


class DB:
    """数据库连接（查询/执行）。配置查找：技能 config/db_config.json -> .trellis/.db-config.json。"""

    def __init__(self, skill_dir: str):
        config = self._load_config(skill_dir)
        self.host = config["host"]
        self.port = config["port"]
        self.user = config["user"]
        self.password = config["password"]
        self.database = config["database"]
        self._conn = None

    def _load_config(self, skill_dir: str) -> dict:
        paths = [
            os.path.join(skill_dir, "config", "db_config.json"),
            os.path.join(skill_dir, "..", ".trellis", ".db-config.json"),
            os.path.join(skill_dir, "..", "..", ".trellis", ".db-config.json"),
        ]
        for p in paths:
            p = os.path.abspath(p)
            if os.path.exists(p):
                with open(p) as f:
                    cfg = json.load(f)
                # 支持 password_env 从环境变量读密码
                if "password_env" in cfg and "password" not in cfg:
                    env_name = cfg.pop("password_env")
                    cfg["password"] = os.environ.get(env_name, "")
                return cfg
        print(f"{TTY_RED}❌ 未找到数据库配置文件{TTY_RESET}", file=sys.stderr)
        sys.exit(1)

    def query(self, sql: str) -> list[dict]:
        import pymysql
        conn = pymysql.connect(
            host=self.host, port=self.port, user=self.user,
            password=self.password, database=self.database,
            cursorclass=pymysql.cursors.DictCursor,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                return cur.fetchall()
        finally:
            conn.close()

    def execute(self, sql: str) -> int:
        import pymysql
        conn = pymysql.connect(
            host=self.host, port=self.port, user=self.user,
            password=self.password, database=self.database,
        )
        try:
            with conn.cursor() as cur:
                affected = cur.execute(sql)
                conn.commit()
                return affected
        finally:
            conn.close()


class CheckResult:
    """校验结果收集器。"""

    def __init__(self):
        self.passed: list[str] = []
        self.failed: list[str] = []
        self.skipped: list[str] = []

    def ok(self, msg: str):
        self.passed.append(msg)
        print(f"  {TTY_GREEN}✅{TTY_RESET} {msg}")

    def fail(self, msg: str):
        self.failed.append(msg)
        print(f"  {TTY_RED}❌{TTY_RESET} {msg}")

    def skip(self, msg: str):
        self.skipped.append(msg)
        print(f"  {TTY_YELLOW}⏭️ {TTY_RESET}{msg}")

    def summary(self) -> str:
        total = len(self.passed) + len(self.failed)
        return f"通过 {len(self.passed)}/{total}，失败 {len(self.failed)}"

    def is_pass(self) -> bool:
        return len(self.failed) == 0
