---
name: backend-module-generator-module-config
description: md_module 配置生成
parent_skill: backend-module-generator
related_table: md_module, md_database, md_module_type
---

# 子技能: md_module 配置生成

## 对应文件

- `generators/module_gen.py`

## 写入内容

INSERT INTO md_module — 模块定义 + 数据源关联 + 基类推导

## 关键规则

- base_class 按 4 步决策树：显式 > flow_code > 默认 ModuleEntityOnlyId
- data_source_id 通过子查询反查 md_database.code='projectDatabase'
- m_t_id 硬编码为 busi 类型（40282b81...）
- frontend 节点自动写入 LIST_JS / edited_js
- flow_id 通过 flow_integration.py 后续回填