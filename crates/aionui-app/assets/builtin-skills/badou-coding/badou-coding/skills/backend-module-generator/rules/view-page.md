# 查看页配置（md_form.view_* 系列）

> **何时读**：配置查看页字段展示规则时。
> **配置项权威**：`.claude/skills/badou-coding/common/md_form.md` §2.4（md_form.view_* 配置项矩阵）
> **view_type 推断权威**：`.claude/skills/badou-coding/common/md_form.md` §4（view_type 自动推断规则）
> **物理 schema 权威**：`.claude/docs/backend/database/ddl/module/md_form.md`

---

## §1 view_type 自动推断

| display_type | 默认 view_type |
|--------------|----------------|
| `text` | `textarea` |
| `varchar` | `label` |
| `date` / `datetime` | `label`（自动格式化） |
| `int` / `bigint` / `decimal` | `label` |
| 字典字段 | `label`（显示字典 label） |
| `blob` | `image` |

## §2 is_full_line 自动推断

| 场景 | is_full_line |
|------|--------------|
| text / textarea / blob | true（占满整行） |
| 短字段（varchar 50） | false |
| 默认 | false |

## §3 查看页硬编码隐藏

> 🚨 系统字段在查看页隐藏（同编辑页，详见 `rules/edit-page.md` §3）。

## §4 view_drill

| 属性 | 说明 |
|------|------|
| `view_drill` | 是否可点击字段穿透（如外键字段穿透到关联模块） |
| `view_drill_target` | 穿透目标模块 code |

## §5 form 新增字段清单

> 📖 编辑与新增共用 md_form 行；新增模式与编辑模式共用 `is_edit` / `regex_rule` 规则。

| 模式 | 差异 |
|------|------|
| add | id/create_time 等为空，INSERT 后框架填充 |
| edit | id/create_time 等 hidden 但保留值 |

## §6 配置项 → 详见 common spec

> 完整 md_form.view_* 6 列配置项矩阵（含 generator 写入策略 + 合法值 + 变更敏感度）见 `.claude/skills/badou-coding/common/md_form.md` §2.4。
> 
> **view_type 自动推断规则**见 common spec §4。
> 
> **view_show / view_tip / is_full_line / view_drill / view_drill_target** 等 view_* 列见 common spec §2.4 表。

## §7 JSON 写法示例

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
      "form": {
        "view_drill": false,
        "is_full_line": false
      }
    },
    {
      "field_name": "remark",
      "display_type": "text",
      "comment": "备注",
      "nullable": true,
      "form": {
        "is_full_line": true
      }
    }
  ]
}
```

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口
- [rules/edit-page.md](edit-page.md) — 编辑页与查看页共用 md_form
- [rules/list-page.md](list-page.md) — 列表穿透
- [rules/module-link.md](module-link.md) — 关联字段穿透

**common spec**：
- [common/md_form.md](../../../common/md_form.md) — md_form 配置项矩阵 §2.4（view_* 列）+ §4（view_type 推断）

**DDL 文档**：
- [md_form.md](../../../../../docs/backend/database/ddl/module/md_form.md) — view_* 列定义

**示例**：
- [examples/module.json](../../examples/module.json) — 8 字段查看页