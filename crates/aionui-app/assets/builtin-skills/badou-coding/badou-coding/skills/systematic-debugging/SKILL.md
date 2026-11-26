---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Manager wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - They often contain the exact solution
   - Read stack traces completely
   - Note line numbers, file paths, error codes

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - What are the exact steps?
   - Does it happen every time?
   - If not reproducible → gather more data, don't guess

3. **Check Recent Changes**
   - What changed that could cause this?
   - Git diff, recent commits
   - New dependencies, config changes
   - Environmental differences

4. **Gather Evidence in Multi-Component Systems**

   **WHEN system has multiple components (CI → build → signing, API → service → database):**

   **BEFORE proposing fixes, add diagnostic instrumentation:**
   ```
   For EACH component boundary:
     - Log what data enters component
     - Log what data exits component
     - Verify environment/config propagation
     - Check state at each layer

   Run once to gather evidence showing WHERE it breaks
   THEN analyze evidence to identify failing component
   THEN investigate that specific component
   ```

   **Example (multi-layer system):**
   ```bash
   # Layer 1: Workflow
   echo "=== Secrets available in workflow: ==="
   echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"

   # Layer 2: Build script
   echo "=== Env vars in build script: ==="
   env | grep IDENTITY || echo "IDENTITY not in environment"

   # Layer 3: Signing script
   echo "=== Keychain state: ==="
   security list-keychains
   security find-identity -v

   # Layer 4: Actual signing
   codesign --sign "$IDENTITY" --verbose=4 "$APP"
   ```

   **This reveals:** Which layer fails (secrets → workflow ✓, workflow → build ✗)

5. **Trace Data Flow**

   **WHEN error is deep in call stack:**

   See `root-cause-tracing.md` in this directory for the complete backward tracing technique.

   **Quick version:**
   - Where does bad value originate?
   - What called this with bad value?
   - Keep tracing up until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis

**Find the pattern before fixing:**

1. **Find Working Examples**
   - Locate similar working code in same codebase
   - What works that's similar to what's broken?

2. **Compare Against References**
   - If implementing pattern, read reference implementation COMPLETELY
   - Don't skim - read every line
   - Understand the pattern fully before applying

3. **Identify Differences**
   - What's different between working and broken?
   - List every difference, however small
   - Don't assume "that can't matter"

4. **Understand Dependencies**
   - What other components does this need?
   - What settings, config, environment?
   - What assumptions does it make?

### Phase 3: Hypothesis and Testing

**Scientific method:**

1. **Form Single Hypothesis**
   - State clearly: "I think X is the root cause because Y"
   - Write it down
   - Be specific, not vague

2. **Test Minimally**
   - Make the SMALLEST possible change to test hypothesis
   - One variable at a time
   - Don't fix multiple things at once

3. **Verify Before Continuing**
   - Did it work? Yes → Phase 4
   - Didn't work? Form NEW hypothesis
   - DON'T add more fixes on top

4. **When You Don't Know**
   - Say "I don't understand X"
   - Don't pretend to know
   - Ask for help
   - Research more

### Phase 4: Implementation

**Fix the root cause, not the symptom:**

1. **Create Failing Test Case**
   - Simplest possible reproduction
   - Automated test if possible
   - One-off test script if no framework
   - MUST have before fixing
   - Use the `superpowers:test-driven-development` skill for writing proper failing tests

2. **Implement Single Fix**
   - Address the root cause identified
   - ONE change at a time
   - No "while I'm here" improvements
   - No bundled refactoring

3. **Verify Fix**
   - Test passes now?
   - No other tests broken?
   - Issue actually resolved?

4. **If Fix Doesn't Work**
   - STOP
   - Count: How many fixes have you tried?
   - If < 3: Return to Phase 1, re-analyze with new information
   - **If ≥ 3: STOP and question the architecture (step 5 below)**
   - DON'T attempt Fix #4 without architectural discussion

5. **If 3+ Fixes Failed: Question Architecture**

   **Pattern indicating architectural problem:**
   - Each fix reveals new shared state/coupling/problem in different place
   - Fixes require "massive refactoring" to implement
   - Each fix creates new symptoms elsewhere

   **STOP and question fundamentals:**
   - Is this pattern fundamentally sound?
   - Are we "sticking with it through sheer inertia"?
   - Should we refactor architecture vs. continue fixing symptoms?

   **Discuss with your human partner before attempting more fixes**

   This is NOT a failed hypothesis - this is a wrong architecture.

## Red Flags - STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals new problem in different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (see Phase 4.5)

## your human partner's Signals You're Doing It Wrong

**Watch for these redirections:**
- "Is that not happening?" - You assumed without verifying
- "Will it show us...?" - You should have added evidence gathering
- "Stop guessing" - You're proposing fixes without understanding
- "Ultra-think this" - Question fundamentals, not just symptoms
- "We're stuck?" (frustrated) - Your approach isn't working

**When you see these:** STOP. Return to Phase 1.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify | Bug resolved, tests pass |

## When Process Reveals "No Root Cause"

If systematic investigation reveals issue is truly environmental, timing-dependent, or external:

1. You've completed the process
2. Document what you investigated
3. Implement appropriate handling (retry, timeout, error message)
4. Add monitoring/logging for future investigation

**But:** 95% of "no root cause" cases are incomplete investigation.

## Supporting Techniques

These techniques are part of systematic debugging and available in this directory:

- **`root-cause-tracing.md`** - Trace bugs backward through call stack to find original trigger
- **`defense-in-depth.md`** - Add validation at multiple layers after finding root cause
- **`condition-based-waiting.md`** - Replace arbitrary timeouts with condition polling

**Related skills:**
- **superpowers:test-driven-development** - For creating failing test case (Phase 4, Step 1)
- **superpowers:verification-before-completion** - Verify fix worked before claiming success

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

## Badou Enterprise Addendum

## 字典下拉空白

**症状**：前端下拉框空，但 `comm_dictionary` 里有数据。

**3 个条件缺一不可**：
1. 字段有 `dict` 属性（如 `"dict": "GENDER"`）
2. JSON 顶层有 `dictionaries` 数组（声明 `"type": "GENDER"` + `"items": [...]`）
3. 字段的 `form.edit_type: "select"`

漏任何一条 → 生成器不会建字典关联 → 前端下拉空白。

**调试**：打开生成的 `md_field` 记录，看 `DICT_TYPE` 列是否非空。

## flow_code 字段冲突

**症状**：跑 `crud_generator.py --def module.json` 报 Pydantic 校验错误（"approval_status" 字段类型不匹配等）。

**原因**：`module.flow_code` 非空时，生成器**自动注入 7 个流程字段**到业务表（含 `BO_STATUS`）。如果 module.json 自己也定义了 `approval_status` / `audit_status` / `status` 等字段，会和 `BO_STATUS` 冲突。

**修复**：删掉 module.json 里所有"审批/审核/状态"相关字段——`BO_STATUS` 字典（草稿/审批中/已通过/已驳回）由生成器自动维护。

## flow_code processor_value

**症状**：跑 `--flow-only flow.json --flow-execute` 时 Pydantic 报 "value 第三段错误"。

**原因**：抽象处理人（`type=1`）的 `value` 格式是 `"1!@!拟稿人/填报人!@!<comm_handler_rule.ID>"`，第三段**必须**是 `comm_handler_rule` 表里的 ID，**不是** `0`。

**修复示例**：
```json
// ❌ 错误
{"type": 1, "value": "1!@!拟稿人/填报人!@!0"}

// ✅ 正确（拟稿人/填报人 = comm_handler_rule.ID 3）
{"type": 1, "value": "1!@!拟稿人/填报人!@!3"}
```

## cleanup 顺序

**症状**：重跑 `crud_generator.py` 时 `INSERT` 冲突（重复主键）。

**原因**：`cleanup.sql` 按依赖倒序删除。直接重跑不清 cleanup 会留脏数据。

**修复**：每次重跑前**先**执行 `cleanup.sql`：

```bash
python3 .claude/skills/backend-module-generator/db_executor.py \
    output/<module>/v<ver>/<module>_cleanup.sql \
    --config-from-brain .trellis/PROJECT-BRAIN.md
```

或者依赖 `idempotent_check.py` 在生成前自动 cleanup（默认行为）。

## 跨项目 DB 串台

**症状**：跑了生成器，发现写到了"别的项目"的库。

**原因**：`<project>/.trellis/PROJECT-BRAIN.md` 是项目级配置；不同项目路径不同。

**修复**：每次跑生成器前**先确认** PROJECT-BRAIN.md 路径正确，不要复制粘贴上次的命令。

## 必须用 db_executor

**症状**：用 `mysql < create.sql` 部分 SQL 失败（"Unknown column" 或 "Variable not set"）。

**原因**：生成器 SQL 用大量 MySQL 用户变量（`@module_id` / `@field_xxx` / `@menu_resource_id`），依赖**同一连接的会话上下文**。裸 `mysql` CLI 每次执行可能换连接，丢失变量。

**修复**：用 `db_executor.py`（内部用状态机按 `;` 分割 + 单一 PyMySQL 连接 + autocommit=False + 失败回滚）。

## 不要做

- **不**手编 `output/` 下的 SQL"修一下"——改了 JSON 重跑会被覆盖
- **不**假设 idempotency 不验证——必须跑 `idempotent_check.py` 确认
- **不**对抽象处理人写 `0`——找 `comm_handler_rule` 表里的真实 ID
- **不**裸 `mysql <` 执行生成 SQL——必须用 `db_executor.py`

## 与 superpowers 的差异

superpowers 调试是通用（任何 stack）；我们的 debugging 专攻生成器输出的 6 类已知失败模式（字典/字段冲突/processor_value/cleanup/串台/db_executor）。
