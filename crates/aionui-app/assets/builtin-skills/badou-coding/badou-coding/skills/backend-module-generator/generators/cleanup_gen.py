"""CRUD SQL Generators - cleanup: idempotent cleanup + full cleanup orchestrator"""
from __future__ import annotations
import datetime
from common.generator_shared.models import ModuleDefinition, _to_pascal_case


def _get_menu_code(defn: ModuleDefinition) -> str:
    return defn.menu.resource_code or "SYSTEM_" + _to_pascal_case(defn.module.code).upper()


def generate_idempotent_cleanup(defn: ModuleDefinition) -> str:
    m = defn.module
    menu_code = _get_menu_code(defn)
    dict_codes = [d.type_name for d in defn.dictionaries] if defn.dictionaries else []
    dict_cleanup = ""
    if dict_codes:
        code_list = ", ".join(f"'{c}'" for c in dict_codes)
        dict_cleanup = (
            "-- 删除字典项\n"
            "DELETE FROM comm_dictionary_item WHERE dictionary_id IN (\n"
            f"    SELECT id FROM comm_dictionary WHERE code IN ({code_list})\n"
            ");\n"
            "-- 删除字典类型\n"
            f"DELETE FROM comm_dictionary WHERE code IN ({code_list});\n"
        )
    return (
        "-- ========== 步骤0: 清理历史数据（幂等，确保可重复执行）==========\n"
        + dict_cleanup
        + "-- 删除角色资源关联\n"
        "DELETE FROM sys_role_resource WHERE resource_id IN (\n"
        f"    SELECT id FROM sys_resource WHERE code = '{menu_code}' AND RESOURCE_TYPE = 0\n"
        ") OR resource_id IN (\n"
        "    SELECT id FROM sys_resource WHERE parent_id IN (\n"
        f"        SELECT id FROM sys_resource WHERE code = '{menu_code}' AND RESOURCE_TYPE = 0\n"
        "    ) AND RESOURCE_TYPE = 1\n"
        ");\n"
        "-- 删除按钮资源\n"
        "DELETE FROM sys_resource WHERE parent_id IN (\n"
        "    SELECT id FROM (\n"
        f"        SELECT id FROM sys_resource WHERE code = '{menu_code}' AND RESOURCE_TYPE = 0\n"
        "    ) AS _sys_tmp\n"
        ") AND RESOURCE_TYPE = 1;\n"
        "-- 删除菜单资源\n"
        f"DELETE FROM sys_resource WHERE code = '{menu_code}' AND RESOURCE_TYPE = 0;\n"
        "-- 删除按钮\n"
        f"DELETE FROM md_button WHERE module_id IN (SELECT id FROM md_module WHERE code = '{m.code}');\n"
        "-- 删除表单\n"
        f"DELETE FROM md_form WHERE mod_id IN (SELECT id FROM md_module WHERE code = '{m.code}');\n"
        "-- 删除模块关联\n"
        f"DELETE FROM md_module_link WHERE module_id IN (SELECT id FROM md_module WHERE code = '{m.code}');\n"
        "-- 删除字段\n"
        f"DELETE FROM md_field WHERE module_id IN (SELECT id FROM md_module WHERE code = '{m.code}');\n"
        "-- 删除模型\n"
        f"DELETE FROM md_module WHERE code = '{m.code}';\n"
        "-- 删除业务表\n"
        f"DROP TABLE IF EXISTS `{m.db_table}`;\n"
    )


def generate_cleanup_sql(defn: ModuleDefinition) -> str:
    from generators import role_cleanup, resource_cleanup, button_cleanup, relation_cleanup
    from generators import form_cleanup, field_cleanup, dict_cleanup, module_cleanup, ddl_cleanup
    from generators.flow_cleanup import generate_flow_cleanup
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [
        f"-- {'='*59}", f"-- 清理脚本: {defn.module.name_cn} ({defn.module.code}) | 版本: v{defn.version}",
        f"-- 生成时间: {now}", f"-- {'='*59}", "",
    ]
    if defn.flow_code:
        parts.extend(["-- ========== 流程引擎清理 ==========", generate_flow_cleanup(defn), ""])
    parts.extend([role_cleanup(defn), "", resource_cleanup(defn), "", button_cleanup(defn), "",
                  relation_cleanup(defn), "", form_cleanup(defn), "", field_cleanup(defn), "",
                  dict_cleanup(defn), "", module_cleanup(defn), "", ddl_cleanup(defn)])
    return "\n".join(parts)