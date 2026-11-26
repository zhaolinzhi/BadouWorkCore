"""Tests for backend-module-updater rules and incremental diff engine.

Aligned with spec §3.2 + D21-D26 follow-ups:
* structure / help / validate / baseline smoke
* D21: --update emits ALTER + UPSERT SQL
* D22: destructive ALTER rejected
* D24: backup SQL created before DROP COLUMN
* D25: idempotent re-run produces "0 改动"
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

UPDATER_DIR = Path(__file__).resolve().parent.parent

EXPECTED_UPDATE_RULES = [
    "module-basic-config.md",
    "module-flow-code.md",
    "field-add.md",
    "field-remove.md",
    "field-modify.md",
    "dictionary-change.md",
    "button-change.md",
    "form-config-change.md",
    "relation-change.md",
    "resource-permission.md",
    "data-migration-safety.md",
    "idempotency.md",
    "sql-execution.md",
]


def _run(args: list[str], cwd: Path = UPDATER_DIR) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(UPDATER_DIR / "crud_updater.py"), *args],
        capture_output=True, text=True, cwd=str(cwd),
    )


def test_skill_md_exists_and_describes_no_data_loss():
    body = (UPDATER_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "保留业务数据" in body


def test_all_13_update_rules_exist():
    rules_dir = UPDATER_DIR / "update_rules"
    missing = [n for n in EXPECTED_UPDATE_RULES if not (rules_dir / n).exists()]
    assert not missing, f"missing: {missing}"


def test_crud_updater_py_supports_update_flag():
    result = _run(["--help"])
    assert "--update" in result.stdout
    assert "--module-code" in result.stdout


def test_section_numbering_continuous():
    rules_dir = UPDATER_DIR / "update_rules"
    for name in EXPECTED_UPDATE_RULES:
        text = (rules_dir / name).read_text(encoding="utf-8")
        headings = re.findall(r"^## §(\d+)", text, flags=re.MULTILINE)
        nums = [int(h) for h in headings]
        assert nums == list(range(1, max(nums) + 1) if nums else []), (
            f"{name}: 章节不连续 {nums}"
        )


def test_3_examples_pass_validate():
    for ex_name in ("update_purchase_request_add_field.json",
                    "update_product_add_relation.json",
                    "update_server_rack_add_flow.json"):
        result = _run(["--update", "--module-code", "test", "--def", f"examples/{ex_name}", "--validate"])
        assert result.returncode == 0, f"{ex_name}: {result.stderr}"


def test_baseline_matches_examples():
    baseline_lines = [
        ln.strip() for ln in (UPDATER_DIR / "baselines" / "backend-module-updater-baseline.txt").read_text().splitlines() if ln.strip()
    ]
    actual = []
    for ex_name in ("update_purchase_request_add_field.json",
                    "update_product_add_relation.json",
                    "update_server_rack_add_flow.json"):
        result = _run(["--update", "--module-code", "test", "--def", f"examples/{ex_name}", "--validate", "--line-count"])
        actual.append(f"{'PASSED' if result.returncode == 0 else 'FAILED'}: examples/{ex_name} | lines={len(result.stdout.splitlines())}")
    assert actual == baseline_lines, f"baseline 不一致\n--- actual ---\n{actual}"


def test_crud_updater_generates_alter_sql(tmp_path: Path):
    ex_path = UPDATER_DIR / "examples" / "update_purchase_request_add_field.json"
    snapshot = tmp_path / "old.json"
    snapshot.write_text(json.dumps({"module": {"code": "purchase_request", "db_table": "t_purchase_request"}, "fields": []}))
    result = _run(["--update", "--module-code", "purchase_request", "--def", str(ex_path), "--output", str(tmp_path), "--snapshot", str(snapshot)])
    assert result.returncode == 0, result.stderr
    sql = (tmp_path / "purchase_request" / "update.sql").read_text()
    assert "ADD COLUMN" in sql or "MODIFY COLUMN" in sql
    assert "md_module" in sql  # UPSERT coverage


def test_destructive_alter_rejected(tmp_path: Path):
    new_path = tmp_path / "new.json"
    new_path.write_text(json.dumps({
        "module": {"code": "demo", "db_table": "t_demo"},
        "fields": [{"field_name": "name", "display_type": "varchar", "length": 16, "nullable": True, "_action": "modify"}],
    }))
    snapshot = tmp_path / "old.json"
    snapshot.write_text(json.dumps({"module": {"code": "demo", "db_table": "t_demo"}, "fields": [{"field_name": "name", "display_type": "varchar", "length": 64, "nullable": True}]}))
    result = _run(["--update", "--module-code", "demo", "--def", str(new_path), "--output", str(tmp_path), "--snapshot", str(snapshot)])
    assert result.returncode != 0
    assert "length" in result.stderr or "拒绝" in result.stderr


def test_backup_created_before_drop(tmp_path: Path):
    new_path = tmp_path / "new.json"
    new_path.write_text(json.dumps({
        "module": {"code": "demo", "db_table": "t_demo"},
        "fields": [],
    }))
    snapshot = tmp_path / "old.json"
    snapshot.write_text(json.dumps({"module": {"code": "demo", "db_table": "t_demo"}, "fields": [{"field_name": "obsolete", "display_type": "varchar", "length": 32, "nullable": True}]}))
    result = _run(["--update", "--module-code", "demo", "--def", str(new_path), "--output", str(tmp_path), "--snapshot", str(snapshot), "--confirm-delete"])
    assert result.returncode == 0, result.stderr
    cleanup = (tmp_path / "demo" / "update_cleanup.sql").read_text()
    assert "__bak_" in cleanup and "CREATE TABLE" in cleanup


def test_idempotency_skip(tmp_path: Path):
    ex_path = UPDATER_DIR / "examples" / "update_purchase_request_add_field.json"
    snapshot = tmp_path / "old.json"
    snapshot.write_text(json.dumps({"module": {"code": "purchase_request", "db_table": "t_purchase_request"}, "fields": []}))
    first = _run(["--update", "--module-code", "purchase_request", "--def", str(ex_path), "--output", str(tmp_path), "--snapshot", str(snapshot)])
    assert first.returncode == 0
    second = _run(["--update", "--module-code", "purchase_request", "--def", str(ex_path), "--output", str(tmp_path), "--snapshot", str(snapshot)])
    assert "0 改动" in second.stdout
