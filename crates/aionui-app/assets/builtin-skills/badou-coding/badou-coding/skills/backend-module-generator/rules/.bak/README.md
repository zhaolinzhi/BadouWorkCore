# rules/.bak/

**保留目的**：2026-07-21 backend-module-generator 规则重构前的旧文件备份。

**保留时长**：7 天（2026-07-21 ~ 2026-07-28）。

**包含文件**：
- `BASIC-CRUD.md`（445 行，已拆分为 `basic-crud.md` 等 8 个新文件）
- `MODULE-LINK.md`（428 行，已重命名为 `module-link.md` + 编号修复）
- `FLOW-CONTRACT.md`（49 行，已重命名为 `flow-contract.md` + 扩展为 ~200 行）

**macOS APFS 注意**：因 APFS 默认 case-insensitive 文件系统，git 删除的 SCREAMING_SNAKE 文件可能在磁盘上仍以 case-only alias 形式存在（指向 kebab-case 文件的 inode）。这是文件系统特性，不影响 git 跟踪状态。

**清理方式**：2026-07-28 后由维护者手动删除：

```bash
rm -rf .claude/skills/badou-coding/skills/backend-module-generator/rules/.bak/
```

**回滚**：如需回滚，参考 specs/2026-07-21-backend-module-generator-rules-refactor-design.md §6。

> **测试范围说明**：AC5（无占位符残留）和 AC10（原则 3 内容待补充）的扫描范围仅为
> 活跃的 `rules/*.md`（kebab-case 文件），不覆盖 `.bak/` 备份文件。备份中的占位符
> 属于历史 artifacts，不影响验证通过状态。