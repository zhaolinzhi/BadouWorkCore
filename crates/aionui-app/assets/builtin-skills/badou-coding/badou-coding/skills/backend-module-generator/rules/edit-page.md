# 编辑页配置（md_form.edit_* 系列）

> **何时读**：配置编辑页字段展示规则时。
> **配置项权威**：`.claude/skills/badou-coding/common/md_form.md` §2.3（md_form.edit_* 配置项矩阵）
> **edit_type 推断权威**：`.claude/skills/badou-coding/common/md_form.md` §3（edit_type 白名单 + display_type 默认映射）
> **物理 schema 权威**：`.claude/docs/backend/database/ddl/module/md_form.md`

---

## §1 edit_type 映射表（display_type → edit_type）

| display_type | 默认 edit_type | 用户可改 |
|--------------|----------------|---------|
| `varchar` (短文本) | `input` | ✅ |
| `varchar` (业务编码) | `input`（校验唯一） | ✅ |
| `text` | `textarea` | ✅ |
| `int` / `bigint` | `input`（number 校验） | ✅ |
| `decimal` | `input`（number 校验） | ✅ |
| `date` | `date` | ✅ |
| `datetime` | `datetime` | ✅ |
| `tinyint` (布尔) | `switch` | ✅ |
| 字典字段 | `select` | ✅ |
| `blob` / `clob` | `file` | ❌ |

## §2 校验规则自动推断

| display_type | 默认校验（regex_rule） |
|--------------|------------------------|
| `varchar` (短文本) | 无 |
| `int` / `bigint` / `decimal` | `/^-?\d+(\.\d+)?$/` |
| `date` / `datetime` | 日期格式 |
| `email` 命名约定 | `/.+@.+/` |
| `phone` 命名约定 | `/^1\d{10}$/` |
| `id_card` 命名约定 | `/(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/` |

✅ 自定义校验：在 `form.regex_rule` 直接写正则。

## §3 编辑页硬编码隐藏规则

> 🚨 **以下字段在编辑页隐藏但保留在 DDL**：

| 字段 | 处理 |
|------|------|
| `id` | `edit_type: "hidden"` |
| `create_time` / `creator` / `creator_name` / `update_time` / `updator` / `updator_name` / `flg_deleted` | `edit_type: "hidden"` |
| type=2 外键 | `edit_type: "hidden"` + `nullable=true`（详见 `rules/field-config.md` §4） |

## §4 校验规则

| 校验 | 错误信息 |
|------|---------|
| 业务 hidden 字段 `nullable=false` | Pydantic 阻断：hidden 字段不会被框架填充，NOT NULL 必失败 |
| `edit_type: "select"` 但无 `dict` | generator 不会绑定字典 |
| `regex_rule` 非正则字符串 | "regex_rule must be a valid regex" |

## §5 配置项 → 详见 common spec

> 完整 md_form.edit_* 9 列配置项矩阵（含 generator 写入策略 + 合法值 + 变更敏感度）见 `.claude/skills/badou-coding/common/md_form.md` §2.3。
> 
> **is_edit / editable / edit_tip 等可写性属性** + **is_required / is_edit / edit_default 等用户行为属性**见 common spec §2.3 表。
> 
> **edit_type 白名单 + display_type 默认推断表**见 common spec §3。

## §6 JSON 写法示例

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
      "form": {"edit_type": "select", "is_required": true}
    },
    {
      "field_name": "duration",
      "display_type": "int",
      "length": 11,
      "comment": "请假天数",
      "nullable": false,
      "form": {"edit_type": "input", "is_required": true}
    }
  ]
}
```

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口
- [rules/field-config.md](field-config.md) — 字段长度与系统字段
- [rules/data-safety.md](data-safety.md) — hidden 字段安全约束
- [rules/dictionary.md](dictionary.md) — select 与字典绑定

**common spec**：
- [common/md_form.md](../../../common/md_form.md) — md_form 配置项矩阵 §2.3（edit_* 列）+ §3（edit_type 白名单）

**DDL 文档**：
- [md_form.md](../../../../../docs/backend/database/ddl/module/md_form.md) — edit_* 列定义

**示例**：
- [examples/module.json](../../examples/module.json) — leave_type select / duration input