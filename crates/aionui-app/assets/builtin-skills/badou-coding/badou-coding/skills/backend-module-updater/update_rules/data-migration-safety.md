# data-migration-safety.md

> **何时读**：任意破坏性 ALTER 操作前
> **配置项权威**：`.claude/skills/badou-coding/common/md_module.md`、`.claude/skills/badou-coding/common/md_field.md`（变更敏感度）
> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_field.md`

---

## §1 破坏性 ALTER 拦截清单

以下操作被列为**破坏性**，需用户确认：

| 操作 | 风险 |
|------|------|
| `DROP COLUMN` | 数据丢失 |
| `length 缩小` | 截断风险 |
| 不兼容 `display_type` 变更（如 `varchar → int`） | 数据转换失败 |
| `module.code` 变更 | 业务数据丢失（需 rebuild） |
| `nullable = true → false` | 数据完整性风险 |

## §2 自动备份机制

**触发条件**：任意破坏性 ALTER。

**备份内容**：
- 受影响表全量数据备份：`CREATE TABLE t_xxx__bak_<timestamp> AS SELECT * FROM t_xxx`
- 受影响 `md_*` 表快照：`SELECT * INTO OUTFILE 'backup/md_xxx_<timestamp>.sql'`

**备份路径**：`output/<module.code>/backup/<timestamp>/`

## §3 影响范围输出

**输出格式**：
```
影响范围：
  - 表：t_purchase_request（10 行数据）
  - 字段：supplier_phone（20 条记录非空）
  - 表单：3 行 md_form 引用
  - 关联：1 行 md_module_link 引用
```

**用户确认机制**：输出影响范围后，等待用户键入 `y` 或 `yes` 确认；输入其他内容退出。

## 📎 引用清单

**相关规则文档**：
- [rules/field-remove.md](field-remove.md)
- [rules/field-modify.md](field-modify.md)
- [rules/idempotency.md](idempotency.md)

**common spec**：
- [common/md_module.md](../../../common/md_module.md)
- [common/md_field.md](../../../common/md_field.md)

**DDL 文档**：
- [md_field.md](../../../../../docs/backend/database/ddl/module/md_field.md)

**示例**：
- [examples/update_purchase_request_add_field.json](../../examples/update_purchase_request_add_field.json)