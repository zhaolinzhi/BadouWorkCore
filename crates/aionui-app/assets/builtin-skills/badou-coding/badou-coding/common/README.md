# md 通用规则索引（Single Source of Truth）

> **职责**：所有 md_* 表的配置项矩阵 + generator 写入策略 + 变更敏感度 + updater 兼容矩阵
> **来源**：派生自 `.claude/docs/backend/database/ddl/module/md_*.md`（物理 schema）
> **使用者**：`skills/backend-module-generator/rules/*.md` 与 `skills/backend-module-updater/update_rules/*.md`

## 文件清单

| 文件 | 覆盖表 | 详/简 | 列数 |
|---|---|---|---|
| `md_module.md` | md_module | 详 | 46 |
| `md_field.md` | md_field | 详 | 21 |
| `md_form.md` | md_form | 详 | 52 |
| `md_flow.md` | md_flow | 详 | 6 |
| `md_module_link.md` | md_module_link | 详 | 20 |
| `md_button.md` | md_button | 简 | 25 |
| `md_database.md` | md_database | 简 | 15 |

> md_module_type（11 列）**不抽取**：generator 不写入此表（`module_gen.py` 硬编码 `m_t_id = '40282b815b6f9ac5015b7052f35d0008'`）。

## 每个 md_*.md 结构

1. **表概述**：用途、行数、与 generator 关系、关键含义
2. **schema 概览**：引用物理 DDL 文档
3. **配置项矩阵**：列名 / 类型 / generator 写入策略 / 用户 JSON 提供方式 / 默认值 / 合法值范围 / 变更敏感度
4. **updater 兼容矩阵**：metadata-only / ddl-safe / ddl-risky / forbidden

## 维护流程

1. brainstorming 阶段发现需要扩展 md_* 配置项 → **先改 common/md_*.md**
2. generator / updater rules 同步引用（人工）
3. `tests/test_md_config_consistency.py` 验证三方一致

## 不属于本目录

- 物理 schema 定义（见 `.claude/docs/backend/database/ddl/module/md_*.md`）
- generator / updater 行为规则（见各自 rules/）
