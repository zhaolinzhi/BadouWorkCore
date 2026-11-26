---
name: backend-module-generator-form-config
description: 表单配置 + 校验规则
parent_skill: backend-module-generator
related_table: md_form
---

# 子技能: 表单配置 + 校验规则

## 对应文件

- `generators/form_gen.py`
- `rules/infer_form.py`

## 写入内容

INSERT INTO md_form — 表单配置

## 关键规则

- display_type → edit_type 映射
- 字典字段自动设为 select
- nullable=False 字段自动加 required
- 搜索字段自动生成 SearchBox JSON
- hidden + NOT NULL + 无默认值 = 设计错误