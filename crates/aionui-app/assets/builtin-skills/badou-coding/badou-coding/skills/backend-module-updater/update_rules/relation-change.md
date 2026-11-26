# relation-change.md

> **何时读**：`relations` 数组变化
> **配置项权威**：`.claude/skills/badou-coding/common/md_module_link.md`
> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_module_link.md`

---

## §1 relations 数组差分

**差分算法**：
1. 读取当前 `md_module_link` 中记录（`module_code` 匹配）
2. 对比新 JSON 中的 `relations` 数组
3. 新增关系：标记 `_action = 'add'`
4. 删除关系：标记 `_action = 'remove'`
5. 修改关系：标记 `_action = 'modify'`

## §2 md_module_link DELETE + INSERT 全量

**策略**：对当前 module 的 `md_module_link` 执行 DELETE + INSERT 全量。

```sql
DELETE FROM md_module_link WHERE module_code = ?;
-- 逐条 INSERT
INSERT INTO md_module_link (module_code, field_name, related_module_code, related_table, related_field, type, show_type, display_name, ...)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ...);
```

## §3 关联 SQL 重新生成

**关联查询 SQL 重新生成**：
- 基于当前 `relations` 数组
- 重新生成 `SELECT` 语句中的 JOIN 部分
- 更新 `md_module` 中 `list_sql` / `form_sql`（如果存在）

## 📎 引用清单

**相关规则文档**：
- [rules/field-add.md](field-add.md)
- [rules/resource-permission.md](resource-permission.md)

**common spec**：
- [common/md_module_link.md](../../../common/md_module_link.md)

**DDL 文档**：
- [md_module_link.md](../../../../../docs/backend/database/ddl/module/md_module_link.md)

**示例**：
- [examples/update_product_add_relation.json](../../examples/update_product_add_relation.json)