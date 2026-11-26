"""CRUD Generator - Rule Engine: field defaults inference"""
from common.generator_shared.models import FieldDef, FormConfig, FLOW_FIELDS


def inject_system_fields(fields: list[FieldDef]) -> list[FieldDef]:
    from rules.system_fields import get_system_fields
    existing = {f.field_name for f in fields}
    return fields + [f for f in get_system_fields() if f.field_name not in existing]


def inject_flow_fields(fields: list[FieldDef], flow_code: str | None) -> list[FieldDef]:
    if not flow_code:
        return fields
    existing = {f.field_name for f in fields}
    for fw in FLOW_FIELDS:
        if fw["field_name"] not in existing:
            fields.append(FieldDef(
                field_name=fw["field_name"], display_type=fw["display_type"],
                length=fw.get("length"), comment=fw["comment"],
                nullable=fw.get("nullable", True), default_value=fw.get("default_value"),
                dict=fw.get("dict"),
                form=FormConfig(show_in_grid=False, show_in_page=False, editable=False, searchable=False),
            ))
    return fields


def set_field_priorities(fields: list[FieldDef]) -> list[FieldDef]:
    for i, f in enumerate(fields, start=1):
        if f.priority is None:
            f.priority = i
    return fields
