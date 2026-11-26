---
name: backend-module-generator-button-config
description: 标准按钮配置
parent_skill: backend-module-generator
related_table: md_button
---

# 子技能: 标准按钮配置

## 对应文件

- `generators/button_gen.py`

## 写入内容

INSERT INTO md_button — 6 个标准按钮

## 关键规则

- 默认按钮集：add/edit/view/import/export/delete
- 可通过 defn.buttons 自定义
- 按钮资源同步生成到 sys_resource
- 按钮通过 module_id 过滤