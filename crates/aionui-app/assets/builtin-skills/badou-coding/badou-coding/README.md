# badou-coding Plugin

企业版 Claude Code plugin。`/badou-coding:*` 命名空间暴露 28 个 skill（14 个 upstream + 14 个自定义）。

`name: badou-coding`（见 `.claude-plugin/plugin.json`）。

## 命名空间结构

### 14 个 upstream superpowers skill（自动同步）

| Skill | 作用 |
|---|---|
| `brainstorming` | 把想法变成设计 |
| `writing-plans` | 写实施计划 |
| `test-driven-development` | TDD 工作流 |
| `verification-before-completion` | 完成前验证 |
| `subagent-driven-development` | 子代理驱动开发 |
| `dispatching-parallel-agents` | 并行调度 |
| `executing-plans` | 执行计划 |
| `finishing-a-development-branch` | 完成分支 |
| `requesting-code-review` | 请求代码审查 |
| `receiving-code-review` | 接收代码审查 |
| `systematic-debugging` | 系统调试 |
| `using-git-worktrees` | 用 worktree |
| `writing-skills` | 写技能 |
| `using-badou` | badou-coding 家族入口 |

### 14 个自定义 skill（手动维护，sync 不触碰）

| Skill | 来源 | 命名规则 |
|---|---|---|
| `backend-module-generator` | 本仓 | `backend-module-<name>`（特殊：去 `crud`） |
| `backend-flow-engine` | 本仓 | `backend-<name>`（特殊：无 `module`） |
| `frontend-module-quickstart` | frontend feature-skill-wll | `frontend-module-<name>` |
| `frontend-module-list` | frontend | `frontend-module-<name>`（去 `customsetting`） |
| `frontend-module-edit` | frontend | `frontend-module-<name>`（去 `customsetting`） |
| `frontend-module-child-edit` | frontend feature-skill-wll 独有 | `frontend-module-<name>`（去 `customsetting`） |
| `frontend-module-tree-edit` | frontend | `frontend-module-<name>`（去 `customsetting`） |
| `frontend-module-tree-list` | frontend | `frontend-module-<name>`（去 `customsetting`） |
| `frontend-module-tree-table` | frontend | `frontend-module-<name>`（去 `customsetting`） |
| `frontend-module-extend-field` | frontend | `frontend-module-<name>` |
| `frontend-module-global-styles` | frontend | `frontend-module-<name>` |
| `frontend-module-list-search-set-value` | frontend | `frontend-module-<name>` |
| `frontend-module-page-debug` | frontend | `frontend-module-<name>` |
| `frontend-module-this-reference` | frontend | `frontend-module-<name>` |

## Plugin layout

```
.claude/skills/badou-coding/
├── .claude-plugin/plugin.json          # Plugin manifest (name=badou-coding)
├── README.md                           # This file
├── badou-coding-sync.py                # Sync script (UPSTREAM_SKILLS only)
└── skills/                             # 28 sub-skills
    ├── (14 upstream superpowers)
    ├── (14 custom)
    └── ...
```

## sync 命令

```bash
# 同步 14 个 upstream skill（自定义 14 个完全不动）
python3 .claude/skills/badou-coding/badou-coding-sync.py

# 选项
python3 .claude/skills/badou-coding/badou-coding-sync.py --dry-run       # 仅 log 不改文件
python3 .claude/skills/badou-coding/badou-coding-sync.py --list-skills   # 列出 28 个 skill
python3 .claude/skills/badou-coding/badou-coding-sync.py --check-addendum # 验证 addendum 是否同步

# 测试
cd .claude && python3 -m pytest tests/test_badou_coding_sync.py -v
```

### Addendum 自动保留与注入

sync 会自动保留企业规则 addendum 并注入到 SKILL.md：

| 步骤 | 行为 |
|---|---|
| 1. Extract | sync 前扫描 `dst/<skill>/.badou-local.md` 和 `.badou-local.en.md`，抽取 `<!-- BADOU-LOCAL-USER-CONTENT -->` 之下的用户内容 |
| 2. rmtree + copytree | 从 upstream cache 重新生成 `dst/<skill>/`（纯 upstream 内容，无 addendum） |
| 3. Restore | 把 step 1 抽取的 `.badou-local.*` 内容写回 `dst/<skill>/`（upstream 不带这些文件） |
| 4. Inject | 把 addendum 作为 `## Badou Enterprise Addendum` 段 append 到 SKILL.md 末尾（幂等：已存在不重复） |

**保留对象**：14 个 upstream skill 各自对应的 `.badou-local.md` / `.badou-local.en.md` 文件全部自动保留（sync 不会丢失企业规则源）。

**custom skill 不参与 addendum 流程**：14 个 `frontend-module-*` / `backend-*` skill 由 sync 完全不动。

### `--check-addendum`（CI 用法）

退出码反映 addendum 同步状态：

| 退出码 | 含义 | 修复 |
|---|---|---|
| 0 | 所有 14 个 upstream skill 的 `.badou-local.*` 源 + SKILL.md `## Badou Enterprise Addendum` 段都完整 | 无需操作 |
| 1 | 至少一个 skill 的 SKILL.md 缺少 addendum 段（drift：源还在但 SKILL.md 没注入） | 跑 `python3 badou-coding-sync.py`（无 flag）修复 |

`--check-addendum` 隐含 `--dry-run`，不会修改文件，适合 CI pipeline：

```bash
# In CI: fail the build if sync is needed
python3 .claude/skills/badou-coding/badou-coding-sync.py --check-addendum \
  || echo "::error::addendum drift detected; run sync to fix"
```

**Drift 检测的精确语义**：drift = 「有 `.badou-local.*` 源（有非空用户内容）」 AND 「SKILL.md 缺少 `## Badou Enterprise Addendum` 段」。restore `.badou-local.*` 文件本身不算 drift（设计行为）。

## 如何添加自定义 skill

1. 在 `.claude/skills/badou-coding/skills/<新名>/` 创建 `SKILL.md`
2. frontmatter 必须含 `name: <新名>` + `description: ...`
3. **不会被 sync 覆盖**（sync 只处理 14 个 upstream skill）
4. 在本 README 的"自定义 skill"表中加一行
5. reload plugin: `/reload-plugins`

## Design invariants

1. **不修改 upstream 缓存**（`~/.claude/plugins/cache/claude-plugins-official/superpowers/...`）只读
2. **sync 只动 UPSTREAM_SKILLS 名单内的目录**（14 个 upstream skill）
3. **safety_check() 启动时扫描 skills/**：对不在 UPSTREAM_SKILLS 的任何目录**只打印 "preserving"**，绝不 rm
4. **SKILL.md frontmatter 必须含 name + description**（描述会被 Claude Code 用作触发判定）
5. **命名空间归一化**：所有 `superpowers:foo` 引用自动变 `badou-coding@skills-dir:foo`
