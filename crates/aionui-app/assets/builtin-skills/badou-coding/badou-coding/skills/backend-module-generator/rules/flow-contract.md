# 流程引擎集成契约（CRUD 侧）

> **何时读**：`module.json` 带 `flow_code` 时。
> **关键约束**：流程 8 表（busi / flw_flow / flw_node / flw_route / flw_view_dictionary / comm_handler / comm_handler_instance）的**生成**由独立技能 `backend-flow-engine` 负责；本技能只负责契约对接。
> **配置项权威**：`.claude/skills/badou-coding/common/md_flow.md`（md_flow 配置项矩阵）
> **物理 schema 权威**：`.claude/docs/backend/database/ddl/module/md_flow.md`

<!-- Source: generated for backend-module-generator stability design, do not edit by hand without syncing the plan. -->

---

## §1 触发条件

`module.flow_code` 非空时，CRUD 生成器执行流程集成。

触发 generator 自动行为的 3 个条件（详见 `md_flow.md` §3.3）：

1. `module.flow_code` 在 module.json 中非空
2. `(SELECT id FROM flw_flow WHERE flow_code=:flow_code)` 子查询返回非 NULL
3. `(SELECT id FROM md_module WHERE code=:module_code)` 子查询返回非 NULL

> ⚠️ **顺序倒过来 = flow_id 关联失效**：必须先用 `backend-flow-engine` 创建 flw_flow，再用本技能生成模块。

### §1.1 配置项 → 详见 common spec

> 完整 md_flow 配置项矩阵（含 generator 写入策略 + 变更敏感度）见 `.claude/skills/badou-coding/common/md_flow.md` §2。

---

## §2 CRUD 侧自动行为

### §2.1 7 个固化字段自动注入

注入到业务表 DDL、md_field、md_form（`edit_type=hidden, editable=False`）：

| 字段 | 类型 |
|------|------|
| FLOW_ID | varchar(64) |
| FLOW_NAME | varchar(2000) |
| FLOW_INSTANCE_ID | varchar(64) |
| NODE_INSTANCE_ID | varchar(64) |
| NODE_INSTANCE_NAME | varchar(2000) |
| BO_STATUS | int(1) |
| NODE_CODE | varchar(64) |

> 字段定义规范详见 `field-config.md` §6。

### §2.2 BO_STATUS 字典自动注入

generator 自动写入 `comm_dictionary` + `comm_dictionary_item`：

| code | name_cn | items |
|------|---------|-------|
| BO_STATUS | 审批状态 | 0=草稿 / 1=审批中 / 2=已通过 / 3=已驳回 |

> 字典定义规范详见 `dictionary.md`。

### §2.3 flow_id 关联

generator 写入：

```sql
UPDATE md_module SET flow_id = (SELECT id FROM flw_flow WHERE code = '<flow_code>')
WHERE code = '<module_code>';
```

> ⚠️ **该 UPDATE 在 md_module 主行写入后立即执行**，依赖 flw_flow 已存在。

### §2.4 base_class 自动推断

`md_module.base_class` 用 `ModuleEntityFlowWithNodeCode`（非流程模块用 `ModuleEntityOnlyId`）。

### §2.5 cleanup 联动

cleanup.sql 追加流程表倒序清理（8 表）：

```
comm_handler_instance → comm_handler → flw_route → flw_node →
flw_flow → flw_view_dictionary → busi → md_module_link
```

---

## §3 禁止项

> 🚨 **以下字段定义会导致 Pydantic 硬阻断**：

| ❌ 禁止 | 原因 |
|---------|------|
| 在 fields 定义 `approval_status` | 由 BO_STATUS 承担 |
| 在 fields 定义 `audit_status` | 由 BO_STATUS 承担 |
| 在 fields 定义审批语义的 `status`（如 `comment="审核"`） | 由 BO_STATUS 承担 |

> 📖 校验实现见 `models/field.py::FieldDef.flow_business_name_not_in_fields`。

---

## §4 协作顺序

```
步骤 1：用 backend-flow-engine 创建 flw_flow
        flow_generator.py --flow-only flow.json --flow-execute

步骤 2：追加读本文件了解契约

步骤 3：写 module.json
        module.flow_code = "LEAVE_APPROVAL"
        module.flow_business_name_field = "applicant_name"  # 必须在 fields 中

步骤 4：生成模块
        crud_generator.py --def module.json
```

> 🚨 **顺序倒过来 = flow_id 关联失效**。

---

## §5 JSON 配置示例

```json
{
  "module": {
    "code": "leave_request",
    "flow_code": "LEAVE_APPROVAL",
    "flow_business_name_field": "applicant_name"
  },
  "fields": [
    {"field_name": "applicant_name", "display_type": "varchar", "comment": "申请人姓名", "nullable": true, "length": 50}
  ]
}
```

`flow_business_name_field` 必须存在于 `fields` 中，作为流程待办标题。

---

## §6 校验规则

| 校验 | 错误信息 |
|------|---------|
| `flow_code` 在 flw_flow 不存在 | "flow_code='<x>' 不在 flw_flow 中，请先用 backend-flow-engine 创建" |
| `flow_business_name_field` 不在 fields | "flow_business_name_field '<x>' 不在 fields 数组中" |
| fields 中定义 `approval_status` | Pydantic 阻断：flow 模块禁止定义该字段 |
| fields 中定义 `audit_status` | 同上 |

---

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口
- [rules/module-config.md](module-config.md) — module.flow_code 字段定义
- [rules/field-config.md](field-config.md) — §6 流程字段自动注入
- [rules/dictionary.md](dictionary.md) — BO_STATUS 字典三条件
- [rules/sql-execution.md](sql-execution.md) — §1 流程模块执行顺序
- [rules/data-safety.md](data-safety.md) — 流程 hidden 字段 nullable

**common spec**：
- [common/md_flow.md](../../../common/md_flow.md) — md_flow 配置项矩阵

**DDL 文档**：
- [md_flow.md](../../../../../docs/backend/database/ddl/module/md_flow.md) — 流程关联表结构
- `.claude/docs/backend/database/ddl/flow/flw_flow.md` — 流程定义表

**协作技能**：
- `backend-flow-engine` — flw_flow / flw_node / flw_route / comm_handler 生成

**示例**：
- [examples/module.json](../../examples/module.json) — leave_request 完整流程模块