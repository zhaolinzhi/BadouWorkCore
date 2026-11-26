"""D27 shim — 让 ``badou_md_common.db_executor.resolve_db_config`` 可用。

实现已迁入 ``badou-coding/common/db_config_resolver.py``；本 shim 仅做 import path 兼容。
非空 reason：旧 db_executor.py / db_executor shim 用 ``from badou_md_common.db_executor import ...``，
D27 重构后保留同路径。
"""
from pathlib import Path
from typing import Callable, Optional

# badou-coding/common/ 在 badou_md_common 内属于 sibling package。
# 用文件路径解析 sys.path，避免依赖安装顺序。
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BADOU_CODING_COMMON = os.path.normpath(os.path.join(_HERE, "..", "..", "badou-coding", "common"))
if _BADOU_CODING_COMMON not in sys.path:
    sys.path.insert(0, _BADOU_CODING_COMMON)

from db_config_resolver import (  # noqa: E402
    ConfigNotFoundError,
    resolve_db_config as _resolve,
)


def resolve_db_config(
    project_root: Path | str,
    explicit_config: Optional[Path | str] = None,
    interactive: bool = True,
    input_fn: Callable[[str], str] = input,
) -> dict:
    """兼容封装，文档见 ``badou-coding/common/db_config_resolver.py``。"""
    return _resolve(
        project_root=project_root,
        explicit_config=explicit_config,
        interactive=interactive,
        input_fn=input_fn,
    )


__all__ = ["ConfigNotFoundError", "resolve_db_config"]
