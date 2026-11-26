"""CRUD Generator - Data Models: DictItem, DictionaryDef"""
from __future__ import annotations
from pydantic import BaseModel


class DictItem(BaseModel):
    code: str
    value: str
    name: str
    priority: int = 1
    flg_default: int = 0


class DictionaryDef(BaseModel):
    type_name: str
    name: str
    value: str = ""
    items: list[DictItem] = []
