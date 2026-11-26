---
name: backend-module-generator
description: "基于 MD 模块驱动架构，通过 JSON 定义生成 CRUD 功能的 **SQL 脚本与 MD 元数据**（md_module / md_field / md_form / md_button / md_module_link / comm_dictionary / sys_resource）。**无需生成任何 Java 代码类或前端代码，仅通过 JSON 配置即可启用标准 CRUD 功能**——框架运行时读取 md_* 表动态渲染页面与构造 SQL。单表 CRUD 读 rules/basic-crud.md；多表关联追加读 rules/module-link.md；流程引擎集成通过 flow_code 契约对接独立技能 backend-flow-engine：当 module.flow_code 非空时自动注入流程固化字段到 DDL 与 md_field，并生成流程关联 SQL。"
metadata:
  version: 3.3.0
  rules:
    - rules/basic-crud.md          # 入口/索引 + 总检查清单（必读）
    - rules/module-link.md         # 多表关联（relations 存在时追加读）
    - rules/flow-contract.md       # 流程引擎契约（flow_code 非空时追加读）
---

# backend-module-generator

<!-- Source: generated for backend-module-generator stability design, do not edit by hand without syncing the plan. -->

---

## 🚨 工作原理（Agent 必读，避免越过边界）

**一句话**：本技能生成 SQL 与 MD 元数据；**标准 CRUD 无需生成 Java 实体类 / Controller / Service，也无需生成前端 Vue 组件**——框架在运行时读取 md_module / md_field / md_form / md_button 即可动态渲染列表页、表单页并响应 CRUD 请求。

### 生成产物

- ✅ MD 元数据 SQL：md_module / md_field / md_form / md_button / md_module_link
- ✅ 数据字典 SQL：comm_dictionary / comm_dictionary_item
- ✅ 资源权限 SQL：sys_resource / sys_role_resource
- ✅ 流程绑定 SQL（当 module.flow_code 非空）：md_flow 行 + md_module.flow_id UPDATE
- ✅ 业务表 DDL（create.sql 中包含的 t_xxx 建表语句）

### 适用场景（一条 JSON 就能搞定的）

- 标准 CRUD（增删改查 + 列表 / 搜索 / 详情 / 导入导出）
- 多表关联（一对多 / 多对一 / 中间表 tab 展示）
- 流程审批模块（与 backend-flow-engine 配合，注入 BO_STATUS 等固化字段）

### 不适用场景（请走其他工具 / 技能）

- 高度定制的业务逻辑（复杂计算字段、跨服务调用、复杂校验链）
- 非 MD 驱动的子模块（定时任务、CAS 单点登录、uniapp 移动端）
- 一次性数据迁移 / 初始化脚本

> 🛑 **误判自救指南**：如果你想写 `entity_gen.py` / `controller_gen.py` / `mybatis_gen.py` → 停下来。MD 架构下标准 CRUD **不需要生成代码类**，JSON 配置即"代码"；定制业务逻辑请写到后端项目对应的包下，不要让 generator 生成代码类。

---

## 📚 规则文档索引

| 规则文件 | 何时读 | 职责 |
|---------|--------|------|
| `rules/basic-crud.md` | **总是** | 入口/路由、字典三条件总览、JSON 生成总检查清单、SQL 执行顺序 |
| `rules/module-config.md` | 写 module 段时 | md_module 必填字段、code 命名、base_class 选择、menu 配置 |
| `rules/field-config.md` | 写 fields 段时 | display_type 白名单、字段属性、系统字段注入（8 个）、流程字段注入（3 个）、主键与外键长度统一 |
| `rules/dictionary.md` | 含字典字段时 | 字典三条件规则、字典 JSON 定义、BO_STATUS 自动注入 |
| `rules/list-page.md` | 配置列表列时 | show_in_grid 默认值、LIST_WIDTH、character_num、SORTABLE、list_drill_* |
| `rules/search-condition.md` | 配置搜索框时 | searchable、search_type、search_box 操作符、字典搜索三条件 |
| `rules/edit-page.md` | 配置编辑页字段时 | edit_type 映射表、regex_rule 校验规则自动推断、is_edit 默认值、edit_tip |
| `rules/view-page.md` | 配置查看页字段时 | view_type 自动推断表、is_full_line 推断、view_drill_*、form 新增字段清单 |
| `rules/button-config.md` | 配置按钮时 | 6 个标准按钮、toolbar/row/form 三种 type、priority 约定、自定义按钮 |
| `rules/data-safety.md` | 含 hidden/readonly 字段时 | 框架填充边界、业务字段 nullable 规则、Pydantic 阻断模式 |
| `rules/sql-execution.md` | 执行生成 SQL 前 | 执行顺序表、db_executor.py 使用、@variable 单连接约束 |
| `rules/module-link.md` | **含 relations 时追加** | md_module_link 字段映射、type/SHOW_TYPE 规则、关联 SQL 二阶段执行 |
| `rules/flow-contract.md` | **module.flow_code 非空时追加** | flow_code 契约、7 个流程字段、BO_STATUS 注入、与 backend-flow-engine 配合 |

## 📦 通用规则（common spec — 单一权威源）

> **所有 md_* 表的配置项矩阵 + generator 写入策略 + 变更敏感度 + updater 兼容矩阵**

| 文件 | 覆盖表 | 列数 |
|------|--------|------|
| [common/README.md](../../../common/README.md) | 索引 + 维护指南 | — |
| [common/md_module.md](../../../common/md_module.md) | md_module | 46 |
| [common/md_field.md](../../../common/md_field.md) | md_field | 21 |
| [common/md_form.md](../../../common/md_form.md) | md_form | 52 |
| [common/md_flow.md](../../../common/md_flow.md) | md_flow | 6 |
| [common/md_module_link.md](../../../common/md_module_link.md) | md_module_link | 20 |
| [common/md_button.md](../../../common/md_button.md) | md_button | 25（简）|
| [common/md_database.md](../../../common/md_database.md) | md_database | 15（简）|

> 扩展 md_* 配置项时**只改 common spec**，rules 自动引用。

---

## 📖 数据库结构参考（必读）

| 类别 | 路径 | 内容 |
|------|------|------|
| 模块元数据 | `.claude/docs/backend/database/ddl/module/md_<table>.md` | md_module / md_field / md_form / md_button / md_module_link / md_flow / md_database / md_module_type |
| 资源权限 | `.claude/docs/backend/database/ddl/resource/` | sys_resource / sys_role_resource / sys_role |
| 数据字典 | `.claude/docs/backend/database/ddl/dic/` | comm_dictionary / comm_dictionary_item |
| 流程引擎 | `.claude/docs/backend/database/ddl/flow/` | flw_* / comm_handler* |

> 💡 **找不到字段含义时**：先查 MD 文档（如 `md_module.md`）；规则文档中的 `📖` 标记会指引到对应 DDL 章节。

---

## 🔀 路由流程图

```
用户需求
    │
    ├── 仅单表 CRUD（无关联）
    │   └── 读 rules/basic-crud.md
    │       → 按需展开 module-config / field-config / dictionary /
    │         list-page / search-condition / edit-page / view-page /
    │         button-config / data-safety / sql-execution
    │
    ├── 含多表关联（relations）
    │   ├── 读 rules/basic-crud.md + 上述子文件
    │   └── 追加读 rules/module-link.md
    │
    ├── 含流程引擎集成（纯流程，无模块）
    │   └── 用 backend-flow-engine（本技能不涉及）
    │
    └── 含流程引擎（审批流）
        ├── 步骤 1: backend-flow-engine 创建 flw_flow
        ├── 步骤 2: 追加读 rules/flow-contract.md
        ├── 步骤 3: 写 module.json（含 flow_code）
        └── 步骤 4: crud_generator.py --def module.json
```

---

## 🔥 请假审批场景完整流程（标准示例）

### 场景说明

用户要求开发「请假审批管理」，包含：
- CRUD 模块：请假类型、开始/结束日期、请假天数、请假原因
- 流程引擎：提交申请 → 部门经理审批 → 人事审批 → 结束
- 两者关联：`module.flow_code = "LEAVE_APPROVAL"`

### Agent 执行步骤

```bash
# 0. 确定项目 → 读取 PROJECT-BRAIN.md 获取数据库连接

# 1. 写出 flow.json（流程定义）
#    包含 busi、4 个节点（START + REVIEW_01 + REVIEW_02 + end）、5 条路由
#    首环节使用抽象处理人（type=1），其余用保底管理员（type=20）

# 2. 执行流程引擎 SQL
python3 $FLOW_SKILL_DIR/flow_generator.py --flow-only flow.json --flow-execute

# 3. 写出 module.json
#    module.flow_code = "LEAVE_APPROVAL"
#    module.flow_business_name_field = "applicant_name"

# 4. 执行 CRUD 生成
python3 $SKILL_DIR/crud_generator.py \
  --def module.json \
  --config-from-brain .trellis/PROJECT-BRAIN.md \
  --output ./crud-generator/output/

# 5. 执行生成的 SQL
python3 db_executor.py output/leave_request/v3.1.0/leave_request_create.sql \
  --config-from-brain .trellis/PROJECT-BRAIN.md

# 6. 幂等校验
python3 $SKILL_DIR/validators/idempotent_check.py module.json
# → ALL PASSED ✅
```

> ⚠️ **步骤 2 必须先于步骤 4**——flw_flow 不存在时，模块的 flow_id 关联会失效。

---

## ⚠️ 常见错误

| 错误 | 后果 | 修复 |
|------|------|------|
| module.json 没有设置 `flow_code` | 不注入流程字段、不关联 flow_id | 添加 `"flow_code": "LEAVE_APPROVAL"` |
| 先执行 create.sql 再执行 flow.sql | flow_id 关联失效 | 补跑 `UPDATE md_module SET flow_id = ...` |
| ⚠️ fields 中定义 `approval_status`/`audit_status`/审批 status | Pydantic 校验阻断 | 删除该字段，由 BO_STATUS 自动注入 |
| 业务 hidden 字段 `nullable: false` | Pydantic 校验拦截 | 设 `nullable: true` |
| type=1 抽象处理人 processor_value 第三段填了 `0` | Pydantic 校验阻断 | 第三段填 `3`（拟稿人/填报人对应 ID） |

---

## 多项目隔离规则

| 规则 | 说明 |
|------|------|
| **项目确认优先** | 任何操作前，必须先确定当前是哪个项目 |
| **DB 配置隔离** | 每个项目的数据库连接信息从各自的 PROJECT-BRAIN.md 读取 |
| **输出路径隔离** | 生成的 SQL 文件写入对应项目的 `crud-generator/output/` 目录 |
| **不跨项目引用** | 生成 SQL 时，所有引用（数据源、菜单、创建者）都使用当前项目的值 |
| **多项目询问** | 存在多个活跃项目时，主动询问用户要使用哪个 |
| **禁止硬编码** | 不在 Skill 内写死任何项目的数据库信息 |
