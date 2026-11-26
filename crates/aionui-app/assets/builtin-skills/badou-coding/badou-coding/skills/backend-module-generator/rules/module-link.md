# 多表关联配置规则（md_module_link）

> **适用条件**：模块定义 JSON 中包含 `relations` 数组。
> **配置项权威**：`.claude/skills/badou-coding/common/md_module_link.md`（md_module_link 配置项矩阵）
> **物理 schema 权威**：`.claude/docs/backend/database/ddl/module/md_module_link.md`
> **关联阅读**：`rules/field-config.md` §4（type=2 外键自动隐藏）、`rules/sql-execution.md` §5（关联二阶段执行）。

<!-- Source: generated for backend-module-generator stability design, do not edit by hand without syncing the plan. -->

---

## §1 概述

`md_module_link` 是系统唯一的关联关系配置表，支持两种关联类型：

- **type=1**：一对一（当前模块通过外键指向关联模块）
- **type=2**：一对多（关联模块通过外键指向当前模块）

所有关联配置在模块定义 JSON 的 `relations` 数组中声明。

---

## §2 核心规则

### §2.1 type 与 SHOW_TYPE 绑定

| type | 含义 | SHOW_TYPE | SHOW_TYPE 含义 |
|------|------|-----------|----------------|
| **1** | 一对一 | **0**（固定） | 内联表格 |
| **2** | 一对多 | **1**（固定） | 弹窗选择 |

> ⚡ **SHOW_TYPE 由 type 决定，不可独立配置。type=1→0, type=2→1。**

### §2.2 show_style 与 tab_name 绑定

| show_style | 含义 | tab_name 要求 |
|-----------|------|--------------|
| **1** | 平级TAB | **必填** — 填写 Tab 页名称 |
| **2** | 子TAB | **必填** — 填写子 Tab 页名称 |
| **3** | 按顺序展示 | 可选 — 无需 Tab 名称 |

### §2.3 edit_module 关联模式

| edit_module | 含义 | 适用场景 |
|------------|------|---------|
| **0** | 父子表 | 主从关系（如订单→订单明细） |
| **1** | 中间表 | 多对多/间接关联（如用户↔角色） |

### §2.4 配置项 → 详见 common spec

> 完整 md_module_link 配置项矩阵（含非空约束、默认值、generator 写入策略 + 变更敏感度）见 `.claude/skills/badou-coding/common/md_module_link.md` §2。

---

## §3 JSON 定义示例

### §3.1 一对一关联 (type=1, edit_module=0)

```json
{
  "relations": [
    {
      "type": 1,
      "related_module": "customer",
      "field_name": "customer_id",
      "related_field_name": "name",
      "display_name": "客户名称",
      "edit_module": 0,
      "is_cascade": 0,
      "show_style": 1,
      "tab_name": "客户信息"
    }
  ]
}
```

**含义**：当前模块的 `customer_id` 字段指向 `customer` 模块的主键，显示关联记录的 `name` 字段值。在平级TAB中展示。

### §3.2 一对多关联 (type=2, edit_module=0)

```json
{
  "relations": [
    {
      "type": 2,
      "related_module": "order_item",
      "related_field_name": "order_id",
      "display_name": "订单明细",
      "edit_module": 0,
      "is_cascade": 1,
      "show_style": 2,
      "tab_name": "明细"
    }
  ]
}
```

**含义**：`order_item` 模块中有 `order_id` 字段指向当前模块的主键。删除当前订单时级联删除明细。在子TAB中展示。

### §3.3 中间表关联 (edit_module=1)

```json
{
  "relations": [
    {
      "type": 2,
      "related_module": "role",
      "display_name": "订单角色",
      "edit_module": 1,
      "is_cascade": 0,
      "show_style": 1,
      "tab_name": "角色"
    }
  ]
}
```

**含义**：通过中间表关联订单和角色（不直接存外键）。使用弹窗选择。在平级TAB中展示。

### §3.4 按顺序展示 (show_style=3)

```json
{
  "relations": [
    {
      "type": 1,
      "related_module": "customer",
      "field_name": "customer_id",
      "related_field_name": "name",
      "display_name": "所属客户",
      "edit_module": 0,
      "is_cascade": 0,
      "show_style": 3,
      "tab_name": null
    }
  ]
}
```

**含义**：不带 Tab 标签，直接按顺序在页面中内嵌显示。

---

## §4 relations 路由与字段归属

`relations` 中 `field_name` / `field_id` 描述当前模型字段，`related_field_name` / `related_field` 描述关联模型字段。type=1 时当前模型持有外键；type=2 时关联模型持有指向当前模型的外键。完整 JSON → md_module_link 映射见 common spec。

---

## §5 各规则组合下的生成行为

| type | edit_module | is_cascade | show_style | SHOW_TYPE | SHOW_TAB | 生成行为 |
|------|------------|-----------|-----------|-----------|---------|---------|
| 1 | 0 | 0 | 1 | 0 | 1 | JOIN + 平级TAB内联展示，不级联 |
| 1 | 0 | 1 | 1 | 0 | 1 | JOIN + 平级TAB，级联删除 |
| 1 | 1 | 0 | 1 | 0 | 1 | 中间表 JOIN + 平级TAB，不级联 |
| 2 | 0 | 0 | 2 | 1 | 1 | 子表弹窗 + 子TAB，不级联 |
| 2 | 0 | 1 | 2 | 1 | 1 | 子表弹窗 + 子TAB，级联删除子表 |
| 2 | 1 | 0 | 2 | 1 | 1 | 中间表弹窗 + 子TAB，不级联 |

> 共 type×edit_module×show_style = 2×2×3 = 12 种组合，上表仅列出常见 6 种。

---

## §6 relations 字段校验规则

| 校验 | 规则 | 错误信息 |
|------|------|---------|
| type | ∈ {1, 2} | "type 只能是 1 或 2" |
| edit_module | ∈ {0, 1} | "edit_module 只能是 0 或 1" |
| show_style | ∈ {1, 2, 3} | "show_style 只能是 1/2/3" |
| tab_name | show_style=1/2 时必填 | "show_style 为 1/2 时 tab_name 不能为空" |
| field_name | type=1 时必填 | "type=1 时 field_name 不能为空" |
| field_name 存在性 | type=1 的 field_name 必须在 fields 数组中 | "field_name 'xxx' 在 fields 中不存在" |
| related_module | 必填 | "related_module 不能为空" |
| related_field_name | 必填 | "related_field_name 不能为空" |
| display_name | 必填 | "display_name 不能为空" |

---

## §7 生成的 SQL 说明

### §7.1 type=1（一对一）+ edit_module=0

```sql
INSERT INTO md_module_link (id, module_id, related_module_id, field_name, field_id,
    related_table, related_field, related_field_name, type, is_edit, display_name,
    edit_module, is_cascade, priority, SHOW_TAB, SHOW_TYPE, show_style, tab_name)
VALUES (@link_uuid, @module_id, @related_module_id,
    '${field_name}', @field_id_for_field_name,
    '${related_table}', @related_field_id, '${related_field_name}',
    1, 1, '${display_name}',
    ${edit_module}, ${is_cascade}, ${priority},
    ${SHOW_TAB}, 0, ${show_style},
    '${tab_name}');
```

### §7.2 type=2（一对多）+ edit_module=0

```sql
INSERT INTO md_module_link (id, module_id, related_module_id, field_name, field_id,
    related_table, related_field, related_field_name, type, is_edit, display_name,
    edit_module, is_cascade, priority, SHOW_TAB, SHOW_TYPE, show_style, tab_name)
VALUES (@link_uuid, @module_id, @related_module_id,
    '', '',
    '${related_table}', @related_field_id, '${related_field_name}',
    2, 1, '${display_name}',
    0, ${is_cascade}, ${priority},
    1, 1, ${show_style},
    '${tab_name}');
```

---

## §8 执行顺序（⚠️ 两阶段执行）

> 🚨 **md_module_link INSERT 不能放在单个模块的 create.sql 中执行**。原因：执行时关联模块可能还不存在，子查询返回 NULL 导致关联数据异常。

### §8.1 正确执行流程

```
第一阶段：创建所有模块
├── mysql < category_create.sql
├── mysql < product_create.sql
└── mysql < order_create.sql

第二阶段：创建所有关联（模块全部存在后）
├── mysql < category_relation.sql
├── mysql < product_relation.sql
└── mysql < order_relation.sql
```

> 完整执行顺序与 db_executor.py 用法详见 `sql-execution.md`。

### §8.2 SQL 文件位置

```
output/{module_code}/v1.0.0/
├── {module_code}_create.sql
├── {module_code}_relation.sql    # 仅含 relations 时生成
├── {module_code}_cleanup.sql
└── manifest.json
```

---

## §9 注意事项

### §9.1 type=1 的依赖关系
- `field_name` 必须同时出现在当前模块的 `fields` 数组中
- 关联模块必须先存在（先创建关联模块，再创建当前模块）
- type=1 生成 JOIN 类型的查询 SQL

### §9.2 type=2 一对多的"多"端字段处理

> 详细规则见 `field-config.md` §4。

简要：

| 处理方式 | 说明 |
|---------|------|
| 列表展示 | ❌ `is_show_in_grid=0` |
| 编辑页展示 | ❌ `edit_type="hidden"` |
| 字段长度 | ✅ 自动强制 `length=64` |
| 数据库字段 | ✅ 保留作为外键存储 |

### §9.3 edit_module=1（中间表）
- 不在当前模块存外键，通过中间表关联
- 同时需要生成中间表的 INSERT/DELETE（但当前生成器不创建中间表的 md_module 定义）
- 适用于多对多关系（如用户↔角色）

### §9.4 跨模块 @variable 链接
- `@related_module_id` → 关联模块的 `@module_id`
- `@field_id_for_field_name` → 当前模块对应字段的 `@field_id`
- `@related_field_id` → 关联模块对应字段的 `@field_id`
- SQL 必须按正确顺序拼接（关联模块的 module/field 先于 current 模块的 module_link）

---

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口
- [rules/field-config.md](field-config.md) — §4 type=2 外键自动隐藏
- [rules/sql-execution.md](sql-execution.md) — §5 关联二阶段执行
- [rules/data-safety.md](data-safety.md) — hidden 字段 nullable 约束

**common spec**：
- [common/md_module_link.md](../../../common/md_module_link.md) — md_module_link 配置项矩阵

**DDL 文档**：
- [md_module_link.md](../../../../../docs/backend/database/ddl/module/md_module_link.md) — 关联表结构（20 列权威）

**示例**：
- [examples/order_with_items.json](../../examples/order_with_items.json) — 一对多关联完整示例
- [examples/category_def.json](../../examples/category_def.json) — 多对一完整示例