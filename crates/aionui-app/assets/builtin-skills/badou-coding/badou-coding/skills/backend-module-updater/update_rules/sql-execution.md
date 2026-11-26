# sql-execution.md

> **何时读**：SQL 执行前
> **配置项权威**：无（执行顺序约束）
> **物理 schema**：无

---

## §1 执行顺序

**严格顺序**（违反会导致外键约束失败）：
1. **业务表 DDL**（`ALTER TABLE`）：ADD / MODIFY / DROP COLUMN
2. **MD 元数据 UPSERT**：`md_module` UPDATE → `md_field` UPSERT → `md_form` DELETE+INSERT
3. **MD 元数据 DELETE+INSERT**：`md_button` → `md_module_link`
4. **数据字典 UPSERT**：`comm_dictionary` → `comm_dictionary_item`
5. **资源权限 UPSERT**：`sys_resource` → `sys_role_resource`
6. **流程绑定 UPDATE**：`md_flow` → `md_module.flow_id`

## §2 db_executor.py 使用

**db_executor.py 路径**：`.claude/skills/badou-md-common/badou_md_common/db_executor.py`

**使用方式**（D27 起走 3 层 fallback）：
```python
from db_config_resolver import resolve_db_config, ConfigNotFoundError

try:
    resolved = resolve_db_config(
        project_root=".",
        explicit_config=".trellis/PROJECT-BRAIN.md",  # 或 None
        interactive=False,  # CI/headless 推荐 False
    )
except ConfigNotFoundError as exc:
    raise SystemExit(str(exc))

db_config = resolved["database"]  # 含 host/port/user/password/name
```

**Fallback 链**：
1. `explicit_config`（CLI `--config-from-brain` 或 `--config`）
2. `<project>/.trellis/PROJECT-BRAIN.md`
3. `<project>/backend/pom.xml` + `application*.yml` / `.properties`（Spring Boot）
4. 交互式 `input()`（仅在 `interactive=True` 且 stdin tty 时）

**CLI 等价**：
```bash
python3 db_executor.py update.sql \
  --config-from-brain .trellis/PROJECT-BRAIN.md \
  --project-root . \
  --no-interactive
```

## §3 @variable 单连接约束

**约束**：所有 `@variable` 定义在同一个数据库连接中执行。
- 使用 `-- connection 1` 注释标记所有相关语句
- 不允许跨连接拆分 `@variable` 定义
- 所有 SQL 在单个 `execute_sql` 调用中一次性提交

## 📎 引用清单

**相关规则文档**：
- [rules/module-basic-config.md](module-basic-config.md)
- [rules/field-add.md](field-add.md)
- [rules/field-remove.md](field-remove.md)
- [rules/form-config-change.md](form-config-change.md)
- [rules/relation-change.md](relation-change.md)

**common spec**：
- 无

**示例**：
- 无