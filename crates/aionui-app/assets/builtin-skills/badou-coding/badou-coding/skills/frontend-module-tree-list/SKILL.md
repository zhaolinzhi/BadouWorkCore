---
name: frontend-module-tree-list
description: 八斗 Module 平台**树模型列表** customSetting 完整指南。**何时调用**:用户做树模型(左树+右表)列表页的定制,需要知道树专属的 3 个 key(treeAjaxConfig/treeOpenSecondNode/defaultParams)、与普通列表的差异(路由/按钮/this 指向)、特殊方法(取当前选中树节点、删列表同步删树节点)、或跳转树列表/树编辑页面的路径。**何时不调用**:① 用户只是普通列表(无树)定制 → 走 `frontend-module-list`;② 用户做表单(Edit/Add/View) → 走 `frontend-module-edit`;③ 用户首次接触 Module 平台 → 走 `frontend-module-quickstart`;④ 通用 Vue/Element UI 问题。
---

# Module 树模型列表 customSetting

> 树模型 = **左树 + 右表** 布局(见 [ModuleListTree/index.vue](../../../src/components/frame/Module/ModuleListTree/index.vue) 与 [views/module/tree/List.vue](../../../src/views/module/tree/List.vue))。
> **核心原则**:右侧列表的所有 customSetting **与普通列表完全一致**;只在**路由跳转**和**树相关的 3 个专属 key** 上有差异。
> 本 skill 专门讲差异点,共有的 40+ key(列渲染/按钮/搜索栏/数据流/选择/表格外观/导入导出)**直接复用 `frontend-module-list` 的 sub-skill**。

---

## ⚠️ 0. 动手前先确认 JS 路径(必读)

**树模型的 customSetting JS 文件** 与普通列表**是同一个**——同样是 `public/moduleJs/{mdCode}/list.js`(或业务方自定义子目录)。后端模型设计器上配置的 `customJs` 指向同一个文件,**不需要**额外配置。

唯一要确认的是入口视图文件(决定路由跳到哪儿):

| 入口视图 | 路由 | 后端菜单 URL 应配 |
|----------|------|---------------------|
| 普通列表 | `/module/stander/list/:mdCode/:symbol` | `/module/stander/list/{mdCode}/{symbol}` |
| **树模型列表** | `/module/tree/list/:mdCode/:symbol` | `/module/tree/list/{mdCode}/{symbol}` |
| 普通编辑 | `/module/stander/:editStyle/:mdCode/:id` | `/module/stander/{table/...}/{mdCode}/{id}` |
| **树模型编辑** | `/module/tree/edit/:mdCode/:id` | `/module/tree/edit/{mdCode}/{id}` |

> **关键事实**:业务方**改的是同一个 `list.js`**。同一个 `mdCode`,**入口视图可以是普通列表,也可以是树模型列表**——后端菜单配置决定哪个视图生效。
> 决定"用哪个视图"的关键是**后端菜单的 URL 路径**,**不是** JS 文件。

具体确认 4 项(同 [frontend-module-list §0](frontend-module-list/SKILL.md#0-动手前先确认-js-路径必读)):

1. `mdCode`
2. **入口视图**:普通列表(`stander/list`) 还是 树模型(`tree/list`)
3. JS 完整路径
4. 后端是否已配 `customJs`

---

## 1. 路由 / 入口组件 / 加载流程

### 1.1 三条路由对比

| 视图 | path | component | meta |
|------|------|-----------|------|
| 普通列表 | `module/stander/list/:mdCode/:symbol` | `views/module/stander/List.vue` | hasList / keepAlive |
| **树模型列表** | `module/tree/list/:mdCode/:symbol` | `views/module/tree/List.vue` | hasList / keepAlive |
| 树模型编辑 | `module/tree/edit/:mdCode/:id` | `views/module/tree/Edit.vue` | — |

> 路由定义见 [src/router/modules/model.js](../../../src/router/modules/model.js) 第 8-41 行。

### 1.2 入口组件关系

```
<views/module/tree/List.vue>  →  <module-list-tree>  (src/components/frame/Module/ModuleListTree/index.vue)
                                    ├─ <bd-tree>  左侧树(el-tree 懒加载)
                                    └─ <module-list>  右侧普通列表
                                          ↑
                                    customSetting 在这里被消费
```

> [!IMPORTANT]
> **`module-list-tree` 本身不直接消费 customSetting**。它只解构 3 个**树专属 key**(`treeAjaxConfig` / `treeOpenSecondNode` / `defaultParams`),其余 40+ key 全部通过 `_$attrs` 透传给内部的 `module-list`(即普通列表),由 [ModuleList/index.vue](../../../src/components/frame/Module/ModuleList/index.vue) 的 `updateCustomSetting` 消费。
>
> 这就是为什么"右侧列表配置同普通列表一样配置"——**它就是普通列表**。

### 1.3 加载流程

1. `List.vue` 从路由拿 `mdCode` / `searchParam` / `defaultSearchParam`,传给 `module-list-tree`
2. `module-list-tree` 监听 `mdCode`,调 `ModuleUtils.listModuleCfg(mdCode)` 拉模型配置
3. 合并 `_module.customSetting` + `this.$attrs?.customSetting`(页面级覆盖)
4. **走 `afterModuleJSON` 钩子**(若存在)改 `module`
5. **调 `updateCustomSetting`** 解构 3 个树专属 key
6. 把合并后的 `customSetting` 整体透传给 `module-list` 组件

### 1.4 也可嵌入面板/弹窗

- **面板 PPage**([src/components/frame/Panel/BlockContent/items/PPage.vue](../../../src/components/frame/Panel/BlockContent/items/PPage.vue)):`modulePathDic` 配 `/module/tree/list` → `module-list-tree`
- **弹窗 MPopupItem**([src/components/frame/Common/Popup/components/MPopupItem.vue](../../../src/components/frame/Common/Popup/components/MPopupItem.vue)):`type === 'standerTreeCode'` → `module-list-tree`

---

## 2. 树专属 3 个 key(树模型区别于普通列表的全部差异)

> 来源:[ModuleListTree/index.vue:281-294](../../../src/components/frame/Module/ModuleListTree/index.vue#L281-L294) 的 `updateCustomSetting`。

### 2.1 `treeAjaxConfig` ⭐⭐⭐⭐⭐ (高频)

**作用**:自定义**左侧树**的节点加载请求(树节点懒加载)。

**签名**:`function (nodeParentId, data, node) => { url, params, method, ...option }`

| 参数 | 说明 |
|------|------|
| `nodeParentId` | 当前节点的父 id(根节点时为 `''`/空) |
| `data` | 当前节点 data 对象 |
| `node` | el-tree 节点对象(node.level / node.childNodes ...) |

**this 指向**:**`module-list-tree` 实例** ⚠️ 不是 mList / moduleList。

**默认行为**(没配时):调 `Tree_Node_List_URL`(`/jdbc/common/basecommontree/tree.do`),参数 `{ mdCode, nodeId: nodeParentId }`。

**业务方实例**:

```js
// public/moduleJs/frame/baseService/rolePermission/sys_org_list.js
treeAjaxConfig: function (nodeParentId, data, node) {
    if (nodeParentId) {
        // 加载子节点
        return {
            url: `${this.BASEURL}/org/department/departmenttree/ptree.do`,
            params: { pid: nodeParentId }
        }
    }
    // 加载根节点
    return {
        url: `${this.BASEURL}/org/department/departmenttree/tree.do`,
        params: {}
    }
}
```

**易错点**:
- 必须 **return** 一个对象;不 return 就走默认配置
- 根节点(`nodeParentId` 为空)和子节点**通常需要返回不同的 url**
- 返回值会被 `finalRequest` 包装,支持 `method`/`data`/`headers` 等 axios options

### 2.2 `treeOpenSecondNode` ⭐⭐

**作用**:是否在请求一级节点时**自动展开二级节点**。

**类型**:`Boolean`,默认 `true`。

```js
treeOpenSecondNode: false  // 根节点加载后不自动展开二级
```

**业务场景**:根节点是"全公司"这种粗粒度数据时,不希望一进来就展开几千个部门,设为 `false`。

### 2.3 `defaultParams` ⭐⭐⭐⭐⭐ (高频)

**作用**:自定义**右侧列表**请求时携带的默认参数(通常带当前选中树节点的 id)。

**签名**:`function (params, data, node, nodeComponent) => paramsObj`

| 参数 | 说明 |
|------|------|
| `params` | 已有参数(从父级 `defaultParamsObj` 深拷贝而来) |
| `data` | **当前选中树节点**的 data |
| `node` | 树节点对象 |
| `nodeComponent` | 节点实例 |

**this 指向**:**`module-list-tree` 实例**。

**默认行为**(没配时):

```js
// ModuleListTree/index.vue:213-242 默认实现
{
    sortname: 'layerNum,priority',
    sortorder: 'asc,asc',
    defaultSearchParam: JSON.stringify([
        { name: 'parentId', type: GlobalConst.searchBar.type, value: data.id }
    ])
}
```

> 默认按 `parentId` 等于当前节点 id 过滤,并按 `layerNum, priority` 升序。

**业务方实例**:

```js
// public/moduleJs/frame/baseService/rolePermission/user_manager_list.js
defaultParams: function (params, data, node, nodeComponent) {
    return {
        ...(params || {}),
        departmentId: data.id  // 改用 departmentId 过滤,而非默认的 parentId
    }
}
```

```js
// public/moduleJs/frame/baseService/rolePermission/user_role_list.js
defaultParams: function (params, data, node, nodeComponent) {
    return {
        ...(params || {}),
        roleId: data.id || '',
        searchParam: '[]'  // 强制清空搜索栏
    }
}
```

**易错点**:
- **必须 return** 一个新对象(不能 mutate `params` 后不 return)
- 保留 `params` 的其他字段时记得展开:`...(params || {})`
- 想覆盖父级传的 `defaultSearchParam` 时,直接 `defaultSearchParam: '[]'`(空数组字符串)
- 这里的过滤参数是**走 `defaultSearchParam` 字段(后端全局过滤)**,不走 `searchParam`(搜索栏)。如果业务方要的是搜索栏,见 [module-list-search](../frontend-module-list/sub/search/SKILL.md)

---

## 3. `this` 指向速查(树模型 customSetting)

| 上下文 | `this` 指向 | 备注 |
|--------|-------------|------|
| `treeAjaxConfig` / `treeOpenSecondNode` / `defaultParams` / `afterModuleJSON` | **module-list-tree 实例** | 树专属 key,this 是 tree-list 上层 |
| `dataUrl` / `buttons[].click` / `dblClick` / `searchConditionChange` / `createListFun` 内方法 | **moduleList 实例**(右侧普通列表) | 与普通列表**完全一致** |
| `paramsBeforeRequest` / `afterListJSON` / `afterListRender` / `selectionChange` / `createFun` 内方法 / `renderField.*` / `showSummary` / `spanMerge` / `renderFieldHeader.*` | **mList 实例** | 与普通列表**完全一致** |
| `buttons[].isHide`(函数式) | **按钮对象 `btnObj`** ⚠️ | 不是 moduleList!要读 Vuex 用 `import store from '@/store'` |
| `freezeColumnIndex` / `freezeColumnLastIndex` | **无 this**(纯静态) | 直接写数字 |

> 详见 [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)。

---

## 4. 树模型特殊属性 / 方法(在 `this.$attrs` / `this` 上可拿到)

> 这一节是**业务方在 customSetting 各种回调里能调用的"特殊 API"**——是树模型与普通列表最关键的差异。

### 4.1 当前选中树节点

```js
// 在 buttons click / renderField click 等回调里(以 moduleList 实例为主)
let currentTreeNode = this.$attrs.currentTreeNode  // el-tree 节点对象
let currentTreeNodeData = currentTreeNode?.data    // 节点的 data
let parentId = currentTreeNodeData?.id
let parentName = currentTreeNodeData?.name
```

> ⚠️ `this.$attrs.currentTreeNode` 是 **module-list-tree 透传过来的**,不是 moduleList 自身的状态——别在 `created`/`mounted` 里读,这时还没点击树节点。

### 4.2 当前展开的节点 keys(用于返回时恢复状态)

```js
let defaultExpandedKeys = this.$attrs.defaultExpandedKeys  // Array
```

### 4.3 删除列表行时同步删树节点

```js
// 在自定义 delete 按钮的 click 里(基于 moduleList)
click: function (btnObj) {
    // ... 删除成功后:
    this.$emit('afterDelete', selection)  // 通知 module-list-tree 删除对应树节点
}
```

> 这是**树模型删除的特殊魔法**。普通列表里 `$emit('afterDelete', ...)` 没人监听;树模型里 [ModuleListTree/index.vue:170-177](../../../src/components/frame/Module/ModuleListTree/index.vue#L170-L177) 收到后会调 `treeRef.remove(i.id)` 把树节点也删了。
>
> **业务方必须保证列表数据的 `id` 字段**与**树节点的 `nodeKey`**(默认 `id`)一致,否则树节点删不掉。

### 4.4 树组件 ref(在 module-list-tree 内部,可经由 `createListFun` 注入)

```js
createListFun: {
    refreshTree () {
        // 拿到 module-list-tree 实例上的 getTreeRef
        // 注意:createListFun 的 this 是 moduleList,不是 tree
        // 所以要先向上找一层:
        let treeList = this.$parent  // 或 this.$refs.moduleListTree
        let treeRef = treeList?.getTreeRef?.()  // 内部 el-tree ref
        treeRef?.setCurrentKey('xxx')  // 选中节点
    }
}
```

> `getTreeRef()` 在 [ModuleListTree/index.vue:163-165](../../../src/components/frame/Module/ModuleListTree/index.vue#L163-L165) 定义,返回内部 el-tree ref。

### 4.5 跳转到树编辑页(必带 3 个 query 参数)

```js
// 在自定义按钮的 click 里
click: function (btnObj) {
    let currentTreeNode = this.$attrs.currentTreeNode
    let currentTreeNodeData = currentTreeNode?.data
    let addFormData = {
        parentId: currentTreeNodeData?.id,
        parentName: currentTreeNodeData?.name
    }
    let backParams = {
        defaultExpandedKeys: (this.$attrs?.defaultExpandedKeys || []).toString()
    }
    this.pushPage({
        path: `/module/tree/edit/${this.mdCode}/add`,  // /:id 表示编辑
        query: {
            addFormData: encodeURIComponent(JSON.stringify(addFormData)),
            backParams: encodeURIComponent(JSON.stringify(backParams)),
            currentTreeNodeData: encodeURIComponent(JSON.stringify(currentTreeNodeData))
        },
        title: '...'
    })
}
```

> 这 3 个 query 是**`ModuleEditTree` 组件**赖以"知道返回后回到哪个树节点"的依据。漏掉会导致:
> - `addFormData` 漏 → 新增时父节点 id 丢了
> - `backParams` 漏 → 保存返回后树展开状态丢了
> - `currentTreeNodeData` 漏 → 关联父节点数据丢了
>
> 见 [src/components/frame/Module/BtnBaseFun/tree-list.js](../../../src/components/frame/Module/BtnBaseFun/tree-list.js) `pushEditPage`。

### 4.6 跳转到树列表页(从其他模块跳过来)

```js
// 在普通列表 / 表单 / 面板按钮里
this.pushPage({
    path: `/module/tree/list/${this.mdCode}/${symbol}`,  // 树列表
    // 或 path: `/module/tree/list/${this.mdCode}/placeholder`  // 占位符
    title: '树模型列表'
})
```

---

## 5. 默认 URL 与内置接口(可不配 customSetting 也能跑)

| 资源 | 默认 URL | 来源 |
|------|----------|------|
| 左侧树根节点 | `Tree_Node_List_URL` = `${VUE_APP_BASE_API}/jdbc/common/basecommontree/tree.do` | [src/api/frame/common.js](../../../src/api/frame/common.js) |
| 左侧树子节点 | 同上,params `{ mdCode, nodeId }` | 同上 |
| 右侧列表 | `Tree_List_URL(mdCode)` = `${VUE_APP_BASE_API}/jdbc/common/basecommontreelist/listJSON.do?mdCode=${mdCode}` | 同上 |
| 节点是否叶子 | `isLeaf(data)` = `!(data.isParent || data.hasChild)` | [ModuleListTree/index.vue:247-249](../../../src/components/frame/Module/ModuleListTree/index.vue#L247-L249) |
| 节点 key | `nodeKey = 'id'` | [ModuleListTree/index.vue:108](../../../src/components/frame/Module/ModuleListTree/index.vue#L108) |

> 业务方**完全可以用 `treeAjaxConfig` + `dataUrl` + `defaultParams` 三个 key 替换**默认值,无需碰框架代码。

---

## 6. 按钮差异:为什么树模型按钮是另一份

> 来源:[src/components/frame/Module/BtnBaseFun/tree-list.js](../../../src/components/frame/Module/BtnBaseFun/tree-list.js)(85 行,只有 Add/Edit 重写,其余从 `list.js` 继承)。

| 按钮 | 树模型 vs 普通列表 | 差异原因 |
|------|---------------------|----------|
| `Add` | 跳 `/module/tree/edit/...` + 带 3 个 query | 表单要知道新增到哪个父节点下 |
| `Edit` | 跳 `/module/tree/edit/...` + 带 3 个 query | 表单要知道当前父节点 + 回到时树的状态 |
| `View` / `Import` / `Export` / `Delete` | **完全继承**自 `list.js` | — |

**默认按钮列表** 见 [ModuleListTree/index.vue:59-66](../../../src/components/frame/Module/ModuleListTree/index.vue#L59-L66):

```js
const Default_Btn_List = [
    { id: 'add', click: Add, loading: false },
    { id: 'edit', click: Edit, loading: false },
    { id: 'view', click: View, loading: false },
    // { id: 'import', click: Import, loading: false },  // 注释
    { id: 'export', click: Export, loading: false },
    { id: 'delete', click: Delete, loading: false }
]
```

> 默认隐藏了 `import`(没写在数组里),需要时显式加进去。

**业务方覆盖** 与普通列表一样,直接覆盖 `buttons` 数组:

```js
// public/moduleJs/.../xxx_list.js
buttons: [
    { id: 'view', isHide: true },  // 隐藏默认按钮
    {
        id: 'custom',
        name: '自定义',
        icon: 'xxx',
        type: 'primary',
        click: function (btnObj) {
            // this 是 moduleList 实例
            let treeNode = this.$attrs.currentTreeNode
            // ...
        }
    }
]
```

---

## 7. 高频 40+ key(右侧列表,同普通列表)

> 这些 key 在树模型里**与普通列表完全一致**,**直接复用 `frontend-module-list` 的 sub-skill**。
> 跳到 [frontend-module-list §2 子 skill 索引](frontend-module-list/SKILL.md#2-7-个子-skill-跳转高频)。

| 场景 | 跳到 |
|------|------|
| 列渲染(状态徽章/单元格点击/JSX 按钮组) | [module-list-render-field](frontend-module-list/sub/render-field/SKILL.md) |
| 按钮(顶部/行/搜索栏按钮、按钮子属性) | [module-list-buttons](frontend-module-list/sub/buttons/SKILL.md) |
| 搜索栏交互(条件变化、级联清空、显隐) | [module-list-search](frontend-module-list/sub/search/SKILL.md) |
| 主动设置/修改搜索项的值 | [frontend-module-list-search-set-value](../frontend-module-list-search-set-value/SKILL.md) |
| 请求/数据流(自定义 URL、加签、响应处理、模型配置变更) | [module-list-data-flow](frontend-module-list/sub/data-flow/SKILL.md) |
| 选择 + 双击 | [module-list-selection-row](frontend-module-list/sub/selection-row/SKILL.md) |
| 表格外观(冻结列/合计行/行列合并) | [module-list-table-look](frontend-module-list/sub/table-look/SKILL.md) |
| 导入导出 | [module-list-import-export](frontend-module-list/sub/import-export/SKILL.md) |

> ⚠️ 写树模型 customSetting 时,只要**右侧表格**相关的 key 不知道怎么写,直接看上面 sub-skill——不用怀疑"树模型是不是有不同写法"。

---

## 8. 关键事实

### 8.1 3 个 tree-* key 的执行顺序

```
组件 mount
    ↓
watch mdCode 触发
    ↓
ModuleUtils.listModuleCfg(mdCode) → 拿到 _module.customSetting
    ↓
合并 $attrs.customSetting(页面级覆盖)
    ↓
执行 afterModuleJSON(module) → 得到 module
    ↓
调 updateCustomSetting(merged)
    ├─ 解构 treeAjaxConfig → 存到 diy_treeAjaxConfig
    ├─ 解构 treeOpenSecondNode → 存到 diy_treeOpenSecondNode
    ├─ 解构 defaultParams → 存到 diy_defaultParams
    └─ 把整个 customSetting 通过 _$attrs 透传给 module-list
    ↓
用户点击树节点 → setCurrentNode → 走 setDefaultParam(data, node, nodeComponent)
    ├─ 若有 diy_defaultParams → 调它,return 啥用啥
    └─ 若没有 → 用默认 parentId 过滤
    ↓
右侧 module-list 收到 defaultParams → 发请求
```

### 8.2 treeAjaxConfig 的两次执行

树组件加载时会**先请求根节点**(根节点 `nodeParentId` 是空),再请求子节点(`nodeParentId` 是父节点 id)。`treeAjaxConfig` 会被**调用多次**,业务方要根据 `nodeParentId` 区分根/子节点逻辑。

### 8.3 defaultParams 的执行时机

`defaultParams` 在**用户点击树节点时**触发,**不是在组件 mount 时**。所以 `data`/`node` 是真实的当前节点。

### 8.4 defaultSearchParam 与 searchParam 的区别

| 字段 | 用途 | 是否在 URL |
|------|------|------------|
| `defaultSearchParam` | **后端全局过滤**(默认勾上的过滤项,不可见) | JSON 字符串塞进 params |
| `searchParam` | **搜索栏**(可见可编辑) | JSON 字符串塞进 params |

`defaultParams` 默认走 `defaultSearchParam`;若业务方要用搜索栏,得自己覆盖 `defaultSearchParam: '[]'`(空),然后在 `searchConditionChange` / 自定义搜索栏按钮里改 `searchParam`。

### 8.5 列表 `dataUrl` 也能覆盖

```js
// public/moduleJs/.../xxx_list.js
dataUrl: function () {
    // this 是 moduleList 实例
    return `${this.BASEURL}/xxx/listJSON.do`
}
```

> 覆盖后,默认的 `Tree_List_URL(mdCode)` 不再被使用。

### 8.6 `afterModuleJSON` 是树模型额外支持的钩子

`ModuleList` 没有 `afterModuleJSON`(它叫别的名字或没有),但 `ModuleListTree` **支持**:

```js
afterModuleJSON: function (module) {
    // this 是 module-list-tree 实例
    // module 是从后端拉的模型配置
    // 改完后必须 return
    return {
        ...module,
        // ... 改写
    }
}
```

> 走 `afterModuleJSON` 后,透传给右侧 module-list 的 customSetting 也会用修改后的 module 里的。

---

## 9. 常见问题

| 问题 | 现象 | 解决 |
|------|------|------|
| 菜单配了 `module/stander/list/...` 但想用树模型 | 页面是普通列表 | 改后端菜单 URL 为 `module/tree/list/...`,JS 文件**不用动** |
| 树模型编辑返回后,左侧树状态全没了 | 漏了 `backParams` | 跳转编辑时 `backParams.defaultExpandedKeys` 要 toString 带上 |
| 列表删除后,树节点没被删 | 没 `$emit('afterDelete', ...)` 或 id 不一致 | 自定义 delete 按钮里 `this.$emit('afterDelete', selection)`;确保 `selection[i].id === treeNodeKey` |
| `defaultParams` 改了但右侧请求不带新参数 | 没 return / 漏展开 `params` | 必须 `return { ...(params || {}), ... }` |
| `treeAjaxConfig` 改了但根节点请求还走默认 | 根节点分支没 return | `if (nodeParentId) {...} return { ...根节点配置 }` |
| 新增的子节点保存后,左侧树没刷新 | 默认行为就只删不增 | 需在编辑页 `afterSave` 钩子里调 `treeRef.refreshCurrentNodeData()`(el-tree 懒加载) |
| `this.$attrs.currentTreeNode` 是 undefined | 在 `created`/`mounted` 里读 / 没点过树节点 | 必须在用户点击树节点后的回调里读 |
| `this.mdCode` 在 `treeAjaxConfig` 里是 undefined | this 指向错位 | `treeAjaxConfig` 的 this 是 module-list-tree,**有** `mdCode`;`dataUrl` / `buttons.click` 的 this 是 moduleList,**也有** `mdCode` |
| `paramsBeforeRequest` 在树模型里失效 | — | 不会失效,只是 this 是 mList。注意改的字段是 list 请求参数,不是树节点参数 |
| 树节点没"+"展开箭头 | `isLeaf` 误判 / 接口没返回 `isParent` | 检查接口返回的 `isParent` / `hasChild` 字段;或自定义 `isLeaf` 钩子(目前 framework 没暴露) |
| `nodeKey` 想换 | 组件写死 `'id'` | 改 [ModuleListTree/index.vue:108](../../../src/components/frame/Module/ModuleListTree/index.vue#L108),或同步接口字段名 |
| 面板里嵌入树列表,点了不展开 | PPage 缺 `modulePath` | 面板 URL 必须含 `/module/tree/list/...` 前缀,见 [PPage.vue:90-99](../../../src/components/frame/Panel/BlockContent/items/PPage.vue#L90-L99) |

---

## 10. 验证 checklist

写完一个树模型 customSetting,过一遍:

- [ ] 菜单 URL 用的是 `/module/tree/list/...`(不是 `/module/stander/list/...`)
- [ ] 后端 `customJs` 指向 `public/moduleJs/{mdCode}/list.js`(或业务方自定义路径)
- [ ] 树能正常加载根节点
- [ ] 树能正常展开子节点(若 `treeOpenSecondNode: true`)
- [ ] 点击树节点后,右侧列表能请求到该节点的子项
- [ ] `defaultParams` 改动后,Network 请求参数里能看到新字段
- [ ] 添加按钮点击后跳转到树编辑页(URL 含 `tree/edit`)
- [ ] 编辑保存后,左侧树节点数据有更新(若有相关钩子)
- [ ] 列表删除后,左侧树节点同步被删
- [ ] 编辑页返回后,左侧树展开状态保留
- [ ] `console` 无 error
- [ ] 右侧列表的所有通用 customSetting(`renderField` / `buttons` / `searchConditionChange` / 导入导出等)与普通列表**写法完全一致**

---

## 11. 下一步去哪

- 写**普通列表** customSetting → [frontend-module-list](frontend-module-list/SKILL.md)(40+ key 总览)
- 写**树模型编辑页** customSetting → [frontend-module-tree-edit](frontend-module-tree-edit/SKILL.md)(3 大差异 + 1 个树专属 key + 3 个 query 参数)
- **在普通列表里展示树形数据**(行展开嵌套,如菜单树、评论楼中楼) → [frontend-module-tree-table](frontend-module-tree-table/SKILL.md)(讲 el-table 原生树形属性 + 透传机制 + 3 种数据模式)
- 写**树模型自定义按钮** → [module-list-buttons](frontend-module-list/sub/buttons/SKILL.md) + 本 skill §4 特殊属性
- 写**树模型列渲染** → [module-list-render-field](frontend-module-list/sub/render-field/SKILL.md)
- 写**树模型请求/响应处理** → [module-list-data-flow](frontend-module-list/sub/data-flow/SKILL.md)
- 首次接触 Module 平台 → [frontend-module-quickstart](../frontend-module-quickstart/SKILL.md)
- 页面出问题 → [frontend-module-page-debug](../frontend-module-page-debug/SKILL.md)
- this 指向 = 具体文件 速查 → [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)
