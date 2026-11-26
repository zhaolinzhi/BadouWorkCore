"""DB 配置解析器：3 层 fallback。

来源链（顺序）：
1. explicit_config：调用方直接传入的路径（--config-from-brain，brain/crud-config 二选一）
2. PROJECT-BRAIN.md：<project_root>/.trellis/PROJECT-BRAIN.md
3. backend/pom.xml + application*.yml/properties（Spring Boot fallback）
4. 交互式询问（仅当 interactive=True 且 stdin tty 可用）

设计原则：
- **不引入新依赖**：yml 用最简正则手写解析、properties 用 configparser（stdlib）、pom 用 xml.etree（stdlib）
- **互不污染**：每层独立 try/except，失败不影响下一层
- **可测**：所有 IO 通过 tempfile + monkeypatch，input() 通过 input_fn 参数注入

新增于 D27。已存在的 parse_brain_markdown / load_config 不删，保留作内部实现。
"""
from __future__ import annotations

import configparser
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable, Optional


class ConfigNotFoundError(RuntimeError):
    """所有 fallback 链都耗尽后抛出。"""


# ─────────────────────────────────────────────────────────────────────────────
# Source 1: PROJECT-BRAIN.md（已存在的解析逻辑，直接复用）
# ─────────────────────────────────────────────────────────────────────────────

def _try_brain(project_root: Path) -> tuple[dict | None, str]:
    """在 project_root/.trellis/PROJECT-BRAIN.md 查找 DB 配置。

    使用 badou_md_common.config_loader.parse_brain_markdown 完整版（database + system + project）。
    """
    brain = project_root / ".trellis" / "PROJECT-BRAIN.md"
    if not brain.is_file():
        return None, ""
    try:
        from badou_md_common.config_loader import parse_brain_markdown  # 延迟 import 可测
    except ImportError:  # pragma: no cover - 安全网
        return None, ""

    cfg = parse_brain_markdown(str(brain))
    db = cfg.get("database") or {}
    if not db.get("host"):
        return None, ""
    # 归一化 port → int
    if "port" in db:
        try:
            db["port"] = int(db["port"])
        except (TypeError, ValueError):
            db.pop("port", None)
    return db, "brain"


# ─────────────────────────────────────────────────────────────────────────────
# Source 2: backend/pom.xml + application*.yml/properties
# ─────────────────────────────────────────────────────────────────────────────

_POM_ARTIFACT_RE = re.compile(r"<artifactId>([^<]+)</artifactId>")
_YML_DS_RE = re.compile(r"^\s*(spring:|\.\.\.|---|\s*spring\s*:\s*$)", re.MULTILINE)


def _looks_like_spring_boot_pom(pom_path: Path) -> bool:
    """粗略判断 pom.xml 是不是 Spring Boot 项目。

    启发式：含 <artifactId>spring-boot-starter-*</artifactId> 父类即可。
    """
    try:
        text = pom_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return bool(re.search(r"<artifactId>spring-boot-starter", text))


def _parse_simple_yml(text: str) -> dict:
    """最简 yaml 解析：仅支持 spring.datasource.{url,username,password,driver-class-name}。

    实现策略：用 2 个空格缩进的 key:value 字典，dot 连接 key。
    不依赖 PyYAML；显式忽略注释 / 多行字符串 / 锚点（足够 Spring datasource）。
    """
    result: dict = {}
    stack: list[tuple[int, dict]] = [(-1, result)]

    for raw in text.splitlines():
        # 跳过空行 + 注释 + 文档分隔符
        stripped = raw.rstrip()
        if not stripped or stripped.lstrip().startswith("#") or stripped.strip() == "---":
            continue

        # 算缩进
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, value = stripped.lstrip().partition(":")
        value = value.strip()
        if not key:
            continue

        # 弹栈直到找到当前 indent 的父节点
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not stack:
            stack = [(-1, result)]

        parent = stack[-1][1]

        if value == "":
            # 嵌套 dict
            new_dict: dict = {}
            parent[key] = new_dict
            stack.append((indent, new_dict))
        else:
            # 简单标量；剥最外层引号
            parent[key] = _strip_scalar(value)

    return result


def _strip_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _collect_application_configs(backend_dir: Path) -> list[Path]:
    """收集 src/main/resources/application*.{yml,properties}，按优先级排序。

    application.yml > application-{profile}.yml > application.properties > application-{profile}.properties
    """
    res_dir = backend_dir / "src" / "main" / "resources"
    if not res_dir.is_dir():
        return []
    found: list[Path] = []
    for ext in ("yml", "yaml", "properties"):
        for path in sorted(res_dir.glob(f"application*.{ext}")):
            # 优先无 profile 版本
            found.append(path)
    # 排序：application.{ext} (no profile) 优先，其次按文件名长度，再按字典序
    def _key(p: Path) -> tuple[int, int, str]:
        name = p.name
        is_base = name.startswith("application.") and not name[len("application."):-len(p.suffix.lstrip('.'))].count("-")
        return (0 if is_base else 1, len(name), name)
    found.sort(key=_key)
    return found


def _extract_datasource(config_text: str, suffix: str) -> dict | None:
    """从 yml/properties 文本中提取 spring.datasource.* 段。

    yml 用 _parse_simple_yml；properties 用 configparser。
    """
    if suffix in ("yml", "yaml"):
        doc = _parse_simple_yml(config_text)
        spring = doc.get("spring") or {}
        ds = spring.get("datasource") or {}
    else:  # properties
        cp = configparser.ConfigParser()
        # configparser 默认要求 [section]；properties 没有 section 时用 _default_ 模拟
        cp.read_string("[default]\n" + config_text)
        ds = dict(cp.items("default"))
        # 还原 spring.datasource.url → spring:datasource:url
        ds = {k.replace(".", ":"): v for k, v in ds.items()}
        spring = {}
        ds_section = ds.get("spring:datasource")
        # properties 风格不支持嵌套 dict；用 key 前缀扫描
        ds = {
            k.split(":")[-1]: v
            for k, v in ds.items()
            if k.startswith("spring:datasource:")
        }

    url = ds.get("url")
    username = ds.get("username")
    password = ds.get("password")
    driver = ds.get("driver-class-name")
    if not url:
        return None

    # jdbc:mysql://host:port/dbname → host/port/name
    out = {
        "driver": driver or "com.mysql.cj.jdbc.Driver",
    }
    m = re.match(r"jdbc:mysql://([^:/]+):?(\d+)?(/(\S+))?", url)
    if m:
        out["host"] = m.group(1)
        if m.group(2):
            out["port"] = int(m.group(2))
        if m.group(4):
            out["name"] = m.group(4).split("?")[0]
    else:
        # 非 MySQL / 格式未知：保留 url，由调用方决定
        out["host"] = "127.0.0.1"
        out["port"] = 3306
        out["name"] = ""
        out["url"] = url

    if username:
        out["user"] = username
    if password is not None:
        out["password"] = password
    return out


def _try_pom_and_yml(project_root: Path) -> tuple[dict | None, str]:
    """从 backend/pom.xml + application*.yml 提取 DB 配置。"""
    backend = project_root / "backend"
    pom = backend / "pom.xml"
    if not pom.is_file() or not _looks_like_spring_boot_pom(pom):
        return None, ""

    candidates = _collect_application_configs(backend)
    if not candidates:
        return None, ""

    # 取第一个含 spring.datasource.url 的文件
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        suffix = path.suffix.lstrip(".")
        ds = _extract_datasource(text, suffix)
        if ds:
            return ds, "pom"
    return None, ""


# ─────────────────────────────────────────────────────────────────────────────
# Source 4: 交互式询问（input_fn 可注入，便于测试）
# ─────────────────────────────────────────────────────────────────────────────

def _ask_interactive(input_fn: Callable[[str], str] = input) -> dict:
    """通过 stdin 询问用户输入 DB 配置。"""
    def _ask(prompt: str, default: str = "") -> str:
        suffix = f" [{default}]" if default else ""
        try:
            val = input_fn(f"{prompt}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt) as exc:
            raise ConfigNotFoundError("用户取消输入") from exc
        return val or default

    host = _ask("数据库 host", "127.0.0.1")
    port_str = _ask("数据库 port", "3306")
    name = _ask("数据库名", "")
    user = _ask("用户名", "root")
    password = _ask("密码", "")
    try:
        port = int(port_str)
    except ValueError as exc:
        raise ConfigNotFoundError(f"port 不是整数: {port_str}") from exc
    return {
        "host": host,
        "port": port,
        "name": name,
        "user": user,
        "password": password,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 公共入口
# ─────────────────────────────────────────────────────────────────────────────

def resolve_db_config(
    project_root: Path | str,
    explicit_config: Optional[Path | str] = None,
    interactive: bool = True,
    input_fn: Callable[[str], str] = input,
) -> dict:
    """3 层 fallback + 询问用户，返回 DB 配置。

    :param project_root: 项目根目录（含 .trellis/ 或 backend/）
    :param explicit_config: 调用方直接传入的 brain/crud-config 路径（CLI 参数 --config-from-brain）
    :param interactive: 启用 input() 询问作为最后 fallback；CI 应设为 False
    :param input_fn: 可注入的 input 函数（测试用）
    :returns: ``{"database": {...}, "source": "brain|pom|interactive|explicit", "extras": {...}}``
    :raises ConfigNotFoundError: 全部 fallback 失败且 interactive=False
    """
    project_root = Path(project_root)

    # 1. explicit —— 直接路径
    if explicit_config is not None:
        cfg_path = Path(explicit_config)
        if cfg_path.is_file():
            try:
                from badou_md_common.config_loader import parse_brain_markdown
                cfg = parse_brain_markdown(str(cfg_path))
                db = cfg.get("database") or {}
                if db.get("host"):
                    return {
                        "database": db,
                        "source": "explicit",
                        "extras": {k: v for k, v in cfg.items() if k != "database"},
                    }
            except Exception:
                pass  # 继续 fallback

    # 2. PROJECT-BRAIN.md
    db, src = _try_brain(project_root)
    if db and db.get("host"):
        return {"database": db, "source": src, "extras": {}}

    # 3. backend/pom.xml + application*.yml
    db, src = _try_pom_and_yml(project_root)
    if db and db.get("host"):
        return {"database": db, "source": src, "extras": {}}

    # 4. 交互式
    if interactive:
        # 当调用方显式提供 input_fn（非默认 input()）时：信任调用方，跳过 tty 探测
        # ——便于测试，也避免 pipe 场景下被阻塞。
        _uses_custom_input = input_fn is not input
        try:
            if _uses_custom_input or (sys.stdin is not None and sys.stdin.isatty()):
                db = _ask_interactive(input_fn=input_fn)
                return {"database": db, "source": "interactive", "extras": {}}
        except (ConfigNotFoundError, OSError):
            pass

    raise ConfigNotFoundError(
        f"无法解析 DB 配置：project_root={project_root} 下既无 "
        f".trellis/PROJECT-BRAIN.md，也无 backend/pom.xml+application*.yml；"
        f"且 {'interactive=False 禁止询问' if not interactive else 'stdin 非 tty'}"
    )


__all__ = [
    "ConfigNotFoundError",
    "resolve_db_config",
    "_try_brain",
    "_try_pom_and_yml",
    "_parse_simple_yml",
]
