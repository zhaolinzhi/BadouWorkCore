"""CRUD Generator - Rule Engine: form config inference"""
from common.generator_shared.models import FieldDef, FormConfig, SearchBox


def infer_form_config(f: FieldDef) -> FormConfig:
    form = f.form
    if f.dict:
        # Dict-bound field: 仅在 edit_type 为 select 系(空/显式 "select")时注入字典绑定
        # 修复 Task 4-fix 回归: 原无条件注入会导致 input/textarea 字段被错误写入
        # data_source=1 + dic_name=<dict>,与表单语义冲突(md_form 后端会按 select 处理)
        # 守卫同时覆盖 Task 4-fix 场景: 显式 edit_type="select" + searchable=true 仍要注入
        is_select_like = not form.edit_type or form.edit_type == "select"
        if is_select_like:
            form.data_source = 1
            form.dic_name = f.dict
            if not form.edit_type:
                form.edit_type = "select"
            if form.searchable and not form.search_box:
                form.search_box = SearchBox(id=f.entity_name or f.field_name, name=f.comment or f.field_name,
                                            defaultText="全部", queryType="other-query", selectType=0)
                form.search_data_source = 1
                form.search_data = f.dict
    if f.display_type == "date" and not form.edit_type:
        form.edit_type = "date"
    if f.display_type == "text" and not form.edit_type:
        form.edit_type = "textarea"
    if f.display_type == "decimal":
        if not form.edit_type:
            form.edit_type = "number"
        if not form.regex_rule:
            form.regex_rule = "decimal"
        elif "decimal" not in form.regex_rule:
            form.regex_rule = f"{form.regex_rule},decimal"
    if f.display_type == "datetime" and not form.edit_type:
        form.edit_type = "datetime"
    if not f.nullable and f.field_name not in {"id", "create_time", "update_time", "flg_deleted"}:
        if not form.regex_rule:
            form.regex_rule = "required"
        elif "required" not in form.regex_rule:
            form.regex_rule = f"required,{form.regex_rule}"
    return form
