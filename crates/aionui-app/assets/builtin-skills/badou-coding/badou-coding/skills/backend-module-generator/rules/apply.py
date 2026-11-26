"""CRUD Generator - Rule Engine: rule orchestrator"""
from common.generator_shared.models import ModuleDefinition, DictionaryDef, DictItem, FormConfig, SearchBox
from rules.infer_field import inject_system_fields, inject_flow_fields, set_field_priorities
from rules.infer_form import infer_form_config
from rules.infer_module import infer_module_defaults

# ⚠️ 禁止额外定义审批状态字段（BO_STATUS 已自动注入）
_FORBIDDEN_STATUS_FIELDS = {
    'approval_status', 'approve_status', 'approved_status',
    'audit_status', 'audited_status',
    'review_status', 'reviewed_status',
    'flow_status', 'process_status', 'wf_status', 'workflow_status',
    'biz_status', 'business_status',
    'approve_state', 'audit_state', 'review_state', 'flow_state',
    'shp_status', 'shp_state',
    'shenpi_status', 'shenpi_state',
    'auditflag', 'approveflag', 'reviewflag',
}


def _get_flow_code(defn: ModuleDefinition) -> str | None:
    """获取有效 flow_code（顶层 > module 内）"""
    return defn.flow_code or defn.module.flow_code


def _validate_flow_fields(defn: ModuleDefinition) -> None:
    """校验 flow_code 相关字段约束"""
    flow_code = _get_flow_code(defn)
    if not flow_code:
        return

    # 1. 禁止字段校验
    for f in defn.fields:
        fn_lower = f.field_name.lower()
        if fn_lower in _FORBIDDEN_STATUS_FIELDS:
            raise ValueError(
                f"字段 '{f.field_name}' 是多余的审批状态字段。\n"
                f"  ⛔ 当 flow_code 存在时，流程审批状态由 BO_STATUS 固化字段自动管理。"
            )

    # 2. flow_business_name_field 校验
    biz_field = defn.flow_business_name_field or defn.module.flow_business_name_field
    if biz_field:
        field_names = {f.field_name for f in defn.fields}
        if biz_field not in field_names:
            raise ValueError(
                f"flow_business_name_field='{biz_field}' 在 fields 中不存在。"
            )


def _inject_bo_status_dict(defn: ModuleDefinition) -> None:
    """自动注入 BO_STATUS 字典"""
    flow_code = _get_flow_code(defn)
    if not flow_code:
        return
    if any(d.type_name == "BO_STATUS" for d in defn.dictionaries):
        return
    defn.dictionaries.append(DictionaryDef(
        type_name="BO_STATUS",
        name="业务状态",
        items=[
            DictItem(code="0", value="0", name="草稿", priority=1),
            DictItem(code="1", value="1", name="审批中", priority=2),
            DictItem(code="2", value="2", name="已通过", priority=3),
            DictItem(code="3", value="3", name="已驳回", priority=4),
        ],
    ))


def _patch_bo_status_form(defn: ModuleDefinition) -> None:
    """修复 BO_STATUS 字段的 form 配置"""
    flow_code = _get_flow_code(defn)
    if not flow_code:
        return
    for f in defn.fields:
        if f.field_name == "BO_STATUS":
            f.form = FormConfig(
                show_in_grid=True, show_type="dic", list_width="100px",
                sortable=True, show_in_page=False, editable=False,
                searchable=True, edit_type="hidden",
                data_source=1, dic_name="BO_STATUS",
                search_data_source=1, search_data="BO_STATUS",
                search_box=SearchBox(
                    id="bo_status", name="业务状态", defaultText="全部",
                    queryType="other-query", selectType=0,
                ),
            )


def apply_rules(defn: ModuleDefinition) -> ModuleDefinition:
    infer_module_defaults(defn)
    defn.fields = inject_system_fields(defn.fields)
    flow_code = _get_flow_code(defn)
    defn.fields = inject_flow_fields(defn.fields, flow_code)
    _validate_flow_fields(defn)
    _inject_bo_status_dict(defn)
    for f in defn.fields:
        infer_form_config(f)
    _patch_bo_status_form(defn)  # 必须在 infer_form_config 之后执行，覆盖 BO_STATUS 特殊配置
    defn.fields = set_field_priorities(defn.fields)
    return defn
