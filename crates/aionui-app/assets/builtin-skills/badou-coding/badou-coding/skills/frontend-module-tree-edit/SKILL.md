---
name: frontend-module-tree-edit
description: 八斗 Module 平台**树模型编辑/查看页** customSetting 完整指南。**何时调用**:用户做树模型(左树+右表单)的编辑页/查看页定制,需要知道树专属的 1 个 key(`addFormData` 作函数)、与普通编辑的 3 大差异(路由/saveUrl/addFormData 函数化)、接收的 3 个 query 参数(`addFormData`/`backParams`/`currentTreeNodeData`)、保存后如何刷新左侧树、或跳转树编辑页的路径。**何时不调用**:① 用户只是普通编辑(无树)定制 → 走 `frontend-module-edit`;② 用户做树列表(左树+右表) → 走 `frontend-module-tree-list`;③ 用户首次接触 Module 平台 → 走 `frontend-module-quickstart`;④ 通用 Vue/Element UI 问题。
---

# Module 树模型编辑 customSetting

> 树模型编辑 = 左侧树(ModuleListTree)+ 右侧表单(ModuleEditTree),见 [views/module/tree/Edit.vue](../../../src/views/module/tree/Edit.vue) 与 [src/components/frame/Module/ModuleEditTree/index.vue](../../../src/components/frame/Module/ModuleEditTree/index.vue)。
>
> **核心原则**:右侧表单的所有 customSetting **与普通编辑完全一致**(`afterEditJSON`/`valueChange`/`validateRule`/`beforeRender`/`saveUrl` 等都是同一份 `edit.js`);只在**入口路由**和**1 个树专属 key(`addFormData` 作函数)** 上有差异。
>
> 本 skill 专门讲差异点,共有的 30+ key(字段联动/校验/数据流/布局/按钮/保存流程)**直接复用 `frontend-module-edit` 的 8 个 sub-skill**。

---

## ⚠️ 0. 动手前先确认 JS 路径(必读)

**树模型编辑的 customSetting JS 文件** 与普通编辑**是同一个**——同样是 `public/moduleJs/{mdCode}/edit.js`(或业务方自定义子目录)。后端模型设计器上配置的 `customJs` 指向同一个文件,**不需要**额外配置。

唯一要确认的是入口视图文件(决定路由跳到哪儿):

| 入口视图 | 路由 | 后端菜单 URL 应配 |
|----------|------|---------------------|
| 普通列表 | `/module/stander/list/:mdCode/:symbol` | `/module/stander/list/{mdCode}/{symbol}` |
| **树模型列表** | `/module/tree/list/:mdCode/:symbol` | `/module/tree/list/{mdCode}/{symbol}` |
| 普通编辑 | `/module/stander/:editStyle/:mdCode/:id` | `/module/stander/{table/...}/{mdCode}/{id}` |
| **树模型编辑** | `/module/tree/edit/:mdCode/:id` | `/module/tree/edit/{mdCode}/{id}` |

> **关键事实**:业务方**改的是同一个 `edit.js`**。同一个 `mdCode`,**入口视图可以是普通编辑,也可以是树模型编辑**——后端菜单配置决定哪个视图生效。
> 决定"用哪个视图"的关键是**后端菜单的 URL 路径**,**不是** JS 文件。

具体确认 4 项(同 [frontend-module-list §0](frontend-module-list/SKILL.md#0-动手前先确认-js-路径必读)):

1. `mdCode`
2. **入口视图**:普通编辑(`stander/edit`) 还是 树模型(`tree/edit`)
3. JS 完整路径
4. 后端是否已配 `customJs`

---

## 1. 路由 / 入口组件 / 加载流程

### 1.1 路由对比

| 视图 | path | component |
|------|------|-----------|
| 普通编辑 | `module/stander/:editStyle/:mdCode/:id` | `views/module/stander/Edit.vue` |
| **树模型编辑** | `module/tree/edit/:mdCode/:id` | `views/module/tree/Edit.vue` |

> 路由定义见 [src/router/modules/model.js](../../../src/router/modules/model.js) 第 25-41 行。
> **关键差异**:树模型编辑路由**没有 `:editStyle` 参数**——`editStyle` 从 query 里读,只有 `edit` 才走真正的编辑,其他都视为表格视图。

### 1.2 入口组件关系

```
<views/module/tree/Edit.vue>           (本文件)
   ↓ 解析路由 params/query + 3 个特殊 query 参数
   ↓ mdCode / detailId / editStyle / addFormData / backParams / currentTreeNodeData
<module-edit-tree>                     (src/components/frame/Module/ModuleEditTree/index.vue)
   ├─ watch mdCode → ModuleUtils.editModuleCfg/viewModuleCfg(mdCode)
   │     ↓
   │  合并 customSetting + $attrs.addFormData
   │     ↓
   │  调 updateCustomSetting(merged)
   │     ↓ (解构 addFormData 保存为 diy_addFormData)
   │
   └─ <module-edit>  ←── 完全复用普通编辑组件 ──
         │
         └─ <module-form> → customSetting 在这里被消费
```

> [!IMPORTANT]
> **`module-edit-tree` 本身不直接消费 customSetting**。它只做 2 件事:
> 1. 根据 `mdCode` 拉模型配置(`editModuleCfg` 或 `viewModuleCfg`)
> 2. 解构 `addFormData`(作为函数,见 §3)存为 `diy_addFormData`,在渲染表单时调用
>
> 其余 30+ key 全部**通过 `_$attrs` 透传给内部的 `module-edit`**,由 [ModuleEdit/index.vue](../../../src/components/frame/Module/ModuleEdit/index.vue) 的 `updateCustomSetting` 消费。
>
> 这就是为什么"树模型编辑配置同普通编辑一样配置"——**它就是普通编辑**。

### 1.3 加载流程(与普通编辑的 4 个差异点)

```text
1. 路由进入 /module/tree/edit/:mdCode/:id
2. Edit.vue 从路由拿 mdCode/detailId/editStyle(editStyle 从 query 读)
3. 解码 query 里的 3 个特殊参数(addFormData/backParams/currentTreeNodeData)
4. 把这 3 个 query 参数和 editStyle 作为 props 传给 <module-edit-tree>
5. module-edit-tree watch mdCode:
   ├─ isView ? ModuleUtils.viewModuleCfg : ModuleUtils.editModuleCfg  ← 差异 1:树走独立 API
   ├─ 合并 _module.customSetting + $attrs.customSetting(页面级覆盖)
   ├─ afterModuleJSON(module)                                        ← 改 model
   ├─ diy_addFormData = addFormData(来自 customSetting)              ← 差异 2:树专属 key
   ├─ if (detailId): getFormData(dataUrl) → afterEditJSON           ← 拉详情
   └─ isReady = true → 渲染 <module-edit>
6. <module-edit> 渲染表单(内部消费其他所有 customSetting)
   ├─ updateCustomSetting(merged)                                   ← 差异 3:saveUrl 默认值不同
   └─ mounted() → 处理 addFormData prop → 触发 diy_addFormData      ← 差异 2 接续
```

### 1.4 树编辑页接收的 3 个 query 参数(必须)

树列表的 Add/Edit 按钮跳转时会自动拼这 3 个 query(详见 [src/components/frame/Module/BtnBaseFun/tree-list.js:49-75](../../../src/components/frame/Module/BtnBaseFun/tree-list.js#L49-L75)):

| query key | 内容 | 作用 | 漏了会怎样 |
|-----------|------|------|----------|
| `addFormData` | `{ parentId, parentName }`(JSON.stringify + encodeURIComponent) | 新增时携带父节点信息;`module-edit-tree` 会作为函数参数传给 `customSetting.addFormData(currentNodeData, ...)` | 新增时表单里没有父节点 id,保存后找不到归属 |
| `backParams` | `{ defaultExpandedKeys: '1,2,3' }` | 返回树列表后保留展开状态 | 返回后树全部折叠 |
| `currentTreeNodeData` | 当前选中节点的 data(整对象) | 传给 `customSetting.addFormData` 的第一个参数,可在 customSetting 里读 | `addFormData` 函数拿不到节点数据 |

**Edit.vue 解码示例**(详见 [views/module/tree/Edit.vue:54-73](../../../src/views/module/tree/Edit.vue#L54-L73)):

```js
// 在 Edit.vue 的 computed 里
addFormData () {
    if (this.query) {
        return JSON.parse(decodeURIComponent(this.query.addFormData)) || {}
    }
    return {}
},
backParams () {
    if (this.query) {
        return JSON.parse(decodeURIComponent(this.query.backParams)) || {}
    }
    return {}
},
currentTreeNodeData () {
    if (this.query) {
        return JSON.parse(decodeURIComponent(this.query.currentTreeNodeData)) || {}
    }
    return {}
}
```

> 这 3 个 query 是**`ModuleEditTree` 赖以"知道当前是哪个树节点下"的依据**。**业务方从外部跳转到树编辑页**(比如自定义按钮 / 面板)时,必须**手动拼上**——不然 `customSetting.addFormData` 函数拿不到 `currentNodeData`,而且返回后树展开状态也会丢。

---

## 2. 树专属 1 个 key(`addFormData` 作函数)

> 来源:[ModuleEditTree/index.vue:84-95](../../../src/components/frame/Module/ModuleEditTree/index.vue#L84-L95) 的 `_addFormData` computed。

### 2.1 `addFormData` ⭐⭐⭐⭐⭐ (高频)

**位置**:`edit.js`(树模型编辑的 customSetting)

**签名**:`addFormData(currentNodeData, addFormData) → 新参数对象`

| 参数 | 说明 |
|------|------|
| `currentNodeData` | 当前选中的树节点数据(从 query 解码来的 `currentTreeNodeData`) |
| `addFormData` | 路由 query 里的原始 `addFormData` prop,通常是 `{ parentId, parentName }` |

**this 指向**:**`module-edit-tree` 实例** ⚠️ 不是 moduleEdit。

**默认行为**(没配时):直接 return 路由传过来的 `addFormData` prop。

**业务方实例**(典型场景:新增子节点时,根据父节点信息填默认值):

```js
// public/moduleJs/.../xxx_edit.js
addFormData: function (currentNodeData, addFormData) {
    return {
        // 保留原 addFormData(通常是 { parentId, parentName })
        ...(addFormData || {}),
        // 再补充当前节点的 id(用于 level/sort 等联动字段)
        nodeId: currentNodeData?.id,
        nodeName: currentNodeData?.name,
        // 默认值场景:新增时填父节点信息作为初始值
        parentId: currentNodeData?.id,
        parentName: currentNodeData?.name
    }
}
```

**易错点**:

| 问题 | 现象 | 解决 |
|------|------|------|
| **没 return** | 新增时父节点 id 丢失 | 必须 `return` 一个对象(可以是原 `addFormData` 的扩展) |
| 忘了展开 `addFormData` | 父节点的 parentId/parentName 丢了 | 用 `...(addFormData || {})` 保留 |
| `currentNodeData` 是 undefined | 从外部跳到树编辑页时没传 `currentTreeNodeData` query | 跳转时**必带 3 个 query**(见 §1.4) |
| 用了普通编辑的 `addFormData` 写法 | 业务方以为是 prop,直接 `addFormData: { xxx: 1 }` | 在树模型里**它是函数不是对象** |

### 2.2 与普通编辑的 `addFormData` prop 的区别

| 维度 | 普通编辑 | 树模型编辑 |
|------|---------|----------|
| 来源 | 路由 params/query 或代码直接传入 | 同左,但**额外**从 query 解码 `currentTreeNodeData` |
| 类型 | `Object` prop | **`Function`(customSetting key)** |
| 何时用 | 直接在 data 里读 `addFormData` | 在 `customSetting` 里写 `addFormData(currentNodeData, addFormData) => obj` |
| this 指向 | — | `module-edit-tree` 实例 |
| 默认行为 | 原样传给 `<module-edit>` | 调用函数返回值传给 `<module-edit>` |

> 普通编辑的 `addFormData` 是 prop,树模型编辑的 `addFormData` 是 **customSetting key**——同名不同物。

---

## 3. `this` 指向速查(树模型编辑 customSetting)

| 上下文 | `this` 指向 | 备注 |
|--------|-------------|------|
| `addFormData`(customSetting 函数) | **module-edit-tree 实例** | 唯一树专属 key |
| `afterModuleJSON` / `dataUrl` / `valuePath` / `paramsBeforeRequest` / `afterEditJSON` | **moduleEditCode / moduleEditTree 实例** | 与普通编辑一致(`moduleEditCode` 在 tree 版本里就是 `module-edit-tree`) |
| `beforeModuleInitRender` / `buttons` / `saveUrl` | **moduleEdit 实例** | 同普通编辑 |
| `beforeFieldChange` / `beforeRender` / `valueChange` / `validateRule` / `fieldCustom` / `appendDom` | **moduleForm / MForm 实例** | 同普通编辑 |
| `contentRender` / `appendDom.appendRender` | **DiyFormRender**(MForm 子组件) | 同普通编辑,formData 走 `D('xxx').value` |
| `renderField.*`(查看模式) | **MForm 实例** | 同普通编辑 |
| `viewType` / `openBtnSaveAndAdd` | 无 this(纯配置) | 同普通编辑 |

> ⚠️ 树模型编辑的 `this` 指向**几乎完全继承普通编辑**,只有 `addFormData` 是 `module-edit-tree`。
> 详见 [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)。

---

## 4. 树模型编辑 vs 普通编辑的 3 大差异

> **核心结论**:30+ key 写法 100% 一致,只有这 3 处不同。

| # | 差异点 | 普通编辑 | 树模型编辑 |
|---|--------|---------|----------|
| 1 | **入口路由** | `/module/stander/:editStyle/:mdCode/:id` | `/module/tree/edit/:mdCode/:id`(无 `:editStyle`,从 query 读) |
| 2 | **保存 URL 默认值** | `Save_URL(mdCode)` = `/jdbc/common/basecommontsave/saveIncludeFile.do?mdCode=xxx` | `Save_Tree_URL(mdCode)` = `/jdbc/common/basecommontreesave/saveIncludeFile.do?mdCode=xxx`(末尾 `tree`,后端会同步更新树节点) |
| 3 | **`addFormData` 写法** | prop(Object) | **customSetting 函数**(`addFormData(currentNodeData, addFormData) => obj`) |

### 4.1 差异 1:入口路由(后端菜单配置)

- 普通编辑菜单 URL:`/module/stander/edit/{mdCode}/{id}`(或 `/table/...`)
- **树模型编辑菜单 URL:`/module/tree/edit/{mdCode}/{id}`**

> 决定"用哪个视图"的关键是**后端菜单的 URL 路径**,**不是** JS 文件。
> 同一个 `edit.js` 既能跑普通编辑又能跑树模型编辑。

### 4.2 差异 2:saveUrl 默认值(后端会同步更新树)

```js
// 普通编辑默认
this._saveUrl = Save_URL(this.mdCode)
// = `/jdbc/common/basecommontsave/saveIncludeFile.do?mdCode=${mdCode}`

// 树模型编辑默认
this._saveUrl = Save_Tree_URL(this.mdCode)
// = `/jdbc/common/basecommontreesave/saveIncludeFile.do?mdCode=${mdCode}`
```

> ⚠️ **关键差异在 URL 末尾**:`basecommontsave` vs `basecommonttreesave`(多了 `tree`)。
> 后端 `tree` 版本除了保存数据,还会**同步更新对应树节点的 `name`/`sort` 等字段**,免去业务方手动 `$emit` 通知树刷新。
> 来源:[src/api/frame/common.js:40-41](../../../src/api/frame/common.js#L40-L41) 和 [ModuleEditTree/index.vue:97-105](../../../src/components/frame/Module/ModuleEditTree/index.vue#L97-L105)。

**业务方覆盖**(同普通编辑):

```js
// public/moduleJs/.../xxx_edit.js
saveUrl: function (mdCode) {
    return `${this.BASEURL}/custom/tree/save.do`
}
```

### 4.3 差异 3:`addFormData` 写法(树模型作函数)

详见 §2.2 和 §2.1 的对比表。

---

## 5. 默认按钮与生命周期

### 5.1 默认按钮列表

```js
// src/components/frame/Module/ModuleEditTree/button.js
let defaultButtons = [
    {
        id: 'back',
        name: '返回',
        icon: 'back',
        type: 'danger',
        click: async function () {
            await Event_Expand.call(this, 'before', arguments[1])
            this.goBack()
            await Event_Expand.call(this, 'after', arguments[1])
        }
    },
    {
        id: 'save',
        name: '保存',
        icon: 'save',
        type: 'primary',
        loading: false,
        click: async function (btnObj) {
            // this: bd-module-edit组件作用域
            let formRef = this.getFormRef()
            await Event_Expand.call(this, 'beforeValidate', arguments[1], formRef)
            formRef.validateForm().then(async (res) => {
                btnObj.loading = true
                await Event_Expand.call(this, 'before', arguments[1], res, formRef)
                this.post(this._saveUrl, res).then(async res => {
                    if (res?.hasOk) {
                        await Event_Expand.call(this, 'after', arguments[1], formRef, res)
                        this.$message.success('保存成功')
                        // 新增+有关联 tab 时替换路由到 edit,否则 goBack
                        let resDetail = res.bean?.returnDetails
                        if (!this.detailId && resDetail && this.childTab?.length > 0) {
                            // ... 替换路由
                        } else {
                            this.goBack()
                        }
                    } else {
                        this.$message.error(`保存失败！${res.message || ''}`)
                    }
                }).finally(async () => {
                    btnObj.loading = false
                    await Event_Expand.call(this, 'finally', arguments[1], formRef)
                })
            })
        }
    }
]
```

> 与普通编辑的默认按钮**几乎一致**([src/components/frame/Module/BtnBaseFun/edit.js](../../../src/components/frame/Module/BtnBaseFun/edit.js))。
> **差异**:树模型默认按钮只有 `back` + `save`(没有 `saveAndNew`,业务方需要时手动加)。
> 查看模式下默认只有 `back`。

### 5.2 生命周期

```
用户进入树编辑页(URL: /module/tree/edit/:mdCode/:id)
  │
  ├─ Edit.vue mounted
  │    └─ 解码 3 个 query 参数(addFormData / backParams / currentTreeNodeData)
  │
  ├─ module-edit-tree watch mdCode 触发
  │    ├─ isView ? viewModuleCfg : editModuleCfg  (注意:树用独立 API)
  │    ├─ afterModuleJSON(module)
  │    ├─ diy_addFormData = addFormData(来自 customSetting)
  │    ├─ if (detailId): getFormData(dataUrl) → afterEditJSON
  │    └─ isReady = true → 渲染 <module-edit>
  │
  └─ module-edit 渲染表单(与普通编辑完全一致)
       ├─ beforeRender(fieldList)
       ├─ beforeFieldChange(fieldObj)
       ├─ mounted: 把 addFormData prop 合到 fieldList(调 diy_addFormData 函数)
       ├─ 用户交互: valueChange / valuePath / validateRule
       └─ 保存: saveUrl → Save_Tree_URL → 返回上一页(goBack)
            └─ 默认 save 接口会同步更新树节点(因 URL 含 `tree`)
```

---

## 6. 高频 30+ key(右侧表单,同普通编辑)

> 这些 key 在树模型编辑里**与普通编辑完全一致**,**直接复用 `frontend-module-edit` 的 8 个 sub-skill**。
> 跳到 [frontend-module-edit §2 子 skill 索引](frontend-module-edit/SKILL.md#2-8-个子-skill-跳转高频)。

| 场景 | 跳到 |
|------|------|
| 字段值变更/联动/属性注入 | [sub/fields](frontend-module-edit/sub/fields/SKILL.md) |
| 字段后追加 DOM / 整个表单重排版 | [sub/form-react](frontend-module-edit/sub/form-react/SKILL.md) |
| 校验规则 / 动态显隐 / 动态只读 | [sub/validation](frontend-module-edit/sub/validation/SKILL.md) |
| 数据请求/响应(改 URL/参数/数据处理) | [sub/submit-flow/detail-data](frontend-module-edit/sub/submit-flow/detail-data.md) |
| 模型配置定制(动态加按钮/字段/改视图) | [sub/submit-flow/module-config](frontend-module-edit/sub/submit-flow/module-config.md) |
| 保存/按钮(改保存接口/自定义按钮/暂存/拦截) | [sub/submit-flow/save-and-buttons](frontend-module-edit/sub/submit-flow/save-and-buttons.md) |
| 布局(列数 / 渲染前)/ 标题栏右侧 | [sub/layout](frontend-module-edit/sub/layout/SKILL.md) |
| Tab 切换 / 关联子表(嵌套) | [sub/tab-nav](frontend-module-edit/sub/tab-nav/SKILL.md) |

> ⚠️ 写树模型编辑 customSetting 时,只要**右侧表单**相关的 key 不知道怎么写,直接看上面 sub-skill——不用怀疑"树模型编辑是不是有不同写法"。

---

## 7. 关键事实

### 7.1 树模型编辑的"魔法":保存自动同步树节点

树模型编辑默认 `Save_Tree_URL`(URL 含 `tree`),后端除了保存表单数据外,还会**同步更新对应树节点**(`name`/`sort`/`parentId` 等)。

> 来源:[src/api/frame/common.js:40-41](../../../src/api/frame/common.js#L40-L41)。

所以**默认行为下**:
- 编辑一个节点的"名称"字段,保存返回后,左侧树该节点的显示文本会更新
- 修改"父节点",保存后树会自动移到新父节点下(后端实现)

**但有例外**:
- 如果业务方**自定义了 `saveUrl`**(覆盖默认的 `Save_Tree_URL`),且新 URL **不含 `tree`**,那保存后**树不会自动更新**——业务方需要自己在 `afterSave` 钩子里手动通知树刷新(见 §7.2)
- 新增节点保存后:**左侧树不会自动出现新节点**(懒加载机制,见 §7.3)

### 7.2 自定义 saveUrl 后如何通知树刷新

```js
// public/moduleJs/.../xxx_edit.js
saveUrl: function (mdCode) {
    return `${this.BASEURL}/custom/save.do`  // 自定义 URL(不含 tree)
},
afterSave: function (formData, saveRes) {
    // 通知左侧树刷新当前节点
    // 思路:从 saveRes 或 formData 拿到 id,然后调 el-tree 的 updateKeyChildren / refreshCurrentNodeData
    let treeRef = this.getTreeRef?.()
    treeRef?.refreshCurrentNodeData?.()
    // 或更精细:treeRef?.updateKeyChildren(saveRes.bean.id, { ... })
}
```

> ⚠️ `getTreeRef()` 是 [ModuleListTree/index.vue:163-165](../../../src/components/frame/Module/ModuleListTree/index.vue#L163-L165) 定义的方法,**只有 moduleListTree 实例**有。
> 树编辑页的 `this` 是 moduleEdit/moduleEditTree,**没有** `getTreeRef`。
> 业务方通常需要通过 `this.$parent` / `this.$refs` / vuex 等方式拿到上层 moduleListTree 实例,然后调它的 `getTreeRef()`。

### 7.3 新增子节点后左侧树不刷新(常见痛点)

el-tree 懒加载机制下,**新保存的子节点不会自动出现在父节点下**——因为懒加载只在首次展开时拉取数据。

**默认行为**:**只删不增**——列表删除时通过 `$emit('afterDelete')` 同步删树节点,但新增没有这个钩子。

**业务方解决方案**:

方案 1:在 `afterSave` 里调 `treeRef.refreshCurrentNodeData()`(推荐,见 §7.2)

方案 2:**让用户手动刷新父节点**——不做处理,提示用户重新点击父节点重新加载(体验差,基本不可接受)

方案 3:**改用非懒加载树**(改框架,不推荐)

### 7.4 editStyle 不在路由参数里

```js
// views/module/tree/Edit.vue
editStyle () {
    // 注意:这里是 query 不是 params
    return this.params?.editStyle !== 'edit' ? 'table' : ''
}
```

> 普通编辑路由是 `/module/stander/:editStyle/:mdCode/:id`,**树编辑路由没有 `:editStyle` 参数**。
> 如果后端菜单用 `/module/tree/edit/...` 跳过来,`editStyle` 是 undefined,会被 `!== 'edit'` 判为 `table`(表格视图)。
> **业务方跳转时**:
> - 想用表格视图 → 拼 query `?editStyle=table` 或不带
> - 想用普通表单视图 → 拼 query `?editStyle=edit`

### 7.5 `this.$attrs` 特殊属性

树编辑页的 `this.$attrs` 上有这些特殊属性(由 `module-edit-tree` 注入):

| 属性 | 内容 |
|------|------|
| `currentTreeNodeData` | 路由 query 解码后的当前树节点数据 |
| `backParams` | 路由 query 解码后的返回参数(含 `defaultExpandedKeys`) |
| `addFormData` | 路由 query 解码后的添加表单数据(默认 `{ parentId, parentName }`) |
| `editStyle` | 从 query 读,`'edit'` 时是表单视图,其他为表格视图 |

> `customSetting` 各种回调里可以 `this.$attrs.currentTreeNodeData` 拿到当前树节点数据(同 `addFormData` 函数的第一个参数)。

---

## 8. 常见问题

| 问题 | 现象 | 解决 |
|------|------|------|
| 菜单配了 `/module/stander/edit/...` 但想用树编辑 | 页面是普通编辑 | 改后端菜单 URL 为 `/module/tree/edit/...`,JS 文件**不用动** |
| 新增节点后左侧树没出现新节点 | el-tree 懒加载机制 | 见 §7.3 方案 1 |
| 编辑保存后树节点 name 没更新 | 自定义了 `saveUrl`,URL 不含 `tree` | 见 §7.2 |
| `addFormData` 写了没生效 | 把它当 prop 用了,直接 `addFormData: { xxx: 1 }` | 树模型里 `addFormData` 是**函数**不是对象 |
| `addFormData` 函数的 `currentNodeData` 是 undefined | 从外部跳转时漏了 query | 跳转时必带 3 个 query(见 §1.4) |
| 返回树列表后树全折叠了 | 漏了 `backParams.defaultExpandedKeys` | 跳转时 `backParams: { defaultExpandedKeys: '1,2,3' }` |
| 新增时父节点 id 丢失 | 漏了 `addFormData` query | 跳转时 `addFormData: encodeURIComponent(JSON.stringify({parentId, parentName}))` |
| 表单 `saveUrl` 改了还是走默认 | 函数忘了 return URL | 必须 return string |
| `this.$attrs.currentTreeNodeData` 是 undefined | 路由没传 / 路由拼错 | 检查路由 query 的 `currentTreeNodeData` 拼写 |
| 编辑页 view 模式下还能点保存 | 没注意 `isView` 判断 | view 模式框架会自动只读,业务不要在按钮里强行走保存 |
| `customSetting.addFormData` 函数 this 拿不到 `formData` | this 是 moduleEditTree | 走 `this.formData`(如果有) 或 `this.$attrs.formData` |
| 树编辑页找不到 el-tree ref | this 是 moduleEditTree | 需通过 `this.$parent` / 父组件注入的方式拿 moduleListTree 实例 |

---

## 9. 验证 checklist

写完一个树模型编辑 customSetting,过一遍:

- [ ] 菜单 URL 用的是 `/module/tree/edit/...`(不是 `/module/stander/edit/...`)
- [ ] 后端 `customJs` 指向 `public/moduleJs/{mdCode}/edit.js`(或业务方自定义路径)
- [ ] 树能正常加载根节点和子节点(看树列表页)
- [ ] 从树列表点 "新增" 按钮,URL 含 3 个 query 参数(addFormData/backParams/currentTreeNodeData)
- [ ] 新增表单保存后,左侧树出现新节点(若 `addFormData` 函数返回了带 parentId 的对象)
- [ ] 编辑保存后,左侧树节点 name 有更新(走默认 `Save_Tree_URL` 时)
- [ ] 编辑返回后,左侧树展开状态保留(走 `backParams.defaultExpandedKeys`)
- [ ] 自定义 `saveUrl` 后,若有树刷新需求,在 `afterSave` 调 `treeRef.refreshCurrentNodeData()`
- [ ] `addFormData` 函数在 `customSetting` 里(不是 prop 写法)
- [ ] `addFormData` 函数正确处理 `currentNodeData` 可能为 undefined 的情况
- [ ] 所有普通编辑的 customSetting(`afterEditJSON`/`valueChange`/`validateRule` 等)与普通编辑**写法完全一致**
- [ ] view 模式下只显示返回按钮(没误显示保存按钮)
- [ ] console 无 error

---

## 10. 下一步去哪

- 写**普通编辑** customSetting → [frontend-module-edit](frontend-module-edit/SKILL.md)(30+ key 总览)
- 写**树模型列表**(左树+右表) → [frontend-module-tree-list](frontend-module-tree-list/SKILL.md)(3 个树专属 key + this.$attrs 特殊属性 + 跳编辑页带 3 个 query)
- **在普通列表里展示树形数据**(行展开嵌套,如菜单树、评论楼中楼) → [frontend-module-tree-table](frontend-module-tree-table/SKILL.md)(讲 el-table 原生树形属性 + 透传机制 + 3 种数据模式)
- 写**流程表单** → [sub/flow](frontend-module-edit/sub/flow/SKILL.md)
- 首次接触 Module 平台 → [frontend-module-quickstart](../frontend-module-quickstart/SKILL.md)
- 页面出问题 → [frontend-module-page-debug](../frontend-module-page-debug/SKILL.md)
- this 指向 = 具体文件速查 → [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)