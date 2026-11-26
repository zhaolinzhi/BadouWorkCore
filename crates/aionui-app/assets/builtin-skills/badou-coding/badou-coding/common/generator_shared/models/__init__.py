"""CRUD Generator - Data Models (re-export)"""
from common.generator_shared.models.base import _to_camel_case, _to_pascal_case
from common.generator_shared.models.form import FormConfig, SearchBox
from common.generator_shared.models.dict import DictItem, DictionaryDef
from common.generator_shared.models.relation import RelationDef
from common.generator_shared.models.field import FieldDef, VALID_DISPLAY_TYPES, SYSTEM_FIELD_NAMES, FLOW_FIELDS
from common.generator_shared.models.module import ModuleDef, ModuleDefinition, MenuDef, FrontendConfig, CreatorInfo, RoleDef

# Backward compatibility aliases
SYSTEM_FIELDS = SYSTEM_FIELD_NAMES
CreatorDef = CreatorInfo
