# 基础 CRUD 规则（入口）

> **适用条件**：单表 CRUD（无关联、无流程审批）。本文件是所有生成任务的入口与总检查清单。
> **追加规则**：含 relations → 追加读 `rules/module-link.md`；module.flow_code 非空 → 追加读 `rules/flow-contract.md`。
> **前置 schema 参考**：所有 md_* 表结构详见 `.claude/docs/backend/database/ddl/module/md_<table>.md`
> **common spec 索引**：[common/README.md](../../../common/README.md) — 所有 md_* 配置项的单一权威源

<!-- Source: generated for backend-module-generator stability design, do not edit by hand without syncing the plan. -->

---

## §1 入口与路由

| 场景 | 读哪些规则文件 |
|------|--------------|
| 单表 CRUD（最常见） | 仅本文件 + 按需展开 `module-config` / `field-config` / `dictionary` / `list-page` / `search-condition` / `edit-page` / `view-page` / `button-config` / `data-safety` / `sql-execution` |
| 含 relations 数组 | 本文件 + 上述子文件 + `rules/module-link.md` |
| module.flow_code 非空 | 本文件 + 上述子文件 + `rules/flow-contract.md` |

---

## §2 字典三条件（缺一不可）

> 🚨 **任何含字典语义的字段必须同时满足以下三条**，否则 generator 不会绑定字典。

| 条件 | 字段属性 | 含义 |
|------|---------|------|
| ① | `dict` 属性 | 字段上指定字典名（如 `dict: "leave_type"`） |
| ② | `dictionaries` 数组 | 模块顶层声明该字典的定义 |
| ③ | `form.edit_type: "select"` | 表单使用 select 控件 |

❌ 错误：只设 `dict` 不设 `dictionaries` → 前端找不到字典数据源。
❌ 错误：只设 `dict` 和 `dictionaries`，但 `edit_type` 不是 select → 前端展示成普通输入框。
✅ 正确：三条同时满足，generator 自动写入 `dict_id` 子查询。

---

## §3 JSON 生成总检查清单

写完 `module.json` 后，逐条核对：

- [ ] **module.code** 满足 `[a-z][a-z0-9_]*` 命名（如 `leave_request`）
- [ ] **module.db_table** 与 code 同语义（如 `t_leave_request`）
- [ ] **module.data_source_code = "projectDatabase"`（数据源硬编码）
- [ ] **每个 field** 含 `field_name` / `display_type` / `comment` / `nullable`
- [ ] **含 dict 字段** → 三条件全齐（见 §2）
- [ ] **8 个系统字段**（id/create_time/creator/creator_name/updator/updator_name/update_time/flg_deleted）由 generator 自动注入，不要写在 fields 数组里
- [ ] **主键与外键 length=64**（与 md_module.id 一致）
- [ ] **业务 hidden/readonly 字段 nullable=true**（框架不填充，详见 `rules/data-safety.md` §1）
- [ ] **approval_status / audit_status / 审批 status** 不写在 fields 里（流程模块由 BO_STATUS 自动注入，详见 `rules/flow-contract.md`）

---

## §4 标准 JSON 模板（最小可运行示例）

```json
{
  "module": {
    "code": "leave_request",
    "name_cn": "请假管理",
    "db_table": "t_leave_request",
    "package_name": "com.badou.entity",
    "data_source_code": "projectDatabase"
  },
  "fields": [
    {"field_name": "applicant_name", "display_type": "varchar", "comment": "申请人姓名", "nullable": true, "length": 50, "form": {"searchable": true, "editable": false}},
    {"field_name": "leave_type", "display_type": "varchar", "comment": "请假类型", "nullable": false, "length": 20, "dict": "leave_type", "form": {"edit_type": "select"}},
    {"field_name": "duration", "display_type": "decimal", "comment": "请假天数", "nullable": true, "length": 10, "decimal_digits": 1}
  ],
  "dictionaries": [
    {"code": "leave_type", "name_cn": "请假类型", "items": [
      {"code": "1", "name_cn": "事假"},
      {"code": "2", "name_cn": "病假"}
    ]}
  ],
  "buttons": ["add", "edit", "view", "import", "export", "delete"]
}
```

---

## §5 字段定义详细规则

详细规则按字段属性拆分到独立文件：

| 字段属性主题 | 读哪个文件 |
|-------------|----------|
| 字段类型 / 长度 / 系统字段注入 | `rules/field-config.md` |
| 字典字段三条件 | `rules/dictionary.md` |
| 列表列配置 | `rules/list-page.md` |
| 搜索框配置 | `rules/search-condition.md` |
| 编辑页配置 | `rules/edit-page.md` |
| 查看页配置 | `rules/view-page.md` |
| 按钮配置 | `rules/button-config.md` |
| hidden/readonly 安全约束 | `rules/data-safety.md` |

---

## 📎 引用清单

**相关规则文档**：
- [rules/module-config.md](module-config.md) — md_module 必填与 code 命名
- [rules/field-config.md](field-config.md) — display_type 白名单与字段长度
- [rules/dictionary.md](dictionary.md) — 字典三条件与 BO_STATUS
- [rules/sql-execution.md](sql-execution.md) — 执行顺序与 db_executor.py

**DDL 文档**：
- [md_module.md](../../../../../docs/backend/database/ddl/module/md_module.md) — 模块表结构
- [md_field.md](../../../../../docs/backend/database/ddl/module/md_field.md) — 字段表结构
- [md_form.md](../../../../../docs/backend/database/ddl/module/md_form.md) — 表单配置表结构

**示例**：
- [examples/module.json](../../examples/module.json) — 请假管理（带流程）
- [examples/vehicle_def.json](../../examples/vehicle_def.json) — 纯 CRUD
