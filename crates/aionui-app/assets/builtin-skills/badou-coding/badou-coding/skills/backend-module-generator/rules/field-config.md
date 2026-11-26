# 字段配置（md_field）

> **何时读**：写 module.json 的 `fields` 数组时。
> **配置项权威**：`.claude/skills/badou-coding/common/md_field.md`（md_field 配置项矩阵）
> **物理 schema 权威**：`.claude/docs/backend/database/ddl/module/md_field.md`

---

## §1 字段必填属性

| 属性 | 必填 | 说明 |
|------|------|------|
| `field_name` | ✅ | 字段名（小写下划线，见 §5 命名约束） |
| `display_type` | ✅ | 见 §2 白名单 |
| `comment` | ✅ | 中文注释（DDL + 前端 label） |
| `nullable` | ✅ | true / false |
| `length` | varchar 必填 | 默认 64（主键/外键），文本 50-200，大字段用 text |
| `decimal_digits` | decimal 必填 | 小数位数（如 1 表示 1 位小数） |
| `dict` | 字典字段必填 | 字典 code |

## §2 display_type 白名单

> 完整白名单与历史脏数据见 `.claude/skills/badou-coding/common/md_field.md` §3（generator 强制执行的合法值集合）。

| display_type | Java/SQL 类型 | 适用 |
|--------------|---------------|------|
| `varchar` | varchar(N) | 短文本（姓名、编码） |
| `text` | text | 长文本（备注、说明） |
| `int` | int(11) | 整数 |
| `bigint` | bigint(20) | 大整数 |
| `decimal` | decimal(M,D) | 金额、天数 |
| `date` | date | 仅日期 |
| `datetime` | datetime | 日期 + 时间 |
| `tinyint` | tinyint(4) | 布尔/枚举值 |
| `blob` | blob | 二进制 |
| `clob` | clob | 大文本（text 别名） |

❌ 错误：`display_type: "string"`（不在白名单，Pydantic 阻断）。
✅ 正确：`display_type: "varchar"`.

## §3 字段长度统一

| 字段类型 | length | 说明 |
|---------|--------|------|
| 主键 `id` | 64 | 与 md_module.id 一致 |
| 外键（指向主键） | 64 | 与目标模块主键一致 |
| 业务字段 | 业务合理值（50-200） | 短文本 50、长文本 200 |
| 长文本（备注） | N/A | 用 `display_type: "text"` 不用 length |

> 🚨 **主键与外键 length 必须为 64**，否则框架 JOIN 失败。

## §4 type=2 外键自动隐藏规则

> 多表关联场景下，"多"端的外键字段在表单中自动隐藏（详见 `module-link.md` §3）。

| 显示位置 | 是否展示 | 配置 |
|---------|---------|------|
| 列表 | ❌ | `is_show_in_grid=0` |
| 编辑页 | ❌（hidden） | `edit_type: "hidden"` |
| 可编辑性 | ✅ | `is_edit=1` + `edit_type="hidden"`（模型配置工具可写入） |
| 数据库 | ✅ | 字段保留，作为外键存储关联 |

❌ 错误：手动配置 `edit_type: "select"` + 绑定字典 → 与分类 TAB 选择产品造成数据冗余。
✅ 正确：保留 `display_type: "varchar"`, `nullable: true`, `length: 64`，由规则引擎自动配置 hidden。

## §5 字段命名约束

- `field_name` 必须满足 `[a-z][a-z0-9_]*`
- 长度 ≤ 30
- 不与系统字段名冲突（id / create_time 等）
- 不与 SQL 保留字冲突（`order` / `group` / `select` 等）→ 改名（如 `order_id` / `sort_num`）

## §6 配置项 → 详见 common spec

> 完整 md_field 21 列配置项矩阵（含 generator 写入策略 + 变更敏感度 + updater 兼容矩阵）见 `.claude/skills/badou-coding/common/md_field.md` §2。

**自动注入字段**（由 generator 注入，不在 fields 数组中声明）：

| 来源 | 字段 | 说明 |
|------|------|------|
| **系统字段**（8 个，自动） | `id`, `create_time`, `creator`, `creator_name`, `updator`, `updator_name`, `update_time`, `flg_deleted` | 详见 common spec §2 |
| **流程字段**（`flow_code` 非空时自动） | `BO_STATUS` 等 3 个 | 详见 `flow-contract.md` §「CRUD 侧自动行为」 |

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
      "dict": "leave_type"
    },
    {
      "field_name": "duration",
      "display_type": "int",
      "length": 11,
      "comment": "请假天数",
      "nullable": false
    }
  ]
}
```

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口与总检查清单
- [rules/dictionary.md](dictionary.md) — 字典三条件
- [rules/data-safety.md](data-safety.md) — hidden/readonly 字段 nullable 约束
- [rules/module-link.md](module-link.md) — type=2 外键自动隐藏
- [rules/flow-contract.md](flow-contract.md) — 流程字段注入

**common spec**：
- [common/md_field.md](../../../common/md_field.md) — md_field 配置项矩阵

**DDL 文档**：
- [md_field.md](../../../../../docs/backend/database/ddl/module/md_field.md) — 字段表结构（21 列权威）
- [md_form.md](../../../../../docs/backend/database/ddl/module/md_form.md) — 表单配置表结构（52 列权威）

**示例**：
- [examples/module.json](../../examples/module.json) — 8 字段 + 字典完整示例