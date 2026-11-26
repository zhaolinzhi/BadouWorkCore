# 数据字典配置（comm_dictionary + comm_dictionary_item）

> **何时读**：module.json 含 dict 字段或 `dictionaries` 数组时。
> **配置项权威**：`.claude/skills/badou-coding/common/md_field.md` §「dict 字段」（md_field.dict 列）
> **表单绑定权威**：`.claude/skills/badou-coding/common/md_form.md` §2.3（dic_name / data_source 列）
> **物理 schema 权威**：`.claude/docs/backend/database/ddl/dic/comm_dictionary.md`

---

## §1 字典三条件（缺一不可）

> 🚨 **任何含字典语义的字段必须同时满足以下三条**，否则 generator 不绑定字典。

| # | 字段属性 | 含义 |
|---|---------|------|
| ① | `field.dict` | 字段上指定字典 code（如 `"leave_type"`） |
| ② | `dictionaries` 数组 | 模块顶层声明字典定义 |
| ③ | `form.edit_type: "select"` | 表单 select 控件 |

## §2 字典搜索三条件

> 搜索框使用字典字段详见 `search-condition.md` §「字典搜索三条件」（与编辑页同源）。

| # | 字段属性 | 含义 |
|---|---------|------|
| ① | `field.dict` | 字段指定字典 code |
| ② | `dictionaries` 数组 | 字典定义存在 |
| ③ | `form.search_type: "select"` | 搜索框用 select |

## §3 dict 属性正确写法

```json
// ❌ 错误：仅在字段上写 dict，不在 dictionaries 声明
{"field_name": "leave_type", "dict": "leave_type"}

// ❌ 错误：仅在 dictionaries 声明，字段上无 dict
{"field_name": "leave_type"}

// ❌ 错误：edit_type 不是 select
{"field_name": "leave_type", "dict": "leave_type", "form": {"edit_type": "input"}}

// ✅ 正确：三条件齐全
{"field_name": "leave_type", "dict": "leave_type", "form": {"edit_type": "select"}}
```

## §4 BO_STATUS 自动注入（流程模块）

> 流程模块的字典三条件由 generator 自动满足，详见 `flow-contract.md` §「CRUD 侧自动行为」。

流程模块（含 `flow_code`）由 generator 自动注入：

| 项目 | 值 |
|------|---|
| 字典 code | `BO_STATUS` |
| 字典名 | "审批状态" |
| items | `0=草稿` / `1=审批中` / `2=已通过` / `3=已驳回` |
| 字段 | BO_STATUS int(1) 自动添加到 md_field |

## §5 配置项 → 详见 common spec

> **md_field.dict 列**（21 列配置项矩阵中 dict 字段）见 `.claude/skills/badou-coding/common/md_field.md` §2。
> 
> **md_form 表单绑定**（dic_name / data_source / edit_type 推断）见 `.claude/skills/badou-coding/common/md_form.md` §2.3。
> 
> **comm_dictionary / comm_dictionary_item 物理表结构**见 `.claude/docs/backend/database/ddl/dic/comm_dictionary.md`。

## §6 校验规则

| 校验 | 错误信息 |
|------|---------|
| `dict` 字段未在 `dictionaries` 声明 | "field '<x>' has dict='<y>' but dictionaries array has no '<y>'" |
| `dictionaries` 数组中有未引用的字典 | warning: "dictionary '<x>' is declared but no field uses it" |
| `edit_type` 不是 select | "dict field '<x>' must have form.edit_type='select'" |

## §7 JSON 写法示例

```json
{
  "dictionaries": [
    {
      "code": "leave_type",
      "name_cn": "请假类型",
      "items": [
        {"code": "1", "name_cn": "事假"},
        {"code": "2", "name_cn": "病假"},
        {"code": "3", "name_cn": "年假"}
      ]
    }
  ],
  "fields": [
    {
      "field_name": "leave_type",
      "display_type": "varchar",
      "length": 64,
      "comment": "请假类型",
      "nullable": false,
      "dict": "leave_type",
      "form": {"edit_type": "select"}
    }
  ]
}
```

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口与总检查清单
- [rules/field-config.md](field-config.md) — 字段定义
- [rules/search-condition.md](search-condition.md) — 搜索框字典三条件
- [rules/flow-contract.md](flow-contract.md) — BO_STATUS 自动注入

**common spec**：
- [common/md_field.md](../../../common/md_field.md) — md_field 配置项矩阵（含 dict 字段）
- [common/md_form.md](../../../common/md_form.md) — md_form 配置项矩阵（含 dic_name/data_source）

**DDL 文档**：
- [md_form.md](../../../../../docs/backend/database/ddl/module/md_form.md) — dict 三条件列定义
- `comm_dictionary.md` — 字典表结构

**示例**：
- [examples/module.json](../../examples/module.json) — leave_type 字典完整示例