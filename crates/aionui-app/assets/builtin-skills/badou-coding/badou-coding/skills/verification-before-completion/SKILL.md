---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## Why This Matters

From 24 failure memories:
- your human partner said "I don't believe you" - trust broken
- Undefined functions shipped - would crash
- Missing requirements shipped - incomplete features
- Time wasted on false completion → redirect → rework
- Violates: "Honesty is a core value. If you lie, you'll be replaced."

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to:**
- Exact phrases
- Paraphrases and synonyms
- Implications of success
- ANY communication suggesting completion/correctness

## The Bottom Line

**No shortcuts for verification.**

Run the command. Read the output. THEN claim the result.

This is non-negotiable.

## Badou Enterprise Addendum

## 三件套门槛

任何含 `backend-module-generator` 的模块在宣告"完成"前**必须**跑这 3 步，全部退出码 0：

```bash
# 1. 生成器退出码 0
python3 .claude/skills/backend-module-generator/crud_generator.py \
    --def <module>.json --output ./output
# Expected: exit 0 + 输出 "✅ Sync complete"

# 2. SQL 执行退出码 0
python3 .claude/skills/backend-module-generator/db_executor.py \
    output/<module>/v<ver>/<module>_create.sql \
    --config-from-brain .trellis/PROJECT-BRAIN.md
# Expected: exit 0

# 3. 验证器退出码 0 + ALL PASSED
python3 .claude/skills/backend-module-generator/validators/idempotent_check.py \
    <module>.json
# Expected: exit 0 + 末行 "ALL PASSED ✅"
```

**任一退出码非 0 = 没完成。**

## idempotent_check 验证什么

8 类检查：

1. **模型设计器**：md_module 存在、名称/表名正确、flow_id 关联（如有）
2. **字段完整性**：所有 JSON 字段在 md_field 中存在、类型匹配
3. **表单合理性**：dict→select 下拉、date→日期选择器、text→textarea、decimal→number+校验
4. **字典数据**：字典类型存在、字典项数量正确、名称匹配
5. **菜单权限**：菜单存在、6 个标准按钮资源全、角色授权
6. **流程引擎**（若 flow_code）：busi/flw_flow/flw_node/flw_route/comm_handler 数量一致、关联完整
7. **DDL 完整性**：业务表存在、id/create_time/update_time/flg_deleted 四字段齐全
8. **幂等安全性**：可安全重复清理重建、不影响其他模块

## 退出码

- **0 = 通过**：可以宣告完成
- **1 = 失败**：必须修复后重跑完整流水线（不是只重跑验证器）

## 失败处理

`idempotent_check.py` 失败时：

1. 看哪一类检查失败（输出里有 ❌ 标记）
2. 修复对应的 JSON / 数据
3. **重跑完整 3 步**（不是只重跑验证器）—— 因为可能需要重新生成 SQL 和重新执行
4. 直到 ALL PASSED

只重跑验证器 = 假装通过 = 数据没真正修好。

## 重跑安全

3 步全部幂等：可以重跑 N 次同一模块。`crud_generator.py` 会先 `rm -rf` + `cp -R`（生成器产物可重建）；`db_executor.py` 用 `INSERT` 模式且 `idempotent_check.py` 验证数据已存在；验证器本身无副作用。

**前提**：必须用 `db_executor.py`（不是裸 `mysql`）—— 裸 `mysql` 在重跑时可能因为用户变量丢失导致 SQL 部分失败。

## CI 集成

推荐 pipeline（如项目配了 CI）：

```bash
mvn checkstyle:check \
  && python3 .claude/skills/backend-module-generator/crud_generator.py --def module.json --output ./output \
  && python3 .claude/skills/backend-module-generator/db_executor.py output/<module>/v<ver>/<module>_create.sql --config-from-brain .trellis/PROJECT-BRAIN.md \
  && python3 .claude/skills/backend-module-generator/validators/idempotent_check.py module.json
```

**顺序不能换**——先静态检查（checkstyle），再生成，再执行，再验证。

## 不要做

- **不**跳 `idempotent_check.py`——跳过的模块 100% 有问题（dict 三条件、flow 字段冲突等）
- **不**在输出 "ALL PASSED" 缺失时宣告完成
- **不**修改生成的 SQL 后不重跑验证——SQL 改了 = 偏离 JSON 定义，下次重跑覆盖
- **不**把"验证器失败"当作"已知问题"留给后人——必须当场修
- **不**只跑验证器不跑生成器和执行器——三者必须一起

## 与 superpowers 的差异

superpowers 验证是"测试通过 + lint 干净"；我们的 verification 额外要求 `idempotent_check.py` 输出 `ALL PASSED`，覆盖 8 类生成器特有检查。
