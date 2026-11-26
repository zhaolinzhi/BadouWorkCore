"""CRUD Generator - Base utilities: string conversion helpers"""
from __future__ import annotations


def _to_camel_case(snake_str: str) -> str:
    """将 snake_case / UPPER_SNAKE 字符串转为 camelCase。

    ⚠️ 修复 issue #1: 先把整段 lower 化再 split，避免 FLOW_ID → FLOWId 的残留大写。
    支持的输入形式：
      - snake_case:        leave_type           → leaveType
      - UPPER_SNAKE_CASE:  FLOW_ID              → flowId
      - 单段首字母大写:    Id                   → id
    """
    parts = snake_str.lower().split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def _to_pascal_case(snake_str: str) -> str:
    return "".join(p.title() for p in snake_str.lower().split("_"))
