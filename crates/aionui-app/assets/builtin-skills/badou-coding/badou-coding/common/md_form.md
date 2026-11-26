# md_form 配置项矩阵

> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_form.md`
> **覆盖**：52 列
> **详/简**：详

## §1 表概述

- **用途**：描述每个字段在**列表 / 表单 / 搜索框**的呈现；一行 = 一行 md_field（同 field_id）
- **与 generator 关系**：`form_gen.py` 写入；与 md_field 一一对应
- **关键含义**：用户实际看到的"配置"——决定 grid 上是否显示、form 上用什么控件、search 是否可输入

## §2 配置项分组

> md_form 52 列按用途分 4 组：list_* / search_* / edit_* / view_*，每组与 md_field 一一映射。

### §2.1 list_* 列（列表页）

| 列名 | 类型 | 写入策略 | 用户提供 | 默认 | 合法值 | 敏感度 |
|------|------|---------|---------|------|--------|--------|
| `list_show_in_grid` | tinyint(1) | auto-inject（系统字段为 0） | `fields[].is_show_in_grid` | true | 0/1 | metadata-only |
| `list_width` | int(11) | user-optional | `fields[].LIST_WIDTH` | 自动 | 像素 | metadata-only |
| `list_character_num` | int(11) | user-optional | `fields[].character_num` | 30 | 整数 | metadata-only |
| `list_sortable` | tinyint(1) | user-optional | `fields[].SORTABLE` | false | 0/1 | metadata-only |
| `list_drill` | tinyint(1) | user-optional | `fields[].list_drill` | false | 0/1 | metadata-only |
| `list_drill_target` | varchar(64) | user-optional | `fields[].list_drill_target` | view | view/edit | metadata-only |
| `list_format` | varchar(64) | user-optional | `fields[].list_format` | — | 日期/数字格式串 | metadata-only |

### §2.2 search_* 列（搜索框）

| 列名 | 类型 | 写入策略 | 用户提供 | 默认 | 合法值 | 敏感度 |
|------|------|---------|---------|------|--------|--------|
| `search_show` | tinyint(1) | user-optional | `fields[].searchable` | false | 0/1 | metadata-only |
| `search_type` | varchar(64) | user-optional | `fields[].search_type` | input | input/select/date/between/like | metadata-only |
| `search_box` | varchar(64) | user-optional | `fields[].search_box` | =（input）/ LIKE（like） | =, !=, >, <, >=, <=, LIKE, IN, BETWEEN | metadata-only |
| `search_default` | varchar(256) | user-optional | `fields[].search_default` | — | 默认值 | metadata-only |

### §2.3 edit_* 列（编辑页）

| 列名 | 类型 | 写入策略 | 用户提供 | 默认 | 合法值 | 敏感度 |
|------|------|---------|---------|------|--------|--------|
| `edit_type` | varchar(64) | user-required | `fields[].form.edit_type` | **自动推断自 display_type**（见 §3） | 见 §3 白名单 | metadata-only（仅 UI 变化）|
| `data_source` | int(11) | user-optional（字典字段） | `fields[].form.data_source` | 0（字典）/ 1（SQL）/ 2（自定义） | 0/1/2 | metadata-only |
| `dic_name` | varchar(128) | user-optional（字典字段） | `fields[].dict` | — | comm_dictionary.code | metadata-only |
| `is_required` | tinyint(1) | user-optional | `fields[].required` | false | 0/1 | metadata-only |
| `is_edit` | tinyint(1) | user-optional | `fields[].is_edit` | true | 0/1 | metadata-only |
| `editable` | tinyint(1) | auto-inject | — | true | 0/1 | metadata-only |
| `regex_rule` | varchar(2048) | user-optional | `fields[].form.regex_rule` | **自动推断自 display_type** | 正则字符串 | metadata-only |
| `edit_tip` | varchar(512) | user-optional | `fields[].form.edit_tip` | — | 提示文本 | metadata-only |
| `edit_default` | varchar(256) | user-optional | `fields[].form.default_value` | — | 默认值 | metadata-only |

### §2.4 view_* 列（查看页）

| 列名 | 类型 | 写入策略 | 用户提供 | 默认 | 合法值 | 敏感度 |
|------|------|---------|---------|------|--------|--------|
| `view_type` | varchar(64) | auto-inject | — | **自动推断自 display_type**（见 §4） | 同 edit_type | metadata-only |
| `view_show` | tinyint(1) | auto-inject | — | true | 0/1 | metadata-only |
| `is_full_line` | tinyint(1) | user-optional | `fields[].form.is_full_line` | false | 0/1 | metadata-only |
| `view_drill` | tinyint(1) | user-optional | `fields[].view_drill` | false | 0/1 | metadata-only |
| `view_drill_target` | varchar(64) | user-optional | `fields[].view_drill_target` | view | view/edit | metadata-only |
| `view_tip` | varchar(512) | user-optional | `fields[].form.view_tip` | — | 提示文本 | metadata-only |

## §3 edit_type 白名单 + display_type 默认映射

> 此处仅列 edit_type 合法值；**display_type → 默认 edit_type 的推断表保留在 generator 的 `edit-page.md` §1**（叙述性规则，非配置项枚举）。

| edit_type | 控件 | 典型 display_type |
|-----------|------|-------------------|
| `input` | 文本输入框 | varchar / int / decimal |
| `textarea` | 多行文本 | text / clob |
| `select` | 下拉 | 字典字段（必填 dict + dictionaries + data_source=0）|
| `select_multi` | 多选下拉 | 字典字段（多值）|
| `radio` | 单选 | 字典字段（小集合）|
| `checkbox` | 多选 | 字典字段（小集合）|
| `date` | 日期选择 | date |
| `datetime` | 日期时间选择 | datetime |
| `number` | 数字输入 | int / bigint / decimal |
| `upload` | 文件上传 | blob |
| `switch` | 开关 | tinyint (布尔) |
| `hidden` | 隐藏 | 系统字段 / type=2 外键 |
| `readonly` | 只读 | 外部回填字段 |

## §4 view_type 自动推断（generator 行为规则）

> 此规则保留在 generator `view-page.md`（叙述性），不在本文件展开。

## §5 updater 兼容矩阵

> md_form 所有列变更**仅 metadata**（不改 DDL）；UI 配置变更。

| 变更类型 | 行为 |
|---|---|
| 改 list_* / search_* / edit_* / view_* 任意列 | metadata-only（DELETE + INSERT md_form 全量） |
| 加字段 | 同步加 md_form 行（参见 field-add.md） |
| 删字段 | 同步删 md_form 行（参见 field-remove.md） |

## 📎 引用

- 物理 schema：`.claude/docs/backend/database/ddl/module/md_form.md`
- generator rules：`.claude/skills/badou-coding/skills/backend-module-generator/rules/{list-page,search-condition,edit-page,view-page}.md`
- updater rule：`.claude/skills/badou-coding/skills/backend-module-updater/update_rules/form-config-change.md`