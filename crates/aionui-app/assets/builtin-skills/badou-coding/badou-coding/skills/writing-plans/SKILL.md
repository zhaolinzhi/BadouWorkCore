---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** If working in an isolated worktree, it should have been created via the `superpowers:using-git-worktrees` skill at execution time.

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Task Right-Sizing

A task is the smallest unit that carries its own test cycle and is worth a
fresh reviewer's gate. When drawing task boundaries: fold setup,
configuration, scaffolding, and documentation steps into the task whose
deliverable needs them; split only where a reviewer could meaningfully
reject one task while approving its neighbor. Each task ends with an
independently testable deliverable.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

## Global Constraints

[The spec's project-wide requirements — version floors, dependency limits,
naming and copy rules, platform requirements — one line each, with exact
values copied verbatim from the spec. Every task's requirements implicitly
include this section.]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Interfaces:**
- Consumes: [what this task uses from earlier tasks — exact signatures]
- Produces: [what later tasks rely on — exact function names, parameter
  and return types. A task's implementer sees only their own task; this
  block is how they learn the names and types neighboring tasks use.]

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Remember
- Exact file paths always
- Complete code in every step — if a step changes code, show the code
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/superpowers/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:executing-plans
- Batch execution with checkpoints for review

## Badou Enterprise Addendum

## 计划结构（5 步）

任何新模块（含 CRUD）的实施计划必须按这 5 步走：

| 步骤 | 内容 | 产出 |
|---|---|---|
| 1. 确认需求 | 字段清单 + 场景（单表/多表/流程） | 评审过的 module.json |
| 2. 跑生成器 | `crud_generator.py --def <json>` | `output/<module>/v<ver>/*.sql` |
| 3. 执行 SQL | `db_executor.py <create.sql>` | DB 中已有模块 |
| 4. 验证 | `idempotent_check.py <json>` 退出码 0 + "ALL PASSED" | 验证通过 |
| 5. 定制 | 写 service / controller / validator | 业务功能可用 |

**步骤 1-4 不能合并**。**步骤 5 才是 TDD 阶段**。

## 生成步骤细节

步骤 2 写进计划时必须包含：

- **命令**：`crud_generator.py --def <绝对路径> --output <绝对路径>`
- **输入 JSON 路径**：`<project>/crud-generator/module_defs/<module>.json`
- **输出验证**：计划里要写"检查 output 目录下生成了 create.sql + cleanup.sql + manifest.json 三个文件"
- **失败回退**：若生成器退出码非 0，不要继续步骤 3，先查 JSON 校验错误

## 流程引擎变体

若 `module.flow_code` 非空：

1. **先**写 `flow.json`（流程定义：busi + nodes + routes）
2. `crud_generator.py --flow-only flow.json --flow-execute` 创建流程 5 表
3. **再**写 `module.json`（在 `module.flow_code` 里引用上面流程）
4. `crud_generator.py --def module.json` 创建业务模块
5. `db_executor.py` + `idempotent_check.py`

**顺序倒过来 = flow_id 关联失效**（create.sql 里的 `UPDATE md_module SET flow_id` 子查询查不到 flw_flow）。

## 多项目变体

步骤 1 加一条：

- 确认 `<project>/.trellis/PROJECT-BRAIN.md` 存在
- 确认 DB 连接信息已填（host / port / db / user / password）
- 不要假设 DB——读 PROJECT-BRAIN.md

## 定制阶段

步骤 5 要写明定制范围（不要让 plan 写"做完即可"）：

- 自定义 service 方法（业务逻辑、跨表操作）
- 自定义 controller（特殊 URL、特殊参数）
- 自定义 validator（跨字段校验、远程校验）
- 自定义前端（如果 md_field + md_form 不够用）

每条定制都要有"对应测试用例"链接到 TDD 阶段。

## 幂等性

计划里必须明确：**任何生成步骤都可以重跑**。若步骤 4 失败，修复 JSON 后重跑步骤 2-4，不要手动改 SQL。

CI 集成（如项目配了）：

```bash
mvn checkstyle:check \
  && python3 .claude/skills/backend-module-generator/validators/idempotent_check.py module.json \
  && mvn test
```

## 不要做

- **不**把"修改生成 SQL"写进计划——改了等于绕过生成器，下次重跑覆盖
- **不**跳步骤 4 验证——`idempotent_check.py` 检查 8 类问题，跳过必踩坑
- **不**对同 DB 的多个模块 plan 并行生成——MySQL 用户变量冲突
- **不**为"图快"用裸 `mysql < create.sql`——必须用 `db_executor.py`（保留会话变量）

## 与 superpowers 的差异

superpowers 计划到"开始实现"为止；我们的计划**显式包含生成阶段**（步骤 2-4），先生成模型数据再手写定制代码。

---

## Output location override

本项目 plan 输出**不要**用上游默认路径 `docs/superpowers/plans/`，**统一写到 workspace 根目录 `docs/badoucoding/plans/`**（plain folder，不入 git；跨团队参考用）。

- 跨栈 plan → workspace 根 `docs/badoucoding/plans/`
- 单一栈 plan → workspace 根 `docs/badoucoding/plans/`（也写到根，不再分仓）

`.claude/docs/` 仅存前后端业务/通用说明文档，**不**放 plan。

## Task scope 标注

每个 plan 任务标注 `scope`，让 subagent-driven-development 知道 `cd` 到哪个目录：

| scope | 含义 | 任务运行时 cwd |
|---|---|---|
| `backend` | 仅后端 | `backend/` |
| `frontend` | 仅前端 | `frontend/` |
| `cross-stack` | 跨栈 | 当前 workspace 根（`badou-workspace/`） |
| `framework` | 第三仓 | `.claude/` |

**任务模板**：

```markdown
### Task N: <title>
- scope: backend | frontend | cross-stack | framework
- cwd: backend/ | frontend/ | .claude/ | .
- skill: <skill-name>
- inputs:
  - contracts/<mdCode>/<contract-file>.yaml
  - <other inputs>
- outputs:
  - <expected outputs>
- validation:
  - <how to verify>
```

subagent-driven-development 子 Agent 行为：进入任务时 `cd <task.scope 对应目录>`，不跨 scope；`scope=cross-stack` 任务由主 Agent 亲自执行，不派子 Agent。
