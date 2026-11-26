# 流程引擎集成契约（CRUD 侧）

> 本文件说明：当 `module.json` 带 `flow_code` 时，CRUD 生成器如何与流程引擎协作。
> 流程 8 表的**生成**由独立技能 `backend-flow-engine` 负责；本技能只负责契约对接。

## 触发

`module.flow_code` 非空时，CRUD 生成器执行流程集成。

## CRUD 侧自动行为

1. **7 个固化字段**注入到业务表 DDL、md_field、md_form（`edit_type=hidden, editable=False`）：

   | 字段 | 类型 |
   |---|---|
   | FLOW_ID | varchar(64) |
   | FLOW_NAME | varchar(2000) |
   | FLOW_INSTANCE_ID | varchar(64) |
   | NODE_INSTANCE_ID | varchar(64) |
   | NODE_INSTANCE_NAME | varchar(2000) |
   | BO_STATUS | int(1)（审批状态：0草稿/1审批中/2已通过/3已驳回） |
   | NODE_CODE | varchar(64) |

2. **BO_STATUS 字典**自动注入（草稿/审批中/已通过/已驳回）。
3. **flow_id 关联**：生成 `UPDATE md_module SET flow_id = (SELECT id FROM flw_flow WHERE code = '<flow_code>')`。
4. **base_class**：`md_module.base_class` 用 `ModuleEntityFlowWithNodeCode`。
5. **cleanup 联动**：cleanup.sql 追加流程表倒序清理（comm_handler_instance/comm_handler/flw_route/flw_node/flw_flow/flw_view_dictionary/busi/md_module_link）。

## 禁止项

- ❌ 不得在 `fields` 定义 `approval_status`/`audit_status`/审批语义的 `status`--由 BO_STATUS 管理，Pydantic 会阻断。

## 协作顺序

🚨 先用 `backend-flow-engine` 创建 `flw_flow`，再用本技能带 `flow_code` 生成模块。反了则 `flow_id` 关联失效。

## JSON 配置

```json
{
  "module": {
    "code": "leave_request",
    "flow_code": "LEAVE_APPROVAL",
    "flow_business_name_field": "applicant_name"
  }
}
```

`flow_business_name_field` 必须存在于 `fields` 中，作为流程待办标题。
