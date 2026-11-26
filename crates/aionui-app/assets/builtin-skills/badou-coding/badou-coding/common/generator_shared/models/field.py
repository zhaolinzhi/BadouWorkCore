"""CRUD Generator - Data Models: FieldDef"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from common.generator_shared.models.form import FormConfig, SearchBox
from common.generator_shared.models.base import _to_camel_case

VALID_DISPLAY_TYPES = {
    "varchar", "int", "decimal", "datetime", "text",
    "bigint", "date", "tinyint", "float", "double"
}

SYSTEM_FIELD_NAMES = {"id", "create_time", "update_time", "flg_deleted",
                      "creator", "creator_name", "updator", "updator_name"}

FLOW_FIELDS = [
    {"field_name": "FLOW_ID", "display_type": "varchar", "length": 64, "comment": "流程实例ID", "nullable": True},
    {"field_name": "FLOW_NAME", "display_type": "varchar", "length": 2000, "comment": "流程实例名称", "nullable": True},
    {"field_name": "FLOW_INSTANCE_ID", "display_type": "varchar", "length": 64, "comment": "流程实例唯一标识", "nullable": True},
    {"field_name": "NODE_INSTANCE_ID", "display_type": "varchar", "length": 64, "comment": "环节实例ID", "nullable": True},
    {"field_name": "NODE_INSTANCE_NAME", "display_type": "varchar", "length": 2000, "comment": "环节实例名称", "nullable": True},
    {"field_name": "BO_STATUS", "display_type": "int", "length": 1, "comment": "业务状态", "nullable": False, "default_value": "0", "dict": "BO_STATUS"},
    {"field_name": "NODE_CODE", "display_type": "varchar", "length": 64, "comment": "当前环节编码", "nullable": True},
]


class FieldDef(BaseModel):
    field_name: str
    entity_name: Optional[str] = None
    comment: str = ""
    display_type: str = "varchar"
    primary_key: bool = False
    unique: bool = False
    nullable: bool = True
    length: Optional[int] = None
    default_value: Optional[str] = None
    is_db_field: bool = True
    priority: Optional[int] = None
    form: FormConfig = Field(default_factory=FormConfig)
    dict: Optional[str] = None

    @field_validator("display_type")
    @classmethod
    def validate_display_type(cls, v: str) -> str:
        if v not in VALID_DISPLAY_TYPES:
            raise ValueError(f"display_type '{v}' 不在允许值中。允许值: {', '.join(sorted(VALID_DISPLAY_TYPES))}")
        return v

    @field_validator("comment")
    @classmethod
    def validate_comment_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("字段 comment 必填（DB COMMENT 不能为空，否则 DBA 无法识别字段含义）")
        return v.strip()

    @field_validator("field_name")
    @classmethod
    def validate_field_name_length(cls, v: str) -> str:
        if len(v) > 64:
            raise ValueError(f"字段名 '{v}' 超过 64 字符（DB md_field.field_name varchar(64)）")
        return v

    @model_validator(mode="after")
    def validate_field_name_no_system_collision(self) -> "FieldDef":
        if self.field_name in SYSTEM_FIELD_NAMES:
            raise ValueError(f"字段名 '{self.field_name}' 与系统字段冲突，请使用其他名称")
        return self

    @model_validator(mode="after")
    def infer_entity_name(self) -> "FieldDef":
        if not self.entity_name:
            self.entity_name = _to_camel_case(self.field_name)
        return self

    @model_validator(mode="after")
    def validate_hidden_nonnull_no_default(self) -> "FieldDef":
        if self.field_name in SYSTEM_FIELD_NAMES:
            return self
        if not self.nullable:
            form = self.form if self.form else FormConfig()
            no_user_input = form.edit_type == "hidden" or form.editable is False
            has_default = self.default_value is not None
            if no_user_input and not has_default:
                field_type = "hidden" if form.edit_type == "hidden" else "只读(editable=false)"
                raise ValueError(
                    f"字段 '{self.field_name}': {field_type} + NOT NULL + 无默认值 是设计错误。\n"
                    f"  修复方案：设 nullable=True（推荐），或设 default_value 提供数据库级默认值。"
                )
        return self

    @model_validator(mode="after")
    def infer_form_from_metadata(self) -> "FieldDef":
        form = self.form
        if self.dict:
            if not form.edit_type:
                form.edit_type = "select"
                form.data_source = 1
                form.dic_name = self.dict
            if form.searchable and not form.search_box:
                form.search_box = SearchBox(
                    id=self.entity_name or self.field_name,
                    name=self.comment or self.field_name,
                    defaultText="全部", queryType="other-query", selectType=0,
                )
                form.search_data_source = 1
                form.search_data = self.dict
        if self.display_type == "date" and not form.edit_type:
            form.edit_type = "date"
        if self.display_type == "text" and not form.edit_type:
            form.edit_type = "textarea"
        if self.display_type == "decimal":
            if not form.edit_type:
                form.edit_type = "number"
            if not form.regex_rule:
                form.regex_rule = "decimal"
            elif "decimal" not in form.regex_rule:
                form.regex_rule = f"{form.regex_rule},decimal"
        if self.display_type == "datetime" and not form.edit_type:
            form.edit_type = "datetime"
        if not self.nullable and self.field_name not in {"id", "create_time", "update_time", "flg_deleted"}:
            if not form.regex_rule:
                form.regex_rule = "required"
            elif "required" not in form.regex_rule:
                form.regex_rule = f"required,{form.regex_rule}"
        return self
