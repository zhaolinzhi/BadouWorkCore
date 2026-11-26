---
name: frontend-module-quickstart
description: 八斗 Module 低代码平台 5 分钟上手指南(总览/入口)。**何时调用**:① 用户说"写一个 module 页面/列表/表单"、"新增业务模块"、"用 mdCode 做个 CRUD"、"ModuleList/ModuleEditCode 怎么用"等要做标准 CRUD 页的需求;② 用户首次接触 Module 平台,需要快速建立"业务方做什么 / 框架自动做什么"的心智模型;③ 作为 frontend-module-list / frontend-module-edit / frontend-module-page-debug / frontend-module-extend-field 等子 skill 的入口和总览。**何时不调用**:① 用户已明确要改 customSetting 某个具体 key(如 renderField、buttons、valueChange)→ 直接跳到 frontend-module-list 或 frontend-module-edit 的对应子 skill;② 用户要排查具体报错/白屏/不生效 → 用 frontend-module-page-debug;③ 问的是通用 Vue/Element UI 问题 → 与 Module 平台无关。
---

# Module 平台快速上手

> 5 分钟读懂"业务方用 Module 平台写一个标准 CRUD 页面"的全貌。涉及具体子能力时,请跳转到对应 skill。

---

## 0. Module 平台 & 模型设计器基础

> **第一次接触 Module 平台必读。** 讲清"什么是模型设计器、它能配什么、不能配什么",后续章节再讲怎么写代码。

### 0.1 什么是 Module 平台 / 模型设计器

- **Module 平台**:八斗的低代码页面平台,业务方**不用从零写 Vue 代码**,而是"配"出一个标准 CRUD 页面。配出来的页面**仍然**走正常的 `<module-list-code>` / `<module-edit-code>` 组件渲染,只是页面"长什么样、有什么字段"由配置决定。
- **模型设计器**:后端提供的一个**可视化配置工具**。业务方(或后端同学)在模型设计器里,先选定一张数据库表,平台自动读取该表的所有字段,然后业务方在界面上"勾一勾、选一选"就能生成对应页面。

> ⚠️ **模型设计器 ≠ 前端代码**。它在后端(或独立后端服务),前端拿到的是它返回的 JSON 配置(`Standard_List` / `Standard_Edit` / `Standard_View` 三个接口的返回)。前端能做的只是"基于这份配置渲染页面 + 通过 `customSetting` 补刀",改不动的只能回去找后端改设计器。

### 0.2 模型设计器能配什么 / 不能配什么

模型设计器主要负责配置**三类页面的字段和显示规则**,但它**不是万能的**,有些能力必须由前端 `customSetting` 补。下面这张表是分界线,务必熟记:

| 页面 | 模型设计器**能直接配** | 模型设计器**配不了**,需前端 `customSetting` |
|------|----------------------|----------------------------------------------|
| **列表页** | ① **搜索条件**:哪些字段作为搜索项、用什么类型(输入框/下拉/日期等)<br>② **表格列**:表格里要展示哪些字段、列标题、对齐方式、宽度、是否排序等 | ① **过滤器**:表头右上角的过滤器(高级搜索/分类筛选)<br>② **按钮模块**:顶部按钮区、行内按钮、操作列的交互逻辑(点击事件、权限、确认弹窗、二次确认等) |
| **编辑页** | ① **可显示的编辑表单字段**:每个字段用哪种类型(详见 §9 字段类型全集)<br>② **隐藏字段**:字段类型选 `隐藏` → **不在页面渲染但提交时会带上**(常用于主键、创建人、创建时间等无需用户填写但需后端拿到的字段)<br>③ 常见类型:`input` / `select` / `textarea` / `number` / `date` / `switch` / `radio` / `checkbox` / `cascader` / `attach` / `image` / `richtext` 等 | ① **字段联动**(A 变 → B 跟着变 / 显隐 / 必填)<br>② **自定义校验规则**(正则、异步校验、唯一性)<br>③ **保存/详情接口替换 / 加签 / 加密**<br>④ **字段后追加 DOM / 整表单重排版**<br>⑤ **保存后跳转逻辑 / 二次确认** |
| **查看页** | ① **可展示的字段**:哪些字段在查看页显示、按什么顺序<br>② **每个字段的查看显示类型**:用文本/标签/图片/字典翻译/自定义格式等不同方式呈现 | ① **字段值二次加工**(如状态码转中文、日期格式化、关联表字段拼装)<br>② **整页内容重排版 / 插入自定义区块**<br>③ **打印 / 导出 PDF 等特殊行为** |

### 0.3 一张图看清边界

```
┌──────────────────────────┐
│       模型设计器(后端)    │
│  - 字段清单、表名         │
│  - 搜索条件、表格列       │
│  - 编辑字段类型(含'隐藏') │
│  - 查看字段显示类型       │
└────────────┬─────────────┘
             │ JSON 配置
             ▼
┌──────────────────────────┐
│    前端 Module 组件       │
│  按 JSON 渲染默认页面    │
└────────────┬─────────────┘
             │ customSetting 补刀
             ▼
┌──────────────────────────┐
│  public/moduleJs/         │
│  {mdCode}/list.js | edit.js
│  - 过滤器、按钮           │
│  - 联动、校验、加签等     │
└──────────────────────────┘
```

**记忆口诀**:**"页面骨架"找模型设计器,页面"血肉/交互"找 customSetting。**

> 💡 第一次不知道某个能力该找谁时:先看 §0.2 的"能/不能"表。能配的 → 找后端同学改模型设计器;配不了的 → 走 customSetting(见 §4、§8,以及 [frontend-module-list](../frontend-module-list/SKILL.md) / [frontend-module-edit](../frontend-module-edit/SKILL.md))。

---

## 1. 一句话理解 Module 平台

**业务方只需要做两件事:**

1. **后端配置**一个 `mdCode`(模型编码):定义字段、列表显示列、搜索条件、按钮权限
2. **前端引用**两个组件:`<module-list-code>` 渲染列表、`<module-edit-code>` 渲染表单

框架自动:
- 请求后端 `Standard_List` / `Standard_Edit` / `Standard_View` 三个接口
- 加载后端配置 + `customSetting`(自定义 JS)
- 渲染搜索栏、表格、表单、按钮
- 处理分页、选中、行操作、保存、删除、导入导出

**业务方 99% 的代码量,集中在"如何配置 customSetting"上。**

---

## 2. 三类典型页面

项目里所有 Module 页面都基于这三类"标准容器"二次封装,集中在 [src/router/modules/model.js](../../../../src/router/modules/model.js):

| 容器 | 路由前缀 | 用途 | 关键视图 |
|------|---------|------|---------|
| **stander**(标准) | `/module/stander/` | 业务方最常用,90% 业务都用这个 | [List.vue](../../../../src/views/module/stander/List.vue), [Edit.vue](../../../../src/views/module/stander/Edit.vue) |
| **tree**(树型) | `/module/tree/` | 左侧树 + 右侧列表 | `views/module/tree/*` |
| **dic**(字典) | `/module/dic/` | 简化版,常用于系统字典维护 | `views/module/dic/*` |
| **view**(查看) | `/module/view/` | 只读视图、报表 | `views/module/view/*` |
| **flow**(流程) | `/module/flow/` | 流程发起/审核(workEdit/workView) | `views/module/flow/*` |

**90% 的需求落在 `stander` 上**,本 skill 以它为例。

---

## 3. 快速上手:3 步写一个标准 CRUD 页面

### 第 1 步:确认 `mdCode`

后端已经在模型设计器里配好了一个 `mdCode`(比如 `user_info`)。

### 第 2 步:写一个 List.vue(列表页)

直接基于 [`stander/List.vue`](../../../../src/views/module/stander/List.vue) 模板,**实际业务几乎不用改代码**:

```vue
<template>
    <div class="bd-page-list">
        <module-list-code
            ref="moduleListCode"
            :mdCode="mdCode"
            fullHeight
            v-bind="$attrs"
            v-on="$listeners">
        </module-list-code>
    </div>
</template>
<script>
import ModuleListCode from '@/components/frame/Module/ModuleListCode'
export default {
    name: 'userInfoList',
    components: { [ModuleListCode.name]: ModuleListCode },
    data () {
        return { mdCode: 'user_info' }
    }
}
</script>
<style scoped>
.bd-page-list { height: 100%; }
</style>
```

### 第 3 步:写一个 Edit.vue(表单页)

直接基于 [`stander/Edit.vue`](../../../../src/views/module/stander/Edit.vue) 模板:

```vue
<template>
    <div class="bd-page-edit">
        <module-edit-code
            ref="moduleEditCode"
            :mdCode="mdCode"
            :detailId="detailId"
            fullHeight>
        </module-edit-code>
    </div>
</template>
<script>
import ModuleEditCode from '@/components/frame/Module/ModuleEditCode'
export default {
    name: 'userInfoEdit',
    components: { [ModuleEditCode.name]: ModuleEditCode },
    computed: {
        mdCode () { return 'user_info' },
        detailId () { return this.$route?.params?.id !== 'add' ? this.$route?.params?.id : '' }
    }
}
</script>
```

**完成。** 现在列表能搜、能翻页、能选、能编辑;表单能填值、能保存。

---

## 4. 什么时候"必须"动代码

只有当以下需求出现时,才需要写代码:

| 需求 | 落点 | 跳转到 |
|------|------|--------|
| 给某列加"状态徽章"/JSX 渲染 | `customSetting.renderField` | [sub/render-field](../frontend-module-list/sub/render-field/SKILL.md) |
| 加一个"导出 Excel"按钮 / 顶部按钮 | `customSetting.buttons` | [sub/buttons](../frontend-module-list/sub/buttons/SKILL.md) |
| 搜索条件默认值 / 联动 | `customSetting.searchConditionChange` | [sub/search](../frontend-module-list/sub/search/SKILL.md) |
| 改请求方法/参数/加签 | `customSetting.paramsBeforeRequest` | [sub/request-flow](../frontend-module-list/sub/request-flow/SKILL.md) |
| 字段 A 变化时联动字段 B(表单) | `customSetting.valueChange` | [sub/fields](../frontend-module-edit/sub/fields/SKILL.md) |
| 字段后追加 DOM / 自定义排版 | `customSetting.appendDom` / `contentRender` | [sub/form-react](../frontend-module-edit/sub/form-react/SKILL.md) |
| 表单校验规则 / 动态显隐 | `customSetting.validateRule` | [sub/validation](../frontend-module-edit/sub/validation/SKILL.md) |
| 改保存接口 / 详情接口 / 自定义按钮 | `customSetting.saveUrl` / `dataUrl` / `buttons` | [sub/submit-flow](../frontend-module-edit/sub/submit-flow/SKILL.md) |
| 改表单列数 / 标题右侧 / 字段重排 | `customSetting.columnNum` / `titleRightSlot` | [sub/layout](../frontend-module-edit/sub/layout/SKILL.md) |
| tab 切换拦截 / 关联子表 | `customSetting.beforeTabLeave` / `childTab` | [sub/tab-nav](../frontend-module-edit/sub/tab-nav/SKILL.md) |
| 表格冻结列/合计行/合并 | `customSetting.showSummary` 等 | [sub/table-look](../frontend-module-list/sub/table-look/SKILL.md) |
| 列表/表单报错排查 | 控制台 + 缓存检查 | `frontend-module-page-debug` |
| 加一种新字段类型 | `items/index.js` 注册 | `frontend-module-extend-field` |

> ⚠️ **进入 customSetting 之前,先确认当前模型的 JS 路径**——`mdCode` + `list|edit` + 完整文件路径 + 是否已配 customJs,详见下面 4.1。

### 4.1 customSetting 之前:先问 JS 路径(必读)

**List 和 Edit 是两个完全不同的 customSetting 文件**,而且 `mdCode` 到 JS 路径不是 1:1 写死——后端可以指向任意路径(可能有自定义目录如 `business/text/xxx_list.js`)。

进入任何 customSetting 修改前,**先用 AskUserQuestion 一次性问清 4 项**:

| 询问项 | 为什么 |
|--------|--------|
| **mdCode**(模型编码) | 决定 `public/moduleJs/{mdCode}/` 根目录 |
| **list 还是 edit** | 决定改 `list.js` 还是 `edit.js`——结构和可用 key 都不同 |
| **完整路径** | 一些模型有自定义目录(如 `business/text/xxx`),不是默认 `{mdCode}/list.js` |
| **是否已配置 customJs** | 没配的话需要先在模型设计器指一下才能生效 |

**推荐问法**:

> "请确认下:① 改哪个 `mdCode`? ② **list** 页还是 **edit** 页? ③ `customSetting` JS 文件的完整路径是? ④ 是否已在模型设计器配过 `模型表单配置`?"

拿到回答后:
- **先 Read 现有文件**(`Read ${customJsPath}`),别直接覆盖
- 文件**不存在** → 提示用户去配置 `列表/编辑页 js` 路径,或放默认路径 `public/moduleJs/{mdCode}/list.js`
- 文件**已存在** → 先**备份原内容**,再增量修改——直接 `export default { ... }` 覆盖会清掉原有配置

**什么时候可以不问**:
- 用户**明确给了** mdCode + list|edit + 完整路径
- 用户的描述里**自带文件位置**(如"改 `user_info/list.js` 里的 `renderField`")

---

## 4.1 默认 JS 路径规则(任何业务模块优先遵循)

业务模块的 customSetting JS 路径**默认**落 `public/moduleJs/business/{mdCode}/` 子目录:

| 文件 | 默认路径 |
|------|----------|
| 列表 customSetting | `public/moduleJs/business/{mdCode}/list.js` |
| 表单 customSetting | `public/moduleJs/business/{mdCode}/edit.js` |

约定:
- 仅在用户**显式指定**其他路径(例如 `public/moduleJs/frame/...` 或多级子目录)时,才覆盖默认值。
- `backend-module-generator` 默认会向 `md_module` 写入 `LIST_JS='/business/{mdCode}/list.js'`;`edited_js` **仅在用户显式设置 `frontend.edit_js_path` 时才写入**(默认保持 NULL,框架按"无 edit.js customSetting"处理)。前端 `ModuleUtils` 拼接 `public/moduleJs` 前缀后即落 `business/{mdCode}/`。
- `frontend-module-*-search-set-value` 之类的技能在用户未给出路径时也应使用此默认,不再默认回落到 `public/moduleJs/{mdCode}/list.js`。
- 框架子模块(`public/moduleJs/frame/...`)与历史业务目录(如 `business/text/wjx_*`)维持现状,不在本期默认覆盖范围内。

---

## 5. 核心组件速查

### 5.1 ModuleListCode(列表页入口)

文件: [src/components/frame/Module/ModuleListCode.vue](../../../../src/components/frame/Module/ModuleListCode.vue)

**最常用的 props:**

| prop | 类型 | 说明 |
|------|------|------|
| `mdCode` | String | **必填**,模型编码 |
| `fullHeight` | Boolean | 设置 true 则高度 100% |
| `height` | String/Number | 自定义高度(支持 px 和 %) |
| `searchParam` | Object | 搜索栏默认值 |
| `defaultParamsObj` | Object | 列表请求固定参数 |
| `permissionBtnList` | Array | 权限过滤按钮 |
| `isStartReList` | Boolean | keep-alive 时是否自动刷新 |
| `customSetting` | Object | **核心:自定义 JS 配置** |

> 业务方直接用 `ModuleListCode`,基本不用碰底层 `ModuleList` 组件。

### 5.2 ModuleEditCode(表单页入口)

文件: [src/components/frame/Module/ModuleEditCode.vue](../../../../src/components/frame/Module/ModuleEditCode.vue)

**最常用的 props:**

| prop | 类型 | 说明 |
|------|------|------|
| `mdCode` | String | **必填**,模型编码 |
| `detailId` | String | 数据 id,新增传 `''`,查看/编辑传 id |
| `isView` | Boolean | 是否查看模式(只读) |
| `viewType` | String | 表格模式等样式控制(交给 stander/Edit 处理) |
| `defaultParamsObj` | Object | 请求表单详情前的默认参数 |
| `historyData` | Array | 历史 tab 数据(框架自动处理) |
| `fullHeight` | Boolean | 高度 100% |
| `refName` | String | ref 名称,默认 `edit` |
| `customSetting` | Object | **核心:自定义 JS 配置** |

### 5.3 ref 调用方法(在父组件里 `$refs.moduleEditCode.getFormRef().xxx()`)

| 方法 | 说明 |
|------|------|
| `getModuleEditRef()` | 获取 ModuleEdit 实例 |
| `getFormRef()` | 获取最底层表单实例 |
| `getFormData(diy_dataUrl)` | 主动请求表单详情(支持自定义 URL) |
| `setDetailId(formData)` | 手动设置 id |
| `refresh(updateId)` | 刷新表单(传新 id) |

---

## 6. 路由约定

`mdCode` 通过路由参数传递,业务方**基本不直接配置路由**,系统会动态生成。

标准路由见 [src/router/modules/model.js](../../../../src/router/modules/model.js):

| 名称 | path | 说明 |
|------|------|------|
| `standerList` | `/module/stander/list/:mdCode/:symbol` | 列表页(标准) |
| `standerEdit` | `/module/stander/:editStyle/:mdCode/:id` | 编辑页(标准) |
| `standerListTree` | `/module/tree/list/:mdCode/:symbol` | 列表页(树型) |
| `standerEditTree` | `/module/tree/edit/:mdCode/:id` | 编辑页(树型) |

**路由跳转示例**(统一使用 `this.pushPage`,详见 [src/service/router.js](../../../src/service/router.js)):

```js
// 跳转列表
this.pushPage({
    name: 'standerList',
    params: { mdCode: 'user_info', symbol: 'list' },
    title: '用户列表' // 必传:用于保存到 Tab 历史,不传则该页面不会进 Tab 历史,且会在 dev 环境弹窗警告
})

// 跳转新增
this.pushPage({
    name: 'standerEdit',
    params: { mdCode: 'user_info', editStyle: 'add', id: 'add' },
    title: '新增用户'
})

// 跳转编辑
this.pushPage({
    name: 'standerEdit',
    params: { mdCode: 'user_info', editStyle: 'edit', id: '12345' },
    title: '编辑用户'
})

// 跳转查看
this.pushPage({
    name: 'standerEdit',
    params: { mdCode: 'user_info', editStyle: 'view', id: '12345' },
    title: '查看用户'
})
```

> ⚠️ **不要再使用 `this.$router.push`**,统一用 `this.pushPage`。它是对 `router.push/replace` 的封装(`this.$router` 在 Vue 原型上仍可用,但框架强约束走 `pushPage` 以便统一处理 Tab 历史和跳转埋点)。两者支持相同字段,`pushPage` 额外多 `title` / `storage` / `replace` 三个参数。

---

## 7. 后端数据流(理解原理用,业务方不用记)

```
┌─────────────────┐
│ 模型设计器  │ 配置 mdCode、字段、按钮
└────────┬────────┘
         │ (数据库)
         ▼
┌────────────────────────────────────────────┐
│ Standard_List   GET  /jdbc/common/.../listModule.do?mdCode=xxx  │
│ Standard_Edit   GET  /jdbc/common/.../editModule.do?mdCode=xxx  │
│ Standard_View   GET  /jdbc/common/.../viewModule.do?mdCode=xxx  │
└────────┬───────────────────────────────────┘
         │ 返回 JSON
         ▼
┌────────────────────────────────────────────┐
│ src/js/ModuleUtils.js                       │
│   listModuleCfg / editModuleCfg / viewModuleCfg │
│   - 解析后端字段                             │
│   - 加载 customSetting(customJs 路径 → require)│
│   - 合并 formOption(list/edit)               │
└────────┬───────────────────────────────────┘
         │ module 对象
         ▼
┌────────────────────────────────────────────┐
│ ModuleListCode / ModuleEditCode             │
│   - 渲染 searchFilter / table / form        │
│   - 调用 BtnBaseFun(Add/Edit/View/...)      │
│   - customSetting 注入到内部 data           │
└────────────────────────────────────────────┘
```

**两个环境变量影响数据流:**

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `VUE_APP_OPEN_MODULE_STORAGE` | 0 | 设为 1 开启模块配置缓存(系统稳定后启用) |
| `VUE_APP_BASE_API` | (见 .env) | 后端 API 根地址 |

---

## 8. customSetting 速览(后续 skill 详解)

`customSetting` 是**业务方魔改 Module 行为的主战场**。它是一个对象,key 按功能区分,value 多为函数。

```js
// 典型 customSetting(放在 public/moduleJs/{mdCode}/list.js 或 edit.js)
export default {
    // 1. 自定义按钮(覆盖默认增删改查)
    buttons: [
        { id: 'export', name: '导出', icon: 'el-icon-download', click: this.handleExport }
    ],

    // 2. 自定义列渲染(状态徽章/图片预览等)
    renderField: (h, { row, field }) => {
        return h('el-tag', { type: row.status === 1 ? 'success' : 'danger' }, row.statusText)
    },

    // 3. 搜索条件变化监听
    searchConditionChange: function (searchFieldList) { ... },

    // 4. 表单值变更监听(字段联动)
    onChange: function (field, value, formData) { ... },

    // 5. 请求前改参数(加签/解密/参数补充)
    paramsBeforeRequest: function (params) { ... },

    // 6. 请求后处理数据
    afterListJSON: function (res) { ... },
    afterEditJSON: function (formData) { ... },

    // 7. 自定义数据请求 URL
    dataUrl: function () { return '/my/custom/url' },

    // 8. 模块加载完成后处理
    afterModuleJSON: function (module) { ... }
}
```

**关键事实:**
- List 和 Edit 的 `customSetting` **结构不完全一样**(API、this 指向、可用 key)
- 完整 key 列表和示例见各 `module-customsetting-*` skill
- 文件路径:`public/moduleJs/{mdCode}/list.js` 和 `edit.js`(由后端配置指向)

---

## 9. 字段类型全集(20 种)

定义: [src/components/frame/Common/MForm/components/items/index.js](../../../../src/components/frame/Common/MForm/components/items/index.js)

| 类型(type) | 组件 | 典型场景 |
|------------|------|---------|
| `text` | Text | 短文本 |
| `textarea` | Textarea | 长文本 |
| `number` | Number | 数字(可配置精度) |
| `select` | Select | 下拉单选 |
| `radio` | Radio | 单选 |
| `checkbox` | Checkbox | 多选 |
| `switch` | Switch | 开关 |
| `date` | Date | 日期(支持 date/datetime/time) |
| `cascader` | Cascader | 级联选择 |
| `autocomplete` | AutoComplete | 联想输入 |
| `attach` | Attach | 附件上传 |
| `image` | ImagePicker | 图片(单/多) |
| `richtext` | RichText | 富文本 |
| `code` | Code | JSON 编辑器 |
| `codemirror` | CodeMirror | SQL/Java/Python 等代码 |
| `addresspicker` | AddressPicker | 省市区选择 |
| `addressbook` | AddressBook | 通讯录选择 |
| `dialoglist` | DialogList | 弹窗列表选择 |
| `colorpicker` | ColorPicker | 颜色选择 |
| `iconpicker` | IconPicker | 图标选择 |
| `pathpicker` | PathPicker | 页面路径选择 |
| `roadmap` | Roadmap | 路线图(里程碑) |
| `rate` | Rate | 评分 |

> ⚠️ 部分 type 在不同 Model 版本里有别名(比如 `FormText` ≡ `text`),后端配置时优先用**小写短名**。

---

## 10. 工具方法(从 `src/service/module.js` 挑出最常用的)

| 方法 | 用途 |
|------|------|
| `Merge_Btn(btnList, customBtnList)` | 合并默认按钮和自定义按钮 |
| `ShowStatus(item)` | 判断字段/按钮的显隐状态 |
| `HandleClick(btn, scope)` | 按钮事件统一分发 |
| `Get_Module_ClassName(mdCode, type, isView)` | 获取模型专属 CSS 类名(用于隔离样式) |
| `Get_Validation_Rule(fieldItem)` | 根据字段定义生成校验规则 |
| `Value_Unique_Fun(rule, value, callback, fieldItem)` | 唯一性校验(后端查重) |
| `GetSearchFieldList(searchCondition, selectorData)` | 组装搜索字段 |
| `ExportData(params)` / `ImportData(params)` | 导入导出 |
| `Get_Search_Type(fieldType)` | 字段 type → 搜索 queryType 映射 |

> 这些方法在 `customSetting` 的 JS 文件里**直接 import 就能用**,见各子 skill 的示例。

---

## 11. 常见问题(写错一次就记住)

| 问题 | 现象 | 解决 |
|---|------|------|
| `mdCode` 拼错 | 列表白屏,接口 404 | 跟后端确认编码 |
| `customSetting` 改完没生效 | 文件没保存 / 后端没指向 | 看 ModuleUtils 加载 customJs 的日志 |
| `fieldList` 没声明 | 字段不显示 | 后端模型设计器里加显示列 |
| `customSetting` 写错位置 | 报"xxx is not a function" | 看 console.error 提示文件路径 |
| List 高度为 0 | 父级没设置高度 | 加 `fullHeight` 或父级 `height: 100%` |
| 修改后没刷新 | 缓存导致 | 改 `VUE_APP_OPEN_MODULE_STORAGE=0` 或 `Refresh_Module_Cache` |
| `this` 指向错 | 报错 undefined | 看 customSetting 写在 `methods` 还是 `data` |

更多调试技巧见 `frontend-module-page-debug`。

---

## 12. 一个完整例子:含 customSetting 的列表页

```vue
<!-- 业务页面 src/views/business/UserList.vue -->
<template>
    <div class="bd-page-list">
        <module-list-code
            ref="moduleListCode"
            :mdCode="'user_info'"
            fullHeight>
        </module-list-code>
    </div>
</template>
<script>
import ModuleListCode from '@/components/frame/Module/ModuleListCode'
export default {
    name: 'userInfoList',
    components: { [ModuleListCode.name]: ModuleListCode }
}
</script>
<style scoped>
.bd-page-list { height: 100%; }
</style>
```

```js
// public/moduleJs/user_info/list.js
import { Message } from 'element-ui'

export default {
    // 加一个"批量启用"按钮
    buttons: [
        {
            id: 'batchEnable',
            name: '批量启用',
            icon: 'el-icon-check',
            click: function (btn, scope) {
                const rows = scope.selection || []
                if (!rows.length) {
                    Message.warning('请先勾选数据')
                    return
                }
                // ...业务逻辑
            }
        }
    ],

    // "状态"列渲染成彩色徽章
    renderField: function (h, scope) {
        const map = { 0: { type: 'info', text: '禁用' }, 1: { type: 'success', text: '启用' } }
        const cfg = map[scope.row.status] || map[0]
        return h('el-tag', { type: cfg.type, size: 'mini' }, cfg.text)
    }
}
```

**完成。** 一个有"批量启用按钮 + 状态徽章"的列表页就出来了。

---

## 13. 验证 checklist

写完一个 Module 页面,过一遍这个清单:

- [ ] 路由跳转后能正常看到列表/表单
- [ ] `mdCode` 与后端一致
- [ ] 搜索栏能搜出数据
- [ ] 分页、排序正常
- [ ] 新增 / 编辑 / 查看 / 删除 全流程跑通
- [ ] 自定义按钮(如有)能点击并触发正确逻辑
- [ ] 字段联动(如有)在值变化时正确响应
- [ ] 没有 console.error
- [ ] 关闭浏览器开发者工具后(此项目会禁用),再开看一遍(测试 devtools-protection 的副作用)

---

## 14. 下一步去哪

### 列表页 customSetting(已拆分为子 skill,放在 `frontend-module-list/sub/`)

- **总览/索引/低频 key(插槽/分页/作用域)** → [frontend-module-list](../frontend-module-list/SKILL.md)
- **列渲染**(状态徽章/单元格点击/JSX) → [sub/render-field](../frontend-module-list/sub/render-field/SKILL.md)
- **按钮**(顶部/行/搜索栏按钮) → [sub/buttons](../frontend-module-list/sub/buttons/SKILL.md)
- **搜索栏交互**(搜索条件变化/显隐) → [sub/search](../frontend-module-list/sub/search/SKILL.md)
- **请求/数据流**(加签/参数/动态加列) → [sub/data-flow 索引](../frontend-module-list/sub/data-flow/SKILL.md)(再跳 [sub/request-flow](../frontend-module-list/sub/request-flow/SKILL.md) / [sub/response-flow](../frontend-module-list/sub/response-flow/SKILL.md) / [sub/module-config-mutation](../frontend-module-list/sub/module-config-mutation/SKILL.md))
- **选择 + 双击 + 多选** → [sub/selection-row](../frontend-module-list/sub/selection-row/SKILL.md)
- **表格外观**(冻结列/合计行/合并) → [sub/table-look](../frontend-module-list/sub/table-look/SKILL.md)
- **导入导出** → [sub/import-export](../frontend-module-list/sub/import-export/SKILL.md)

### 表单页 customSetting(已拆分为子 skill,放在 `frontend-module-edit/sub/`)

- **总览/索引/低频 key** → [frontend-module-edit](../frontend-module-edit/SKILL.md)
- **字段值变更/联动/属性注入** → [sub/fields](../frontend-module-edit/sub/fields/SKILL.md)
- **字段后追加 DOM / 整个表单重排版** → [sub/form-react](../frontend-module-edit/sub/form-react/SKILL.md)
- **校验规则 / 动态显隐/只读/必填** → [sub/validation](../frontend-module-edit/sub/validation/SKILL.md)
- **数据请求/响应/保存/按钮覆盖** → [sub/submit-flow](../frontend-module-edit/sub/submit-flow/SKILL.md)
- **布局(列数 / 渲染前) / 标题栏右侧** → [sub/layout](../frontend-module-edit/sub/layout/SKILL.md)
- **Tab 切换 / 关联子表(嵌套)** → [sub/tab-nav](../frontend-module-edit/sub/tab-nav/SKILL.md)

### 其它

- **页面出问题** → `frontend-module-page-debug`
- **新增字段类型** → `frontend-module-extend-field`
- **this 指向 = 具体文件 速查** → [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)(顶层,`Skill` 工具可加载)

---

## 附:相关文件路径速查

| 用途 | 路径 |
|------|------|
| 列表入口组件 | [src/components/frame/Module/ModuleListCode.vue](../../../../src/components/frame/Module/ModuleListCode.vue) |
| 列表核心 | [src/components/frame/Module/ModuleList/index.vue](../../../../src/components/frame/Module/ModuleList/index.vue) |
| 表单入口组件 | [src/components/frame/Module/ModuleEditCode.vue](../../../../src/components/frame/Module/ModuleEditCode.vue) |
| 表单核心 | [src/components/frame/Module/ModuleEdit/index.vue](../../../../src/components/frame/Module/ModuleEdit/index.vue) |
| 模型加载器 | [src/js/ModuleUtils.js](../../../../src/js/ModuleUtils.js) |
| 后端 API | [src/api/frame/module.js](../../../../src/api/frame/module.js) |
| 平台服务方法 | [src/service/module.js](../../../../src/service/module.js) |
| 字段类型注册 | [src/components/frame/Common/MForm/components/items/index.js](../../../../src/components/frame/Common/MForm/components/items/index.js) |
| 路由定义 | [src/router/modules/model.js](../../../../src/router/modules/model.js) |
| 标准 List 模板 | [src/views/module/stander/List.vue](../../../../src/views/module/stander/List.vue) |
| 标准 Edit 模板 | [src/views/module/stander/Edit.vue](../../../../src/views/module/stander/Edit.vue) |
| 默认按钮 | [src/components/frame/Module/BtnBaseFun/list.js](../../../../src/components/frame/Module/BtnBaseFun/list.js) |
| customSetting 加载路径 | `public/moduleJs/{mdCode}/{list|edit}.js` |
