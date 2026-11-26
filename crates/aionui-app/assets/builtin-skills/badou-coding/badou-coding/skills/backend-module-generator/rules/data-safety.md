# 数据安全设计原则

> **何时读**：配置 hidden / readonly / NOT NULL 字段，或排查 Pydantic ValidationError 时。
> **配置项权威**：`.claude/skills/badou-coding/common/md_field.md`（md_field 配置项矩阵）
> **Pydantic 校验来源**：`models/field.py::FieldDef.hidden_nonnull_trap`

<!-- Source: generated for backend-module-generator stability design, do not edit by hand without syncing the plan. -->

---

## §1 框架填充边界

**框架只自动填充系统标准字段**（id/create_time/creator/creator_name/updator/updator_name/flg_deleted），**不填充业务字段**。业务 hidden、readonly 与 normal 字段都必须由调用方提供数据或允许为空。

---

## §2 配置项 → 详见 common spec

> 完整 md_field 配置项矩阵（含 hidden/readonly 相关写入策略 + 变更敏感度）见 `.claude/skills/badou-coding/common/md_field.md` §2。

---

## §3 业务 hidden/readonly 字段必须 nullable=true

> 🚨 **业务字段设为 hidden 或 readonly 后必须 `nullable=true`**，否则 Pydantic 硬阻断。

❌ 错误：
```json
{"field_name": "applicant_id", "nullable": false, "form": {"edit_type": "hidden"}}
// → Pydantic ValidationError: 字段不会被填充，违反 NOT NULL
```

❌ 错误：
```json
{"field_name": "applicant_name", "nullable": false, "form": {"editable": false}}
// → 同上
```

✅ 正确：
```json
{"field_name": "applicant_id", "nullable": true, "form": {"edit_type": "hidden"}}
{"field_name": "applicant_name", "nullable": true, "form": {"editable": false, "searchable": true}}
```

---

## §4 三大设计原则

| 原则 | 说明 |
|------|------|
| **原则 1**：hidden/readonly 字段由调用方填充 | 框架只填充系统字段；业务字段即使隐藏，调用方必须显式赋值 |
| **原则 2**：nullable 必须与数据来源匹配 | 必填的字段一定有数据源；无数据源的字段一定 nullable |
| **原则 3**：业务 hidden/readonly + NOT NULL + 无默认值 = 设计错误（Pydantic 硬阻断） | 三者同时存在 → INSERT 时无值 → NOT NULL 失败 → Pydantic 抛 ValidationError |

---

## §5 Pydantic 阻断模式

`models/field.py` 中的 `hidden_nonnull_trap` 检测：

```python
@validator("form")
def check_hidden_not_null(cls, v, values):
    if v.edit_type == "hidden" and not values.get("nullable", True):
        raise ValueError("hidden 字段必须 nullable=true")
    return v
```

---

## §6 与 generator 的协作

generator 在生成 md_field + DDL 时：
- hidden 字段 → DDL 用 `nullable=true` 写入
- readonly 字段 → DDL 用 `nullable=true` 写入
- 但**用户输入**仍按 module.json 的 nullable 校验

---

## §7 常见错误与修复

| 错误 | 修复 |
|------|------|
| 业务 hidden + NOT NULL | 设 `nullable: true` |
| readonly 字段未填写 default_value | 设 `nullable: true` 或 `default_value: ""` |
| 系统字段名冲突 | 改名（系统字段由 generator 自动注入） |

---

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口
- [rules/field-config.md](field-config.md) — 字段定义
- [rules/edit-page.md](edit-page.md) — hidden 字段处理
- [rules/module-link.md](module-link.md) — type=2 外键 hidden

**common spec**：
- [common/md_field.md](../../../common/md_field.md) — md_field 配置项矩阵

**Pydantic 源**：
- `models/field.py::FieldDef.hidden_nonnull_trap` — 校验逻辑权威
- `tests/test_models.py::test_hidden_nonnull_trap` — 回归测试

**示例**：
- [examples/module.json](../../examples/module.json) — applicant_id/applicant_name 正确写法
