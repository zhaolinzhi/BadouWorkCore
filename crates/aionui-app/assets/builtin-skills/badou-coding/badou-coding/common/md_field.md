# md_field 配置项矩阵

> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_field.md`
> **覆盖**：21 列
> **详/简**：详

## §1 表概述

- **用途**：存储每个模块的字段元数据；一行 = 一个业务字段
- **与 generator 关系**：`field_gen.py` 写入业务字段；`system_fields.py` 注入 8 个系统字段；流程场景注入 BO_STATUS
- **关键含义**：md_field 描述字段 schema 维度（类型/长度/校验），与 md_form 配对

## §2 配置项矩阵

| 列名 | 类型 | 写入策略 | 用户提供 | 默认 | 合法值 | 敏感度 |
|------|------|---------|---------|------|--------|--------|
| `ID` | varchar(64) | auto-inject | — | UUID | UUID | metadata-only |
| `module_id` | varchar(64) | auto-inject | — | UUID | UUID | metadata-only |
| `field_name` | varchar(64) | user-required | `fields[].field_name` | — | `[a-z][a-z0-9_]*`, ≤30 | forbidden（field_name 是身份） |
| `comments` | varchar(1024) | user-required | `fields[].comment` | — | 中文 | metadata-only |
| `validation_rule` | varchar(2048) | user-optional | `fields[].regex_rule` | — | 正则字符串 | metadata-only |
| `length` | int(11) | user-required（varchar/text 除外） | `fields[].length` | 64（主外键）/ 50-200 | 整数 | **ddl-risky**（缩小 length 拒） |
| `display_type` | varchar(64) | user-required | `fields[].display_type` | — | 白名单见 §3 | **ddl-risky**（不兼容转换拒） |
| `decimal_digits` | int(11) | user-required（decimal） | `fields[].scale` | — | 0-30 | ddl-safe |
| `nullable` | tinyint(1) | user-required | `fields[].nullable` | — | 0/1 | metadata-only |
| `default_value` | varchar(256) | user-optional | `fields[].default` | — | 字符串 | metadata-only |
| `dict` | varchar(64) | user-optional（字典字段） | `fields[].dict` | — | comm_dictionary.code | metadata-only |
| `pri` | tinyint(1) | auto-inject | — | 0（系统主键 id 除外） | 0/1 | metadata-only |
| `pri_type` | int(11) | auto-inject | — | — | — | metadata-only |
| `type` | int(11) | auto-inject | — | — | 1=业务 / 2=外键 | metadata-only |
| `hidden` | tinyint(1) | auto-inject（系统字段 + type=2 外键） | — | — | 0/1 | metadata-only |
| `readonly` | tinyint(1) | user-optional | `fields[].readonly` | — | 0/1 | metadata-only |
| `create_time` / `update_time` | date | auto-inject | — | NOW | — | metadata-only |
| `creator` / `updator` | varchar | auto-inject | — | 当前用户 | — | metadata-only |

## §3 display_type 白名单（generator 强制）

| display_type | Java/SQL 类型 | 适用 |
|--------------|---------------|------|
| `varchar` | varchar(N) | 短文本 |
| `text` | text | 长文本 |
| `int` | int(11) | 整数 |
| `bigint` | bigint(20) | 大整数 |
| `decimal` | decimal(M,D) | 金额 |
| `date` | date | 仅日期 |
| `datetime` | datetime | 日期 + 时间 |
| `tinyint` | tinyint(4) | 布尔/枚举 |
| `blob` | blob | 二进制 |
| `clob` | clob | 大文本（text 别名） |
| `hidden` | — | 系统隐藏 |
| `readonly` | — | 系统只读 |

## §4 updater 兼容矩阵

| 变更类型 | 行为 | DDL |
|---|---|---|
| 加字段 | ddl-safe | ALTER TABLE ADD COLUMN + INSERT md_field |
| 删字段 | ddl-risky | **DROP COLUMN 前自动备份** `t_xxx__bak_<ts>.sql` + DELETE md_field + 输出影响范围 |
| 改 `display_type` | ddl-risky | 不兼容转换（如 `varchar → int`）**拒绝**；其他 ALTER TABLE MODIFY |
| 改 `length`（缩小）| ddl-risky | **拒绝**；要求先备份 |
| 改 `length`（放大）| ddl-safe | ALTER TABLE MODIFY |
| 改 `nullable` / `comments` / `validation_rule` / `dict` / `default_value` | metadata-only | UPDATE md_field |
| 改 `field_name` | forbidden（field_name 是身份）| — |

## 📎 引用

- 物理 schema：`.claude/docs/backend/database/ddl/module/md_field.md`
- generator rule：`.claude/skills/badou-coding/skills/backend-module-generator/rules/field-config.md`
- updater rules：`.claude/skills/badou-coding/skills/backend-module-updater/update_rules/{field-add,field-remove,field-modify}.md`
