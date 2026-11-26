# resource-permission.md

> **何时读**：资源权限变化（按钮/关系变更时自动同步）
> **配置项权威**：`.claude/docs/backend/database/ddl/module/sys_resource.md`
> **物理 schema**：`.claude/docs/backend/database/ddl/module/sys_resource.md`

---

## §1 sys_resource UPSERT（按 code 对齐）

```sql
INSERT INTO sys_resource (resource_code, resource_name, resource_type, parent_code, ...)
VALUES (?, ?, ?, ?, ...)
ON DUPLICATE KEY UPDATE resource_name = ?, resource_type = ?, ...;
```

**命名规则**：`resource_code = 'module_code:button_code'`（按钮级）或 `'module_code:menu'`（菜单级）。

## §2 sys_role_resource 在 button 变更时自动同步

**新增按钮**：
- 创建 `sys_resource` 记录
- 为默认角色绑定 `sys_role_resource`（`role_id = 'admin'`）

**删除按钮**：
- 删除 `sys_resource` 记录
- 清理 `sys_role_resource` 中对应绑定

## §3 sys_role_resource 在 relation 变更时自动同步

**新增 relation**：
- 如果 relation 有 `display_name`，创建对应 `sys_resource` 记录
- 为默认角色绑定 `sys_role_resource`

**删除 relation**：
- 清理 `sys_resource` 中对应记录
- 清理 `sys_role_resource` 中对应绑定

## 📎 引用清单

**相关规则文档**：
- [rules/button-change.md](button-change.md)
- [rules/relation-change.md](relation-change.md)

**common spec**：
- [common/md_module.md](../../../common/md_module.md)

**DDL 文档**：
- [sys_resource.md](../../../../../docs/backend/database/ddl/module/sys_resource.md)

**示例**：
- [examples/update_product_add_relation.json](../../examples/update_product_add_relation.json)