"""CRUD Generator - Rule Engine: module defaults inference"""
from common.generator_shared.models.base import _to_pascal_case


def infer_module_defaults(defn) -> None:
    m = defn.module
    if not m.module_name:
        m.module_name = _to_pascal_case(m.code)
    if not m.table_name_cn:
        m.table_name_cn = m.name_cn
