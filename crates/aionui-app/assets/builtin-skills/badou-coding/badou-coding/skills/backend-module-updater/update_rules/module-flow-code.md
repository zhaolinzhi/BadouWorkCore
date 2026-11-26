# module-flow-code.md

> **何时读**：`module.flow_code` 变化时
> **配置项权威**：`.claude/skills/badou-coding/common/md_flow.md`
> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_flow.md`

---

## §1 加 flow_code（从无流程变为有流程）

**5 步清理序列**：
1. 调用 `backend-flow-engine` 注册流程定义（`flow_code` + `flow_name`）
2. `UPDATE md_module SET flow_id = (SELECT id FROM md_flow WHERE flow_code = ?) WHERE code = ?`
3. `ALTER TABLE t_xxx ADD COLUMN bo_status varchar(16) DEFAULT NULL COMMENT '流程状态'`
4. 在 `md_field` 中插入 `bo_status` 字段定义（`field_name = 'bo_status'`，`nullable = true`）
5. 在 `md_form` 中插入 `bo_status` 表单配置（`editable = false`，`hidden = true`）

## §2 去 flow_code（从有流程变为无流程）

**反向清理**：
1. `ALTER TABLE t_xxx DROP COLUMN bo_status`
2. `DELETE FROM md_field WHERE module_code = ? AND field_name = 'bo_status'`
3. `DELETE FROM md_form WHERE module_code = ? AND field_name = 'bo_status'`
4. `UPDATE md_module SET flow_id = NULL WHERE code = ?`
5. 调用 `backend-flow-engine` 删除流程定义

## §3 改 flow_code（从流程 A 变为流程 B）

**综合清理**：
1. 执行去 flow_code 流程（清理旧流程）
2. 执行加 flow_code 流程（注册新流程）
3. 注意：`bo_status` 字段保留（无需 DROP + ADD）

## 📎 引用清单

**相关规则文档**：
- [rules/field-add.md](field-add.md)（bo_status 字段插入）
- [rules/form-config-change.md](form-config-change.md)（bo_status 表单配置）

**common spec**：
- [common/md_flow.md](../../../common/md_flow.md)
- [common/md_field.md](../../../common/md_field.md)
- [common/md_form.md](../../../common/md_form.md)

**DDL 文档**：
- [md_flow.md](../../../../../docs/backend/database/ddl/module/md_flow.md)
- [md_module.md](../../../../../docs/backend/database/ddl/module/md_module.md)

**示例**：
- [examples/update_server_rack_add_flow.json](../../examples/update_server_rack_add_flow.json)