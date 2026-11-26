# module-basic-config.md

> **何时读**：总是（任意 module 基础配置变更）
> **配置项权威**：`.claude/skills/badou-coding/common/md_module.md`
> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_module.md`

---

## §1 配置项变更路径与 SQL 模板

### module.code 改名

**行为**：`--mode=rebuild` flag + 用户确认。等同 generator 全量重建，**业务数据丢失**。
**阻断条件**：`--mode=update` 下检测到 `code` 变更 → 报错退出。

### db_table 变更

**行为**：`RENAME TABLE old_name TO new_name`。
**注意**：仅当表名确实变更时执行；检查 `t_xxx` 前缀一致性。

### name_cn / description 变更

**行为**：`UPDATE md_module SET name_cn = ? / description = ? WHERE code = ?`。

### base_class / list_js / form_js / view_js 变更

**行为**：`UPDATE md_module SET base_class = ? / list_js = ? / form_js = ? / view_js = ? WHERE code = ?`。

### menu_resource_code 变更

**行为**：`UPDATE md_module SET menu_resource_code = ? WHERE code = ?`。
**联动**：同步更新 `sys_resource` 中对应 `resource_code` 记录。

## §2 配置项变更敏感度矩阵

| 配置项 | 敏感度 | 安全策略 |
|--------|--------|----------|
| `module.code` | 🔴 破坏性 | 仅 rebuild 模式 |
| `db_table` | 🟡 中等 | RENAME TABLE |
| `name_cn` / `description` | 🟢 安全 | UPDATE 仅 |
| `base_class` / `list_js` / `form_js` / `view_js` | 🟢 安全 | UPDATE 仅 |
| `menu_resource_code` | 🟡 中等 | UPDATE + 联动 |

## §3 典型场景：修改 module 基础配置

1. 用户修改 module.json 中的 `name_cn` 或 `description`
2. updater 检测到 `module.name_cn` 或 `module.description` 变化
3. 生成 `UPDATE md_module SET name_cn = ? WHERE code = ?`
4. 输出到 `output/<module.code>/update.sql`

## 📎 引用清单

**相关规则文档**：
- [rules/field-add.md](field-add.md)
- [rules/module-flow-code.md](module-flow-code.md)

**common spec**：
- [common/md_module.md](../../../common/md_module.md)

**DDL 文档**：
- [md_module.md](../../../../../docs/backend/database/ddl/module/md_module.md)

**示例**：
- [examples/update_purchase_request_add_field.json](../../examples/update_purchase_request_add_field.json)