# button-change.md

> **何时读**：`buttons` 数组变化
> **配置项权威**：`.claude/skills/badou-coding/common/md_button.md`
> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_button.md`

---

## §1 按钮全量 DELETE + INSERT

**策略**：对 `md_button` 执行 DELETE + INSERT 全量策略。

```sql
DELETE FROM md_button WHERE module_code = ?;
-- 逐条 INSERT
INSERT INTO md_button (module_code, button_code, button_name, icon, sort_order, ...)
VALUES (?, ?, ?, ?, ?, ...);
```

## §2 新增按钮的资源自动生成

- 检测 `buttons` 数组新增条目
- 自动生成 `sys_resource` 记录（`resource_code = 'module_code:button_code'`）
- 自动生成 `sys_role_resource` 绑定（对于默认角色）

## §3 删除按钮的资源清理

- 检测 `buttons` 数组删除条目
- 清理 `sys_resource` 中对应 `resource_code` 记录
- 清理 `sys_role_resource` 中对应绑定

## 📎 引用清单

**相关规则文档**：
- [rules/resource-permission.md](resource-permission.md)
- [rules/data-migration-safety.md](data-migration-safety.md)

**common spec**：
- [common/md_button.md](../../../common/md_button.md)

**DDL 文档**：
- [md_button.md](../../../../../docs/backend/database/ddl/module/md_button.md)

**示例**：
- [examples/update_product_add_relation.json](../../examples/update_product_add_relation.json)