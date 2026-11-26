# md_button 配置项简述

> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_button.md`
> **覆盖**：25 列
> **详/简**：简（仅列概述 + 关键列含义；不写完整配置项矩阵）
> **理由**：md_button 由 generator 完整写入；用户仅在 `buttons` 数组声明 code/name；updater 仅做 DELETE + INSERT 全量

## §1 表概述

- **用途**：每个模块在**列表页 / 表单页**的操作按钮；一行 = 一个按钮
- **与 generator 关系**：`button_gen.py` 写入；6 个标准按钮自动生成（add/edit/view/delete/import/export）
- **关键含义**：按钮是用户与数据交互入口；与后端 controller 方法一一对应（function_name）

## §2 关键列（generator / updater 关注）

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | varchar(64) | 主键 UUID |
| `module_id` | varchar(64) | 关联 md_module.id |
| `code` | varchar(64) | 按钮编码（`add`/`edit`/`delete` 等） |
| `name` | varchar(255) | 按钮名称（中文） |
| `function_name` | varchar(64) | 后端 Controller 方法名 |
| `type` | varchar(64) | toolbar / row / form |
| `priority` | int(11) | 显示顺序（数值越小越靠前）|
| `url` | varchar(256) | 自定义 URL |
| `handler` | varchar(256) | 前端 handler 名 |
| `icon` | varchar(255) | Element UI icon 名 |
| `iz_show` | int(1) | 是否展示 0/1 |

## §3 updater 兼容矩阵

| 变更类型 | 行为 |
|---|---|
| 加按钮 | DELETE + INSERT md_button 全量 |
| 删按钮 | DELETE + INSERT md_button 全量 |
| 改按钮属性（code/name/type/priority/handler/icon）| DELETE + INSERT md_button 全量 |

## 📎 引用

- 物理 schema：`.claude/docs/backend/database/ddl/module/md_button.md`
- generator rule：`.claude/skills/badou-coding/skills/backend-module-generator/rules/button-config.md`
- updater rule：`.claude/skills/badou-coding/skills/backend-module-updater/update_rules/button-change.md`
