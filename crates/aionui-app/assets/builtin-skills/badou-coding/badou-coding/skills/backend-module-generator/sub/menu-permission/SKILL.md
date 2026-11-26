---
name: backend-module-generator-menu-permission
description: 菜单资源 + 按钮资源 + 角色授权
parent_skill: backend-module-generator
related_table: sys_resource, sys_role_resource, sys_role
---

# 子技能: 菜单资源 + 按钮资源 + 角色授权

## 对应文件

- `generators/resource_gen.py`
- `generators/role_gen.py`

## 写入内容

INSERT INTO sys_resource（1 菜单 + 6 按钮）+ INSERT INTO sys_role_resource（ROOT 授权 7 条）

## 关键规则

- 菜单 code = 'SYSTEM_<MODULE_CODE_UPPER>'
- 按钮 code = <module_code>_<action>
- 角色授权仅对 ROOT 角色
- parent_id 查找优先级链
- 清理顺序：sys_role_resource → sys_resource(按钮) → sys_resource(菜单)