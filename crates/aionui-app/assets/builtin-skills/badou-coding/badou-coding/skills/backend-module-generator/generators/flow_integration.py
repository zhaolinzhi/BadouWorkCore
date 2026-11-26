"""Flow Engine Integration — 更新 md_module 的 flow 相关字段

当 ModuleDefinition 包含 flow_code 时：
1. 使用子查询从 flw_flow 表按 code 查找 flow_id
2. 使用 code-based 查询更新 md_module（不依赖预生成的 ID）
3. 生成 UPDATE busi SET BUSI_INSTANCE_MODULE SQL
4. 不缓存字面量 ID，避免流程重建后脏数据
"""

from __future__ import annotations
from common.generator_shared.models import ModuleDefinition


def generate_flow_update_sql(defn: ModuleDefinition, db_config: dict | None = None) -> str:
    """生成 md_module + busi 的流程关联 SQL

    使用 code-based 查询，不依赖 reserved_ids 中的预生成 UUID。
    这样即使独立执行（如 flow create 之后再跑），也能正确关联。
    """
    if not defn.flow_code:
        return ""

    busi_name_field = defn.flow_business_name_field or ""
    module_code = defn.module.code
    flow_code = defn.flow_code

    sql = (
        f"-- ========== 流程关联: {flow_code} ==========\n"
        # 1. 更新 md_module.flow_id（使用 code 查询，不缓存字面量 ID）
        f"UPDATE md_module SET\n"
        f"    flow_id = (SELECT id FROM flw_flow WHERE code = '{flow_code}' AND flg_deleted = 0 LIMIT 1),\n"
        f"    flow_business_name = '{busi_name_field}'\n"
        f"WHERE code = '{module_code}' AND flg_deleted = 0;\n"
        "\n"
        # 2. 更新 busi.BUSI_INSTANCE_MODULE 与 md_module.code 保持一致
        f"UPDATE busi SET\n"
        f"    BUSI_INSTANCE_MODULE = '{module_code}'\n"
        f"WHERE id = (SELECT busi_type FROM flw_flow WHERE code = '{flow_code}' AND flg_deleted = 0 LIMIT 1);\n"
    )

    return sql
