# 按钮配置（md_button + sys_resource）

> **何时读**：配置模块按钮或菜单资源时。
> **配置项权威**：`.claude/skills/badou-coding/common/md_button.md`（md_button 配置项矩阵）
> **物理 schema 权威**：`.claude/docs/backend/database/ddl/module/md_button.md`

<!-- Source: generated for backend-module-generator stability design, do not edit by hand without syncing the plan. -->

---

## §1 6 个标准按钮

| code | 名称 | 行为 |
|------|------|------|
| `add` | 新增 | 打开编辑页（add 模式） |
| `edit` | 修改 | 打开编辑页（edit 模式） |
| `view` | 查看 | 打开查看页 |
| `delete` | 删除 | 软删除（UPDATE flg_deleted=1） |
| `import` | 导入 | Excel 上传 |
| `export` | 导出 | Excel 下载 |

> ✅ 默认 6 个按钮全部生成；在 `buttons` 数组中列出则启用。

---

## §2 按钮 type（3 种）

| type | 位置 | 示例 |
|------|------|------|
| `toolbar` | 列表页顶部工具栏 | add / import / export |
| `row` | 列表页每行操作列 | edit / view / delete |
| `form` | 编辑页底部 | save / cancel |

---

## §3 自定义按钮

```json
{
  "buttons": [
    {"code": "approve", "name_cn": "审批", "type": "row", "priority": 10}
  ]
}
```

完整 md_button 配置项及 generator 写入策略见 common spec。

---

## §4 配置项 → 详见 common spec

> 完整 md_button 配置项矩阵（含 generator 写入策略 + 变更敏感度）见 `.claude/skills/badou-coding/common/md_button.md` §2。

---

## §5 priority 约定

- 数值越小越靠前
- 工具栏默认顺序：add(10) / import(20) / export(30) / 自定义(40+)
- 行操作默认顺序：view(10) / edit(20) / delete(30) / 自定义(40+)

---

## §6 与 sys_resource 的关系

每个按钮自动生成对应 `sys_resource` 行（用于角色权限）：
- `code`: `<MODULE_CODE>_<BUTTON_CODE>`（如 `LEAVE_REQUEST_ADD`）
- `type`: 1=菜单 / 2=按钮

> 📖 资源权限详见 `../../../../../docs/backend/database/ddl/resource/sys_resource.md`。

---

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口
- [rules/module-config.md](module-config.md) — menu_resource_code 关联

**common spec**：
- [common/md_button.md](../../../common/md_button.md) — md_button 配置项矩阵

**DDL 文档**：
- [md_button.md](../../../../../docs/backend/database/ddl/module/md_button.md) — 按钮表结构（25 列权威）
- `.claude/docs/backend/database/ddl/resource/sys_resource.md` — 资源表

**示例**：
- [examples/module.json](../../examples/module.json) — 6 标准按钮 + buttons 数组