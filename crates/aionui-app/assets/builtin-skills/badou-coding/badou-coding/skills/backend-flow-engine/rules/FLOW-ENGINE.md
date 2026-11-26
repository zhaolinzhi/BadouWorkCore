# 流程引擎生成规则（flw_engine）

> **用途**: 定义和生成工作流引擎配置数据，包括业务类型、流程定义、环节、路由、视图、处理人。
> **适用条件**: 输入 JSON 中包含 `flow` 根对象。
> **前置要求**: 必须已阅读 `rules/BASIC-CRUD.md`，基础 CRUD 规则是本规则的前提。

---

## 🚨 第一原则：流程集成不需要审批状态字段

> **BO_STATUS 就是审批状态。不要再额外定义 `approval_status`、`audit_status`、`status` 等审批状态字段。**

### 为什么？

当 CRUD 模块的 `flow_code` 不为空时，生成器**自动注入 7 个流程固化字段**到业务表的 DDL、md_field、md_form：

| 字段 | 说明 |
|------|------|
| `FLOW_ID` | 流程实例ID |
| `FLOW_NAME` | 流程实例名称 |
| `FLOW_INSTANCE_ID` | 流程实例唯一标识 |
| `NODE_INSTANCE_ID` | 环节实例ID |
| `NODE_INSTANCE_NAME` | 环节实例名称 |
| **`BO_STATUS`** | **业务状态（即审批状态）** |
| `NODE_CODE` | 当前环节编码 |

**`BO_STATUS` 就是流程的审批状态字段**，由流程引擎在流转过程中自动维护：
- `0` = 草稿
- `1` = 审批中
- `2` = 已通过
- `3` = 已驳回

**你不需要、也不应该在 JSON 中定义任何审批状态相关的字段。如果定义了，Pydantic 模型会报错并阻止生成。**

### 实操规则

| 场景 | 做法 | 说明 |
|------|------|------|
| 在 `fields` 中定义 `approval_status` | ❌ **Pydantic 阻断，报错** | `BO_STATUS` 已自动注入 |
| 在 `fields` 中定义 `audit_status` | ❌ **Pydantic 阻断，报错** | `BO_STATUS` 已自动注入 |
| 在 `fields` 中定义 `status`（且 commentTUS` 已自动注入 |\n| 在 `fields` 中定义 `status`（且 comment 为"审批状态"） | ⚠️ **模糊匹配警告** | 请确认不是审批状态 |\n| 在 `fields` 中定义 `status`（且 comment 为"商品状态"） | ✅ 通过 | 只要不是审批语义就没问题 |\n| 在 `dictionaries` 中定义 `status` 字典 | ✅ 通过 | 只要不与 BO_STATUS 字典冲突 |\n\n> **简单记忆：流程相关的审批状态只用 BO_STATUS。你的 JSON 只需要定义业务字段（申请人、请假类型、天数等）。**\n\n---"}]

## 1. 概述

流程引擎由以下 8 张表构成闭环：

```
busi (业务定义)                  ← 流程绑定的业务类型
  │
flw_flow (流程定义)               ← 流程主定义
  │
flw_node (流程环节)                ← 流程的每个处理节点
  │  ├── handler → comm_handler.ID ← 处理人规则主表（新增）
  │  ├── view_id → flw_view_dictionary.id
  │  └── handle_way → flw_handle_way.id
  │
├── comm_handler (处理人规则)         ← 每个 flw_node 对应一条
│   └── ID ← comm_handler_instance.HANDLER_ID
├── comm_handler_instance (处理人实例) ← 每个 comm_handler 对应一条
│
flw_route (环节路由)              ← 节点间的流转路径
flw_view_dictionary (流程视图)     ← 节点的处理页面（按 busi 动态生成）

处理人关联关系：
flw_node.handler ──→ comm_handler.ID ──→ comm_handler_instance.HANDLER_ID
```

---

## 2. 核心规则

### 规则1：busi — 业务定义

| 字段 | 必填 | 默认值 | 规则 |
|------|------|--------|------|
| code | ✅ UNIQUE | - | 业务编码，全局唯一 |
| NAME | ✅ | - | 业务名称 |
| BUSI_INSTANCE_CLASS | ✅ | `com.badou.designer.module.design.base.ModuleEntityFlowWithNodeCode` | 业务实例类 |
| BUSI_INSTANCE_MODULE | 否 | - | 关联模块 code（与模型设计器的连接点） |
| FLG_BATCH | 否 | 1 | 批量标识 |
| FLG_USE | 否 | 1 | 启用标识（0=停用） |
| PRIORITY | 否 | 1 | 排序 |

**生成逻辑**：
- 每个 flow 先检查 `busi.code` 是否已存在，存在则跳过
- `BUSI_INSTANCE_CLASS` 使用默认值，可在 JSON 中覆盖
- 生成 UUID 作为 id

### 规则2：flw_view_dictionary — 流程视图

> 视图数据根据 busi 动态生成，非基础数据表。

**每个 busi 生成 2 条视图：**

| name | view_url | 适用节点 |
|------|----------|---------|
| **{busi_name}-编辑** | `/module/flow/workEdit/${id}` | 起始节点（编辑） |
| **{busi_name}-审批** | `/module/flow/tableView/${id}/1` | 审批节点 |

> ⚠️ **name 字段格式**：必须使用 `"业务名称-视图类型"` 格式，如 `"请假-编辑"`、`"请假-审批"`。
> 禁止使用裸名称如 "编辑"、"审批"，以避免不同业务间视图名称冲突。

**字段规则**：
- `busi` = busi.code
- `ways` = flw_handle_way.id（默认 1=串行审核）
- `busi_name` = busi.NAME
- `priority` = 1

**视图分配规则**：
- 起始节点（flg_head=1）使用**编辑**视图
- 审批节点（flg_head=0）使用**审批**视图
- 结束节点（code='end'）无需视图

### 规则3：flw_flow — 流程定义

| 字段 | 必填 | 默认值 | 规则 |
|------|------|--------|------|
| org_id | 否 | `ROOT` | 组织ID |
| code | ✅ UNIQUE | - | **流程编码**，全局唯一 |
| flow_name | ✅ | - | 流程名称 |
| busi_type | ✅ | - | 业务类型（关联 busi.code） |
| memo | 否 | - | 备注 |
| flg_allow_modify | 否 | 1 | 允许修改 |
| priority | 否 | - | 排序 |
| flg_deleted | 否 | 0 | 逻辑删除 |

**生成逻辑**：
- 每次生成一条流程定义
- `busi_type` 与 JSON 中 busi.code 一致

### 规则4：comm_handler — 处理人规则主表（新增）

> 每个 flw_node 在生成数据时**同步生成**一条 comm_handler 记录。

| 字段 | 必填 | 默认值 | 规则 |
|------|------|--------|------|
| ID | ✅ PK | - | UUID（32位hex），**flw_node.handler 字段引用此值** |
| DESCRIPTION | 否 | NULL | 描述信息，可选 |

**生成规则**：
- 每个 flw_node 生成一条 comm_handler 记录
- ID 使用新的 UUID
- DESCRIPTION 默认为 NULL
- flw_node.handler 字段**不再使用 processor_value 第三段**，而是引用 comm_handler.ID

### 规则5：comm_handler_instance — 处理人规则实例表（新增）

> 每条 comm_handler 数据生成时**同步生成**一条 comm_handler_instance 记录。

| 字段 | 必填 | 默认值 | 规则 |
|------|------|--------|------|
| ID | ✅ PK | - | 新 UUID |
| HANDLER_ID | ✅ | - | **引用 comm_handler.ID** |
| RULE_ID | ✅ | **0** | **处理人规则ID**，默认为 0（环节处理人），对应 comm_handler_rule.ID |
| ORG_TYPE | ✅ | - | **处理人类型**，从 `node_processor_value` 第一段解析（如 20, 1） |
| HANDLER_NAME | ✅ | - | **处理人名称**，从 `node_processor_value` 第二段解析 |
| ORG_ID | ✅ | - | **处理人ID**，从 `node_processor_value` 第三段解析 |
| PRIORITY | 否 | 0 | 序号 |
| SCALE | 否 | 1.000000 | 权重因子 |
| STF_CFG_ID | 否 | NULL | 未使用 |
| REFER_HANDLER_ID | 否 | NULL | 参考处理人ID，未使用 |

**字段映射规则**（从 node_processor_value 解析）：

```
node_processor_value = "20!@!超级管理员!@!U00001"
                              │           │        │
                              ▼           ▼        ▼
                         ORG_TYPE   HANDLER_NAME ORG_ID
                            =20       =超级管理员  =U00001
```

**node_processor_value 各段对应**：

| processor_value 段 | comm_handler_instance 字段 | 示例 |
|-------------------|--------------------------|------|
| 第一段（类型码） | ORG_TYPE（**见下方特殊规则**） | 20 |
| 第二段（名称） | HANDLER_NAME | `超级管理员` |
| 第三段（引用ID） | ORG_ID | U00001 |

**ORG_TYPE 特殊规则**：
- 当 `node_handler_type = 1`（抽象处理人）时，ORG_TYPE **强制为 100**，不取 processor_value 第一段
- 其他情况（type=0/20/40），ORG_TYPE 取 processor_value 第一段的值

**RULE_ID 默认规则**：
- 默认为 **0**（环节处理人，对应 comm_handler_rule.ID=0）
- 特殊场景（如拟稿人/填报人）可在 JSON handler 定义中显式覆盖

### 规则6：flw_node — 流程环节

#### 6.1 字段定义

| 字段 | 必填 | 默认值 | 规则 |
|------|------|--------|------|
| flow_id | ✅ | - | 所属流程（@variable 引用） |
| code | ✅ | - | 节点编码（如 START, REVIEW_01, end） |
| node_name | ✅ | - | 节点名称 |
| handle_way | 否 | - | 处理方式（FK → flw_handle_way.id） |
| node_handler_type | **✅** | **20** | **环节处理人类型（NOT NULL, 默认20, 取值0/1/20/40）** |
| node_processor_value | ✅ | - | **处理人值，见 6.3** |
| node_processor_text | ✅ | - | **处理人显示文本，见 6.3** |
| handler | **✅** | - | **comm_handler.ID（不再使用 processor_value 第三段）** |
| view_id | ✅ | - | 视图ID（@variable 引用） |
| view_name | ✅ | - | 视图名称（`{busi_name}-编辑` 或 `{busi_name}-审批`） |
| priority | ✅ | - | 节点排序 |
| flg_head | **✅** | **0** | **是否首环节（NOT NULL, 默认0, 第一个环节=1）** |
| flg_root | **✅** | **0** | **是否结束环节（NOT NULL, 默认0, 结束环节=1）** |
| flg_prev_over | 否 | 1 | 前一节点是否结束 |
| flg_deleted | 否 | 0 | 逻辑删除 |
| flg_allow_delete | 否 | 1 | 允许删除 |
| flg_allow_modify | 否 | 1 | 允许修改 |
| window_type | 否 | 0 | 窗口类型 |
| submittype | 否 | 0 | 提交类型 |
| flg_submit_sync | 否 | 1 | 是否同步提交 |
| node_handler_scope | 否 | 1 | 处理人范围 |
| **automatic_terminate** | **✅** | **0** | **自动提交（NOT NULL, 默认0）** |
| **flg_spread** | **✅** | **0** | **环节是否需要传阅属性（NOT NULL, 默认0。所有节点设0）** |

> ⚠️ **automatic_terminate**：该字段在数据库中不允许为空，INSERT 时必须明确赋值为 0。
> 所有节点（包括结束节点）都必须包含此字段。

> ⚠️ **flg_spread**：该字段不允许为空，INSERT 时必须明确赋值为 0。
> 所有节点（包括结束节点）都必须包含此字段。

**时限相关字段**：

| 字段 | 必填 | 默认值 | 规则 |
|------|------|--------|------|
| timelimit_relate_yq | 否 | 0 | 时限：相对年季 |
| timelimit_relate | 否 | 0 | 时限：相对月份 |
| timelimit_date | 否 | 0 | 时限：日期 |
| timelimit_flg_apply | 否 | 0 | 时限：应用（0=不应用, 1=应用） |
| timellimt_house | 否 | 0 | 时限：收到待办小时 |

**传阅相关字段**：

| 字段 | 必填 | 默认值 | 规则 |
|------|------|--------|------|
| flg_spread | **✅** | **0** | 环节是否需要传阅属性（NOT NULL, 默认0） |
| flg_spread_allow | 否 | **1** | 是否允许处理人发待阅（默认1） |

#### 6.2 处理人类型（node_handler_type）

| 值 | 含义 | processor_value 格式 |
|----|------|---------------------|
| **1** | **抽象处理人** | `1!@!{规则名称}!@!{规则ID}` |
| **20** | **指定用户** | `20!@!{用户名称}!@!{用户ID}` |
| **0** | **指定部门** | `0!@!{部门名称}!@!{部门ID}` |
| **40** | **指定角色** | `40!@!{角色名称}!@!{角色ID}` |

#### 6.3 处理人值生成规则（核心）

处理人值（`node_processor_value`）**禁止随意杜撰**，必须从数据库对应表中查询真实数据。

**数据来源映射**：

| node_handler_type | 查询表 | ID来源字段 | 显示名称字段 |
|:-----------------:|--------|-----------|-------------|
| 1 | `comm_handler_rule` | `ID` | `NAME` |
| 20 | `sys_user` ↔ `sys_user_comminfo` | `sys_user.id` | `sys_user_comminfo.name` |
| 0 | `sys_org` | `id` | `name` |
| 40 | `sys_role` | `id` | `name` |

**value 格式**：`{type}!@!{显示名称}!@!{查询到的ID}`

- 三段式，`!@!` 分隔
- 第一段 = node_handler_type，与字段值一致
- 第二段 = 显示名称，与 node_processor_text 一致
- 第三段 = 从数据库查到的真实 ID（UUID，type=1 时为 comm_handler_rule.ID 的小整数如 3）

#### ⚠️ type=1（抽象处理人）第三段特殊规则

> **type=1 的第三段不能填 `0`！它必须是 comm_handler_rule 表中对应规则的真实 ID。**

**常见错误**：Agent 以为第三段 `0` 是占位符，实际上它决定了 `comm_handler_instance` 表的 `ORG_ID` 和 `RULE_ID` 两个字段的值。

**常用 comm_handler_rule ID：**

| ID | 规则名称 | 用途 |
|:--:|---------|------|
| **3** | **拟稿人/填报人** | **首环节默认规则（最常用）** |
| 2 | 审批人 | 普通审批节点 |
| 6 | 部门负责人 | 按部门的审批规则 |
| 4 | 主管领导 | 主管领导审批 |
| 5 | 会签人 | 多人会签规则 |

**type=1 的正确写法：**

```json
// ✅ 正确：第三段填 comm_handler_rule.ID
{"type": 1, "value": "1!@!拟稿人/填报人!@!3", "text": "拟稿人/填报人"}

// ❌ 错误：第三段填 0（Agent 典型幻觉）
{"type": 1, "value": "1!@!拟稿人/填报人!@!0", "text": "拟稿人/填报人"}
// → Pydantic 直接阻断，报错提示正确的 ID
```

**type=1 第三段与其他 type 的区别：**

| 类型 | 第三段含义 | 取值示例 | 说明 |
|:---:|-----------|---------|------|
| 1 | comm_handler_rule.ID | `3`（小整数） | 不是 0，不是 UUID |
| 20 | sys_user.id | `U00001`（字符串） | 用户表主键 |
| 0 | sys_org.id | UUID | 部门表主键 |
| 40 | sys_role.id | UUID | 角色表主键 |

**数据库不可用时的保底策略**：

当无法连接数据库查询真实数据时，使用以下默认值：

| 字段 | 值 |
|------|-----|
| node_handler_type | **20** |
| node_processor_value | **`20!@!超级管理员!@!U00001`** |
| node_processor_text | **`超级管理员`** |

即默认指定「超级管理员」作为处理人。

#### 6.4 节点编码约定

- 非结束节点使用英文编码（如 `START`, `REVIEW_01`）
- 结束节点固定编码 `end`

#### 6.5 节点排序规则

- 起始节点 priority = 0
- 审批节点按顺序递增（1, 2, 3...）
- 结束节点 priority = 999999（固定）

#### 6.6 结束节点规则

- code = 'end'
- node_name = '结束'
- 使用简化的 INSERT（不含 view 相关字段，但含 handler 相关字段）
- `flg_head = 0`（不是首环节）
- **`flg_root = 1`**（是结束环节）
- `automatic_terminate = 0`
- 也生成对应的 comm_handler 和 comm_handler_instance（使用保底值）

#### 6.7 handler 字段规则（修正）

**⚠️ 重要修正**：`handler` 字段值**不再是** `node_processor_value` 的第三段。

`handler` 字段值为**新生成的 comm_handler.ID**（UUID）：

```
生成流程：
1. 生成 comm_handler 记录（UUID = handler_id）
2. 设置 flw_node.handler = handler_id
3. 生成 comm_handler_instance（HANDLER_ID = handler_id）
```

**生成顺序**（每个节点）：
1. `comm_handler` INSERT（ID = handler_uuid）
2. `comm_handler_instance` INSERT（HANDLER_ID = handler_uuid, 字段从 processor_value 解析）
3. `flw_node` INSERT（handler = handler_uuid）

#### 6.8 首环节/结束环节字段规则

| 字段 | 约束 | 首环节 | 审批节点 | 结束节点 |
|------|------|--------|---------|---------|
| `flg_head` | NOT NULL, 默认0 | **1** | 0 | 0 |
| `flg_root` | NOT NULL, 默认0 | 0 | 0 | **1** |

- `flg_head`：NOT NULL，默认 0。**仅首环节（flg_head=1）** 设为 1，其余所有节点为 0
- `flg_root`：NOT NULL，默认 0。**仅结束节点（code='end'）** 设为 1，其余所有节点为 0
- 所有节点 INSERT 必须显式包含这两个字段，不可省略

### 规则7：flw_route — 环节路由

| 字段 | 必填 | 默认值 | 规则 |
|------|------|--------|------|
| node_id | ✅ | - | 起始节点（@variable 引用） |
| next_node_id | ✅ | - | 目标节点（@variable 引用） |
| menu_name | ✅ | - | **按钮显示名称**（如"提交"、"通过"、"退回"） |
| name | ✅ | - | 路由名称 |
| priority | ✅ | 0 | **按钮排序**（同一节点内递增） |
| flg_attribute | ✅ | - | **路由属性**：GOAHEAD=前进, BACK=后退 |
| flg_multi_node | ✅ | 0 | **多节点标识**：0=普通, 1=多目标, 2=多目标单向 |
| code | ✅ | - | 路由编码 |
| flg_deleted | 否 | 0 | 逻辑删除 |
| is_save | 否 | 0 | 是否保存 |
| valid_handler | 否 | 0 | 验证处理器 |
| iz_need_opinion | 否 | 1 | 是否需要意见 |

**路由属性含义**：

| flg_attribute | 含义 | 典型 menu_name |
|--------------|------|----------------|
| **GOAHEAD** | 前进路由 | 提交、通过、提交审批 |
| **BACK** | 后退路由 | 退回、驳回 |

---

## 3. SQL 生成模板

### 3.1 busi INSERT
```sql
INSERT INTO busi (id, code, NAME, BUSI_INSTANCE_CLASS, BUSI_INSTANCE_MODULE,
    FLG_BATCH, FLG_USE, PRIORITY)
VALUES ('{uuid}', '{busi_code}', '{busi_name}',
    '{instance_class}', '{module_code}', 1, 1, 1);
```

### 3.2 flw_view_dictionary INSERT（name 使用 "{busi_name}-编辑/审批" 格式）
```sql
-- {busi_name}-编辑
INSERT INTO flw_view_dictionary (id, name, busi, ways, view_url,
    preview_url, spread_url, done_url, priority, busi_name)
VALUES ('{uuid}', '{busi_name}-编辑', '{busi_code}', '1',
    '/module/flow/workEdit/${id}', '/module/flow/view/${id}',
    '/module/flow/view/${id}', '/module/flow/view/${id}', 1, '{busi_name}');

-- {busi_name}-审批
INSERT INTO flw_view_dictionary (id, name, busi, ways, view_url,
    preview_url, spread_url, done_url, priority, busi_name)
VALUES ('{uuid}', '{busi_name}-审批', '{busi_code}', '1',
    '/module/flow/tableView/${id}/1', '/module/flow/tableView/${id}/1',
    '/module/flow/tableView/${id}/1', '/module/flow/tableView/${id}/1', 1, '{busi_name}');
```

### 3.3 flw_flow INSERT
```sql
INSERT INTO flw_flow (id, org_id, code, flow_name, busi_type, memo,
    flg_allow_modify, priority, flg_deleted)
VALUES ('{uuid}', 'ROOT', '{flow_code}', '{flow_name}',
    '{busi_code}', '{memo}', 1, 0, 0);
```

### 3.4 comm_handler INSERT（新增 — 每个节点一条）
```sql
INSERT INTO comm_handler (ID, DESCRIPTION)
VALUES ('{handler_uuid}', NULL);
```

### 3.5 comm_handler_instance INSERT（新增 — 每个 comm_handler 一条）
```sql
INSERT INTO comm_handler_instance (ID, RULE_ID, HANDLER_ID,
    ORG_TYPE, HANDLER_NAME, ORG_ID, PRIORITY, SCALE)
VALUES ('{instance_uuid}', 0, '{handler_uuid}',
    {org_type}, '{handler_name}', '{org_id}',
    0, 1.000000);
```

### 3.6 flw_node INSERT（含 automatic_terminate）

**非结束节点:**
```sql
INSERT INTO flw_node (id, flow_id, code, node_name, handle_way,
    node_handler_type, node_processor_value, node_processor_text,
    handler,
    view_id, view_name, priority, flg_head, flg_root,
    flg_deleted, flg_allow_delete, flg_allow_modify, window_type,
    submittype, flg_submit_sync, node_handler_scope, flg_prev_over,
    automatic_terminate, flg_spread, flg_spread_allow,
    timelimit_relate_yq, timelimit_relate, timelimit_date,
    timelimit_flg_apply, timellimt_house)
VALUES ('{uuid}', '{flow_id}', '{node_code}', '{node_name}',
    {handle_way}, {handler_type}, '{processor_value}', '{processor_text}',
    '{handler_uuid}',  -- ⚠️ 现在引用 comm_handler.ID，不再是 processor_value 第三段
    '{view_id}', '{view_name}', {priority}, {flg_head}, {flg_root},
    0, 1, 1, 0, 0, 1, 1, 1,
    0, 0, 1,
    0, 0, 0,
    0, 0);
```

> ⚠️ **handler** 字段值现在为 **comm_handler.ID**（UUID），不再从 processor_value 提取。

**结束节点（简化 INSERT）:**
```sql
INSERT INTO flw_node (id, flow_id, code, node_name, priority,
    flg_head, flg_root,
    flg_deleted, flg_allow_delete, flg_allow_modify, flg_prev_over,
    window_type, submittype, flg_submit_sync, node_handler_scope,
    node_handler_type, node_processor_value, node_processor_text,
    handler,
    automatic_terminate, flg_spread, flg_spread_allow,
    timelimit_relate_yq, timelimit_relate, timelimit_date,
    timelimit_flg_apply, timellimt_house)
VALUES ('{uuid}', '{flow_id}', 'end', '结束',
    999999, 0, 1,
    0, 1, 1, 1, 0, 0, 1, 1,
    20, '20!@!超级管理员!@!U00001', '超级管理员',
    '{end_handler_uuid}',  -- ⚠️ 结束节点也有对应的 comm_handler
    0, 0, 1,
    0, 0, 0,
    0, 0);
```

### 3.7 flw_route INSERT
```sql
INSERT INTO flw_route (id, node_id, next_node_id, menu_name, name,
    priority, flg_attribute, flg_multi_node, code, flg_deleted,
    is_save, valid_handler, iz_need_opinion, flow_submit_form_no_valid)
VALUES ('{uuid}', '{from_node_id}', '{to_node_id}',
    '{menu_name}', '{name}', {priority}, '{flg_attribute}', 0, '{code}',
    0, 0, 0, {iz_need_opinion}, 1);
```

---

## 4. 生成器执行流程

```
[用户定义 FlowDefinition JSON]
     │
     ▼
[resolve_flow_handlers()] ← ← ← ← ← ← ← 数据库连接
     │ 逐个节点解析 handler:                      │
     │  type=1  → 查询 comm_handler_rule    ──────┤
     │  type=20 → 查询 sys_user + comminfo  ──────┤
     │  type=0  → 查询 sys_org             ──────┤
     │  type=40 → 查询 sys_role            ──────┤
     │  失败 → 保底: 超级管理员                     ↓
     ▼
[generate_create()]  → 完整的 SQL（生成顺序）
     │
     │  1. busi INSERT
     │  2. flw_view_dictionary INSERT（2条）
     │  3. flw_flow INSERT
     │  4. 对于每个节点：
     │     a. comm_handler INSERT（新 UUID）
     │     b. comm_handler_instance INSERT（引用 a 的 UUID）
     │     c. flw_node INSERT（handler = a 的 UUID）
     │  5. 对于每个非结束节点：
     │     flw_route INSERT
     │
     ▼
[数据库执行]
```

---

## 5. 与模型设计器集成

### 5.1 JSON 扩展

当模块需要关联流程时，在 `ModuleDefinition` 中新增两个字段：

```json
{
  "module": {
    "code": "leave",
    "name_cn": "请假管理",
    "db_table": "t_leave"
  },
  "fields": [
    {"field_name": "user_name", "comment": "申请人", ...}
  ],
  "flow_code": "LEAVE_APPROVAL",            ← 关联的流程编码
  "flow_business_name_field": "user_name"   ← 作为待办标题的业务字段
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `flow_code` | 否 | 关联的 flw_flow.code，不为空时触发流程集成 |
| `flow_business_name_field` | 否 | 从当前模块 fields 中选一个字段名，作为流程待办标题。**必须存在于 fields 中**，否则报错 |

### 5.2 固化生成（7 个流程相关字段）

当 `flow_code` 不为空时，生成器自动在以下位置追加 7 个固化字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `FLOW_ID` | varchar(64) | 流程实例ID |
| `FLOW_NAME` | varchar(2000) | 流程实例名称 |
| `FLOW_INSTANCE_ID` | varchar(64) | 流程实例唯一标识 |
| `NODE_INSTANCE_ID` | varchar(64) | 环节实例ID |
| `NODE_INSTANCE_NAME` | varchar(2000) | 环节实例名称 |
| `BO_STATUS` | int(1) | **业务状态（即审批状态）** |
| `NODE_CODE` | varchar(64) | 当前环节编码 |

这些字段：
- 自动追加到 `CREATE TABLE`（业务表 DDL）
- 自动生成 `md_field` 记录（NOT NULL, 无默认值）
- 自动生成 `md_form` 记录（**edit_type=hidden, editable=False**，不在页面展示）
- 自动追加到 `UPDATE md_module SET flow_id` 流程关联 SQL

#### ⚠️ 禁止额外设计审批状态字段

**`BO_STATUS` 就是流程审批状态字段，不需要也不允许再额外定义审批状态字段。**

| 错误做法 | 正确做法 |
|---------|---------|
| 在 fields 中添加 `approval_status`、`audit_status`、`status` 等审批状态字段 | 不添加，`BO_STATUS` 已由流程固化字段自动注入 |
| 手动创建 `APPROVAL_STATUS` 等字典 | 不创建，`BO_STATUS` 字典已自动注入（草稿/审批中/已通过/已驳回） |
| 在列表页用自定义状态字段展示 | 使用 `BO_STATUS`，已在列表页配置为 `show_type=dic` + `searchable=true` |

**原因**：
1. `BO_STATUS` 由流程引擎自动维护，与其他状态字段不同步
2. 重复定义会导致数据不一致（一个字段说已通过，另一个说审批中）
3. `BO_STATUS` 已绑定 `BO_STATUS` 字典（0=草稿、1=审批中、2=已通过、3=已驳回），在列表页以字典值展示

### 5.3 md_module 集成规则

当 `flow_code` 不为空时：

**md_module.base_class**
- 使用 `com.badou.designer.module.design.base.ModuleEntityFlowWithNodeCode`
- 替代默认的 `ModuleEntityOnlyId`

**busi.BUSI_INSTANCE_MODULE**
- 自动与 `md_module.code` 保持一致
- 通过 `UPDATE busi SET BUSI_INSTANCE_MODULE = '{module_code}'` 同步

### 5.4 生成管线

```
生成顺序（当 flow_code 不为空时）：

步骤0: 幂等清理 ← 清理旧数据
步骤1: DDL (CREATE TABLE) ← 含7个流程字段
步骤2: md_module INSERT
步骤3: md_field INSERT ← 含7个流程字段
步骤4: 数据字典
步骤5: md_form INSERT ← 含7个流程字段(hidden)
步骤6: md_button
步骤7: sys_resource
步骤8: sys_role_resource
步骤9: 验证
步骤10: UPDATE md_module SET flow_id ← [新增] 关联 flw_flow
```

---

## 6. 注意事项

1. **automatic_terminate 不可为空** — 所有节点 INSERT 都必须显式赋值 `automatic_terminate = 0`
2. **处理人值禁止杜撰** — 使用 `resolve_flow_handlers()` 从数据库自动查询真实数据
3. **视图名称加前缀** — `flw_view_dictionary.name` 必须使用 `{busi_name}-编辑` / `{busi_name}-审批` 格式
4. **DB 不可用的保底** — 四种 handler type 均采用 type=20，超级管理员 `20!@!超级管理员!@!U00001`
5. **幂等性** — 生成 SQL 时先执行 cleanup 再 create，支持任意次数重复执行
6. **handler 字段修正** — `flw_node.handler` 引用 `comm_handler.ID`（UUID），不再使用 processor_value 第三段
7. **三表同生命周期** — `comm_handler` + `comm_handler_instance` + `flw_node` 三个 INSERT 同步生成，共用一个节点编码

---

*规则版本: 2.0 · 2026-05-18 · 更新：新增 comm_handler/comm_handler_instance 规则、handler 字段修正、三表同步生成*
