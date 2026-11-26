# field-remove.md

> **何时读**：`fields` 数组删除条目
> **配置项权威**：`.claude/skills/badou-coding/common/md_field.md`
> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_field.md`

---

## §1 删除字段：自动备份

**DROP COLUMN 前自动备份**：
```sql
CREATE TABLE t_xxx__bak_<timestamp> AS SELECT * FROM t_xxx;
```

**备份文件路径**：`output/<module.code>/backup/t_xxx__bak_<ts>.sql`。

## §2 影响范围输出

**删除字段前输出影响范围**：
- 列出所有引用此字段的 `md_form` 行（`field_name` 匹配）
- 列出所有引用此字段的 `md_button` 配置（`condition_field` 等）
- 列出所有引用此字段的 `md_module_link` 配置（`field_name` 匹配）
- 用户确认后方可执行 DROP

## §3 删除元数据索引

```sql
DELETE FROM md_form WHERE module_code = ? AND field_name = ?;
DELETE FROM md_field WHERE module_code = ? AND field_name = ?;
```

**注意**：字段删除后，任何引用此字段的 `md_form` 行也被删除。

## 📎 引用清单

**相关规则文档**：
- [rules/field-modify.md](field-modify.md)
- [rules/data-migration-safety.md](data-migration-safety.md)

**common spec**：
- [common/md_field.md](../../../common/md_field.md)
- [common/md_form.md](../../../common/md_form.md)

**DDL 文档**：
- [md_field.md](../../../../../docs/backend/database/ddl/module/md_field.md)

**示例**：
- [examples/update_purchase_request_add_field.json](../../examples/update_purchase_request_add_field.json)