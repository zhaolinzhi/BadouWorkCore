---
name: backend-module-generator-field-config
description: 字段定义 + 系统字段注入
parent_skill: backend-module-generator
related_table: md_field
---

# 子技能: 字段定义 + 系统字段注入

## 对应文件

- `generators/field_gen.py`
- `rules/infer_field.py`

## 写入内容

INSERT INTO md_field — 字段定义 + 系统字段自动注入 + 流程字段

## 关键规则

- display_type 白名单：10 种类型
- 系统字段自动注入（8 个）
- flow_code 不为空时注入 7 个流程字段
- entity_name 自动推断 camelCase
- field_name ≤ 64 字符