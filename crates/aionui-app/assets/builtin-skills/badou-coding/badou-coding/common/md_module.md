# md_module 配置项矩阵

> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_module.md`
> **覆盖**：46 列
> **详/简**：详

## §1 表概述

- **用途**：存储 MD 模块驱动架构中的模型定义；每行 = 一个 CRUD 模块
- **与 generator 关系**：`module_gen.py` INSERT 主数据；`flow_integration.py` 流程场景下 UPDATE flow_id/flow_business_name
- **关键含义**：MD 体系「头表」，其他 md_* 都通过 module_id 关联

## §2 配置项矩阵

> 列名 | 类型 | generator 写入 | 用户 JSON | 默认值 | 合法值 | 变更敏感度

| 列名 | 类型 | 写入策略 | 用户提供 | 默认 | 合法值 | 敏感度 |
|------|------|---------|---------|------|--------|--------|
| `id` | varchar(64) | auto-inject | — | UUID | UUID | metadata-only |
| `db_table` | varchar(64) | user-required | `module.db_table` | — | 业务表名 | ddl-safe |
| `code` | varchar(64) | user-required | `module.code` | — | `[a-z][a-z0-9_]*` | forbidden（code 是身份，改=重建） |
| `name` | varchar(256) | user-required | `module.name_cn` | — | 中文名 | metadata-only |
| `module_name` | varchar(64) | derived | — | = code 首字母大写 | 同 code | metadata-only |
| `english_name` | varchar(128) | user-optional | `module.english_name` | — | 英文名 | metadata-only |
| `pri_key` | varchar(256) | auto-inject | — | `id` | 字段名 | metadata-only |
| `m_t_id` | varchar(64) | auto-inject | — | `40282b815b6f9ac5015b7052f35d0008` | UUID（对应 `busi`） | forbidden |
| `data_source_id` | varchar(64) | auto-inject | — | `(SELECT id FROM md_database WHERE code='projectDatabase')` | UUID | metadata-only |
| `menu_resource_code` | varchar(64) | user-optional | `module.menu_resource_code` | — | 资源编码 | metadata-only |
| `base_class` | varchar(256) | user-optional | `module.base_class` | `BusinessEntity` | Java class FQN | metadata-only |
| `description` | varchar(512) | user-optional | `module.description` | — | 描述 | metadata-only |
| `list_js` | varchar(256) | user-optional | `module.list_js` | — | JS 文件路径 | metadata-only |
| `form_js` | varchar(256) | user-optional | `module.form_js` | — | JS 文件路径 | metadata-only |
| `view_js` | varchar(256) | user-optional | `module.view_js` | — | JS 文件路径 | metadata-only |
| `flow_id` | varchar(64) | auto-inject（flow_code 非空时） | — | `(SELECT id FROM flw_flow WHERE code=...)` | UUID | metadata-only（SET NULL 也允许）|
| `flow_business_name` | varchar(128) | user-optional（flow_code 非空时） | `module.flow_business_name_field` | — | 字段名 | metadata-only |
| `create_time` / `update_time` | date | auto-inject | — | NOW | — | metadata-only |
| `creator` / `creator_name` / `updator` / `updator_name` | varchar | auto-inject | — | 当前用户 | — | metadata-only |
| `flg_deleted` | int(11) | auto-inject | — | 0 | 0/1 | metadata-only |

> 完整 46 列参考物理 DDL 文档；上表列出 generator / updater 主要关注的列。

## §3 updater 兼容矩阵

| 变更类型 | 行为 | DDL |
|---|---|---|
| 改 `code` | **forbidden**（等同于重建模块；要求 `--mode=rebuild` flag + 用户确认）| DROP 旧 + CREATE 新 |
| 改 `db_table` | ddl-safe（业务表重命名）| `RENAME TABLE` |
| 改 `name` / `description` / `menu_resource_code` / `base_class` / `list_js` / `form_js` / `view_js` | metadata-only | UPDATE md_module |
| 改 `flow_id`（flow_code 加/去/改）| metadata-only | 调 backend-flow-engine；UPDATE md_module.flow_id |
| 改 `m_t_id` / `data_source_id` | forbidden | — |

## 📎 引用

- 物理 schema：`.claude/docs/backend/database/ddl/module/md_module.md`
- generator rule：`.claude/skills/badou-coding/skills/backend-module-generator/rules/module-config.md`
- updater rule：`.claude/skills/badou-coding/skills/backend-module-updater/update_rules/module-basic-config.md`