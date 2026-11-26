---
name: backend-module-generator-flow-integration
description: 流程引擎集成 SQL
parent_skill: backend-module-generator
related_table: md_module, flw_flow, flw_node, flw_route
---

# 子技能: 流程引擎集成 SQL

## 对应文件

- `generators/flow_integration.py`
- `generators/flow_cleanup.py`

## 写入内容

UPDATE md_module SET flow_id（子查询反查）+ 清理流程引擎 SQL

## 关键规则

- flow_code 不为空时自动使用 ModuleEntityFlowWithNodeCode
- flow_integration.py 回填 flow_id
- flow_cleanup.py 清理顺序：comm_handler_instance → ... → busi
- flow 字段自动注入 7 个
- 清理 SQL 仅在 generate_cleanup_sql() 中调用