# dictionary-change.md

> **何时读**：`dictionaries` 数组变化
> **配置项权威**：`.claude/skills/badou-coding/common/md_field.md`（dict 字段）
> **物理 schema**：`.claude/docs/backend/database/ddl/comm/comm_dictionary.md`

---

## §1 comm_dictionary UPSERT 模板

```sql
INSERT INTO comm_dictionary (dict_code, dict_name, ...)
VALUES (?, ?, ...)
ON DUPLICATE KEY UPDATE dict_name = ?, ...;

INSERT INTO comm_dictionary_item (dict_code, item_code, item_name, sort_order, ...)
VALUES (?, ?, ?, ?, ...)
ON DUPLICATE KEY UPDATE item_name = ?, sort_order = ?, ...;
```

## §2 字典三条件联动检测

字典变更需检测以下三个条件：
1. **字典字段是否存在**：检查 `md_field` 中是否有 `dict_code` 绑定到该字典
2. **字典字段是否删除**：如果字典字段被删除，同步清理 `comm_dictionary` 中对应条目
3. **字典字段是否替换**：如果字典字段的 `dict_code` 变更，清理旧字典 + 插入新字典

## §3 item 顺序变化处理

- 读取当前 `comm_dictionary_item` 全量
- 对比新 JSON 中的 item 顺序
- 按新顺序 `UPDATE comm_dictionary_item SET sort_order = ?`
- 新增 item：`INSERT`
- 删除 item：`DELETE`
- 排序变化：`UPDATE sort_order`

## 📎 引用清单

**相关规则文档**：
- [rules/field-modify.md](field-modify.md)（dict 绑定变更）
- [rules/form-config-change.md](form-config-change.md)

**common spec**：
- [common/md_field.md](../../../common/md_field.md)

**DDL 文档**：
- [comm_dictionary.md](../../../../../docs/backend/database/ddl/comm/comm_dictionary.md)

**示例**：
- [examples/update_purchase_request_add_field.json](../../examples/update_purchase_request_add_field.json)