---
name: frontend-module-this-reference
description: Module 平台 **this 指向 = 具体文件** 全局速查。**何时调用**:用户报 "this.xxx undefined"、"this 是哪个 Vue 实例"、"为什么我拿不到 this.$refs.moduleListCode"、"为什么 selectedRows 在按钮里读不到"、"为什么在 renderField 里 this 拿不到 moduleList" 这类 this 指向问题时触发。覆盖 8 个组件实例(moduleListCode/moduleList/mList/moduleEditCode/moduleEdit/moduleForm/mForm/弹窗作用域)的"简称 → 文件路径 → 组件 name → DevTools 验证"四维对照,跨 list/edit 全局通用。**何时不调用**:用户还没开始写 customSetting / 不知道 customSetting 是什么 → 走 frontend-module-quickstart;用户具体在改某个 key → 走 frontend-module-list 或 frontend-module-edit;遇到具体报错 → 走 frontend-module-page-debug。
---

# Module 平台 — this 指向 = 具体文件 全局速查

> customSetting 的所有 key(`valueChange` / `renderField` / `buttons[].click` 等)在不同场景下 `this` 指向**不同的 Vue 实例**——同一个 `this.$store`、同一个 `this.$refs.moduleListCode` 在不同实例下行为可能完全不一样。
>
> 本 skill 是**全局唯一的 this 指向查询入口**,跨 `frontend-module-list` / `frontend-module-edit` / 流程表单 / 树型表单 全通用。

---

## 0. 何时需要查这个速查

出现以下任一现象,先来这里查 `this` 是哪个实例:

| 现象 | 典型原因 |
|------|---------|
| `this.$refs.moduleListCode` 是 undefined | `this` 是 mList,不是 moduleListCode |
| `this.$store.state.user.userInfo` 是 undefined | `this` 是 mList,Vuex 没注入到这里(实际能读到,但用法不对) |
| `this.formData` 是 undefined | `this` 不是 moduleForm,formData 不在它身上 |
| `this.selectedRows` 一会儿有一会儿没有 | `this` 是不同时机,实例不同 |
| 按钮 click 里 `this` 拿不到 renderField 的引用 | `this` 是 moduleList,但 renderField 内 this 是 mList |
| 弹窗里 this 不对 | 流程/审批弹窗 this 是 `mainScope`,不是 moduleEdit |

---

## 1. 8 个组件实例速查总表 ⭐

> **核心速查**:业务方记不住时直接对照这一张表。

| 简称 | 完整文件路径 | 组件 `name` | DevTools 验证 | 常见用途 |
|------|------------|-------------|---------------|---------|
| **moduleListCode 实例** | [src/components/frame/Module/ModuleListCode.vue](../../../../src/components/frame/Module/ModuleListCode.vue) | `module-list-code` | `this.$options.name === 'module-list-code'` | 列表顶层入口;**仅 `afterModuleJSON` 在这一层**(模块配置加载完改字段) |
| **moduleList 实例** | [src/components/frame/Module/ModuleList/index.vue](../../../../src/components/frame/Module/ModuleList/index.vue) | `module-list` | `this.$options.name === 'module-list'` | 列表上层;`buttons[].click` / `searchConditionChange` / `dblClick` / 4 个插槽 / `dataUrl` / `columnFormat` / 全部 import-export key |
| **mList 实例** | [src/components/frame/Common/MList/index.vue](../../../../src/components/frame/Common/MList/index.vue) | `bd-table-list` | `this.$options.name === 'bd-table-list'` | 列表底层表格;`renderField.*.formatter/click/render` / `afterListJSON` / `afterListRender` / `paramsBeforeRequest` / `diySearch` / `selectionChange` / `showSummary`(函数) / `spanMerge`(函数) / `renderFieldHeader` |
| **moduleEditCode 实例** | [src/components/frame/Module/ModuleEditCode.vue](../../../../src/components/frame/Module/ModuleEditCode.vue) | `module-edit-code` | `this.$options.name === 'module-edit-code'` | 表单顶层入口;`dataUrl` / `valuePath` / `paramsBeforeRequest` / `afterEditJSON` / `afterModuleJSON`(Edit 版) |
| **moduleEdit 实例** | [src/components/frame/Module/ModuleEdit/index.vue](../../../../src/components/frame/Module/ModuleEdit/index.vue) | `module-edit` | `this.$options.name === 'module-edit'` | 表单上层;`buttons[].click` / `saveUrl` / `beforeModuleInitRender` / `tabClick` / `tabChange` / `beforeTabLeave` / `flowButtons` / `titleRightSlot` / `treeAjaxConfig` / `defaultParams`(树型) |
| **moduleForm 实例** | [src/components/frame/Module/ModuleForm/index.vue](../../../../src/components/frame/Module/ModuleForm/index.vue) | `module-form` | `this.$options.name === 'module-form'` | 表单字段;`valueChange` / `fieldChange` / `fieldCustom` / `beforeFieldChange` / `validateRule` / `beforeRender` / `appendDom` / `contentRender` / `renderField`(查看态) |
| **mForm / MForm 实例** | [src/components/frame/Common/MForm/index.vue](../../../../src/components/frame/Common/MForm/index.vue) | `bd-form` | `this.$options.name === 'bd-form'` | 表单最底层;`scopeSave`(子表单保存)/ `renderField` 查看态 formatter/click/render 实际挂载点 |
| **弹窗页面作用域** | (流程页"下一步"弹窗页面) | — | — | 仅 `beforeApproveRender`;通过 `this.mainScope` 拿父组件 |

---

## 2. 列表 3 层组件嵌套(this 在层之间如何流动)

```
List 入口
    ↓
┌────────────────────────────────────┐
│ ModuleListCode (name: module-list-code) │
│ - 入口层,仅 afterModuleJSON 在这层   │
└──────────────┬─────────────────────┘
               │ 传入 module 配置
               ↓
┌────────────────────────────────────┐
│ ModuleList (name: module-list)        │
│ - 多数按钮/搜索/请求/响应在这一层    │
└──────────────┬─────────────────────┘
               │ 传 column / data
               ↓
┌────────────────────────────────────┐
│ MList (name: bd-table-list)            │
│ - 列渲染 / DOM 操作 / 分页在这一层    │
└────────────────────────────────────┘
```

**为什么 this 这么碎?**:跨 3 层组件各管一段;**业务方在 customSetting 写的函数由框架在不同层用 `.call(this)` 调用**,this 就是当时所在层的实例。

---

## 3. 表单 4 层组件嵌套

```
Edit 入口
    ↓
┌──────────────────────────────────────────┐
│ ModuleEditCode (name: module-edit-code)   │
│ - 入口层: dataUrl/paramsBeforeRequest     │
│           afterEditJSON/afterModuleJSON   │
└──────────────┬───────────────────────────┘
               │ 传 formData / fieldList
               ↓
┌──────────────────────────────────────────┐
│ ModuleEdit (name: module-edit)              │
│ - 中间层: buttons/saveUrl/tab 切换/title  │
│            beforeModuleInitRender/flowButtons│
└──────────────┬───────────────────────────┘
               │ 传 formData
               ↓
┌──────────────────────────────────────────┐
│ ModuleForm (name: module-form)              │
│ - 字段层: valueChange/beforeFieldChange   │
│           validateRule/beforeRender       │
└──────────────┬───────────────────────────┘
               │ 传 value / fieldItem
               ↓
┌──────────────────────────────────────────┐
│ MForm (name: bd-form)                       │
│ - 最底层: 渲染字段 / scopeSave 子表单      │
└──────────────────────────────────────────┘
```

> 同一字段方法可能跨两层(如 `renderField` formatter 在 moduleForm 注册但调用点在 mForm),详见 §5。

---

## 4. 按 key 查 this 速查(全 customSetting 40+ key)

### 4.1 列表侧(22 个)

| key | this 指向 | 来源文件行号 |
|------|----------|------------|
| `afterModuleJSON` | **moduleListCode 实例** | [ModuleListCode.vue:117-119](../../../../src/components/frame/Module/ModuleListCode.vue#L117-L119) |
| `dataUrl`(函数) | **moduleList 实例** | [ModuleList/index.vue:450-451](../../../../src/components/frame/Module/ModuleList/index.vue#L450-L451) |
| `paramsBeforeRequest` | **mList 实例** | [ModuleList/index.vue:783-785](../../../../src/components/frame/Module/ModuleList/index.vue#L783-L785) |
| `afterListJSON` | **mList 实例** | [ModuleList/index.vue:814-817](../../../../src/components/frame/Module/ModuleList/index.vue#L814-L817) |
| `afterListRender` | **mList 实例** | [ModuleList/index.vue:836-838](../../../../src/components/frame/Module/ModuleList/index.vue#L836-L838) |
| `diySearch` | **mList 实例** | MList init 调用 |
| `searchConditionChange` | **moduleList 实例** | [ModuleList/index.vue:651-660](../../../../src/components/frame/Module/ModuleList/index.vue#L651-L660) |
| `dblClick` | **moduleList 实例** | [ModuleList/index.vue:1120-1126](../../../../src/components/frame/Module/ModuleList/index.vue#L1120-L1126) |
| `selectionChange` | **mList 实例** | [MList/index.vue:860-863](../../../../src/components/frame/Common/MList/index.vue#L860-L863) |
| `buttons[].click` | **moduleList 实例** | [ModuleList/index.vue:1156-1215](../../../../src/components/frame/Module/ModuleList/index.vue#L1156-L1215) `getBtnList` |
| `buttons[].isHide`(函数式) | **按钮对象 `btnObj`** ⚠️ | [module.js:273-276](../../../../src/service/module.js#L273-L276) `ShowStatus` |
| `beforeRowBtnRender` | **mList 实例** | [OperateBtnList.vue:80](../../../../src/components/frame/Common/MList/components/OperateBtnList.vue#L80) |
| `renderField.*.formatter` / `.click` / `.render` | **mList 实例** | [module.js](../../../../src/service/module.js) `getFormatterFieldObj` |
| `renderFieldHeader.*.formatter` / `.render` | **mList 实例** | 同上(表头) |
| `showSummary`(函数) | **mList 实例** | 表格组件合计行调用 |
| `spanMerge`(函数) | **mList 实例** | 表格组件渲染时调用 |
| `freezeColumnIndex` / `freezeColumnLastIndex` | **无 this**(纯静态配置) | [MList/index.vue:467-485](../../../../src/components/frame/Common/MList/index.vue#L467) `_fieldList` getter 里转 `fieldList[i].fixed`;不涉及 Vue 实例 |
| `columnFormat` | **moduleList 实例** | ModuleList `getColumnList` 内 |
| `listTopSlot` / `btnNextLineSlot` / `btnFixedRightSlot` / `searchFixedRightSlot` | **moduleList 实例** | ModuleList 插槽渲染 |
| `exportUrl` / `exportTitle` / `exportProps` / `importUrl` / `importTemplateUrl` / `importTitle` / `importKey` / `importProps`(函数式) | **moduleList 实例** | [module.js:677](../../../../src/service/module.js#L677) `Get_Import_And_Export_Prop.call(this, ...)` |
| `createFun` 内方法 | **mList 实例** | [ModuleList/index.vue](../../../../src/components/frame/Module/ModuleList/index.vue) `this[i] = newVal[i]` 注入 |
| `createListFun` 内方法 | **moduleList 实例** | 同上 |
| `treeAjaxConfig` / `defaultParams`(树型 list) | **moduleList 实例** | 树型 list 入口 |

### 4.2 表单侧(20 个)

| key | this 指向 | 来源文件行号 |
|------|----------|------------|
| `dataUrl` / `valuePath` / `paramsBeforeRequest` / `afterEditJSON` / `afterModuleJSON` | **moduleEditCode 实例** | [ModuleEditCode.vue](../../../../src/components/frame/Module/ModuleEditCode.vue) |
| `saveUrl` / `openBtnSaveAndAdd` / `beforeModuleInitRender` / `buttons[].click` | **moduleEdit 实例** | [ModuleEdit/index.vue](../../../../src/components/frame/Module/ModuleEdit/index.vue) |
| `valueChange[fieldName]` / `fieldChange` / `beforeFieldChange` / `fieldCustom` | **moduleForm 实例** | [ModuleForm/index.vue](../../../../src/components/frame/Module/ModuleForm/index.vue) |
| `validateRule` | **moduleForm 实例** | ModuleForm 校验钩子 |
| `beforeRender` | **moduleForm 实例** | ModuleForm 渲染前 |
| `appendDom` / `contentRender` | **moduleForm 实例** | ModuleForm 渲染 |
| `renderField`(查看态)formatter / click | **mForm 实例** ⚠️ 不是 moduleForm | [MForm/index.vue:679,691,654,666](../../../../src/components/frame/Common/MForm/index.vue#L679) `formatter.call(this, ...)` |
| `renderField`(查看态)render / appendRender | **mForm 实例** | 同上 |
| `tabClick` / `tabChange` / `beforeTabLeave` / `isChangeInfo` | **moduleEdit 实例** | ModuleEdit tab 切换 |
| `childTab` | 无 this(纯配置) | — |
| `scopeSave` | **mForm / MForm 实例**(子模块) | [MForm/index.vue](../../../../src/components/frame/Common/MForm/index.vue) |
| `flowButtons`(数组) | **moduleEdit 实例** | ModuleEdit 流程按钮 |
| `flowButtons`(函数) | **moduleEdit 实例**(return 时) | 同上 |
| `Save.call(this, ...)` 内的钩子 | **moduleEdit 实例** | [BtnBaseFun/flow-edit.js](../../../../src/components/frame/Module/BtnBaseFun/flow-edit.js) |
| `Submit.call(this, ...)` 内的钩子 | **moduleEdit 实例** | 同上 |
| `titleRightSlot` | **moduleEdit 实例** | ModuleEdit 标题栏 |
| `beforeApproveRender` | **弹窗页面作用域**(不是 moduleEdit) | 流程页"下一步"弹窗 |
| `treeAjaxConfig` / `defaultParams`(树型 list) | **moduleList 实例** | 树型 list 入口 |
| `addFormData`(树型 edit) | **moduleEdit 实例** | 树型 edit |

---

## 5. this 指向验证技巧

### 5.1 console.log 看组件 name

在 customSetting 任意函数第一行加:

```js
console.log('this is:', this.$options.name)
// 输出可能是 'module-list-code' / 'module-list' / 'bd-table-list' / 'module-edit-code' / 'module-edit' / 'module-form' / 'bd-form'
```

### 5.2 DevTools Elements 找组件

1. F12 → Elements 选中一个表格单元格 / 按钮 / 表单字段
2. 右下角 "Vue" 面板看组件层级(`<Root>` → `<App>` → `<ModuleListCode>` → `<ModuleList>` → `<MList>`)
3. 选中对应组件,顶部 `this` 就是当前实例

### 5.3 写一行代码判断 this 是不是预期实例

```js
// 期望是 moduleList:
console.assert(this.$options.name === 'module-list', 'this 不是 moduleList,实际是:' + this.$options.name)

// 期望是 mList:
console.assert(this.$options.name === 'bd-table-list', 'this 不是 mList,实际是:' + this.$options.name)
```

---

## 6. this 指向的 8 个易错点

| # | 易错点 | 现象 | 解决 |
|---|--------|------|------|
| 1 | 箭头函数丢 this | `buttons: [{ click: () => this.xxx() }]` 报 undefined | 用 `function` 而非箭头函数,this 自动指向 moduleList |
| 2 | `this.$refs.moduleListCode` undefined | 在 `renderField` 内访问 ref | `this` 是 mList,要么走 `createFun` 注入,要么用 `this.pushPage` |
| 3 | `this.selectedRows` 时有时无 | `selectionChange`(存,mList)和 `buttons[].click`(读,moduleList)实例不同 | 用 `createListFun` 注入到 moduleList 统一管理 |
| 4 | `this.formData` undefined | 期望是 moduleForm,实际是别的层 | 检查是不是在 `valueChange` 里写;`valueChange` 的 `this` 是 moduleForm |
| 5 | `isHide` 函数里 `row` undefined | `ShowStatus` 调用 `isHide` 时**不传参** | 不要在 `isHide` 里写 `row`,改用 `buttons` 函数形式配合 `getSelection()` |
| 6 | `isHide` 函数里 `this.$store` undefined | 函数 `this` 是 btnObj,不是 moduleList | 要读 Vuex 用 `import store from '@/store'`,或改用 `buttons` 函数形式 |
| 7 | 流程页 `this` 不是 moduleEdit | 弹窗作用域下 `this` 是弹窗页面 | 用 `this.mainScope` 拿真正的 moduleEdit |
| 8 | `afterModuleJSON` 内 `this.BASEURL` undefined | 误以为是 mList | `afterModuleJSON` 的 `this` 是 **moduleListCode** / **moduleEditCode**(顶层入口),其他 key 才是 moduleList |

---

## 7. 跨实例调用的 3 种正确姿势

### 7.1 从 mList 调到 moduleList / moduleListCode

```js
// 在 renderField 内(this 是 mList)想跳页面:
// ❌ this.$refs.moduleListCode  undefined
// ✅ 走 this.pushPage(框架方法,在每个实例都有)
this.pushPage({ path: 'xxx', title: 'xxx' })

// 想调 moduleList 暴露的方法:
// ❌ this.someListMethod
// ✅ 走 createFun 注入(在 mList 作用域可访问自己注册的)
```

### 7.2 从 moduleList 调到 mList

```js
// 在 buttons click 内(this 是 moduleList)想刷新表格:
// ✅ moduleList 自己有 listPageRef() / search() 方法
this.search()

// 想调 mList 的方法:
// ✅ 通过 listPageRef() 拿到 mList 实例
this.listPageRef().xxx()
```

### 7.3 从 moduleForm 调到 mForm(MForm)

```js
// 在 valueChange(formScope 是 mForm 实例)里:
// ✅ 直接通过 formScope.xxx 调用 mForm 的方法
formScope.setFieldValue('xxx', 'yyy')
formScope.validateField('xxx')
```

---

## 8. 与其他 skill 的关系

- 业务方具体写某个 key 时 → 跳到 `frontend-module-list` / `frontend-module-edit` 的对应 sub-skill
- 每个 sub-skill 的"关键事实"小节里都有**简化的 this 速查**(如 [module-list-table-look §9.3](../frontend-module-list/sub/table-look/SKILL.md))指向本 skill
- 业务方报"this 指向错" bug 时 → 跳 [frontend-module-page-debug](../frontend-module-page-debug/SKILL.md) §5.2 §9.1
- 新增字段类型时 this 是组件实例 → [frontend-module-extend-field](../frontend-module-extend-field/SKILL.md)

---

## 9. 修订记录

- **2026-07-03**:§4.1 列表侧新增 `freezeColumnIndex` / `freezeColumnLastIndex` 行(标注"无 this,纯静态配置")——补齐 table-look 体系下所有冻结相关 key
- **2026-07-02**:从各 sub-skill 抽出独立的 this 指向 = 具体文件速查 skill(本文件);解决了"this 是 mList 实例"等表述无法直接定位到框架代码文件的问题