# md_flow 配置项矩阵

> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_flow.md`
> **覆盖**：6 列
> **详/简**：详

## §1 表概述

- **用途**：桥接 MD 模块与 BPM 流程引擎（flw_flow / flw_node / flw_route）；每行 = 一个流程关联
- **与 generator 关系**：`flow_integration.py` 写入；流程字段（BO_STATUS 等）由本表存在触发自动注入到 md_field
- **关键含义**：流程模块与 CRUD 模块的耦合点

## §2 配置项矩阵

| 列名 | 类型 | 写入策略 | 用户提供 | 默认 | 合法值 | 敏感度 |
|------|------|---------|---------|------|--------|--------|
| `id` | varchar(64) | auto-inject | — | UUID | UUID | metadata-only |
| `route_id` | varchar(64) | user-required | `flow.json` route id | — | flw_route.id | forbidden（route_id 是身份）|
| `route_name` | varchar(256) | user-optional | `flow.json` route name | — | 路由名 | metadata-only |
| `module_id` | varchar(64) | auto-inject | — | 当前 module.id | UUID | forbidden |
| `class_path` | varchar(256) | user-optional | `flow.json` handler | — | Java class FQN | metadata-only |
| `param` | varchar(256) | user-optional | `flow.json` handler param | — | JSON 字符串 | metadata-only |

## §3 updater 兼容矩阵

| 变更类型 | 行为 | DDL |
|---|---|---|
| 加流程（`module.flow_code` 从空 → 非空）| 调 `backend-flow-engine` 创建 flow → 注入 BO_STATUS 到 md_field + ALTER TABLE | ddl-safe |
| 去流程（`module.flow_code` 从非空 → 空）| DROP BO_STATUS 字段 + DELETE md_flow 行 | **ddl-risky**（先备份业务表）|
| 改流程（`module.flow_code` 变值）| 调 backend-flow-engine 删旧 + 建新 + 重新注入 BO_STATUS | ddl-safe |
| 改 route_name / class_path / param | metadata-only | UPDATE md_flow |

## 📎 引用

- 物理 schema：`.claude/docs/backend/database/ddl/module/md_flow.md`
- generator rule：`.claude/skills/badou-coding/skills/backend-module-generator/rules/flow-contract.md`
- updater rule：`.claude/skills/badou-coding/skills/backend-module-updater/update_rules/module-flow-code.md`
- 协作：`skills/backend-flow-engine/SKILL.md`
