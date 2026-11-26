"""CRUD SQL Generators - validation: create + cleanup validation SQL"""
from common.generator_shared.models import ModuleDefinition, _to_pascal_case


def _get_menu_code(defn: ModuleDefinition) -> str:
    return defn.menu.resource_code or "SYSTEM_" + _to_pascal_case(defn.module.code).upper()


def generate_validation(defn: ModuleDefinition) -> str:
    m = defn.module
    ids = defn.reserved_ids
    menu_code = _get_menu_code(defn)
    dict_codes = [d.type_name for d in defn.dictionaries] if defn.dictionaries else []
    dict_validation = ""
    if dict_codes:
        code_list = ", ".join(f"'{c}'" for c in dict_codes)
        dict_validation = (
            "UNION ALL\n"
            f"SELECT '字典类型', COUNT(*) FROM comm_dictionary WHERE code IN ({code_list})\n"
            "UNION ALL\n"
            f"SELECT '字典项', COUNT(*) FROM comm_dictionary_item WHERE dictionary_id IN (SELECT id FROM comm_dictionary WHERE code IN ({code_list}))\n"
        )
    return (
        "-- ========== 验证 ==========\n"
        f"SELECT '模型' AS type, COUNT(*) AS cnt FROM md_module WHERE id = '{ids['module_id']}' AND flg_deleted = 0\n"
        "UNION ALL\n"
        f"SELECT '字段', COUNT(*) FROM md_field WHERE module_id = '{ids['module_id']}' AND flg_deleted = 0\n"
        "UNION ALL\n"
        f"SELECT '表单', COUNT(*) FROM md_form WHERE mod_id = '{ids['module_id']}'\n"
        "UNION ALL\n"
        f"SELECT '按钮', COUNT(*) FROM md_button WHERE module_id = '{ids['module_id']}' AND FLG_DELETED = 0\n"
        "UNION ALL\n"
        f"SELECT '菜单资源', COUNT(*) FROM sys_resource WHERE code = '{menu_code}' AND RESOURCE_TYPE = 0 AND FLG_DELETED = 0\n"
        "UNION ALL\n"
        "SELECT '按钮资源', COUNT(*) FROM sys_resource WHERE parent_id IN (\n"
        f"    SELECT id FROM sys_resource WHERE code = '{menu_code}' AND RESOURCE_TYPE = 0\n"
        ") AND RESOURCE_TYPE = 1 AND FLG_DELETED = 0\n"
        "UNION ALL\n"
        "SELECT '角色授权', COUNT(*) FROM sys_role_resource WHERE resource_id IN (\n"
        f"    SELECT id FROM sys_resource WHERE code = '{menu_code}' OR parent_id IN (\n"
        f"        SELECT id FROM sys_resource WHERE code = '{menu_code}'\n"
        "    )\n"
        ")\n" + dict_validation + ";\n"
        "\n-- 字段与表单数量一致性检查\n"
        "SELECT\n"
        f"  (SELECT COUNT(*) FROM md_field WHERE module_id = '{ids['module_id']}' AND flg_deleted = 0) AS field_count,\n"
        f"  (SELECT COUNT(*) FROM md_form WHERE mod_id = '{ids['module_id']}') AS form_count,\n"
        "  CASE WHEN\n"
        f"    (SELECT COUNT(*) FROM md_field WHERE module_id = '{ids['module_id']}' AND flg_deleted = 0) =\n"
        f"    (SELECT COUNT(*) FROM md_form WHERE mod_id = '{ids['module_id']}')\n"
        "  THEN '✅ 一致' ELSE '❌ 不一致，请检查' END AS check_result;\n"
    )