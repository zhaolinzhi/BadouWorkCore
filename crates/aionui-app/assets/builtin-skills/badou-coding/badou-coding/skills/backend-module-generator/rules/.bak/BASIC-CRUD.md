# 基础 CRUD 生成规则

> **用途**: 单表 CRUD 生成的核心规则文档。**仅涉及基础操作**（无多表关联、无流程引擎）。
> **引用来源**: `SKILL.md` 中的 JSON 定义生成指南
> **版本**: v2.0.3 基础规则 (提取于 2026-05-11)

---

## 1. 核心原则 — 三条件缺一不可

**每个需要下拉选择的字段，必须同时满足以下 3 个条件，缺一则字典失效：**

1. **字段定义**中有 `dict: "字典type_name"` 属性
2. **dictionaries 数组**中有对应 `type_name` 的字典定义
3. **form 对象**中有 `edit_type: "select"`（下拉框）

❌ **常见错误**: 只定义了 dictionaries，但字段缺少 `dict` 属性 → 下拉框空白

### 字典绑定失败的典型症状

| 症状 | 原因 | 修复方法 |
|------|------|----------|
| 编辑页下拉框空白 | 字段缺少 `dict` 属性 | 在字段定义中加 `"dict": "xxx"` |
| 列表页筛选项没有字典 | 字段缺少 `dict` + `searchable` | 加 `"dict": "xxx"` 和 `"searchable": true` |
| 编辑页是文本框而非下拉 | 字段缺少 `edit_type: "select"` | form 中加 `"edit_type": "select"` |

## 📐 设计原则：主键与关联字段长度统一

> **规则引擎默认生成的主键长度为 64 位，所有主键字段和关联（外键）字段必须统一为 64 位。**

### 原因
- MD 模块驱动架构使用 UUID 作为主键，长度固定为 64 字符（`uuid.uuid4().hex`）
- 关联字段（外键）指向另一个模块的主键，必须与主键长度一致，否则无法存储完整值

### 适用范围
| 字段类型 | 长度要求 | 说明 |
|---------|---------|------|
| 主键字段（`id`） | `length=64` | 系统标准字段，自动强制 |
| 关联外键字段（如 `category_id`, `user_id`） | `length=64` | type=1 关联中的 field_name 字段，自动强制 |
| 普通字段 | 按实际需求 | 不受此原则约束 |

### 🔗 外键字段自动隐藏
当模块定义了 `relations`（type=1 一对一关联）时，关联中的 `field_name` 指向的是当前模块持有的外键字段，代表当前模块是"多"端。规则引擎会自动配置：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `show_in_grid` | `false` | 列表页不展示 |
| `is_edit` | `true` | 可编辑（由模型配置工具赋值） |
| `edit_type` | `"hidden"` | 隐藏字段，用户不可见 |
| `length` | `64` | 强制与主键长度一致 |

> 用户无需手动配置这些属性，规则引擎会在 `apply_rules()` 中自动处理。详见 `rules/MODULE-LINK.md` → 章节「type=2 一对多的"多"端字段处理」。

### 实现方式
- 规则引擎在 `apply_rules()` 中自动检测外键字段，强制设置 `length=64`
- 用户无需手动配置，JSON 定义中的长度值会被自动覆盖

---

## 2. 字段定义规范

### 字段属性参考

| 属性 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `field_name` | string | **必填**，数据库字段名 | `"status"` |
| `display_type` | string | **必填**，字段类型 | `"varchar"`, `"int"`, `"decimal"`, `"date"`, `"datetime"`, `"text"` |
| `comment` | string | **必填**，字段中文名 | `"商品状态"` |
| `length` | int | 长度（varchar/decimal等） | `50` |
| `nullable` | bool | 是否可空 | `true` |
| `primary_key` | bool | 是否主键 | `false` |
| `default_value` | string | 默认值 | `"0"`, `"1"` |
| `dict` | string | **绑定数据字典的 type_name**，有字典时必填 | `"product_status"` |
| `form` | object | 表单配置，可选 | 见下表 |

### display_type 支持列表

| 类型 | 说明 | 对应表单控件 |
|------|------|-------------|
| `varchar` | 单行文本 | 文本框 |
| `text` | 多行文本 | 文本域 |
| `int` | 整数 | 数字框 |
| `decimal` | 小数 | 数字框 |
| `date` | 日期 | 日期选择器 |
| `datetime` | 日期时间 | 日期时间选择器 |
| `select` | 下拉选择 | 下拉框 |
| `file` | 文件上传 | 文件上传 |
| `image` | 图片上传 | 图片上传 |
| `textarea` | 多行文本 | 文本域 |

### form 子对象属性

| 属性 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `show_in_grid` | bool | 是否在列表表格显示 | `true` |
| `show_in_page` | bool | 是否在编辑页显示 | `true` |
| `editable` | bool | 是否可编辑 | `true` |
| `searchable` | bool | 是否作为筛选条件 | `true` |
| `edit_type` | string | 编辑框类型 | `"input"`, `"select"`, `"textarea"`, `"date"` |
| `edit_tip` | string | 编辑提示 | `"请输入..."` |
| `regex_rule` | string | 校验规则，多个用逗号分隔 | `"required"`, `"required,mobile"`, `"email"` |
| `default_value` | string | 默认值 | `"1"` |

### ✨ 校验规则自动推断

规则引擎会自动为以下字段添加 `regex_rule` 校验，无需手动配置：

| 条件 | 自动推断的 regex_rule | 说明 |
|------|----------------------|------|
| `nullable=false` + 可编辑的 input/textarea/select 字段 | `required` | 非空字段自动加必填校验 |
| 用户已显式配置 `regex_rule` | 保留用户值 | 用户配置优先级最高，不覆盖 |
| `nullable=true` 字段 | 不自动设置 | 可空字段无需必填校验 |
| `edit_type="hidden"` 字段 | 不自动设置 | 隐藏字段无需校验 |
| 系统字段（id, create_time 等） | 不自动设置 | 系统字段不可编辑，无需校验 |

> ⚠️ 自动推断在用户显式配置之前执行，因此用户自定义的 `regex_rule` 会覆盖自动推断值。

---

## 3. 数据字典定义规范

```json
{
  "dictionaries": [
    {
      "type_name": "product_status",
      "name": "商品状态",
      "items": [
        { "code": "0", "value": "0", "name": "下架", "priority": 1 },
        { "code": "1", "value": "1", "name": "上架", "priority": 2 }
      ]
    }
  ]
}
```

**规则**:
- `type_name`: 字典编码，全局唯一，必须与字段的 `dict` 值一致
- `items[].code`: 选项编码
- `items[].value`: 选项值（可与 code 相同）
- `items[].name`: 选项显示名
- `items[].priority`: 排序

---

## 4. JSON 定义模板

### 标准 CRUD 模块 JSON

```json
{
  "module": {
    "name_cn": "【模块中文名】",
    "code": "【模块英文标识】",
    "db_table": "t_【表名】"
  },
  "menu": {
    "parent_code": "FRONT-XTGL",
    "name": "【菜单显示名】"
  },
  "dictionaries": [
    {
      "type_name": "【字典编码】",
      "name": "【字典显示名】",
      "items": [
        {"code": "0", "name": "选项1", "priority": 1},
        {"code": "1", "name": "选项2", "priority": 2}
      ]
    }
  ],
  "fields": [
    {
      "field_name": "普通字段",
      "display_type": "varchar",
      "comment": "中文显示名",
      "length": 50,
      "nullable": false,
      "form": {
        "searchable": true,
        "editable": true,
        "show_in_grid": true
      }
    },
    {
      "field_name": "字典字段",
      "display_type": "varchar",
      "comment": "中文显示名",
      "dict": "字典编码",
      "form": {
        "searchable": true,
        "editable": true,
        "show_in_grid": true,
        "edit_type": "select"
      }
    }
  ],
  "version": "1.0.0"
}
```

---

## 5. 字段定义中 `dict` 属性的正确写法

```json
{
  "fields": [
    // ✅ 正确：显式声明 dict 属性，edit_type 设为 select
    {
      "field_name": "status",
      "display_type": "varchar",
      "comment": "商品状态",
      "dict": "product_status",
      "form": {
        "searchable": true,
        "editable": true,
        "show_in_grid": true,
        "edit_type": "select"
      }
    },
    // ❌ 错误：缺 dict 属性 → 下拉框无选项
    {
      "field_name": "status",
      "display_type": "varchar",
      "comment": "商品状态"
    }
  ]
}
```

**`dict` 值必须和 `dictionaries[].type_name` 完全一致。**

---

## 6. JSON 生成检查清单

**每次生成 JSON 定义前，必须逐字段检查：**

#### 6.1 字典绑定完整性
- [ ] 有字典的字段：`dict` 属性存在？且与 `dictionaries[].type_name` 一致？
- [ ] 有字典的字段：`form.edit_type` 是 `"select"`？
- [ ] 有字典的字段：`form.searchable` 是否为 `true`？
- [ ] `dictionaries` 数组中是否有重复的 `type_name`？

#### 6.2 字段类型
- [ ] `display_type` 与数据库字段类型匹配？
- [ ] varchar 字段是否指定了 `length`？

#### 6.3 表单配置
- [ ] 列表显示：`form.show_in_grid: true`
- [ ] 编辑页编辑：`form.editable: true`
- [ ] 筛选条件：`form.searchable: true`

#### 快速自查表

| 字段定义 | 问题 |
|----------|------|
| `{..., "dict": "xxx"}` | ❌ 缺 `form.edit_type: "select"` |
| `{..., "form": {"edit_type": "select"}}` | ❌ 缺 `dict: "xxx"` |
| `{..., "dict": "xxx", "form": {"edit_type": "select"}}` | ✅ 正确 |

---

## 7. SQL 执行顺序

生成的 SQL 按以下顺序执行：

| 顺序 | 表 | 说明 |
|------|-----|------|
| 1 | `comm_dictionary` | 数据字典 |
| 2 | `comm_dictionary_item` | 字典项 |
| 3 | `md_module` | 模型定义 |
| 4 | `md_field` | 字段定义 |
| 5 | `md_form` | 表单配置 |
| 6 | `md_button` | 按钮配置 |
| 7 | `sys_resource` | 菜单资源 |
| 8 | `sys_role_resource` | 角色授权 |

> 使用 `@variable`（如 `@module_id`、`@field_xxx`）在单连接上下文中跨步骤引用。

---

## 8. 参考文档

| 文档 | 说明 |
|------|------|
| `docs/analysis/modules/md_module/module.md` | 模型定义表结构参考 |
| `docs/analysis/modules/md_field/field.md` | 字段定义表结构参考 |
| `docs/analysis/modules/md_form/form.md` | 表单配置表结构参考 |
| `docs/analysis/modules/md_button/button.md` | 按钮定义表结构参考 |
| `docs/analysis/modules/comm_dictionary/overview.md` | 数据字典表结构参考 |
| `docs/analysis/system/resource/resource.md` | 资源表结构参考 |
| `docs/analysis/system/role_resource/role_resource.md` | 角色资源表结构参考 |
| `examples/product_def.json` | 简单示例 |
| `examples/vehicle_def.json` | 复杂示例 |

---

## 🚨 数据安全设计原则（所有 Agent 必须遵守）

### 原则 1：框架只自动填充系统标准字段

**框架只在 INSERT/UPDATE 时自动赋值以下系统标准字段**，业务 hidden/readonly 字段不会自动填充：

| 系统字段 | 框架行为 | 说明 |
|---------|---------|------|
| `id` | 自动生 UUID | 主键 |
| `create_time` | 自动填当前时间 | 创建时间 |
| `update_time` | 自动填当前时间 | 更新时间 |
| `creator` | 自动填当前用户ID | 创建人ID |
| `creator_name` | 自动填当前用户名 | 创建人 |
| `flg_deleted` | 默认填 0 | 逻辑删除 |

**业务字段（如 applicant_id, applicant_name）框架不会自动填充，必须由后端代码或流程引擎赋值。**

```json
// ✅ 正确：系统字段由框架自动填充
{"field_name": "creator", "nullable": false,  ← 框架会自动填值
 "form": {"editable": false}}

// ✅ 正确：业务 hidden 字段由后端代码填充，信任用户的 nullable 定义
{"field_name": "applicant_id", "nullable": false,  ← 需后端代码/流程引擎赋值
 "form": {"edit_type": "hidden"}}

// ✅ 正确：同上
{"field_name": "applicant_name", "nullable": false,  ← 需后端代码填充
 "form": {"editable": false}}

// ❌ 错误：将业务字段设为 nullable=true 作为"兜底"，会导致数据缺失
{"field_name": "applicant_id", "nullable": true,  ← 不应该！
 "form": {"edit_type": "hidden"}}  // 应保持 nullable=false
```

### 原则 2：NOT NULL 字段必须有 regex_rule="required"

自动推导已覆盖此规则。如果手动设了 `nullable: false`（且可编辑），不需要再写 `form.regex_rule`，
`infer_form_from_metadata()` 会自动加上 `required`。

### 原则 3：业务 hidden/readonly + NOT NULL + 无默认值 = 设计错误

**Pydantic 模型已对此模式做硬性校验，Agent 无法通过 JSON 定义绕过此规则。**

```json
// ❌ 错误：hidden + NOT NULL + 无默认值 → Pydantic 直接报错
{"field_name": "applicant_id", "nullable": false,
 "form": {"edit_type": "hidden"}}

// ❌ 错误：editable=false + NOT NULL + 无默认值 → Pydantic 直接报错
{"field_name": "applicant_name", "nullable": false,
 "form": {"editable": false}}

// ✅ 正确：业务 hidden 字段设 nullable=true
{"field_name": "applicant_id", "nullable": true,
 "form": {"edit_type": "hidden"}}

// ✅ 正确：业务只读字段设 nullable=true
{"field_name": "applicant_name", "nullable": true,
 "form": {"editable": false}}

// ✅ 正确：系统字段不受限（框架自动填充）
{"field_name": "creator", "nullable": false,
 "form": {"editable": false}}

// ✅ 正确：有默认值兜底
{"field_name": "BO_STATUS", "nullable": false, "default_value": "0",
 "form": {"edit_type": "hidden"}}
```

**设计原则**：
| 字段类型 | nullable 建议 | 原因 |
|---------|:-----------:|------|
| 系统标准字段 (id/create_time/flg_deleted 等) | `false` 安全 | 框架自动填充值 |
| 业务 hidden 字段 (applicant_id 等) | `true` | 浏览器不提交，框架不填充，后端代码可能出 Bug |
| 业务 readonly 字段 (applicant_name 等) | `true` | 同上 |
| 有 `default_value` 的字段 | `false` 安全 | 数据库层有默认值兜底 |### 原则 3：区分

> （原则 3 内容待补充）

---

## 9. 查看页配置规则

### 9.1 硬编码隐藏规则

**以下规则为硬编码规则，无条件执行，不受用户配置影响：**

#### 规则 A：涉及 ID 的字段在所有页面不展示

| 字段 | show_in_grid | show_in_page | 原因 |
|------|-------------|-------------|------|
| `id`（主键） | `false` | `false` | 用户不需要看到原始主键值 |
| `*_id`（外键字段） | `false` | `false` | 用户不需要看到原始外键值 |
| `creator`（创建人ID） | `false` | `false` | 由 creator_name 替代展示 |
| `updator`（更新人ID） | `false` | `false` | 由 updator_name 替代展示 |

#### 规则 B：`flg_deleted` 在所有页面不展示

逻辑删除是系统内部机制，所有页面均不展示。

#### 规则 C：`edit_type=hidden` 的字段在所有页面不展示

隐藏字段是后端内部使用的，用户不需要查看或编辑。

### 9.2 查看页隐藏规则（非硬编码）

**字段不在编辑页显示时，默认在查看页也不显示。**### 9.2 view_type 自动推断

规则引擎根据 `edit_type` 自动推导查看页展示类型，**无需手动配置**：

| edit_type | view_type | 说明 |
|-----------|-----------|------|
| `select` | `dic` | 字典值翻译显示（显示中文名而非代码） |
| `date` | `date` | 日期格式化 |
| `datetime` | `dateTime` | 日期时间格式化 |
| `textarea` | `richText` | 多行文本富文本展示 |
| `number` | `text` | 数字文本展示 |
| `input` | `text` | 普通文本展示 |
| `hidden` | 不输出 | 隐藏字段不生成 view_type |
| 有 `dict` 绑定 | `dic` | 有字典绑定的字段强制 dic |
| 用户显式设置 | 保留用户值 | 用户配置优先级最高 |

### 9.3 is_full_line 自动推断

| edit_type / view_type | is_full_line | 说明 |
|-----------------------|-------------|------|
| `textarea` | `true` | 多行文本独占一行 |
| `richText` | `true` | 富文本独占一行 |
| 其他 | `null`（不输出） | 默认不独占 |
| 用户显式设置 | 保留用户值 | 用户配置优先级最高 |

### 9.4 form 新增字段

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `view_type` | string | 查看页展示类型 | 自动推断 |
| `view_drill_url` | string | 查看页钻取URL | null |
| `view_drill_open_type` | int | 1=新tab, 2=新页面 | null |
| `view_drill_page_title` | string | 钻取页面标题 | null |
| `is_full_line` | bool | 是否独占一行 | 自动推断 |
| `is_import` | bool | 是否支持导入 | null |
| `is_export` | bool | 是否支持导出 | null |
| `default_value` | string | 表单默认值 | null |

> 所有新增字段的 `null` 默认值表示“不输出到 SQL”，仅当用户显式设置或自动推断有效时才写入 md_form。
