# idempotency.md

> **何时读**：任意重跑（updater 重跑同一 module.json）
> **配置项权威**：无（独立校验逻辑）
> **物理 schema**：无

---

## §1 JSON 哈希计算

**哈希算法**：SHA-256。

**哈希输入**：规范化 JSON（`json.dumps(module_def, sort_keys=True, ensure_ascii=False)`）。

**哈希存储**：
- 写入 `output/<module.code>/.updater.hash`
- 文件内容：`sha256:<64 hex chars>`

## §2 同 module.code + 哈希相同 → 跳过

**检测逻辑**：
1. 检查 `output/<module.code>/` 是否存在
2. 读取 `.updater.hash` 文件
3. 计算当前 module.json 的 SHA-256 哈希
4. 比对：相同 → 跳过；不同 → 执行更新

## §3 输出 0 改动

**跳过输出**：
```
updater: module.code=purchase_request, hash unchanged, 0 changes
```

**正常输出**：
```
updater: module.code=purchase_request, hash changed, generating update SQL...
```

## 📎 引用清单

**相关规则文档**：
- [rules/sql-execution.md](sql-execution.md)
- [rules/data-migration-safety.md](data-migration-safety.md)

**common spec**：
- 无

**示例**：
- 无