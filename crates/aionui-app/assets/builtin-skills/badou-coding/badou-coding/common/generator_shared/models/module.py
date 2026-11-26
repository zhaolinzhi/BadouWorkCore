"""CRUD Generator - Data Models: ModuleDef, ModuleDefinition, FrontendConfig, CreatorInfo"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, model_validator, field_validator
from common.generator_shared.models.field import FieldDef
from common.generator_shared.models.dict import DictionaryDef
from common.generator_shared.models.relation import RelationDef
from common.generator_shared.models.base import _to_pascal_case


class FrontendConfig(BaseModel):
    list_js_path: Optional[str] = None
    edit_js_path: Optional[str] = None

    @field_validator("list_js_path")
    @classmethod
    def validate_list_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.startswith("/"):
                raise ValueError(f"list_js_path 必须以 '/' 开头: '{v}'")
            if ".." in v:
                raise ValueError(f"list_js_path 不允许路径穿越: '{v}'")
            if "public/" in v:
                raise ValueError(f"list_js_path 不应包含 'public/': '{v}'")
        return v

    @field_validator("edit_js_path")
    @classmethod
    def validate_edit_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.startswith("/"):
                raise ValueError(f"edit_js_path 必须以 '/' 开头: '{v}'")
            if ".." in v:
                raise ValueError(f"edit_js_path 不允许路径穿越: '{v}'")
            if "public/" in v:
                raise ValueError(f"edit_js_path 不应包含 'public/': '{v}'")
        return v

    @staticmethod
    def default_list_path(module_code: str) -> str:
        """默认业务路径：public/moduleJs/business/{mdCode}/list.js（去掉 public/ 前缀）"""
        return f"/business/{module_code}/list.js"

    @staticmethod
    def default_edit_path(module_code: str) -> str:
        """默认业务路径：public/moduleJs/business/{mdCode}/edit.js（去掉 public/ 前缀）"""
        return f"/business/{module_code}/edit.js"


class CreatorInfo(BaseModel):
    id: str = "U00001"
    name: str = "系统管理员"


class RoleDef(BaseModel):
    role_id: str = ""
    role_code: str = "ROOT"

    model_config = {"extra": "ignore"}


class MenuDef(BaseModel):
    parent_id: str = ""
    parent_code: Optional[str] = None
    parent_name: str = ""
    level_id: str = "1.1"
    resource_code: Optional[str] = None
    full_path: str = ""
    full_name: str = ""
    priority: int = 1


class ModuleDef(BaseModel):
    module_name: Optional[str] = None
    name_cn: str
    code: str
    db_table: str
    table_name_cn: Optional[str] = None
    package_name: str = "com.badou.entity"
    data_source_code: Optional[str] = None
    base_class: Optional[str] = None
    flow_code: Optional[str] = None
    flow_business_name_field: Optional[str] = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def infer_defaults(self) -> "ModuleDef":
        if not self.module_name:
            self.module_name = _to_pascal_case(self.code)
        if not self.table_name_cn:
            self.table_name_cn = self.name_cn + "表"
        return self

    @field_validator("base_class")
    @classmethod
    def validate_base_class_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("base_class 不能为空字符串，设为 null 使用智能推断")
        return v


class ModuleDefinition(BaseModel):
    module: ModuleDef
    menu: MenuDef = Field(default_factory=MenuDef)
    fields: list[FieldDef]
    dictionaries: list[DictionaryDef] = []
    relations: list[RelationDef] = []
    buttons: list[str] = Field(default_factory=lambda: ["add", "edit", "view", "import", "export", "delete"])
    version: str = "1.0.0"
    flow_code: Optional[str] = None
    flow_business_name_field: Optional[str] = None
    frontend: Optional[FrontendConfig] = None
    role: RoleDef = Field(default_factory=RoleDef)
    creator: CreatorInfo = Field(default_factory=CreatorInfo)
    reserved_ids: dict = Field(default_factory=dict)

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def validate_flow_business_name_field_in_fields(self) -> "ModuleDefinition":
        field_name = self.module.flow_business_name_field or self.flow_business_name_field
        if field_name:
            field_names = {f.field_name for f in self.fields}
            if field_name not in field_names:
                raise ValueError(
                    f"flow_business_name_field='{field_name}' 但 fields 中不存在该字段。"
                    f"请检查字段名拼写，或先在 fields 中定义该字段。"
                )
        return self

    def infer_base_class(self) -> str:
        """4-tier base_class 智能推断决策树 (issue #2):

        1. 用户显式设定 (module.base_class) → 尊重用户
        2. 有关联流程 (module.flow_code 或 顶层 flow_code) → ModuleEntityFlowWithNodeCode
        3. 有业务字段（非 id-only）→ BaseModuleEntity (继承框架默认 create_time/creator 等)
        4. 兜底（id-only 字典表/参考表）→ ModuleEntityOnlyId
        """
        if self.module.base_class:
            return self.module.base_class
        # 兼容 def 文件两种写法: module.flow_code (新) 或顶层 self.flow_code (生产 def 写法)
        flow_code = self.module.flow_code or self.flow_code
        if flow_code:
            return "com.badou.designer.module.design.base.ModuleEntityFlowWithNodeCode"
        # 业务字段 = 除 id 之外的任何字段 (包括框架注入的 create_time/updator 等或用户定义字段)
        # 仅 id 字段的字典表/参考表才走 ModuleEntityOnlyId 兜底
        has_business_field = any(f.field_name != "id" for f in self.fields)
        if has_business_field:
            return "com.badou.designer.module.design.base.BaseModuleEntity"
        return "com.badou.designer.module.design.base.ModuleEntityOnlyId"
