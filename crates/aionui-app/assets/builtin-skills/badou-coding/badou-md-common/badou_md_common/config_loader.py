"""配置加载（家族共享）。

提供：
- parse_brain_markdown：完整版（database + system + project），来自 crud_generator.py
- load_config：加载 crud-config.json
- load_dotreillis_db_config：加载 .trellis/.db-config.json（校验器与流程生成共用）
"""
import json
import os
import re
import sys


def _extract(text: str, config: dict, pattern: str, section: str, key: str) -> None:
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        val = m.group(1).strip().strip("'\"`<> \t")
        if section not in config:
            config[section] = {}
        config[section][key] = val


def parse_brain_markdown(brain_path: str) -> dict:
    """从 PROJECT-BRAIN.md 解析项目配置（完整版：database + system + project）。"""
    with open(brain_path, "r", encoding="utf-8") as f:
        text = f.read()

    config = {"project": {}, "system": {}, "database": {}}
    _extract(text, config, r"(?:IP|Host|主机)[\s：:]+(\d+\.\d+\.\d+\.\d+)", "database", "host")
    _extract(text, config, r"(?:端口|Port)[\s：:]+\s*(\d+)", "database", "port")
    _extract(text, config, r"数据库(?:名)?[\s：:]+\s*(\S+)", "database", "name")
    _extract(text, config, r"(?:账号|用户名|用户|User)[\s：:]+\s*(\S+)", "database", "user")
    _extract(text, config, r"(?:密码|Password)[\s：:]+\s*(\S+)", "database", "password")
    _extract(text, config, r"data[._]source[._]code[\s：:]+\s*(\S{2,})", "system", "data_source_code")
    _extract(text, config, r"creator[\s：:]+[^A-Z\n]*?(U\d{4,})", "system", "creator_id")
    _extract(text, config, r"creator[._]?name[\s：:]+\s*(\S{2,20})", "system", "creator_name")
    _extract(text, config, r"package[._]name[\s：:]+\s*(\S+)", "project", "package_name")
    if not config["project"].get("package_name"):
        m = re.search(r"com\.\w+(?:\.\w+)*", text)
        if m:
            config["project"]["package_name"] = m.group(0)
    config = {k: v for k, v in config.items() if v}
    return config


def load_config(config_path: str) -> dict:
    """加载 crud-config.json。"""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dotreillis_db_config(start_dir: str) -> dict | None:
    """从 start_dir 向上查找 .trellis/.db-config.json。

    校验器（idempotent_check）与流程生成（generate_flow）共用此加载逻辑。
    """
    paths = [
        os.path.join(start_dir, '..', '.trellis', '.db-config.json'),
        os.path.join(start_dir, '..', '..', '.trellis', '.db-config.json'),
    ]
    for p in paths:
        p = os.path.abspath(p)
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return None
