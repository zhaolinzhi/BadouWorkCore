"""CRUD SQL Generators - flow cleanup: 流程引擎清理 SQL"""
from common.generator_shared.models import ModuleDefinition


def generate_flow_cleanup(defn: ModuleDefinition) -> str:
    flow_code = defn.flow_code
    module_code = defn.module.code
    return (
        f"-- 清理流程: {flow_code}\n\n"
        f"DELETE FROM comm_handler_instance WHERE HANDLER_ID IN (\n"
        f"    SELECT id FROM comm_handler WHERE id IN (\n"
        f"        SELECT handler FROM flw_node WHERE flow_id IN (\n"
        f"            SELECT id FROM flw_flow WHERE code = '{flow_code}' AND flg_deleted = 0\n"
        f"        )\n"
        f"    )\n"
        f");\n\n"
        f"DELETE FROM comm_handler WHERE id IN (\n"
        f"    SELECT handler FROM flw_node WHERE flow_id IN (\n"
        f"        SELECT id FROM flw_flow WHERE code = '{flow_code}' AND flg_deleted = 0\n"
        f"    )\n"
        f");\n\n"
        f"DELETE FROM flw_route WHERE node_id IN (\n"
        f"    SELECT id FROM flw_node WHERE flow_id IN (\n"
        f"        SELECT id FROM flw_flow WHERE code = '{flow_code}' AND flg_deleted = 0\n"
        f"    )\n"
        f");\n\n"
        f"DELETE FROM flw_node WHERE flow_id IN (\n"
        f"    SELECT id FROM flw_flow WHERE code = '{flow_code}' AND flg_deleted = 0\n"
        f");\n\n"
        f"DELETE FROM flw_flow WHERE code = '{flow_code}' AND flg_deleted = 0;\n\n"
        f"DELETE FROM flw_view_dictionary WHERE busi IN (\n"
        f"    SELECT code FROM busi WHERE id IN (\n"
        f"        SELECT busi_type FROM flw_flow WHERE code = '{flow_code}'\n"
        f"    )\n"
        f");\n\n"
        f"DELETE FROM busi WHERE BUSI_INSTANCE_MODULE = '{module_code}';\n\n"
        f"DELETE FROM md_module_link WHERE module_id IN (\n"
        f"    SELECT id FROM md_module WHERE code = '{module_code}'\n"
        f");\n"
    )