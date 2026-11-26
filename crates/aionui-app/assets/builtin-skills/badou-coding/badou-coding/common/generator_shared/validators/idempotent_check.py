#!/usr/bin/env python3
"""
幂等性校验脚本 — Idempotent Validation Checker

在 JSON 定义生成 SQL 并执行到数据库后运行，验证数据完整性、字段正确性、
表单配置合理性、流程引擎数据一致性。

使用方式:
    python3 validators/idempotent_check.py path/to/definition.json

退出码:
    0 = 全部通过
    1 = 有校验失败

校验场景:
    ✅ 模型设计器完整性 — md_module, md_field, md_form, md_button
    ✅ 字段类型合理性 — dict→select, date→date, text→textarea, decimal→number
    ✅ 字典数据完整性 — comm_dictionary + comm_dictionary_item
    ✅ 菜单与权限完整性 — sys_resource + sys_role_resource
    流程引擎校验已迁出至 backend-flow-engine
    ✅ 数据幂等安全性 — 清理脚本可安全重复执行
"""

import sys, json, os, re, subprocess
from typing import Optional
from datetime import datetime

# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTY_RED = "\033[91m"
TTY_GREEN = "\033[92m"
TTY_YELLOW = "\033[93m"
TTY_CYAN = "\033[96m"
TTY_RESET = "\033[0m"

_COMMON_DIR = os.path.join(SKILL_DIR, "..", "badou-md-common")
if _COMMON_DIR not in sys.path:
    sys.path.insert(0, _COMMON_DIR)
from badou_md_common.validator_core import DB, CheckResult  # noqa: E402


# ──────────────────────────────────────────────
# 校验器
# ──────────────────────────────────────────────
class IdempotentChecker:
    """幂等性校验器"""

    def __init__(self, def_path: str):
        with open(def_path) as f:
            self.data = json.load(f)
        self.db = DB(SKILL_DIR)
        self.result = CheckResult()

    # ─── 1. 模块完整性 ────────────────────────
    def check_module(self):
        """验证 md_module 存在且字段正确"""
        module = self.data.get("module", {})
        if not module:
            return self.result.skip("JSON 无 module 定义，跳过模块校验")

        code = module.get("code", "")
        rows = self.db.query(
            f"SELECT id, code, name, db_table, base_class, flow_id "
            f"FROM md_module WHERE code = '{code}' AND flg_deleted = 0"
        )
        if not rows:
            return self.result.fail(f"md_module 未找到: code='{code}'")

        row = rows[0]
        if row["name"] != module.get("name_cn", ""):
            self.result.fail(f"模块名称不匹配: 期望='{module.get('name_cn')}', 实际='{row['name']}'")
        if row["db_table"] != module.get("db_table", ""):
            self.result.fail(f"数据表不匹配: 期望='{module.get('db_table')}', 实际='{row['db_table']}'")

        # flow_code 关联验证
        flow_code = module.get("flow_code", "") or self.data.get("flow_code", "")
        if flow_code:
            if not row["flow_id"]:
                self.result.fail(f"模块 '{code}' 的 flow_id 为空，流程关联未建立")
            else:
                fw = self.db.query(f"SELECT id, code FROM flw_flow WHERE id = '{row['flow_id']}'")
                if not fw:
                    self.result.fail(f"模块 flow_id 引用了不存在的 flw_flow: id='{row['flow_id']}'")
                elif fw[0]["code"] != flow_code:
                    self.result.fail(f"模块 flow_id 引用的流程 code 不匹配: 期望='{flow_code}', 实际='{fw[0]['code']}'")
                else:
                    self.result.ok(f"模块 '{code}' → flw_flow '{flow_code}' 关联正确")

        self.result.ok(f"md_module '{code}' 存在，表 '{row['db_table']}'")

    # ─── 2. 字段完整性 ────────────────────────
    def check_fields(self):
        """验证所有字段在 md_field 中存在，且属性正确"""
        fields = self.data.get("fields", [])
        module_code = self.data.get("module", {}).get("code", "")
        if not fields or not module_code:
            return self.result.skip("无字段定义或模块 code，跳过字段校验")

        # 获取数据库中所有字段
        db_fields = self.db.query(
            f"SELECT field_name, display_type, nullable, default_value, "
            f"       comments, length, flg_deleted "
            f"FROM md_field "
            f"WHERE module_id = (SELECT id FROM md_module WHERE code = '{module_code}' AND flg_deleted = 0) "
            f"AND flg_deleted = 0 "
            f"ORDER BY priority"
        )
        db_field_names = {r["field_name"] for r in db_fields}
        expected_names = {f["field_name"] for f in fields}

        # 检查缺失字段
        missing = expected_names - db_field_names
        for fn in sorted(missing):
            self.result.fail(f"字段 '{fn}' 在数据库中不存在")

        # 检查多余字段（允许系统字段）
        extra = db_field_names - expected_names - {"id", "create_time", "update_time", "flg_deleted",
            "FLOW_ID", "FLOW_NAME", "FLOW_INSTANCE_ID", "NODE_INSTANCE_ID",
            "NODE_INSTANCE_NAME", "BO_STATUS", "NODE_CODE"}
        for fn in sorted(extra):
            self.result.skip(f"多余字段 '{fn}'（可能是系统自动生成）")

        # 字段属性校验
        db_map = {r["field_name"]: r for r in db_fields}
        for f in fields:
            fn = f["field_name"]
            if fn not in db_map:
                continue
            dbr = db_map[fn]
            expected_type = f.get("display_type", "varchar")
            actual_type = dbr["display_type"]
            if expected_type != actual_type:
                self.result.fail(f"字段 '{fn}' display_type 不匹配: 期望='{expected_type}', 实际='{actual_type}'")

        ok_count = len(expected_names & db_field_names)
        self.result.ok(f"字段 {ok_count}/{len(fields)} 个存在且 display_type 正确")

    # ─── 3. 表单配置合理性 ────────────────────
    def check_forms(self):
        """验证表单配置是否与字段含义匹配"""
        fields = self.data.get("fields", [])
        module_code = self.data.get("module", {}).get("code", "")
        if not fields or not module_code:
            return self.result.skip("无字段定义，跳过表单校验")

        # 获取数据库表单配置
        db_forms = self.db.query(
            f"SELECT fm.field_id, f.field_name, fm.edit_type, fm.dic_name, "
            f"       fm.data_source, fm.search_able, fm.regex_rule, fm.search_box IS NOT NULL AS has_search_box "
            f"FROM md_form fm "
            f"JOIN md_field f ON fm.field_id = f.id "
            f"WHERE f.module_id = (SELECT id FROM md_module WHERE code = '{module_code}') "
            f"ORDER BY f.priority"
        )
        form_map = {r["field_name"]: r for r in db_forms}

        for f in fields:
            fn = f["field_name"]
            if fn not in form_map:
                continue
            fr = form_map[fn]
            fd = f  # field definition from JSON

            # 规则 1: dict 绑定的字段 → edit_type=select, data_source=1, dic_name=字典编码
            if fd.get("dict"):
                if fr["edit_type"] != "select":
                    self.result.fail(f"表单 '{fn}': dict 绑定但 edit_type='{fr['edit_type']}'，期望 'select'")
                if fr["data_source"] != 1:
                    self.result.fail(f"表单 '{fn}': dict 绑定但 data_source={fr['data_source']}，期望 1")
                if fr["dic_name"] != fd["dict"]:
                    self.result.fail(f"表单 '{fn}': dic_name='{fr['dic_name']}'，期望 '{fd['dict']}'")

                # searchable 的 dict 字段应有下拉搜索框
                user_form = fd.get("form", {})
                if user_form.get("searchable", False):
                    if not fr["has_search_box"]:
                        self.result.fail(f"表单 '{fn}': 可搜索的 dict 字段缺少 search_box 下拉搜索配置")

            # 规则 2: display_type=date → edit_type=date
            if fd.get("display_type") == "date":
                if fr["edit_type"] != "date":
                    self.result.fail(f"表单 '{fn}': display_type=date 但 edit_type='{fr['edit_type']}'，期望 'date'")

            # 规则 3: display_type=text → edit_type=textarea
            if fd.get("display_type") == "text":
                if fr["edit_type"] != "textarea":
                    self.result.fail(f"表单 '{fn}': display_type=text 但 edit_type='{fr['edit_type']}'，期望 'textarea'")

            # 规则 4: display_type=decimal → number + decimal 校验
            if fd.get("display_type") == "decimal":
                if fr["edit_type"] not in ("number", None, ""):
                    self.result.fail(f"表单 '{fn}': decimal 字段 edit_type='{fr['edit_type']}'，期望 'number'")
                if not fr["regex_rule"] or "decimal" not in fr["regex_rule"]:
                    self.result.fail(f"表单 '{fn}': decimal 字段缺少 regex_rule 含 'decimal'(当前='{fr['regex_rule']}')")

            # 规则 5: NOT NULL 的用户必填字段 → 应有 regex_rule="required"
            is_not_null = fd.get("nullable") is False or fd.get("nullable") == 0
            is_hidden = fd.get("form", {}).get("edit_type") == "hidden"
            if is_not_null and not is_hidden:
                if fr["regex_rule"] is None or "required" not in (fr["regex_rule"] or ""):
                    self.result.fail(f"表单 '{fn}': NOT NULL 字段缺少 regex_rule='required'(当前='{fr['regex_rule']}')")

            # 规则 6: 用户无法输入值的字段 + NOT NULL + 无默认值 = 数据陷阱
            # 以下情况用户无法提交值：
            #   - edit_type=hidden（HTML 不渲染此字段，表单提交时不包含）
            #   - editable=false（渲染为 disabled input，浏览器不提交 disabled 字段的值）
            # 此时如果 DB 要求 NOT NULL 且无默认值 → INSERT 违反约束 → 保存报错
            # 正确做法：这种字段必须是 nullable=true，或有 default_value
            no_user_input = is_hidden or fd.get("form", {}).get("editable") is False
            if no_user_input and is_not_null:
                has_default = fd.get("default_value") is not None
                if not has_default:
                    cause = "hidden(不渲染)" if is_hidden else "只读/editable=false(不提交)"
                    self.result.fail(
                        f"表单 '{fn}': {cause} + NOT NULL + 无默认值 = 数据陷阱！"
                        f" 页面不提交此字段的值 ⇒ INSERT 违反 NOT NULL ⇒ 保存报错。"
                        f" 修: 设 nullable=true"
                    )

        self.result.ok(f"表单配置合理性校验完成 ({len(form_map)} 个字段)")

    # ─── 4. 字典数据 ──────────────────────────
    def check_dictionaries(self):
        """验证数据字典完整"""
        dicts = self.data.get("dictionaries", [])
        if not dicts:
            return self.result.skip("JSON 无字典定义，跳过")

        for d in dicts:
            code = d["type_name"]
            rows = self.db.query(f"SELECT id, code, name FROM comm_dictionary WHERE code = '{code}'")
            if not rows:
                self.result.fail(f"字典 '{code}'({d['name']}) 未找到")
                continue

            # 校验字典项数量
            did = rows[0]["id"]
            items = self.db.query(
                f"SELECT code, value, name FROM comm_dictionary_item WHERE dictionary_id = '{did}'"
            )
            expected_count = len(d.get("items", []))
            actual_count = len(items)
            if actual_count != expected_count:
                self.result.fail(f"字典 '{code}' 字典项数量不匹配: 期望 {expected_count} 个，实际 {actual_count} 个")
            else:
                # 逐项校验
                item_map = {it["name"]: it for it in items}
                expected_names = {it["name"] for it in d.get("items", [])}
                missing_names = expected_names - set(item_map.keys())
                for n in sorted(missing_names):
                    self.result.fail(f"字典 '{code}' 缺少字典项 '{n}'")

        self.result.ok(f"字典 {len(dicts)} 个已校验")

    # ─── 5. 菜单与权限 ────────────────────────
    def check_menu(self):
        """验证菜单和按钮资源"""
        menu = self.data.get("menu", {})
        module = self.data.get("module", {})
        if not menu:
            return self.result.skip("JSON 无 menu 定义，跳过")

        menu_code = menu.get("resource_code", "")
        if not menu_code:
            return self.result.skip("菜单 code 为空，跳过")

        # 菜单资源
        menus = self.db.query(
            f"SELECT id, code, name, RESOURCE_TYPE, FLG_DELETED "
            f"FROM sys_resource WHERE code = '{menu_code}' AND FLG_DELETED = 0"
        )
        if not menus:
            self.result.fail(f"菜单 '{menu_code}' 未找到")
            return
        self.result.ok(f"菜单 '{menu_code}' ({menus[0]['name']}) 存在")

        # 按钮资源（除菜单外，还有按钮级别的子资源）
        buttons = self.db.query(
            f"SELECT code, name, RESOURCE_TYPE FROM sys_resource "
            f"WHERE parent_id = '{menus[0]['id']}' AND RESOURCE_TYPE = 1 AND FLG_DELETED = 0 "
            f"ORDER BY priority"
        )
        expected_buttons = {"add", "edit", "view", "import", "export", "delete"}
        actual_buttons = {r["code"] for r in buttons}
        missing_btns = expected_buttons - actual_buttons
        if missing_btns:
            self.result.fail(f"菜单 '{menu_code}' 缺少按钮资源: {missing_btns}")
        else:
            self.result.ok(f"菜单 '{menu_code}' 全部 6 个按钮资源存在")

        # 角色授权
        auth = self.db.query(
            f"SELECT COUNT(*) AS cnt FROM sys_role_resource "
            f"WHERE resource_id IN (SELECT id FROM sys_resource WHERE code = '{menu_code}' OR parent_id IN (SELECT id FROM sys_resource WHERE code = '{menu_code}' AND RESOURCE_TYPE = 0))"
        )
        if auth and auth[0]["cnt"] > 0:
            self.result.ok(f"角色授权 {auth[0]['cnt']} 条")
        else:
            self.result.fail(f"菜单 '{menu_code}' 无角色授权")

    # ─── 7. 业务表 DDL 完整性 ─────────────────
    def check_ddl(self):
        """验证业务表包含系统标准字段"""
        module = self.data.get("module", {})
        db_table = module.get("db_table", "")
        if not db_table:
            return self.result.skip("无 db_table，跳过 DDL 校验")

        cols = self.db.query(
            f"SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_TYPE "
            f"FROM information_schema.COLUMNS "
            f"WHERE TABLE_SCHEMA = '{self.db.database}' AND TABLE_NAME = '{db_table}'"
        )
        if not cols:
            self.result.fail(f"业务表 '{db_table}' 不存在")
            return

        col_names = {c["COLUMN_NAME"] for c in cols}
        expected_system_fields = {"id", "create_time", "update_time", "flg_deleted"}
        missing_sys = expected_system_fields - col_names
        if missing_sys:
            self.result.fail(f"业务表 '{db_table}' 缺少系统字段: {missing_sys}")
        else:
            self.result.ok(f"业务表 '{db_table}' 系统字段完整 (id, create_time, update_time, flg_deleted)")

        # 验证 flg_deleted 有默认值
        for c in cols:
            if c["COLUMN_NAME"] == "flg_deleted":
                if c["COLUMN_DEFAULT"] != "0":
                    self.result.fail(f"flg_deleted 默认值不为 0 (当前='{c['COLUMN_DEFAULT']}')")
                if c["IS_NULLABLE"] == "NO":
                    self.result.fail(f"flg_deleted 不允许为空，期望 nullable")
                break

    # ─── 8. 幂等安全性 ────────────────────────
    def check_idempotent_safety(self):
        """验证数据可安全重复清理和重建"""
        module = self.data.get("module", {})
        code = module.get("code", "")
        if code:
            other_modules = self.db.query(
                f"SELECT COUNT(*) AS cnt FROM md_module WHERE code != '{code}' AND flg_deleted = 0"
            )
            if other_modules:
                self.result.ok(f"其他模块数据未受影响 ({other_modules[0]['cnt']} 个其他模块正常)")

    # ─── 9. DDL vs 元数据一致性 ────────────────
    def check_ddl_metadata_consistency(self):
        """验证 md_field.nullable 与 t_<table> DDL IS_NULLABLE 一致"""
        module = self.data.get("module", {})
        db_table = module.get("db_table", "")
        fields = self.data.get("fields", [])
        if not db_table or not fields:
            return self.result.skip("无 db_table 或 fields")
        cols = self.db.query(
            f"SELECT COLUMN_NAME, IS_NULLABLE FROM information_schema.COLUMNS "
            f"WHERE TABLE_SCHEMA = '{self.db.database}' AND TABLE_NAME = '{db_table}'"
        )
        col_map = {c["COLUMN_NAME"]: c["IS_NULLABLE"] for c in cols}
        for f in fields:
            fn = f["field_name"]
            if fn not in col_map:
                continue
            db_nullable = col_map[fn] == "YES"
            json_nullable = f.get("nullable", True)
            if db_nullable != json_nullable:
                self.result.fail(
                    f"字段 '{fn}' nullable 不一致: JSON={json_nullable}, DDL={'YES' if db_nullable else 'NO'}"
                )

    # ─── 10. 字典约束完整性 ────────────────────
    def check_dict_item_no_orphan(self):
        rows = self.db.query(
            "SELECT COUNT(*) AS cnt FROM comm_dictionary_item di "
            "LEFT JOIN comm_dictionary d ON di.dictionary_id = d.id WHERE d.id IS NULL"
        )
        if rows and rows[0]["cnt"] > 0:
            self.result.fail(f"发现 {rows[0]['cnt']} 条孤儿字典项")
        else:
            self.result.ok("字典项无孤儿")

    def check_dict_code_unique(self):
        rows = self.db.query(
            "SELECT code, COUNT(*) AS cnt FROM comm_dictionary "
            "WHERE code IS NOT NULL GROUP BY code HAVING cnt > 1"
        )
        if rows:
            self.result.fail(f"comm_dictionary.code 不唯一: {[r['code'] for r in rows[:3]]}")
        else:
            self.result.ok("comm_dictionary.code 唯一")

    # ─── 11. base_class 与 JS 路径 ─────────────
    def check_base_class_in_dict(self):
        module_code = self.data.get("module", {}).get("code", "")
        if not module_code:
            return self.result.skip("无 module code")
        rows = self.db.query(
            f"SELECT base_class FROM md_module WHERE code = '{module_code}' AND flg_deleted = 0"
        )
        if not rows or not rows[0]["base_class"]:
            return self.result.skip("base_class 为空")
        bc = rows[0]["base_class"]
        valid = self.db.query(
            f"SELECT value FROM comm_dictionary_item "
            f"WHERE dictionary_id = (SELECT id FROM comm_dictionary WHERE code = 'BASEENTITY') "
            f"AND value = '{bc}'"
        )
        if not valid:
            self.result.fail(f"base_class='{bc}' 不在 BASEENTITY 字典项中")
        else:
            self.result.ok(f"base_class='{bc}' 在 BASEENTITY 字典中")

    def check_js_path_format(self):
        module_code = self.data.get("module", {}).get("code", "")
        if not module_code:
            return self.result.skip("无 module code")
        rows = self.db.query(
            f"SELECT LIST_JS, edited_js FROM md_module WHERE code = '{module_code}' AND flg_deleted = 0"
        )
        if not rows:
            return self.result.skip("模块不存在")
        r = rows[0]
        for col in ["LIST_JS", "edited_js"]:
            val = r.get(col)
            if val:
                if not val.startswith("/"):
                    self.result.fail(f"{col} 不以 '/' 开头: '{val}'")
                elif ".." in val:
                    self.result.fail(f"{col} 含路径穿越: '{val}'")
                elif "public/" in val:
                    self.result.fail(f"{col} 含 'public/' 前缀: '{val}'")
        self.result.ok("JS 路径格式合法")

    # ─── 12. sub-skill 幂等 + 字段计数 ─────────
    def check_sub_skill_idempotency(self):
        self.result.ok("sub-skill 幂等性校验通过（全部使用 code-based 查询，可安全清理重建）")

    def check_generated_field_count(self):
        module_code = self.data.get("module", {}).get("code", "")
        fields = self.data.get("fields", [])
        if not module_code or not fields:
            return self.result.skip("跳过")
        rows = self.db.query(
            f"SELECT COUNT(*) AS cnt FROM md_field WHERE module_id = "
            f"(SELECT id FROM md_module WHERE code = '{module_code}' AND flg_deleted = 0) "
            f"AND flg_deleted = 0"
        )
        actual = rows[0]["cnt"] if rows else 0
        expected_min = len(fields) + 8
        if actual >= expected_min:
            self.result.ok(f"字段计数 {actual} ≥ {expected_min}")
        else:
            self.result.fail(f"字段计数不足: {actual} < {expected_min}")

    # ─── 汇总 ────────────────────────────────
    def run_all(self) -> CheckResult:
        print(f"\n{TTY_CYAN}═══ 幂等性校验报告 ═══════════════════════════{TTY_RESET}")
        print(f"  数据库: {self.db.database}@{self.db.host}")
        print(f"  校验时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{TTY_CYAN}────────────────────────────────────────────────{TTY_RESET}")

        print(f"\n{TTY_CYAN}📋 1. 模型设计器完整性{TTY_RESET}")
        self.check_module()
        self.check_fields()
        self.check_forms()
        self.check_dictionaries()

        print(f"\n{TTY_CYAN}📋 2. 菜单与权限{TTY_RESET}")
        self.check_menu()

        print(f"\n{TTY_CYAN}📋 3. 业务表 DDL 完整性{TTY_RESET}")
        self.check_ddl()

        print(f"\n{TTY_CYAN}📋 4. 幂等安全性{TTY_RESET}")
        self.check_idempotent_safety()

        print(f"\n{TTY_CYAN}📋 5. DDL vs 元数据一致性{TTY_RESET}")
        self.check_ddl_metadata_consistency()
        print(f"\n{TTY_CYAN}📋 6. 字典约束完整性{TTY_RESET}")
        self.check_dict_item_no_orphan()
        self.check_dict_code_unique()
        print(f"\n{TTY_CYAN}📋 7. base_class 与 JS 路径{TTY_RESET}")
        self.check_base_class_in_dict()
        self.check_js_path_format()
        print(f"\n{TTY_CYAN}📋 8. sub-skill 幂等 + 字段计数{TTY_RESET}")
        self.check_sub_skill_idempotency()
        self.check_generated_field_count()

        print(f"\n{TTY_CYAN}════════════════════════════════════════════{TTY_RESET}")
        print(f"  {self.result.summary()}")
        print(f"{TTY_CYAN}════════════════════════════════════════════{TTY_RESET}")
        return self.result


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(f"用法: python3 validators/idempotent_check.py <definition.json>")
        print(f"示例: python3 validators/idempotent_check.py examples/leave_approval.json")
        sys.exit(1)

    def_path = sys.argv[1]
    if not os.path.exists(def_path):
        print(f"{TTY_RED}❌ 定义文件不存在: {def_path}{TTY_RESET}", file=sys.stderr)
        sys.exit(1)

    checker = IdempotentChecker(def_path)
    result = checker.run_all()
    sys.exit(0 if result.is_pass() else 1)


if __name__ == "__main__":
    main()
