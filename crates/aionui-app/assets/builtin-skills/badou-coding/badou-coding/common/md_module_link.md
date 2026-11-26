# md_module_link 配置项矩阵

> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_module_link.md`
> **覆盖**：20 列
> **详/简**：详

## §1 表概述

- **用途**：存储模块间关联关系（一对多 / 多对一 / 多对多）；详情页 tab 展示
- **与 generator 关系**：`relation_gen.py` 写入；关联 SQL 独立到 `output/<mdCode>/_relation.sql`，必须在所有 create.sql 之后执行
- **关键含义**：关联表产生附加展示规则，不改主表；缺关联 tab 时前端 detail 页只能展示主表自身字段

## §2 配置项矩阵

| 列名 | 类型 | 写入策略 | 用户提供 | 默认 | 合法值 | 敏感度 |
|------|------|---------|---------|------|--------|--------|
| `id` | varchar(64) | auto-inject | — | UUID | UUID | metadata-only |
| `field_name` | varchar(128) | user-required | `relations[].field_name` | — | 主模块端关联字段 | forbidden |
| `field_id` | varchar(64) | auto-inject | — | `(SELECT ID FROM md_field WHERE module_id=... AND field_name=...)` | UUID | metadata-only |
| `module_id` | varchar(64) | auto-inject | — | 当前 module.id | UUID | forbidden |
| `related_module_id` | varchar(64) | user-required | `relations[].related_module.code` | — | 子模块 UUID | ddl-safe（schema 无 FK）|
| `related_table` | varchar(128) | user-required | `relations[].related_table` | — | 子模块表名 | metadata-only |
| `related_field` | varchar(128) | user-required | `relations[].related_field` | — | 子模块端关联字段 | metadata-only |
| `type` | int(11) | user-required | `relations[].type` | — | 1=1:N / 2=N:1 / 3=N:N | metadata-only |
| `show_type` | varchar(64) | user-optional | `relations[].show_type` | tab | tab/grid/modal | metadata-only |
| `sort_num` | int(11) | user-optional | `relations[].sort_num` | 数组顺序 | 整数 | metadata-only |
| `display_name` | varchar(256) | user-optional | `relations[].display_name` | — | 中文 tab 名 | metadata-only |
| `parent_field` | varchar(128) | user-optional（N:N） | `relations[].parent_field` | — | 父端字段 | metadata-only |
| `create_time` / `update_time` | date | auto-inject | — | NOW | — | metadata-only |
| `creator` / `updator` | varchar | auto-inject | — | 当前用户 | — | metadata-only |

> 完整 20 列参考物理 DDL 文档。

## §3 updater 兼容矩阵

| 变更类型 | 行为 | DDL |
|---|---|---|
| 加 relation（relations 数组新增）| ddl-safe | INSERT md_module_link + 重生成关联 SQL |
| 删 relation | metadata-only | DELETE md_module_link + 重生成关联 SQL |
| 改 field_name / related_* / type / show_type | metadata-only | DELETE + INSERT md_module_link 全量 |

## 📎 引用

- 物理 schema：`.claude/docs/backend/database/ddl/module/md_module_link.md`
- generator rule：`.claude/skills/badou-coding/skills/backend-module-generator/rules/module-link.md`
- updater rule：`.claude/skills/badou-coding/skills/backend-module-updater/update_rules/relation-change.md`
