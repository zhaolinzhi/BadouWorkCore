# 列表页配置（md_form.list_* 系列）

> **何时读**：配置列表页列展示规则时。
> **配置项权威**：`.claude/skills/badou-coding/common/md_form.md` §2.1（md_form.list_* 配置项矩阵）
> **物理 schema 权威**：`.claude/docs/backend/database/ddl/module/md_form.md`

---

## §1 列表硬编码隐藏规则（系统字段）

> 🚨 **以下字段在列表中永远不展示**，generator 自动写入 `show_in_grid=0`。

| 字段 | 原因 |
|------|------|
| `id` | 主键无意义 |
| `creator` / `updator` | 是 ID，用户看 creator_name 即可 |
| `flg_deleted` | 逻辑删除符 |

## §2 列表展示策略

| 字段类型 | 列表展示方式 |
|---------|-------------|
| 字典字段 | 显示字典 label（如 "事假"），不是 value（"1"） |
| 日期/时间 | 按 `format` 格式化 |
| 布尔 tinyint | "是" / "否" |
| 长文本 text | character_num 截断（默认 30） |

## §3 列表 drill-down（穿透）

| 属性 | 说明 |
|------|------|
| `list_drill` | 是否可点击穿透到查看页 |
| `list_drill_target` | 穿透目标（默认 view 页） |

## §4 配置项 → 详见 common spec

> 完整 md_form.list_* 7 列配置项矩阵（含 generator 写入策略 + 合法值 + 变更敏感度）见 `.claude/skills/badou-coding/common/md_form.md` §2.1。

## §5 JSON 写法示例

```json
{
  "fields": [
    {
      "field_name": "leave_type",
      "display_type": "varchar",
      "length": 64,
      "comment": "请假类型",
      "nullable": false,
      "dict": "leave_type",
      "is_show_in_grid": true,
      "LIST_WIDTH": 120,
      "SORTABLE": true,
      "list_drill": false
    }
  ]
}
```

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口
- [rules/view-page.md](view-page.md) — 列表穿透目标
- [rules/dictionary.md](dictionary.md) — 字典字段列表展示

**common spec**：
- [common/md_form.md](../../../common/md_form.md) — md_form 配置项矩阵 §2.1（list_* 列）

**DDL 文档**：
- [md_form.md](../../../../../docs/backend/database/ddl/module/md_form.md) — 表单配置表（含 list_* 列）

**示例**：
- [examples/module.json](../../examples/module.json) — 8 字段列表配置