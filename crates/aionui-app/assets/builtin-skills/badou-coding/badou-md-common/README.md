# badou-md-common

`badou-md-*` 技能家族共享库（非技能，无 SKILL.md）。提供：

| 模块 | 内容 |
|---|---|
| `badou_md_common.db_executor` | `split_sql_statements` / `execute_sql_file` / `parse_brain_markdown`(精简) / `load_config` |
| `badou_md_common.config_loader` | `parse_brain_markdown`(完整) / `load_config` / `load_dotreillis_db_config` |
| `badou_md_common.validator_core` | `DB` / `CheckResult` |

## 导入方式

技能脚本顶部：
```python
import os, sys
_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "badou-md-common")
if _COMMON not in sys.path:
    sys.path.insert(0, _COMMON)
from badou_md_common.db_executor import split_sql_statements
```

## 版本

v1.0.0（2026-07-09 从 badou-md-crud-generator-skill 抽出）
