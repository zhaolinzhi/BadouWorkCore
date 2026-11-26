# form-config-change.md

> **何时读**：`form` 段变化
> **配置项权威**：`.claude/skills/badou-coding/common/md_form.md`
> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_form.md`

---

## §1 md_form 全量 DELETE + INSERT

**策略**：对 `md_form` 执行 DELETE + INSERT 全量策略。

```sql
DELETE FROM md_form WHERE module_code = ?;
-- 逐条 INSERT
INSERT INTO md_form (module_code, field_name, list_show, editable, hidden, required, width, ...)
VALUES (?, ?, ?, ?, ?, ?, ?, ...);
```

## §2 与 md_field 同步（field_id 对齐）

- 读取 `md_field` 中所有 `field_name` 列表
- 确保 `md_form` 中 `field_name` 与 `md_field` 一一对应
- 如果 `md_field` 中删除了字段，`md_form` 中对应行也删除
- 如果 `md_field` 中新增了字段，`md_form` 中插入默认配置

## §3 字典三条件联动

- 如果字段绑定了 `dict_code`，`md_form` 中自动设置 `dict_code`
- 如果字段的 `dict_code` 变更，`md_form` 中同步更新
- 如果字段的 `dict_code` 删除，`md_form` 中 `dict_code` 置 NULL

## 📎 引用清单

**相关规则文档**：
- [rules/field-add.md](field-add.md)
- [rules/field-remove.md](field-remove.md)
- [rules/dictionary-change.md](dictionary-change.md)

**common spec**：
- [common/md_form.md](../../../common/md_form.md)
- [common/md_field.md](../../../common/md_field.md)

**DDL 文档**：
- [md_form.md](../../../../../docs/backend/database/ddl/module/md_form.md)

**示例**：
- [examples/update_purchase_request_add_field.json](../../examples/update_purchase_request_add_field.json)