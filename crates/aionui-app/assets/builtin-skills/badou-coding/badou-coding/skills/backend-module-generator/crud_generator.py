#!/usr/bin/env python3
"""
CRUD Generator - 基于 MD 模块实现 CRUD 功能的 SQL 生成器

用法:
    python crud_generator.py --def module_def.json
    python crud_generator.py --def module_def.json --output /path/to/output
    python crud_generator.py --def module_def.json --config {项目}/.trellis/crud-config.json
    python crud_generator.py --def module_def.json --config-from-brain {项目}/.trellis/PROJECT-BRAIN.md
    python crud_generator.py --init-project /path/to/project
    python crud_generator.py --check /path/to/project/.trellis/crud-config.json
    python crud_generator.py --validate
    python crud_generator.py --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
import uuid
import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_COMMON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "badou-md-common")
_BADOU_CODING_COMMON = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common")
)
for p in (_COMMON_DIR, _BADOU_CODING_COMMON):
    if p not in sys.path:
        sys.path.insert(0, p)
# 保留旧 import 路径做 fallback（D27 兼容期）
from badou_md_common.config_loader import parse_brain_markdown  # noqa: E402
from db_config_resolver import resolve_db_config, ConfigNotFoundError  # noqa: E402 — D27

# 共享 models/validators 已迁移至 common/generator_shared/
# 需要将 badou-coding/ 加到 sys.path，才能解析 `from common.generator_shared.models import ...`
_SHARED_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
if _SHARED_ROOT not in sys.path:
    sys.path.insert(0, _SHARED_ROOT)

from common.generator_shared.models import ModuleDefinition
from rules import apply_rules
from generators import generate_create_sql, generate_cleanup_sql, generate_relation_sqls


# ============================================================
# ID pre-generation (eliminates MySQL session variable dependency)
# ============================================================
def generate_all_ids(defn: ModuleDefinition) -> dict:
    """预生成所有 UUID，消除对 MySQL SET @variable 的依赖。

    PyMySQL 默认不支持多语句执行，逐条执行时 session 变量会丢失。
    预生成 ID 后直接嵌入 SQL 字面量，确保 PyMySQL 兼容。
    """
    ids = {
        'module_id': uuid.uuid4().hex,
        'menu_resource_id': uuid.uuid4().hex,
        'field_ids': {},
        'link_uuids': [],
    }
    for f in defn.fields:
        ids['field_ids'][f.field_name] = uuid.uuid4().hex
    for _ in defn.relations:
        ids['link_uuids'].append(uuid.uuid4().hex)
    return ids


# ============================================================
# Config loading
# ============================================================
def load_definition(path: str) -> ModuleDefinition:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ModuleDefinition(**data)


def load_project_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_project_config(defn: ModuleDefinition, config: dict) -> ModuleDefinition:
    """将项目配置应用到模块定义上，覆盖默认系统参数。只覆盖显式提供的值。"""
    project_cfg = config.get("project", {})
    if project_cfg.get("package_name"):
        defn.module.package_name = project_cfg["package_name"]

    system_cfg = config.get("system", {})
    if system_cfg.get("creator_id"):
        defn.creator.id = system_cfg["creator_id"]
    if system_cfg.get("creator_name"):
        defn.creator.name = system_cfg["creator_name"]
    if system_cfg.get("data_source_code"):
        defn.module.data_source_code = system_cfg["data_source_code"]
    if system_cfg.get("base_class"):
        if not hasattr(defn, "_extra"):
            defn._extra = {}
        defn._extra["base_class"] = system_cfg["base_class"]

    return defn


# ============================================================
# Output helpers
# ============================================================
def get_output_dir(base_output: str, module_code: str, version: str) -> Path:
    out = Path(base_output) / module_code / f"v{version}"
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_manifest(out_dir: Path, defn: ModuleDefinition, tables_affected: list[str]) -> None:
    manifest = {
        "module_code": defn.module.code,
        "version": defn.version,
        "created_at": datetime.datetime.now().isoformat(),
        "generator_version": "1.0.0",
        "tables_affected": tables_affected,
        "stats": {
            "fields": len(defn.fields),
            "buttons": len(defn.buttons),
            "dictionaries": len(defn.dictionaries),
            "dict_items": sum(len(d.items) for d in defn.dictionaries),
        },
    }
    manifest_path = out_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def update_versions_index(base_output: str, module_code: str, version: str) -> None:
    versions_file = Path(base_output) / module_code / "versions.json"
    versions = []
    if versions_file.exists():
        with open(versions_file, "r", encoding="utf-8") as f:
            versions = json.load(f)
    entry = {"version": version, "created_at": datetime.datetime.now().isoformat(), "path": f"v{version}/"}
    existing = [v for v in versions if v["version"] == version]
    if not existing:
        versions.append(entry)
    else:
        versions[versions.index(existing[0])] = entry
    versions.sort(key=lambda v: [int(x) for x in v["version"].split(".")])
    with open(versions_file, "w", encoding="utf-8") as f:
        json.dump(versions, f, ensure_ascii=False, indent=2)


def auto_increment_version(base_output: str, module_code: str) -> str:
    versions_file = Path(base_output) / module_code / "versions.json"
    if not versions_file.exists():
        return "1.0.0"
    with open(versions_file, "r", encoding="utf-8") as f:
        versions = json.load(f)
    if not versions:
        return "1.0.0"
    parts = versions[-1]["version"].split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


# ============================================================
# Project management
# ============================================================
def init_project(project_dir: str) -> None:
    """为新项目初始化 crud-generator 骨架目录"""
    project_root = Path(project_dir).resolve()
    crud_dir = project_root / "crud-generator"
    for d in [crud_dir / "output", crud_dir / "module_defs"]:
        d.mkdir(parents=True, exist_ok=True)

    config_path = project_root / ".trellis" / "crud-config.json"
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        template = {
            "project": {"name": "", "package_name": "com.badou.entity"},
            "system": {
                "data_source_code": "projectDatabase",
                "creator_id": "U00001",
                "creator_name": "系统管理员",
            },
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)

    print(f"\u2705 项目骨架已初始化: {project_root}")
    print(f"   {crud_dir}/output/")
    print(f"   {crud_dir}/module_defs/")
    print(f"   {config_path}  (请编辑填入实际项目配置)")


def check_project(config_path: str) -> bool:
    """校验项目配置完整性"""
    print("=" * 50)
    print("\U0001f50d 项目配置校验")
    print("=" * 50)
    all_ok = True

    try:
        cfg = load_project_config(config_path)
        print("\u2705 配置文件可解析")
    except Exception as e:
        print(f"\u274c 配置文件解析失败: {e}")
        return False

    checks = [
        ("project.package_name", cfg.get("project", {}).get("package_name")),
        ("system.creator_id", cfg.get("system", {}).get("creator_id")),
        ("system.data_source_code", cfg.get("system", {}).get("data_source_code")),
    ]
    for name, val in checks:
        if val:
            print(f"\u2705 {name} = {val}")
        else:
            print(f"\u26a0\ufe0f  {name} 未配置（将使用默认值）")

    db = cfg.get("database", {})
    if db.get("host") and db.get("user"):
        try:
            import subprocess
            cmd = [
                "mysql", f"-h{db['host']}", f"-P{db.get('port', '3306')}",
                f"-u{db['user']}", f"-D{db.get('name', '')}",
                "-e", "SELECT 1 AS ok;",
            ]
            if db.get("password"):
                cmd.insert(3, f"-p{db['password']}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"\u2705 数据库连接成功: {db['host']}:{db.get('port', '3306')}/{db.get('name', '')}")
            else:
                print(f"\u26a0\ufe0f  数据库连接失败: {result.stderr.strip()}")
                all_ok = False
        except FileNotFoundError:
            print("\u26a0\ufe0f  mysql 客户端未安装，跳过连接测试")
        except Exception as e:
            print(f"\u26a0\ufe0f  数据库连接测试异常: {e}")

    config_dir = Path(config_path).parent.parent
    output_dir = config_dir / "crud-generator" / "output"
    if output_dir.exists():
        print(f"\u2705 输出目录存在: {output_dir}")
    else:
        print(f"\u26a0\ufe0f  输出目录不存在: {output_dir}（首次生成时自动创建）")

    print()
    print("\u2705 项目配置校验通过" if all_ok else "\u26a0\ufe0f  存在警告，但可继续使用")
    return all_ok


def check_module_conflict(base_output: str, module_code: str) -> bool:
    output_dir = Path(base_output) / module_code
    if output_dir.exists():
        versions = list(output_dir.glob("v*"))
        if versions:
            ver_strs = [v.name for v in versions]
            print(f"\u26a0\ufe0f  模块 '{module_code}' 已存在版本: {', '.join(ver_strs)}")
            return True
    return False


def check_shared_db_warning(config: dict) -> None:
    db = config.get("database", {})
    if not db:
        return
    dedicated = db.get("db_dedicated", True)
    if dedicated is False or str(dedicated).lower() in ("false", "no", "0"):
        print("\u26a0\ufe0f  警告: 当前项目使用共享数据库 (db_dedicated=false)")
        print("   请确认生成的 SQL 不会影响其他项目！")
        print()


def warn_unreferenced_dictionaries(defn: ModuleDefinition) -> bool:
    """检查是否有字典定义了但没有任何字段引用，输出警告并返回是否发现问题"""
    if not defn.dictionaries:
        return False

    # 收集所有字段引用的字典 code
    referenced = {f.dict for f in defn.fields if f.dict}

    # 找出定义了但没被引用的字典
    defined = {d.type_name for d in defn.dictionaries}
    unreferenced = defined - referenced

    if unreferenced:
        print("\n\u26a0\ufe0f  字典引用警告：")
        print("  以下字典已在 definitions.dictionaries 中定义，")
        print("  但没有任何字段通过 field.dict 引用它们：")
        for code in sorted(unreferenced):
            dict_name = next((d.name for d in defn.dictionaries if d.type_name == code), code)
            print(f"    \u274c {code} ({dict_name})")
        print("\n  修复方法：在需要使用该字典的字段定义中添加：")
        for code in sorted(unreferenced):
            print(f'    {{"field_name": "xxx", "dict": "{code}", ...}}')
        print("  不引用字典的字段，前端下拉框将没有选项！\n")
        return True
    return False


def check_version_overwrite(base_output: str, module_code: str, version: str, force: bool) -> bool:
    output_dir = Path(base_output) / module_code / f"v{version}"
    create_file = output_dir / f"{module_code}_create.sql"
    if create_file.exists():
        if not force:
            print(f"\u274c 版本 v{version} 已存在: {create_file}")
            print(f"   如需覆盖，请添加 --force 参数")
            return False
        else:
            print(f"\u26a0\ufe0f  强制覆盖已有版本 v{version}")
    return True


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="CRUD SQL 生成器 - 基于 MD 模块实现 CRUD 功能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --def module_def.json --config crud-config.json --output ./output
  %(prog)s --def module_def.json --config-from-brain PROJECT-BRAIN.md
  %(prog)s --init-project /home/projects/my-project
  %(prog)s --check /path/to/project/.trellis/crud-config.json
  %(prog)s --def module_def.json --dry-run
        """,
    )
    parser.add_argument("--def", dest="def_file", help="模块定义文件路径 (JSON)")
    parser.add_argument("--output", "-o", default=None, help="输出目录")
    parser.add_argument("--version", "-v", default=None, help="版本号")
    parser.add_argument("--validate", action="store_true", help="仅校验，不生成")
    parser.add_argument("--dry-run", action="store_true", help="预览生成结果")
    parser.add_argument("--create-only", action="store_true", help="仅生成创建 SQL")
    parser.add_argument("--cleanup-only", action="store_true", help="仅生成清理 SQL")
    parser.add_argument("--config", "-c", default=None, help="项目配置文件路径 (JSON)")
    parser.add_argument("--config-from-brain", default=None, help="从 PROJECT-BRAIN.md 自动解析配置")
    parser.add_argument("--force", action="store_true", help="强制覆盖已存在的版本")
    parser.add_argument("--project-root", default=".",
                        help="D27: 项目根目录（含 .trellis/ 或 backend/），供 fallback chain 使用")
    parser.add_argument("--no-interactive", action="store_true",
                        help="D27: 禁用 input() 询问作为最后一层 fallback（CI 推荐使用）")
    parser.add_argument("--init-project", default=None, help="初始化项目骨架目录")
    parser.add_argument("--check", default=None, help="校验项目配置 (crud-config.json 路径)")

    args = parser.parse_args()

    # Special modes
    if args.init_project:
        init_project(args.init_project)
        return
    if args.check:
        ok = check_project(args.check)
        sys.exit(0 if ok else 1)

    if not args.def_file:
        parser.error("--def 是必需的（或使用 --init-project / --check）")

    # Load project config (D27: 4 层 fallback — explicit / brain / pom+yml / interactive)
    # 注意：--validate 仅推断规则不需要 DB；除非显式提供配置，否则跳过 resolver。
    project_config = None
    if args.validate and not (args.config_from_brain or args.config):
        pass
    else:
        project_root = getattr(args, "project_root", ".") or "."
        try:
            resolved = resolve_db_config(
                project_root=project_root,
                explicit_config=args.config_from_brain or args.config,
                interactive=not getattr(args, "no_interactive", False),
            )
        except ConfigNotFoundError as exc:
            if not (args.config_from_brain or args.config):
                print(f"\u274c DB 配置解析失败: {exc}")
                sys.exit(1)
            raise
        db_cfg = resolved.get("database", {}) or {}
        extras = {k: v for k, v in resolved.items() if k not in ("database", "source")}
        if extras:
            project_config = {"database": db_cfg, **extras}
        elif db_cfg:
            project_config = {"database": db_cfg}
        source = resolved.get("source", "?")
        if project_config:
            print(f"\u2705 DB 配置已解析（source={source}）: host={db_cfg.get('host','?')}, db={db_cfg.get('name','?')}")

    if project_config:
        check_shared_db_warning(project_config)

    # Load and validate
    try:
        defn = load_definition(args.def_file)
        print(f"\u2705 定义文件校验通过: {defn.module.name_cn} ({defn.module.code})")
    except Exception as e:
        print(f"\u274c 定义文件校验失败: {e}")
        sys.exit(1)

    if project_config:
        defn = apply_project_config(defn, project_config)
        print(f"\u2705 项目配置已应用: creator={defn.creator.id}, data_source={defn.module.data_source_code or '(默认)'}")

    if args.validate:
        defn = apply_rules(defn)
        warn_unreferenced_dictionaries(defn)
        print(f"\n\U0001f4cb 推断结果:")
        print(f"  模块: {defn.module.name_cn} ({defn.module.code})")
        print(f"  表名: {defn.module.db_table}")
        print(f"  字段数: {len(defn.fields)}")
        print(f"  按钮数: {len(defn.buttons)}")
        print(f"  字典数: {len(defn.dictionaries)}")
        for f in defn.fields:
            form_info = ""
            if f.form:
                parts = []
                if f.form.show_in_grid:
                    parts.append("列表")
                if f.form.editable:
                    parts.append("编辑")
                if f.form.searchable:
                    parts.append("搜索")
                form_info = f" [{'+'.join(parts)}]"
            dict_info = f" \U0001f4d6dict={f.dict}" if f.dict else ""
            print(f"    - {f.field_name} ({f.display_type}): {f.comment}{form_info}{dict_info}")
        return

    # Apply rules
    defn = apply_rules(defn)
    warn_unreferenced_dictionaries(defn)

    # Pre-generate IDs to eliminate MySQL session variable dependency
    defn.reserved_ids = generate_all_ids(defn)

    # Determine output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_output = args.output or os.path.join(script_dir, "output")

    # Conflict check
    if not args.dry_run:
        check_module_conflict(base_output, defn.module.code)

    # Version
    version = args.version or defn.version or auto_increment_version(base_output, defn.module.code)
    defn.version = version

    # Version overwrite check
    if not args.dry_run:
        if not check_version_overwrite(base_output, defn.module.code, version, args.force):
            sys.exit(1)

    # Generate
    create_sql = generate_create_sql(defn) if not args.cleanup_only else None
    cleanup_sql = generate_cleanup_sql(defn) if not args.create_only else None

    if args.dry_run:
        print("\n" + "=" * 60)
        print("\U0001f4c4 创建 SQL (预览):")
        print("=" * 60)
        if create_sql:
            print(create_sql)
        print()
        print("=" * 60)
        print("\U0001f9f9 清理 SQL (预览):")
        print("=" * 60)
        if cleanup_sql:
            print(cleanup_sql)
        return

    # Write output
    out_dir = get_output_dir(base_output, defn.module.code, version)

    tables_affected = [
        "md_module", "md_field", "md_form", "md_button",
        "sys_resource", "sys_role_resource",
    ]
    if defn.dictionaries:
        tables_affected.extend(["comm_dictionary", "comm_dictionary_item"])
    if defn.relations:
        tables_affected.append("md_module_link")

    if create_sql:
        create_path = out_dir / f"{defn.module.code}_create.sql"
        with open(create_path, "w", encoding="utf-8") as f:
            f.write(create_sql)
        print(f"\u2705 创建脚本已写入: {create_path}")

    if cleanup_sql:
        cleanup_path = out_dir / f"{defn.module.code}_cleanup.sql"
        with open(cleanup_path, "w", encoding="utf-8") as f:
            f.write(cleanup_sql)
        print(f"\u2705 清理脚本已写入: {cleanup_path}")

    # ⚠️ 关联 SQL 独立输出：必须在所有模块的 create.sql 执行完成后再单独执行
    if defn.relations:
        relation_sql = generate_relation_sqls(defn)
        if relation_sql:
            relation_path = out_dir / f"{defn.module.code}_relation.sql"
            with open(relation_path, "w", encoding="utf-8") as f:
                f.write(relation_sql)
            print(f"\u2705 关联脚本已写入: {relation_path}")
            print(f"  ⚠️  请在所有模块创建完成后，再执行此文件")

    write_manifest(out_dir, defn, tables_affected)
    print(f"\u2705 版本清单已写入: {out_dir / 'manifest.json'}")

    update_versions_index(base_output, defn.module.code, version)

    print(f"\n\U0001f4ca 输出统计:")
    print(f"  模块: {defn.module.name_cn} ({defn.module.code})")
    print(f"  版本: v{version}")
    print(f"  输出目录: {out_dir}")
    print(f"  字段数: {len(defn.fields)}")
    print(f"  按钮数: {len(defn.buttons)}")
    print(f"  字典数: {len(defn.dictionaries)}")
    print(f"  关联数: {len(defn.relations)}" if defn.relations else "", end="")
    print(f"  影响表: {', '.join(tables_affected)}")


if __name__ == "__main__":
    main()
