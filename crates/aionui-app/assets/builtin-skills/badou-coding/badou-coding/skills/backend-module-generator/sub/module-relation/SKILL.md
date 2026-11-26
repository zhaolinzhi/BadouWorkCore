---
name: backend-module-generator-module-relation
description: 模块关联（一对多 / 多对一）
parent_skill: backend-module-generator
related_table: md_module_link
---

# 子技能: 模块关联（一对多 / 多对一）

## 对应文件

- `generators/relation_gen.py`

## 写入内容

INSERT INTO md_module_link — 关联定义 + 关联 SQL 独立生成

## 关键规则

- type=1 → SHOW_TYPE=0, type=2 → SHOW_TYPE=1
- show_style=1|2 → SHOW_TAB=1, show_style=3 → SHOW_TAB=0
- 关联 SQL 独立输出到 _relation.sql
- type=1 时 field_name 必填
- show_style=1|2 时 tab_name 必填