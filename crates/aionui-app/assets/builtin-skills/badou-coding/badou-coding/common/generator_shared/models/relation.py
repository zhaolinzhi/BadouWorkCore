"""CRUD Generator - Data Models: RelationDef"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class RelationDef(BaseModel):
    type: int = Field(..., ge=1, le=2)
    related_module: str
    field_name: Optional[str] = None
    related_field_name: str
    display_name: str
    edit_module: int = Field(default=0, ge=0, le=1)
    is_cascade: int = Field(default=0, ge=0, le=1)
    show_style: int = Field(default=1, ge=1, le=3)
    tab_name: Optional[str] = None
    priority: int = 1
    is_edit: int = Field(default=1, ge=0, le=1)

    @model_validator(mode="after")
    def validate_relation(self) -> "RelationDef":
        if self.type == 1 and not self.field_name:
            raise ValueError("type=1（一对一）时 field_name 不能为空")
        if self.show_style in (1, 2) and not self.tab_name:
            raise ValueError(f"show_style={self.show_style} 时 tab_name 不能为空")
        return self

    @property
    def SHOW_TYPE(self) -> int:
        return 0 if self.type == 1 else 1

    @property
    def SHOW_TAB(self) -> int:
        return 1 if self.show_style in (1, 2) else 0
