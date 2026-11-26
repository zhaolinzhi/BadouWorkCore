---
name: backend-flow-engine
description: "流程引擎生成器：从 flow.json 生成工作流 8 表 SQL（busi/flw_flow/flw_node/flw_route/flw_view_dictionary/comm_handler/comm_handler_instance）。支持 --flow-only 独立生成、--flow-execute 直接部署、--flow-clean 仅清理。当业务模块需要审批流时，先用本技能创建 flw_flow，再用 backend-module-generator 带 flow_code 生成模块并关联。"
metadata:
  version: 1.0.0
  rules:
    - rules/FLOW-ENGINE.md
---

# backend-flow-engine

## 职责

生成工作流引擎配置数据 SQL：业务类型（busi）、流程定义（flw_flow）、环节（flw_node）、路由（flw_route）、视图（flw_view_dictionary）、处理人（comm_handler + comm_handler_instance）共 8 张表。

**不负责**业务模块的字段/表单/菜单生成--那是 `backend-module-generator` 的职责。两者通过 `flow_code` 契约协作：本技能造 `flw_flow`，CRUD 技能在 `module.json` 设 `flow_code` 关联它。

## 工作流程

```bash
# 1. 写 flow.json（流程定义：busi + nodes + routes）
# 2. 生成并部署流程 8 表
python3 flow_generator.py --flow-only flow.json --flow-execute
# 或仅预览
python3 flow_generator.py --flow-only flow.json
# 或仅清理
python3 flow_generator.py --flow-only flow.json --flow-clean
```

## 与 CRUD 技能的协作顺序

🚨 **顺序不能反**：先本技能创建 `flw_flow`，再 CRUD 技能带 `flow_code` 生成模块。反了则 `UPDATE md_module SET flow_id` 子查询查不到 `flw_flow`，关联失效。

## 输入：flow.json

见 `examples/flow.json`（请假审批：4 节点 5 路由）。字段规则见 `rules/FLOW-ENGINE.md`。

## 依赖

- `badou-md-common`（db_executor / config_loader / validator_core）
- 执行时需 `.trellis/.db-config.json`（`--flow-execute`）

## 校验

部署后用 `validators/flow_check.py` 校验流程 8 表一致性（busi/flw_flow/flw_node/flw_route/comm_handler 数量与关联）。
