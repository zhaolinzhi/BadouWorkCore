"""CRUD SQL Generators - Step 1: md_module


实际表结构 (md_module):
  id, db_table, type, package_name, module_name, english_name, pri_key,
  path, data_source_id, table_name, remark, code, name, edited_js,
  create_time, creator, creator_name, update_time, updator, updator_name,
  flg_deleted, rw, m_t_id, m_t_name, template_id, template_name,
  default_sort, default_where, after_save_bean, before_delete_bean,
  after_delete_bean, base_class, condition_field, condition_value,
  handler_org_type, msg_url, is_gen_msg, flow_id, flow_business_name,
  chaincode_model_type, LIST_JS, data_source_type, form_option,
  role_codes, role_codes_desc, flow_judge_bean

重要字段约束:
  - data_source_id: 必填，不能为空，必须关联到 md_database.id
  - 默认数据源 code: projectDatabase（对应 id: ff808181623d06cc01623d1127ca0002）
"""
from __future__ import annotations
from common.generator_shared.models import ModuleDefinition

TEMPLATE = """\
-- ========== 步骤1: 创建模型 ==========
INSERT INTO md_module (
    id, module_name, name, english_name, code, db_table, table_name, package_name, pri_key,
    type, data_source_id, base_class, m_t_name, m_t_id,
    create_time, creator, creator_name, flg_deleted
) VALUES (
    '{module_id}',
    '{module_name}',
    '{name_cn}',
    '{module_name}',
    '{code}',
    '{db_table}',
    '{table_name_cn}',
    '{package_name}',
    'id',
    1,
    (SELECT id FROM md_database WHERE code = '{data_source_code}' AND flg_deleted = 0 LIMIT 1),
    '{base_class}',
    'busi',
    '40282b815b6f9ac5015b7052f35d0008',
    NOW(),
    '{creator_id}',
    '{creator_name}',
    0
);
"""

CLEANUP_TEMPLATE = """\
-- ========== 清理: 删除模型 ==========
DELETE FROM md_module WHERE code = '{code}';
"""


def generate_create(defn: ModuleDefinition) -> str:
    m = defn.module
    data_source_code = m.data_source_code or "projectDatabase"
    module_id = defn.reserved_ids['module_id']

    # 智能 base_class 推断（4 步决策树，见 ModuleDefinition.infer_base_class）
    base_class = defn.infer_base_class()

    sql = TEMPLATE.format(
        module_id=module_id,
        data_source_code=data_source_code,
        module_name=m.module_name,
        name_cn=m.name_cn,
        code=m.code,
        db_table=m.db_table,
        table_name_cn=m.table_name_cn,
        package_name=m.package_name,
        base_class=base_class,
        creator_id=defn.creator.id,
        creator_name=defn.creator.name,
    )

    # 前端 JS 路径写入策略 (issue #3: 禁止臆测):
    # - LIST_JS: 默认落业务路径 public/moduleJs/business/{mdCode}/list.js(用户显式覆盖时以用户值为准)
    # - edited_js: 仅在用户显式提供 frontend.edit_js_path 时才写入,避免指向不存在的 edit.js 文件
    frontend = defn.frontend
    list_path = frontend.list_js_path if frontend and frontend.list_js_path else f"/business/{m.code}/list.js"
    list_js_sql = f"UPDATE md_module SET LIST_JS = '{list_path}' WHERE code = '{m.code}';\n"

    edit_path = frontend.edit_js_path if frontend and frontend.edit_js_path else None
    if edit_path:
        # 单条 UPDATE 同时设两个字段(用户显式提供 edit_js_path 的场景)
        edit_js_sql = f"UPDATE md_module SET LIST_JS = '{list_path}', edited_js = '{edit_path}' WHERE code = '{m.code}';\n"
    else:
        # 不臆测 edited_js: 单独 UPDATE LIST_JS,框架对 NULL edited_js 有默认行为
        edit_js_sql = ""

    sql += (
        "\n-- ========== 前端 JS 路径(默认 LIST_JS 业务路径;edited_js 仅显式) ==========\n"
        + list_js_sql
        + edit_js_sql
    )

    return sql


def generate_cleanup(defn: ModuleDefinition) -> str:
    return CLEANUP_TEMPLATE.format(code=defn.module.code)
