# SQL 执行顺序与 db_executor.py

> **何时读**：准备执行 generator 输出的 SQL 时。

<!-- Source: generated for backend-module-generator stability design, do not edit by hand without syncing the plan. -->

---

## §1 执行顺序（5 阶段）

> 🚨 **必须严格按以下顺序执行**，否则会因子查询返回 NULL 而失败。

```
阶段 1：环境依赖
└── md_database 中 code='projectDatabase' 必须存在
    └── md_module_type 中 m_t_id='40282b815b6f9ac5015b7052f35d0008' 必须存在

阶段 2：模块创建（无关联）
└── 对每个模块（按依赖顺序）：
    ├── <code>_create.sql       # 模块 + 字段 + 表单 + 按钮 + 字典 + 资源

阶段 3：模块关联
└── 对每个含 relations 的模块：
    └── <code>_relation.sql     # md_module_link INSERT

阶段 4：流程绑定（仅流程模块）
└── backend-flow-engine 已先创建 flw_flow 后：
    └── <code>_create.sql 中的 UPDATE md_module SET flow_id 子查询

阶段 5：清理（如需）
└── <code>_cleanup.sql         # 倒序删除（含流程模块的 8 表联动清理）
```

---

## §2 为什么不能用裸 `mysql < create.sql`

生成的 SQL 大量使用 MySQL 用户变量（`@module_id` / `@field_xxx` / `@menu_resource_id` / `@resource_id_xxx` 等）。

| 工具 | 多语句 | 会话变量 | 推荐 |
|------|--------|----------|------|
| 裸 `mysql < file.sql` | ✅ | ❌ 每个语句可能换连接 → 变量丢失 | ❌ |
| PyMySQL 默认 | ❌（默认禁用多语句） | — | ❌ |
| `db_executor.py` | ✅ 状态机分割 | ✅ 单一连接 | ✅ |

---

## §3 db_executor.py 用法

```bash
python3 db_executor.py output/<module>/v<ver>/<module>_create.sql \
  --config-from-brain .trellis/PROJECT-BRAIN.md

# 或手动指定
python3 db_executor.py output/<module>/v<ver>/<module>_create.sql \
  --host 192.168.1.100 --port 3306 --db mydb --user root --password xxx
```

工作原理：
1. **D27 起**：DB 配置走 3 层 fallback + 询问用户
   - `explicit_config`（`--config-from-brain` 或 `--config` 显式提供）
   - `<project-root>/.trellis/PROJECT-BRAIN.md`
   - `<project-root>/backend/pom.xml` + `application*.yml` / `.properties`（Spring Boot 识别）
   - 交互式 `input()`（仅在 `interactive=True` 且 stdin 是 tty 时；CI 用 `--no-interactive`）
2. 状态机按 `;` 精确分割 SQL（不破坏字符串/注释内的 `;`）
3. 建立单一 pymysql 连接
4. 逐条执行，`@variable` 在整个会话生命周期内有效
5. 事务模式（autocommit=False），失败自动回滚

> 共享 resolver 见 `badou-coding/common/db_config_resolver.py::resolve_db_config`。
> CI 推荐：始终加 `--no-interactive`，并通过 `--config-from-brain` 或 `--config` 显式提供。

---

## §4 验证：idempotent_check.py

```bash
python3 validators/idempotent_check.py module.json
# → "ALL PASSED" + 退出码 0
```

检查 8 类问题：
1. md_module.code 唯一性
2. md_field 与 DDL 列一致性
3. md_form.is_required 与 DDL NOT NULL 一致性
4. md_button 与 buttons 数组一致性
5. comm_dictionary_item 与字典定义一致性
6. sys_resource 完整性
7. md_module_link 关联字段存在性（仅含 relations 时）
8. md_flow 流程字段一致性（仅含 flow_code 时）

---

## §5 关联模块的执行顺序

```
第一阶段：创建所有模块（按依赖顺序，被依赖的先创建）
├── mysql < customer_create.sql      # 被依赖
└── mysql < order_create.sql         # 依赖 customer

第二阶段：创建所有关联
├── mysql < customer_relation.sql    # 不需要（无 relations）
└── mysql < order_relation.sql       # 关联 customer
```

> ⚠️ **不要在单模块 create.sql 中包含 relation**——关联模块可能还不存在，子查询返回 NULL。

---

## 📎 引用清单

**相关规则文档**：
- [rules/basic-crud.md](basic-crud.md) — 入口
- [rules/module-link.md](module-link.md) — 二阶段关联执行
- [rules/flow-contract.md](flow-contract.md) — 流程模块执行顺序
- [rules/data-safety.md](data-safety.md) — 执行前的数据安全约束

**工具脚本**：
- `db_executor.py` — 项目根工具（PyMySQL 多语句）
- `validators/idempotent_check.py` — 幂等性校验

**示例**：
- [examples/vehicle_def.json](../../examples/vehicle_def.json) — 单表，无关联
- [examples/order_with_items.json](../../examples/order_with_items.json) — 含 relations，演示二阶段
