# badou-md-* 技能家族

基于 MD 模块驱动的工具技能家族，与 `badou-coding`（过程技能）并列。

## 成员

| 技能 | 职责 | 输入 |
|---|---|---|
| `badou-md-crud-generator-skill` | 基础 CRUD + 多表关联 + 流程契约对接 | `module.json` |
| `badou-md-flow-engine-skill` | 工作流 8 表生成（busi/flw_flow/flw_node/flw_route/flw_view_dictionary/comm_handler(_instance)） | `flow.json` |
| `badou-md-customization-skill` | 生成后叠加定制（自定义 Action/业务逻辑/非标准页面） | 已生成的 module code / 表 |
| `badou-md-common` | 共享库：db_executor / config_loader / validator_core（非技能） | - |

## 技能间契约

CRUD 与流程技能的唯一耦合：`module.flow_code` 非空时，CRUD 注入 7 个固化字段 + 关联 `md_module.flow_id`。详见 `badou-md-crud-generator-skill/rules/FLOW-CONTRACT.md`。

## 协作顺序

- 纯 CRUD：直接用 CRUD 技能。
- 纯流程：直接用流程技能。
- CRUD + 流程：**先**流程技能造 `flw_flow`，**再** CRUD 技能带 `flow_code` 生成模块。

## 定制技能（YAGNI 边界）

`badou-md-customization-skill` **暂不创建**。形态已定为「生成后叠加定制」（独立生命周期/意图），独立技能是合适的，但按 YAGNI，首个真实定制场景（如自定义 Struts Action / 仪表盘）出现时再落地。

- 可参数化的定制（自定义按钮/列/校验/表单布局）-> 扩 `module.json`，归 CRUD 技能。
- 生成器做不到的定制（自定义 Action / 业务逻辑 / 非标准页面）-> 未来归定制技能。

## 与 badou-coding 的关系

`badou-coding` 是过程技能家族（brainstorming/writing-plans/TDD/...），指导「怎么做」；`badou-md-*` 是工具技能家族，提供「做什么」的具体生成能力。brainstorming 按场景路由到对应工具技能。
