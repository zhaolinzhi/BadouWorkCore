---
name: backend-module-generator-dictionary
description: 字典类型 + 字典项生成
parent_skill: backend-module-generator
related_table: comm_dictionary, comm_dictionary_item
---

# 子技能: 字典类型 + 字典项生成

## 对应文件

- `generators/dictionary_gen.py`

## 写入内容

INSERT INTO comm_dictionary + comm_dictionary_item

## 关键规则

- type_id 固定为 'OTHRE'
- id 使用 SUBSTR(UUID(),1,32)
- 字典项通过子查询反查 dictionary_id
- 至少 1 个字典项
- code 建议大写常量命名