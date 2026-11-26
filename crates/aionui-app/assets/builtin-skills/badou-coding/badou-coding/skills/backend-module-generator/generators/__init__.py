"""CRUD SQL Generators - __init__: orchestrator"""
from __future__ import annotations
import datetime
from common.generator_shared.models import ModuleDefinition
from generators.ddl_gen import generate_create as ddl_create, generate_cleanup as ddl_cleanup
from generators.module_gen import generate_create as module_create, generate_cleanup as module_cleanup
from generators.field_gen import generate_create as field_create, generate_cleanup as field_cleanup
from generators.form_gen import generate_create as form_create, generate_cleanup as form_cleanup
from generators.button_gen import generate_create as button_create, generate_cleanup as button_cleanup
from generators.dictionary_gen import generate_create as dict_create, generate_cleanup as dict_cleanup
from generators.resource_gen import generate_create as resource_create, generate_cleanup as resource_cleanup
from generators.role_gen import generate_create as role_create, generate_cleanup as role_cleanup
from generators.relation_gen import generate_create as relation_create, generate_cleanup as relation_cleanup
from generators.flow_integration import generate_flow_update_sql
from generators.cleanup_gen import generate_idempotent_cleanup, generate_cleanup_sql
from generators.validation_gen import generate_validation


def generate_create_sql(defn: ModuleDefinition) -> str:
    """生成完整的创建 SQL 脚本"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [
        f"-- {'='*59}", f"-- 模块: {defn.module.name_cn} ({defn.module.code}) | 版本: v{defn.version}",
        f"-- 生成时间: {now}", f"-- 生成器: crud-generator v2.0.0", f"-- {'='*59}", "",
        generate_idempotent_cleanup(defn), "", ddl_create(defn), "", module_create(defn), "",
        field_create(defn), "", dict_create(defn), "", form_create(defn), "", button_create(defn), "",
        resource_create(defn), "", role_create(defn), "", generate_validation(defn),
    ]
    if defn.flow_code:
        parts.extend(["", generate_flow_update_sql(defn)])
    return "\n".join(parts)


def generate_relation_sqls(defn: ModuleDefinition) -> str:
    if not defn.relations:
        return ""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"-- {'='*59}\n" f"-- 模块关联: {defn.module.name_cn} ({defn.module.code})\n"
        f"-- 生成时间: {now}\n" f"-- ⚠️  必须确保所有关联模块已存在\n" f"-- {'='*59}\n\n"
        + relation_create(defn)
    )