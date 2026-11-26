# md_database 配置项简述

> **物理 schema**：`.claude/docs/backend/database/ddl/module/md_database.md`
> **覆盖**：15 列
> **详/简**：简
> **理由**：md_database 是数据源字典表；generator 仅通过 `code='projectDatabase'` 反查，不写入；updater 不动

## §1 表概述

- **用途**：数据源字典表；每行 = 一个可被 MD 模块引用的数据库连接
- **与 generator 关系**：**不写入本表**；`module_gen.py` 通过子查询反查 `code='projectDatabase'`
- **关键含义**：generator 的上游依赖；缺失 `projectDatabase` 行 → 所有新模块 INSERT 失败

## §2 关键列

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | varchar(64) | 主键 UUID |
| `code` | varchar(64) | 数据源编码（generator 识别 `projectDatabase`）|
| `name` | varchar(32) | 数据源名称（中文）|
| `data_source` | varchar(256) | JDBC URL |
| `type` | int(11) | 数据库类型（0=MySQL/1=Oracle）|
| `username` | varchar(128) | 数据库用户名 |
| `password` | varchar(128) | 数据库密码 |

## §3 updater 兼容矩阵

> **md_database 不在 updater 修改范围**；updater 不动此表。

| 变更类型 | 行为 |
|---|---|
| 任何变更 | 手动维护（脚本/管理后台），不走 updater |

## 📎 引用

- 物理 schema：`.claude/docs/backend/database/ddl/module/md_database.md`