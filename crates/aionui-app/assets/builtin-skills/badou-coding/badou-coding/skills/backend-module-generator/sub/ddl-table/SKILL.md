---
name: backend-module-generator-ddl-table
description: 业务表 DDL 建表语句
parent_skill: backend-module-generator
related_table: t_<business_table>
---

# 子技能: 业务表 DDL 建表语句

## 对应文件

- `generators/ddl_gen.py`

## 写入内容

CREATE TABLE — 字段定义 + PK + UNIQUE + INDEX + ENGINE=InnoDB utf8mb4

## 关键规则

- display_type → MySQL 类型映射
- 字段 length 为空时取默认值
- primary_key 字段自动设为 PRI + NOT NULL
- unique 字段自动生成 UNIQUE KEY
- nullable=False 的搜索字段自动加 INDEX