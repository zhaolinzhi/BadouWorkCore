# field-modify.md

> **何时读**：`fields` 数组条目变更
> **配置项权威**：`.claude/skills/badou-coding/common/md_field.md`
> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_field.md`

---

## §1 display_type 兼容性矩阵

| 源类型 | 目标类型 | 安全 | 说明 |
|--------|---------|------|------|
| varchar | text | ✅ 安全 | 长度增大会自动转为 text |
| text | varchar | ⚠️ 警告 | 截断风险，需用户确认 |
| int | varchar | ✅ 安全 | 隐式转换 |
| varchar | int | ❌ 拒绝 | 非数字值无法转换 |
| varchar | datetime | ❌ 拒绝 | 格式不兼容 |
| int | datetime | ❌ 拒绝 | 类型不兼容 |
| datetime | varchar | ✅ 安全 | 隐式转换 |

**安全变更**：`ALTER TABLE t_xxx MODIFY COLUMN <field_name> <new_type>(<new_length>)`。
**拒绝变更**：报错退出，提示用户手动处理。

## §2 length 变更

**放大**：`ALTER TABLE t_xxx MODIFY COLUMN <field_name> varchar(<new_length>)`（安全）。
**缩小**：拒绝执行，提示用户手动备份（截断风险）。

## §3 nullable / comment / dict 变更

**nullable 变更**：
- `nullable = false` → `true`：`ALTER TABLE t_xxx MODIFY COLUMN <field_name> <type> DEFAULT NULL`
- `nullable = true` → `false`：`ALTER TABLE t_xxx MODIFY COLUMN <field_name> <type> NOT NULL DEFAULT <default>`

**comment 变更**：`ALTER TABLE t_xxx MODIFY COLUMN <field_name> <type> COMMENT '<new_comment>'`。

**dict 绑定变更**：`UPDATE md_field SET dict_code = ? WHERE module_code = ? AND field_name = ?`。

## 📎 引用清单

**相关规则文档**：
- [rules/field-add.md](field-add.md)
- [rules/field-remove.md](field-remove.md)
- [rules/dictionary-change.md](dictionary-change.md)

**common spec**：
- [common/md_field.md](../../../common/md_field.md)

**DDL 文档**：
- [md_field.md](../../../../../docs/backend/database/ddl/module/md_field.md)

**示例**：
- [examples/update_purchase_request_add_field.json](../../examples/update_purchase_request_add_field.json)