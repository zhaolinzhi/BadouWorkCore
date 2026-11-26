# field-add.md

> **何时读**：`fields` 数组新增条目
> **配置项权威**：`.claude/skills/badou-coding/common/md_field.md`
> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_field.md`

---

## §1 新增字段：ALTER TABLE 模板

```sql
ALTER TABLE t_xxx ADD COLUMN <field_name> <display_type>(<length>) DEFAULT <default_value> COMMENT '<comment>';
```

**模板规则**：
- `nullable = true` 时：`DEFAULT NULL`（或指定 default_value）
- `nullable = false` 时：`NOT NULL DEFAULT <default_value>`
- `display_type` 映射：`varchar` → `varchar`、`int` → `int`、`datetime` → `datetime`、`text` → `text`

## §2 新增字段：md_field UPSERT

```sql
INSERT INTO md_field (module_code, field_name, display_type, length, nullable, comment, ...)
VALUES (?, ?, ?, ?, ?, ?, ...)
ON DUPLICATE KEY UPDATE display_type = ?, length = ?, nullable = ?, comment = ?, ...;
```

**关联字段**：`field_name` 作为唯一键，支持幂等重跑。

## §3 新增字段后的 md_form 同步

- 读取当前 `md_form` 全量记录
- 为新字段插入 `md_form` 默认配置（`editable = true`，`hidden = false`，`list_show = true`）
- 如果 `md_form` 全量已有，则 ADD 新的 form 行
- 不修改已有字段的 `md_form` 配置

## 📎 引用清单

**相关规则文档**：
- [rules/form-config-change.md](form-config-change.md)
- [rules/field-modify.md](field-modify.md)

**common spec**：
- [common/md_field.md](../../../common/md_field.md)
- [common/md_form.md](../../../common/md_form.md)

**DDL 文档**：
- [md_field.md](../../../../../docs/backend/database/ddl/module/md_field.md)

**示例**：
- [examples/update_purchase_request_add_field.json](../../examples/update_purchase_request_add_field.json)