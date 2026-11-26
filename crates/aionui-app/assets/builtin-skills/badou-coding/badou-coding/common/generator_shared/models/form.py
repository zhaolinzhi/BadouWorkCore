"""CRUD Generator - Data Models: FormConfig, SearchBox"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class SearchBox(BaseModel):
    id: str = ""
    name: str = ""
    defaultText: str = ""
    isExtended: bool = False
    queryType: str = "like-query"
    selectType: Optional[int] = None
    tagName: str = ""


class FormConfig(BaseModel):
    show_in_grid: bool = True
    show_type: str = "text"
    list_width: str = "120px"
    sortable: bool = True
    show_in_page: bool = True
    editable: bool = True
    edit_type: Optional[str] = None
    edit_tip: Optional[str] = None
    regex_rule: Optional[str] = None
    searchable: bool = False
    search_box: Optional[SearchBox] = None
    data_source: Optional[int] = None
    dic_name: Optional[str] = None
    search_data_source: Optional[int] = None
    search_data: Optional[str] = None
    value_field_id: Optional[str] = None
    value_field_text: Optional[str] = None
    view_type: Optional[str] = None
    view_drill_url: Optional[str] = None
    view_drill_open_type: Optional[int] = None
    view_drill_page_title: Optional[str] = None
    is_full_line: Optional[bool] = None
    is_import: Optional[bool] = None
    is_export: Optional[bool] = None
    default_value: Optional[str] = None
    group: Optional[str] = None
