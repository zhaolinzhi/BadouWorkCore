# 模块基础配置（md_module 必填字段）

> **何时读**：写 module.json 的 `module` 段时。
> **配置项权威**：`.claude/skills/badou-coding/common/md_module.md`（md_module 配置项矩阵）
> **物理 schema 权威**：`.claude/docs/backend/database/ddl/module/md_module.md`

---

## §1 module 段必填字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `code` | ✅ | 模块编码（同时是前端路由部分）|
| `db_table` | ✅ | 业务表名（与 code 同语义）|
| `name_cn` | ✅ | 模块中文名 |

## §2 强烈建议填写（generator 自动注入默认值）

| 字段 | 默认 | 说明 |
|------|------|------|
| `english_name` | — | 英文名 |
| `base_class` | `BusinessEntity` | 父类（Java FQN）|
| `description` | — | 描述 |
| `list_js` / `form_js` / `view_js` | — | JS 文件路径 |
| `menu_resource_code` | — | 菜单资源编码 |

## §3 配置项 → 详见 common spec

> 完整 md_module 46 列配置项矩阵（含 generator 写入策略 + 变更敏感度）见 `.claude/skills/badou-coding/common/md_module.md` §2。

## §4 JSON 写法示例

```json
{
  "module": {
    "code": "purchase_request",
    "db_table": "t_purchase_request",
    "name_cn": "采购申请",
    "english_name": "PurchaseRequest",
    "base_class": "com.badou.project.moduledemo.help.PurchaseRequestEntity",
    "description": "采购申请单管理",
    "menu_resource_code": "PURCHASE_REQUEST"
  }
}
```

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口与总检查清单
- [rules/field-config.md](field-config.md) — 字段配置
- [rules/data-safety.md](data-safety.md) — 字段安全约束

**common spec**：
- [common/md_module.md](../../../common/md_module.md) — md_module 配置项矩阵

**DDL 文档**：
- [md_module.md](../../../../../docs/backend/database/ddl/module/md_module.md) — 物理 schema（46 列权威）

**示例**：
- [examples/module.json](../../examples/module.json) — 完整 module 段示例