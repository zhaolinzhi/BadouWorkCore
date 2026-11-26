# 搜索条件配置（md_form.search_* 系列）

> **何时读**：配置列表页搜索框时。
> **配置项权威**：`.claude/skills/badou-coding/common/md_form.md` §2.2（md_form.search_* 配置项矩阵）
> **物理 schema 权威**：`.claude/docs/backend/database/ddl/module/md_form.md`

---

## §1 搜索类型自动推断

| display_type | 默认 search_type |
|--------------|-----------------|
| `varchar` / `text` | `input`（like 匹配） |
| `int` / `bigint` / `decimal` | `input`（equal） |
| `date` / `datetime` | `date_range`（between） |
| 字典字段（dict 字段） | `select`（equal） |

## §2 字典搜索三条件

> 🚨 **字典字段作为搜索条件时必须满足**（与编辑页三条件同源）：

| # | 字段属性 | 含义 |
|---|---------|------|
| ① | `field.dict` | 字段指定字典 code |
| ② | `dictionaries` 数组 | 字典定义存在 |
| ③ | `form.search_type: "select"` | 搜索框用 select |

## §3 常见错误

❌ 错误：日期字段用 `searchable: true` 但未指定 `search_type` → 自动推断为 `input`，用户无法选时间范围。
✅ 正确：`searchable: true, search_type: "date_range"`。

## §4 配置项 → 详见 common spec

> 完整 md_form.search_* 4 列配置项矩阵（含 generator 写入策略 + 合法值 + 变更敏感度）见 `.claude/skills/badou-coding/common/md_form.md` §2.2。

## §5 JSON 写法示例

```json
{
  "fields": [
    {
      "field_name": "start_date",
      "display_type": "datetime",
      "length": 11,
      "comment": "开始日期",
      "nullable": true,
      "searchable": true,
      "search_type": "date_range"
    },
    {
      "field_name": "leave_type",
      "display_type": "varchar",
      "length": 64,
      "comment": "请假类型",
      "nullable": false,
      "dict": "leave_type",
      "searchable": true,
      "search_type": "select"
    }
  ]
}
```

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口
- [rules/dictionary.md](dictionary.md) — 字典三条件
- [rules/list-page.md](list-page.md) — 列表与搜索联动

**common spec**：
- [common/md_form.md](../../../common/md_form.md) — md_form 配置项矩阵 §2.2（search_* 列）

**DDL 文档**：
- [md_form.md](../../../../../docs/backend/database/ddl/module/md_form.md) — search_* 列定义

**示例**：
- [examples/module.json](../../examples/module.json) — start_date 范围搜索