---
name: frontend-module-list
description: 八斗 Module 平台列表页 customSetting **总览/索引**。**何时调用**:用户想做列表页定制,但不确定用哪个 key、想看完整 key 列表、想查 this 指向或低频 key(插槽/分页/作用域注入)、或在多个 key 之间做技术选型。**何时不调用**:① 用户已明确要改某个具体高频 key(如 renderField/buttons/data-flow)→ 跳 sub/ 下的对应子 skill;② 用户还在问"什么是 customSetting"或首次接触 Module 平台 → 走 frontend-module-quickstart;③ 用户问的是表单(Edit/Add/View) → 走 frontend-module-edit;④ 通用 Vue/Element UI 问题 → 与 Module 无关。
---

# Module 列表 customSetting 总览

> 本 skill 只做**索引和低频内容**。**40+ 个 key** 中**高频 6 组**已拆为子 skill(见下),本 skill 只留:
> - ⚠️ 0. 动手前先确认 JS 路径
> - `this` 指向速查(跨所有 key 通用)
> - 完整 40+ key 列表(一行说明 + 链接)
> - 低频 key 一行用法(分页/作用域注入/已废弃)
> - 关键事实 + List vs Edit 差异 + 调试 + 常见问题

---

## ⚠️ 加载子 skill 的正确方式(必读,工具调用相关)

本 skill 的 7 个子 skill(列在 §2 / §11)都是**文件**而不是可被 `Skill` 工具调用的注册项。系统启动时**只注册了顶层 skill**(`frontend-module-list` / `frontend-module-edit` 等),子 skill 需要**用 `Read` 工具直接打开文件**才能加载。

| 操作 | 正确 | 错误 |
|------|------|------|
| 加载本 skill(总览) | `Skill({ skill: "frontend-module-list" })` | — |
| 加载子 skill(列渲染) | `Read({ file_path: ".../sub/render-field/SKILL.md" })` | `Skill({ skill: "frontend-module-list/sub/render-field" })` ❌ |
| 加载子 skill(选择+双击) | `Read({ file_path: ".../sub/selection-row/SKILL.md" })` | `Skill({ skill: "...sub/selection-row" })` ❌ |

**为什么**: `Skill` 工具的 `skill` 参数只认 SKILL.md frontmatter 里的 `name:` 字段(且**仅顶层**);`frontend-module-list/sub/xxx` 不是任何文件的 name,会报 `Unknown skill`。

**`name:` 字段速查**(子 skill 文件 frontmatter 第一行)——加载时按这个 name 找文件:

| 子 skill | 实际文件 | 文件名(name) |
|----------|----------|----------------|
| 列渲染 | [sub/render-field/SKILL.md](sub/render-field/SKILL.md) | `module-list-render-field` |
| 按钮 | [sub/buttons/SKILL.md](sub/buttons/SKILL.md) | `module-list-buttons` |
| 搜索栏 | [sub/search/SKILL.md](sub/search/SKILL.md) | `module-list-search` |
| **数据流**(4 个,**索引** + 3 sub-skill) | [sub/data-flow/SKILL.md](sub/data-flow/SKILL.md) | `module-list-data-flow`(索引) |
| ↳ 请求配置 | [sub/request-flow/SKILL.md](sub/request-flow/SKILL.md) | `module-list-request-flow` |
| ↳ 响应处理 | [sub/response-flow/SKILL.md](sub/response-flow/SKILL.md) | `module-list-response-flow` |
| ↳ 模型配置变更 | [sub/module-config-mutation/SKILL.md](sub/module-config-mutation/SKILL.md) | `module-list-module-config-mutation` |
| 选择+双击 | [sub/selection-row/SKILL.md](sub/selection-row/SKILL.md) | `module-list-selection-row` |
| 表格外观 | [sub/table-look/SKILL.md](sub/table-look/SKILL.md) | `module-list-table-look` |
| 导入导出 | [sub/import-export/SKILL.md](sub/import-export/SKILL.md) | `module-list-import-export` |
| **树模型列表**(左树+右表) | [../frontend-module-tree-list/SKILL.md](../frontend-module-tree-list/SKILL.md) | `frontend-module-tree-list` |

> ⚠️ 2026-06-24 起,`data-flow` 拆成 4 份(索引 + request + response + model-config)。**用户已明确要改某个高频 key 时,跳到对应 sub-skill**;不确定时跳索引。

> 💡 读完后,子 skill 里的内容(代码示例、签名、this 指向)和顶层一样可直接用。

---

## ⚠️ 0. 动手前先确认 JS 路径(必读)

**List 和 Edit 的 customSetting 是两个完全不同的文件**,而且项目里 `mdCode` 和 JS 路径并不是 1:1 写死的——后端模型设计器可以指向任意路径(可能是多级目录,比如 `public/moduleJs/business/text/xxx_list.js`)。

在写任何 customSetting 代码前,**先用 AskUserQuestion 反问清楚下面 4 项**(建议一次性问完):

| 询问项 | 为什么要问 |
|--------|-----------|
| **mdCode**(模型编码) | 决定 `public/moduleJs/{mdCode}/` 根目录 |
| **list 还是 edit** | 决定改的是 `list.js` 还是 `edit.js`——结构和可用 key 都不同 |
| **完整路径** | 一些模型有自定义目录(如 `business/text/xxx`),不是默认 `{mdCode}/list.js` |
| **是否已配置 customJs 路径** | 如果后端没指向,需要先去模型设计器配上才能生效 |

**推荐问法模板**(合并成一个问题):

> "请确认下:
> 1. 这次改的是哪个 `mdCode`?
> 2. 是 **list**(列表页)还是 **edit**(表单页)?
> 3. 当前 `customSetting` JS 文件的**完整路径**是?(如果没配过,我先帮你检查模型配置)"

拿到回答后:
- **先 Read 现有文件**(`Read ${customJsPath}`),别直接覆盖
- 如果文件**不存在**或**没配置**:
  1. 提示用户去后端模型设计器,把 `customJs` 字段指向一个新文件(参考路径见下表)
  2. 或落**默认业务路径** `public/moduleJs/business/{mdCode}/list.js`(由生成器自动写入 `md_module.LIST_JS='/business/{mdCode}/list.js'`)
  2. 或临时放在一个**默认路径** `public/moduleJs/{mdCode}/list.js`,**前提是后端能 require 到这个路径**
- 如果文件已存在,**先备份原内容**,再增量修改——customSetting 是大对象,直接 `export default { ... }` 覆盖会把原有配置清掉

> 💡 **什么时候可以"自信地不必要求问路径"**:
> - 用户明确给了 `mdCode` + `list|edit` + 完整路径
> - 用户在描述里**带上了文件位置**(如"改 `user_info/list.js` 里的 `renderField`")
>
> 其余场景都建议先问。

---

## 1. 文件落点与默认路径

| 用途 | 路径 |
|------|------|
| List customSetting(业务方默认) | `public/moduleJs/business/{mdCode}/list.js` |
| List customSetting(用户显式指定时) | 任意路径,如 `public/moduleJs/frame/...` 或 `business/text/xxx_list.js` |
| 入口组件 | [src/components/frame/Module/ModuleListCode.vue](../../../src/components/frame/Module/ModuleListCode.vue) |
| 列表核心 | [src/components/frame/Module/ModuleList/index.vue](../../../src/components/frame/Module/ModuleList/index.vue) |
| 底层表格 | [src/components/frame/Common/MList/index.vue](../../../src/components/frame/Common/MList/index.vue) |
| 平台服务 | [src/service/module.js](../../../src/service/module.js) |

> 业务模块默认落点已由 `backend-module-generator` 改为 `public/moduleJs/business/{mdCode}/list.js`(写入 `md_module.LIST_JS='/business/{mdCode}/list.js'`,前端 `ModuleUtils` 拼接 `public/moduleJs` 前缀)。仅在用户**显式**指定其他目录时才覆盖。 |

> `public/moduleJs/{mdCode}/list.js` 由后端模型设计器指向,前端通过 `ModuleUtils.js` 动态 `require`。
> 路径相对项目根。

---

## 2. 7 个子 skill 跳转(高频)

> **加载方式**:表中链接是**文件路径**,需要用 `Read` 工具打开(见开篇「加载子 skill 的正确方式」),不要用 `Skill` 工具带路径调用。

| 场景 | 跳转到 |
|------|--------|
| **列渲染**(状态徽章/单元格点击/JSX 按钮组、**字典字段必须用 `xxxDesc`**)| [sub/render-field](sub/render-field/SKILL.md) |
| **按钮**(顶部/行/搜索栏按钮、按钮子属性、按钮样式、按钮过滤、事件插入点、**行按钮获取当前行 getSelection**) | [sub/buttons](sub/buttons/SKILL.md) |
| **搜索栏交互**(搜索条件变化、级联清空、动态 options、显隐、**按角色显隐/动态加减搜索项**) | [sub/search](sub/search/SKILL.md) |
| **主动设置/修改搜索项的值**(运行时改值、初始化默认值、按钮触发、**Date 3 种模式 / 各类型值格式字典**) | **顶层独立** [frontend-module-list-search-set-value](../frontend-module-list-search-set-value/SKILL.md) |
| **请求/数据流**(自定义 URL、加签、数据改写、加载后处理) | [sub/data-flow](sub/data-flow/SKILL.md) |
| **选择 + 双击 + 多选** | [sub/selection-row](sub/selection-row/SKILL.md) |
| **表格外观**(冻结列/合计行/行列合并/表头) | [sub/table-look](sub/table-look/SKILL.md) |
| **导入导出** | [sub/import-export](sub/import-export/SKILL.md) |

---

## 3. `this` 指向速查(写 customSetting 最易出错的地方,**跨所有 key 通用**)

> 💡 完整 22 个 key 全量速查 + 具体文件路径见 [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md) §4.1。本节只列**最高频 8 个 key**(避免每个 key 都重复查)。

| 上下文 | `this` 指向 | 备注 |
|--------|------------|------|
| `afterModuleJSON`(模块配置加载后) | **moduleListCode 实例** | ⚠️ 唯一在入口层,在 `ModuleListCode.vue` |
| `dataUrl` / `buttons[].click` / `dblClick` / `searchConditionChange` / `createListFun` 内方法 | **moduleList 实例** | 上层列表;`this.getSelection()` / `this.search()` 都在这 |
| `paramsBeforeRequest` / `afterListJSON` / `afterListRender` / `selectionChange` / `createFun` 内方法 | **mList 实例** | 多数回调实际是这一层;`this.temp_data` / `this.pushPage` |
| `renderField.*.formatter` / `click` / `render` | **mList 实例** | 同上,**`this.$refs.moduleListCode` 拿不到**,必须走 `pushPage` |
| `exportUrl` / `importUrl` 等所有 import-export key | **moduleList 实例** | `ExportData`/`ImportData` 统一调用 |
| `buttons[].isHide`(函数式) | **按钮对象 `btnObj`** ⚠️ | 不是 moduleList!要读 Vuex 用 `import store from '@/store'` |
| `beforeRowBtnRender` | **mList 实例** | 由 `this.beforeRender.call(this.listScope, ...)` 注入 |
| `showSummary`(函数) / `spanMerge`(函数) / `renderFieldHeader.*` | **mList 实例** | 与 `renderField` 一致 |
| `freezeColumnIndex` / `freezeColumnLastIndex` | **无 this**(纯静态配置) | 直接写数字,框架在 `_fieldList` getter 里转 `fixed` 属性;详见 [table-look §2](sub/table-look/SKILL.md#2-冻结列) |

**为什么这一节最重要**:业务方最容易在 `renderField` 的 `click` 里写 `this.$refs.moduleListCode.xxx()`——但 `this` 是 mList 实例,根本拿不到 ref。**见第 8 节"常见问题"**。

---

## 4. 完整 40+ key 列表(索引)

> 摘自 `ModuleList/index.vue` 第 971-1098 行 `updateCustomSetting`,按"使用频次"排序。
> **⭐⭐⭐⭐⭐** 高频,本 skill 跳转;**⭐⭐⭐** 中频,跳转;**⭐** 低频,本 skill 简述。

| key | 类型 | 用途 | 频次 | 跳转到 |
|------|------|------|------|--------|
| `renderField` | `Object` | 列渲染(formatter/click/render) | ⭐⭐⭐⭐⭐ | `module-list-render-field` |
| `buttons` | `Array\|Function` | 顶部/行按钮(11 个子属性) | ⭐⭐⭐⭐⭐ | `module-list-buttons` |
| `paramsBeforeRequest` | `Function` | 请求前改参数 | ⭐⭐⭐⭐⭐ | `module-list-request-flow` |
| `afterListJSON` | `Function` | 数据返回后处理 | ⭐⭐⭐⭐ | `module-list-response-flow` |
| `afterModuleJSON` | `Function` | 模型配置加载后处理 | ⭐⭐⭐⭐ | `module-list-module-config-mutation` |
| `searchConditionChange` | `Function` | 搜索条件变化监听 | ⭐⭐⭐⭐ | `module-list-search` |
| `dataUrl` | `Function\|String` | 自定义列表请求 URL | ⭐⭐⭐ | `module-list-request-flow` |
| `searchBtns` | `Array` | 自定义搜索栏按钮 | ⭐⭐⭐ | `module-list-buttons` |
| `dblClick` | `Function` | 行双击事件 | ⭐⭐⭐ | `module-list-selection-row` |
| `selectionChange` | `Function` | 选择项变化 | ⭐⭐⭐ | `module-list-selection-row` |
| `renderFieldHeader` | `Object` | 自定义表头 | ⭐⭐ | `module-list-table-look` |
| `multiple` | `Boolean` | 是否支持多选 | ⭐⭐ | `module-list-selection-row` |
| `hideSearch` | `Boolean` | 隐藏整个搜索区 | ⭐⭐ | `module-list-search` |
| `hideSearchFilter` | `Boolean` | 隐藏搜索过滤器(预设条件) | ⭐⭐ | `module-list-search` |
| `diySearch` | `Function` | 自定义搜索(替代默认请求) | ⭐⭐ | `module-list-request-flow` |
| `afterListRender` | `Function` | 列表 DOM 渲染后 | ⭐⭐ | `module-list-response-flow` |
| `createFun` | `Object` | 注入 mList 作用域的函数 | ⭐⭐ | 本 skill §5 |
| `createListFun` | `Object` | 注入 moduleList 作用域的函数 | ⭐⭐ | 本 skill §5 |
| `exportUrl` | `String\|Function` | 导出地址 | ⭐⭐ | `module-list-import-export` |
| `exportTitle` | `String\|Function` | 导出标题 | ⭐ | `module-list-import-export` |
| `exportProps` | `Object\|Function` | 导出配置 | ⭐ | `module-list-import-export` |
| `exportDefined` | `String` | 导出禁用字段(逗号分隔) | ⭐ | `module-list-import-export` |
| `importUrl` | `String\|Function` | 导入地址 | ⭐ | `module-list-import-export` |
| `importTemplateUrl` | `String\|Function` | 导入模版下载地址 | ⭐ | `module-list-import-export` |
| `importTitle` | `String\|Function` | 导入标题 | ⭐ | `module-list-import-export` |
| `importKey` | `Object\|Function` | 导入额外参数 | ⭐ | `module-list-import-export` |
| `importProps` | `Object\|Function` | 导入配置 | ⭐ | `module-list-import-export` |
| `freezeColumnIndex` | `Number` | 前置冻结列数(序号列不计入) | ⭐ | `module-list-table-look` |
| `freezeColumnLastIndex` | `Number` | 后置冻结列数 | ⭐ | `module-list-table-look` |
| `showSummary` | `Boolean\|String\|Function` | 合计行 | ⭐ | `module-list-table-look` |
| `columnFormat` | `Function` | 改表头 | ⭐ | `module-list-table-look` |
| `spanMerge` | `Function\|Object` | 行列合并 | ⭐ | `module-list-table-look` |
| `beforeRowBtnRender` | `Function` | 行按钮渲染前筛选 | ⭐ | `module-list-buttons` |
| `colBtnType` | `String` | 行按钮样式 | ⭐ | `module-list-buttons` |
| `isUsePagination` | `Boolean` | 是否启用分页 | ⭐ | `module-list-table-look` |
| `isShowPagination` | `Boolean` | 是否显示分页(不关功能) | ⭐ | `module-list-table-look` |
| `paginationInfo` | `Object` | 自定义分页参数 | ⭐ | `module-list-table-look` |
| `listTopSlot` | `Function` | 搜索框下/列表顶部插槽 | ⭐ | `module-list-table-look` |
| `btnNextLineSlot` | `Function` | 按钮区下方插槽 | ⭐ | `module-list-table-look` |
| `searchFixedRightSlot` | `Function` | 搜索区右侧固定插槽 | ⭐ | `module-list-table-look` |
| `btnFixedRightSlot` | `Function` | 按钮区右侧固定插槽 | ⭐ | `module-list-table-look` |
| `renderColumn` | `Object` | **【旧,不推荐】** 等同 `renderField` | ⚠️ | `module-list-render-field` |
| `exportDialogTitle` | `String` | **【旧,即将废弃】** 导出弹窗标题 | ⚠️ | `module-list-import-export` |

**`buttons[].xxx` 子属性(11 个)** → 详见 [buttons §3](sub/buttons/SKILL.md#3-button-子属性11-个--必读)

---

## 5. 低频 key 一行用法(无需子 skill)

### 5.1 作用域注入:`createFun` / `createListFun`

```js
// 注入到 mList(底层表格)作用域,供 renderField.*.render 内 this.xxx() 调用
createFun: {
    editFun () { /* this 指向 mList */ }
},
// 注入到 moduleList(上层列表)作用域,供 buttons/搜索栏内 this.xxx() 调用
createListFun: {
    handleExport () { /* this 指向 moduleList */ }
}
```

> 详细 this 差异见 §3。

### 5.2 分页控制(2 个 key)

```js
isUsePagination: false,    // 不启用分页(单次返回所有数据)
isShowPagination: false,   // 隐藏分页 UI(但功能还在,数据全量)
paginationInfo: {          // 自定义分页
    sizes: [10, 20, 50],
    size: 10
}
```

> 详见 [table-look §7](sub/table-look/SKILL.md#7-分页控制3-个-key)。

### 5.3 4 个插槽

```js
listTopSlot () { return <div>列表顶部,搜索框下方</div> },
btnNextLineSlot () { return <el-alert title="提示" /> },  // 按钮区下方
searchFixedRightSlot () { return <el-button>高级搜索</el-button> },  // 搜索区右侧固定位
btnFixedRightSlot () { return <el-button type="text">帮助</el-button> }  // 按钮区右侧固定位
```

> 详见 [table-look §8](sub/table-look/SKILL.md#8-4-个插槽返回-jsxthis-是-modulelist)。
> 4 个插槽**刷新方法**:`this.getXxxSlot()`(在 moduleList 作用域)。

### 5.4 已废弃(别再用)

```js
renderColumn: { ... }       // ⚠️ 改用 renderField
exportDialogTitle: '...'    // ⚠️ 改用 exportTitle
```

---

## 6. 关键事实与最佳实践

### 6.1 render 优先级最高

`renderField.*.render > click > formatter`,只生效一个。

### 6.2 三个函数必须 return

| 函数 | 不 return 后果 |
|------|---------------|
| `afterListJSON` | 列表无数据 |
| `afterModuleJSON` | 模型配置丢失(后续渲染异常) |
| `dataUrl` | 自定义 URL 不生效 |
| `showSummary`(函数形式) | 合计行无内容 |

### 6.3 操作列必须阻止冒泡

```js
nativeOn-click={(e) => {
    this.editFun()
    e.stopPropagation()  // 避免点了按钮顺便勾选整行
}}
```

### 6.4 改完 list.js 不生效?

- customSetting 是**运行时 require**,保存即生效
- 浏览器**硬刷新**一次(Ctrl+Shift+R)
- 清缓存:`localStorage.clear()` + `sessionStorage.clear()`,或临时把 `.env` 的 `VUE_APP_OPEN_MODULE_STORAGE` 设为 0

---

## 7. List vs Edit 关键差异

| key/特性 | List 独有 | Edit 独有 |
|----------|----------|----------|
| `renderField` | ✅ 表格列 | ❌(Edit 用 `render`,无字段级 click) |
| `renderFieldHeader` | ✅ | ❌ |
| `buttons` | 顶部 + 行按钮 | 表单内按钮 |
| `showSummary` / `spanMerge` / `dblClick` / `freezeColumnIndex` / `selectionChange` / `exportUrl` / `importUrl` | ✅ | ❌ |
| `afterListJSON` | ✅ | ❌(对应 `afterEditJSON`) |
| `dataUrl` | 列表请求 | 详情请求(同名不同签名) |
| `createFun` / `createListFun` | 注入 mList / moduleList | 注入 MForm / moduleEdit |
| ❌ | - | `onChange`(字段值变更) / `rules`(动态校验) / `beforeSave` / `afterSave` |

> 业务方做**树模型(左树+右表)列表**的定制 → 独立 skill [frontend-module-tree-list](../frontend-module-tree-list/SKILL.md)(讲路由差异 + 树专属 3 个 key + this.$attrs 特殊属性)
> 业务方在**普通列表里展示树形数据(行展开嵌套)** → 独立 skill [frontend-module-tree-table](../frontend-module-tree-table/SKILL.md)(讲 el-table 原生树形属性 + `elseTableAttrs` 透传机制 + 嵌套/扁平/懒加载 3 种数据模式)
> 👉 **表单(Edit)页面的 customSetting 见 `frontend-module-edit` skill**。

---

## 8. 常见问题(写错一次就记住)

| 问题 | 现象 | 解决 |
|---|------|------|
| `this.$refs.moduleListCode` undefined | 在 `renderField` 内访问 ref | `renderField` 内 `this` 是 mList,不是 moduleListCode |
| `afterListJSON` 忘了 return | 列表无数据 | 必须 return 处理后的数组 |
| `render` 写成了 `template` | 不生效 | renderField 用 `render`,不是 template |
| 按钮 click 报"undefined is not a function" | 用了箭头函数 | `buttons[].click` 用 `function`,这样 `this` 才指向 moduleList |
| JSX 写 `<span></span>` 报错 | 用了字符串引号 | 必须裸标签,不能 `'<span>'` |
| 操作列按钮点了顺便勾选整行 | 没阻止冒泡 | 加 `e.stopPropagation()` |
| 改完 list.js 不生效 | 缓存 | 保存即可,运行时 require;硬刷新(Ctrl+Shift+R)更稳 |
| `fieldList` 在 `afterModuleJSON` 里没 push 上 | 没 return | 必须 `return module` |
| 操作列的 `editFun` 报 undefined | 没在 `createFun` 里注册 | 操作列引用的函数要在 `createFun` 里定义 |
| 行按钮的 `click` 里访问 `this.selectedRows` | undefined | `this` 是 moduleList,但 selectedRows 不一定在那;用 `selectionChange` 存到正确作用域 |
| 字典字段配成原名(`status` 不是 `statusDesc`) | `Number("在售")=NaN`,逻辑全错 | 字典字段必须用 `xxxDesc`,cellValue 是中文,用 `row.xxx` 拿原值(见 §6.4) |
| 普通字段瞎加 `Desc`(`userNameDesc`) | 整列空白,框架不会生成这个字段 | 先判断字段是不是字典(Network 看有没有 `xxxDesc` 字段),别无脑加 Desc |

---

## 9. 调试技巧

### 9.1 打印 customSetting 实际生效情况

```js
// 在 list.js 任意函数内
console.log('=== customSetting 加载完成 ===', {
    renderField: !!this.diy_renderField,
    buttons: this.diy_buttons,
    this: this.$options.name  // 看看 this 指向谁
})
```

### 9.2 临时关闭 customSetting

```js
// 在 ModuleListCode 父组件层面覆盖 props
<module-list-code :mdCode="mdCode" :customSetting="{}" />
```

### 9.3 报"xxx is not a function"

- 先看 console.error 提示的**文件路径行号**
- 90% 是 `renderField` 里 `formatter` 写成了 `render`(或反之)
- 10% 是 `this` 指向错位,需要 `let _this = this` 缓存

### 9.4 字段不显示

| 现象 | 排查 |
|------|------|
| 整列没出来 | `fieldList` 里没声明该字段(去后端模型设计器加) |
| 列出来了但内容空 | `renderField.字段名` 写错了(字段名要严格匹配) |
| 内容是 `[object Object]` | 用了 `render` 但 return 错了(必须是 VNode/JSX) |

---

## 10. 验证 checklist

写完一个列表 customSetting,过一遍这个清单:

- [ ] 列表能正常打开
- [ ] 自定义按钮能正确出现(且没把默认按钮干掉)
- [ ] 状态徽章/格式化列能正常渲染
- [ ] 操作列按钮能点击且**不勾选整行**(阻止冒泡)
- [ ] 自定义按钮的回调里 `this` 能拿到 moduleList 实例
- [ ] `paramsBeforeRequest` 改的参数在 Network 里能看到
- [ ] `afterListJSON` 没破坏列表数据
- [ ] 导出/导入(如有)能弹出正确标题
- [ ] `searchConditionChange` 在条件变化时正确响应
- [ ] console 无 error

---

## 11. 下一步去哪

> **加载方式**:下列子 skill 都是**文件**,需用 `Read` 工具按下面**文件路径**打开(详见开篇「加载子 skill 的正确方式」)。括号内为 `name:` 字段,供你确认文件用,**不是** `Skill` 工具的入参。

- **列渲染** → `sub/render-field/SKILL.md` (`module-list-render-field`)
- **按钮** → `sub/buttons/SKILL.md` (`module-list-buttons`)
- **搜索栏交互** → `sub/search/SKILL.md` (`module-list-search`)
- **主动设置/修改搜索项的值**(运行时改值、初始化默认值、Date 3 种模式、值格式字典) → `frontend-module-list-search-set-value`(顶层,可直接 `Skill` 工具加载)
- **请求/数据流**(自定义 URL / 方法 / 加签 / 响应处理 / 模型配置变更) → 看 [sub/data-flow/SKILL.md](sub/data-flow/SKILL.md) 索引跳 sub-skill:· 请求配置(URL/方法/参数)→ [request-flow](sub/request-flow/SKILL.md) · 响应处理 → [response-flow](sub/response-flow/SKILL.md) · 模型配置变更 → [module-config-mutation](sub/module-config-mutation/SKILL.md) (`module-list-data-flow`)
- **选择 + 双击** → `sub/selection-row/SKILL.md` (`module-list-selection-row`)
- **表格外观** → `sub/table-look/SKILL.md` (`module-list-table-look`)
- **导入导出** → `sub/import-export/SKILL.md` (`module-list-import-export`)
- **写表单页定制** → `frontend-module-edit`(顶层,可直接 `Skill` 工具加载)
- **写树模型列表定制**(左树+右表) → `frontend-module-tree-list`(顶层,讲路由/树专属 3 key/this.$attrs 特殊属性)
- **页面出问题** → `frontend-module-page-debug`
- **新增字段类型** → `frontend-module-extend-field`
- **this 指向 = 具体文件 速查** → [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)(顶层,可直接 `Skill` 工具加载)
