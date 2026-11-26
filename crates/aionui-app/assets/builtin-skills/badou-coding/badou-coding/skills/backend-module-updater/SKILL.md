---
name: backend-module-updater
description: "基于现有 MD 模块的 JSON 配置进行 **增量更新，保留业务数据**。生成 ALTER TABLE + MD 元数据 UPSERT SQL。共享 backend-module-generator 的 models/validators，新增 update_rules/ 描述 13 种修改对象的更新方式（基础配置、字段增删改、字典变更、按钮变更、表单配置、关联关系、流程绑定、资源权限、数据迁移安全、幂等性、SQL 执行）。"
metadata:
  version: 1.0.0
  rules:
    - update_rules/module-basic-config.md
    - update_rules/module-flow-code.md
    - update_rules/field-add.md
    - update_rules/field-remove.md
    - update_rules/field-modify.md
    - update_rules/dictionary-change.md
    - update_rules/button-change.md
    - update_rules/form-config-change.md
    - update_rules/relation-change.md
    - update_rules/resource-permission.md
    - update_rules/data-migration-safety.md
    - update_rules/idempotency.md
    - update_rules/sql-execution.md
---

# backend-module-updater

## 🚨 工作原理

**一句话**：本技能基于现有 MD 模块的 JSON 配置，**增量更新** SQL（ALTER TABLE）和 **MD 元数据**（UPSERT），**保留业务数据**。`module.code` 改名走 `--mode=rebuild` flag（等同 generator 全量重建）。

### 生成产物

- ✅ 业务表 DDL 增量：`ALTER TABLE`（ADD COLUMN / MODIFY COLUMN / DROP COLUMN）
- ✅ MD 元数据 UPSERT：`md_module` UPDATE、`md_field` UPSERT（按 field_name）、`md_form` / `md_button` DELETE+INSERT、`md_module_link` DELETE+INSERT
- ✅ 数据字典 UPSERT：`comm_dictionary` / `comm_dictionary_item`
- ✅ 资源权限 UPSERT：`sys_resource` / `sys_role_resource`
- ✅ 流程绑定 UPDATE：`md_flow` + `md_module.flow_id`

### 与 backend-module-generator 的边界

| 维度 | generator | updater |
|---|---|---|
| 入口路由 | 场景 1/2/3（创建） | 场景 5（更新） |
| DDL 策略 | DROP + CREATE（业务表可空） | ALTER（保留业务数据） |
| 共享层 | models/、validators/、common/md_*.md | 同上 |
| 主入口脚本 | crud_generator.py | crud_updater.py |

### 适用场景

- 加 / 减 / 改 module.json 的 fields、dictionaries、buttons 数组
- 改 module 基础配置（base_class / list_js / form_js 等）
- 加 / 去 / 改 flow_code（流程集成）
- 改 relations 关联
- 加字典 + 字段 dict 绑定

### 不适用场景

- `module.code` 改名（需 `--mode=rebuild` flag + 用户确认，业务数据丢失）
- 跨模块更新（保持单 module.code 范围）

## 📚 规则文档索引

| 规则文件 | 何时读 | 职责 |
|---------|--------|------|
| `update_rules/module-basic-config.md` | **总是** | module.code / db_table / name_cn / menu_resource_code / base_class / list_js / form_js / description 变更 |
| `update_rules/module-flow-code.md` | **module.flow_code 变化时** | flow_code 加/去/改 + BO_STATUS 注入/清理 |
| `update_rules/field-add.md` | **fields 数组新增** | ALTER TABLE ADD + INSERT md_field |
| `update_rules/field-remove.md` | **fields 数组删除** | DROP COLUMN + 自动备份 + DELETE md_field |
| `update_rules/field-modify.md` | **fields 数组变更** | display_type / nullable / length / comment / dict 变更 |
| `update_rules/dictionary-change.md` | **dictionaries 数组变化** | comm_dictionary UPSERT + 字段 dict 绑定 |
| `update_rules/button-change.md` | **buttons 数组变化** | md_button DELETE+INSERT |
| `update_rules/form-config-change.md` | **form 段变化** | md_form DELETE+INSERT 全量 |
| `update_rules/relation-change.md` | **relations 数组变化** | md_module_link DELETE+INSERT |
| `update_rules/resource-permission.md` | **资源权限变化** | sys_resource UPSERT |
| `update_rules/data-migration-safety.md` | **任意破坏性 ALTER** | 备份 + 阻断 + 影响范围输出 |
| `update_rules/idempotency.md` | **任意重跑** | JSON 哈希检测 + 跳过 |
| `update_rules/sql-execution.md` | **执行前** | 执行顺序 + db_executor.py + @variable 单连接 |

## 📦 通用规则（common spec — 单一权威源）

> 所有 md_* 表的配置项矩阵 + 变更敏感度 + updater 兼容矩阵

| 文件 | 覆盖 |
|------|------|
| [common/README.md](../../../common/README.md) | 索引 |
| [common/md_module.md](../../../common/md_module.md) | md_module 46 列 |
| [common/md_field.md](../../../common/md_field.md) | md_field 21 列 |
| [common/md_form.md](../../../common/md_form.md) | md_form 52 列 |
| [common/md_flow.md](../../../common/md_flow.md) | md_flow 6 列 |
| [common/md_module_link.md](../../../common/md_module_link.md) | md_module_link 20 列 |
| [common/md_button.md](../../../common/md_button.md) | md_button 25 列（简）|
| [common/md_database.md](../../../common/md_database.md) | md_database 15 列（简）|