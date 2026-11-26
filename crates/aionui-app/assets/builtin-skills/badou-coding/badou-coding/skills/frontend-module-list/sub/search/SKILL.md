---
name: frontend-module-list-search
description: 八斗 Module 列表 customSetting — 搜索栏交互完整指南。当用户说"搜索条件联动"、"搜索条件变化"、"隐藏搜索区"、"隐藏搜索过滤器"、"部门变了清空员工"、"动态加载搜索项"、**"按角色显示搜索项"**、**"按角色隐藏搜索项"**、**"动态增减搜索项"**时触发。覆盖 searchConditionChange / hideSearch / hideSearchFilter / **afterModuleJSON 修改 searchCondition**。
---

# Module 列表 — 搜索栏交互

> 列表页**搜索栏类**customSetting 指南。**先看 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。
> **按钮(顶部/行/搜索栏按钮)见 [module-list-buttons](../buttons/SKILL.md)**。
> 📌 **本 skill 聚焦"监听变化后的响应"**(联动 / 动态 options / 清空)。若要"主动设值 / 改值"(运行时改值、初始化默认值、Date 3 种模式、值格式字典),看顶层独立 skill [frontend-module-list-search-set-value](../../../frontend-module-list-search-set-value/SKILL.md)。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/list.js` 的 `export default` 对象里。

**进入前必读**:mdCode + list/edit + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 4 个 key

| key | 类型 | 用途 | 频次 |
|------|------|------|------|
| `searchConditionChange` | `Function` | 搜索条件变化监听(联动 / 动态加载 options) | ⭐⭐⭐⭐ |
| `hideSearch` | `Boolean` | 隐藏整个搜索区 | ⭐⭐ |
| `hideSearchFilter` | `Boolean` | 隐藏搜索过滤器(预设条件那一排) | ⭐⭐ |
| **`afterModuleJSON`** | `Function` | **模型配置加载后,改 `searchCondition` / `selectorData` / `fieldList` 等模型级配置**(按角色显隐搜索项、动态加搜索项) | ⭐⭐⭐ |

> ⚠️ `afterModuleJSON` 属于"数据流 - 模型配置变更"层钩子,完整说明在 [module-config-mutation](../module-config-mutation/SKILL.md),但**搜索栏显隐的最常见做法**就是用它,所以也列在本 skill。

---

## 2. `searchConditionChange` ⭐⭐⭐⭐(搜索条件联动)

**来源**:`ModuleList/index.vue` 第 651-660 行

**签名**:`searchConditionChange(fieldName, searchFieldList)`

**this 指向**:**moduleList 实例**

```js
// 示例:读 / 写搜索项值都直接操作 searchFieldList 数组
// 📌 本节聚焦"监听变化后的响应"(联动 / 动态 options / 清空)
// 若要"主动设值"(运行时改值 / 初始化默认值 / Date 3 种模式值格式),看顶层独立 skill [frontend-module-list-search-set-value](../../../frontend-module-list-search-set-value/SKILL.md)
searchConditionChange: function (fieldName, searchFieldList) {
    // fieldName: 刚变化的字段键名(String)
    // searchFieldList: 当前搜索条件数组(每个元素是 {id, name, value, ...})
    //                 与 this.searchFieldList 是同一个引用

    // 例: 当"部门"变了,自动清掉"员工"
    if (fieldName === 'deptId') {
        let empItem = searchFieldList.find(i => i.id === 'userId')
        if (empItem) empItem.value = null
        this.search()   // 清值后框架不会自动搜,需手动触发
    }

    // 例: 根据选择动态加载另一个搜索项的 options
    if (fieldName === 'categoryId') {
        let categoryId = searchFieldList.find(i => i.id === 'categoryId')?.value
        if (!categoryId) return
        this.$axios.post('/api/sub-categories', { categoryId }).then(res => {
            // 直接给目标搜索项的 options / data 字段赋值(具体字段名按搜索组件实现调整)
            let targetItem = searchFieldList.find(i => i.id === 'subCategoryId')
            if (targetItem) targetItem.options = res.data.list
        })
    }
}
```

### 2.1 典型场景

#### 场景 1:级联清空(最常见)

```js
searchConditionChange: function (fieldName, searchFieldList) {
    // 改了"省",清空"市"(直接改 searchFieldList 数组,清值后手动触发搜索)
    if (fieldName === 'provinceId') {
        let cityItem = searchFieldList.find(i => i.id === 'cityId')
        if (cityItem) cityItem.value = null
        this.search()
    }
    // 改了"市",清空"区"
    if (fieldName === 'cityId') {
        let districtItem = searchFieldList.find(i => i.id === 'districtId')
        if (districtItem) districtItem.value = null
        this.search()
    }
}
```

#### 场景 2:动态加载 options

```js
searchConditionChange: function (fieldName, searchFieldList) {
    if (fieldName === 'categoryId') {
        const categoryId = searchFieldList.find(i => i.id === 'categoryId')?.value
        if (!categoryId) return
        this.$axios.post('/api/sub-categories', { categoryId }).then(res => {
            // 直接给目标搜索项的 options / data 字段赋值(具体字段名按搜索组件实现调整)
            let targetItem = searchFieldList.find(i => i.id === 'subCategoryId')
            if (targetItem) targetItem.options = res.data.list
        })
    }
}
```

#### 场景 3:联动设置值

```js
searchConditionChange: function (fieldName, searchFieldList) {
    // 选了"启用",自动给"状态"设值
    if (fieldName === 'enabled') {
        let statusItem = searchFieldList.find(i => i.id === 'status')
        if (statusItem) statusItem.value = '1'
    }
}
```

---

## 3. `hideSearch` / `hideSearchFilter`(显隐控制)

```js
hideSearch: true,           // 隐藏整个搜索栏(没有搜索 UI)
hideSearchFilter: true,     // 隐藏搜索条件过滤器(预设条件那一排)
```

| 配置 | 效果 |
|------|------|
| `hideSearch: true` | 整个搜索区都不显示,包括搜索条件 + 搜索按钮 |
| `hideSearchFilter: true` | 只隐藏预设条件(顶部那一排快捷过滤),保留搜索条件 + 搜索按钮 |

> 注:隐藏后 `searchConditionChange` 仍会触发(由其他途径改变搜索条件时)。

**典型场景**:
- 简单列表(无搜索)→ `hideSearch: true`
- 列表是"详情页"的子模块(已经在外层传了过滤条件)→ `hideSearchFilter: true`

---

## 4. 单个搜索项按角色显隐(`afterModuleJSON` 改 `searchCondition`)⭐⭐⭐

**为什么需要这个**:customSetting 没有"按字段隐藏单个搜索项"的专用 key。`hideSearch` 只能整个搜索区藏起来,`searchConditionChange` 只在用户**主动改**搜索项时触发——初始化时不会触发。

**正确做法**:在 `afterModuleJSON` 里直接改 `module.searchCondition`(后端 `loadListCfg` 返回的搜索条件数组),框架后续会拿修改后的数组生成 `searchFieldList`(`ModuleList/index.vue:1237` 调用 `GetSearchFieldList(this.searchCondition, this.selectorData)`)。

### 4.1 关键事实

| 项 | 说明 |
|---|---|
| **触发时机** | `listModuleCfg` 执行完之后、`GetSearchFieldList` 生成 `searchFieldList` 之前(`ModuleListCode.vue:117-124`) |
| **this 指向** | `ModuleListCode` 组件实例 |
| **签名** | `afterModuleJSON(module) => module`(必须 return) |
| **module.searchCondition 类型** | **数组**(注意:`loadListCfg` 返回的是 JSON 字符串,但 `listModuleCfg` 内部已经 `Str_To_Obj` 转成数组了,见 `src/js/ModuleUtils.js:95`,所以可以直接 `filter`,**`push` 仅作为备用方案**) |
| **module.selectorData 类型** | 同上,数组(`ModuleUtils.js:97`) |
| **必须 return** | 不 return → `GetSearchFieldList` 拿不到修改后的配置 → 搜索栏不刷新(见 [module-config-mutation](../module-config-mutation/SKILL.md)) |
| **默认约定** | **只做 `filter`,不动态 `push`**——后端没配就过滤不生效,排查困难;依赖后端在模型设计器先把字段配为搜索条件 |

### 4.2 典型场景

#### 场景 1:按角色显示搜索项(最常见)

> "只有 SUPER 角色才能看到 description 商品描述搜索框"

```js
import store from '@/store'

export default {
    afterModuleJSON: function (module) {
        let roleCode = store.state.user.userInfo.roleCode
        if (roleCode !== 'SUPER') {
            // 角色不可见:从 searchCondition + selectorData 中过滤掉
            if (Array.isArray(module.searchCondition)) {
                module.searchCondition = module.searchCondition.filter(i => i.id !== 'description')
            }
            if (Array.isArray(module.selectorData)) {
                module.selectorData = module.selectorData.filter(i => i.id !== 'description')
            }
        }
        return module
    }
}
```

> 💡 **为何 searchCondition / selectorData 要同步过滤**:`GetSearchFieldList` 会按 id 把这两个数组合并(`src/service/module.js:449`),只过滤一边会留下脏数据。
>
> ⚠️ **默认约定**:一般情况**不**动态 push 搜索项(后端没配就过滤不生效,排查困难)。代码只做 `filter`,依赖后端已在模型设计器把 description 配为搜索条件。
>
> **如果改完不生效(搜索项还在)**:需要用户提供 `listModule.do` 接口返回值(`listModuleCfg` 内部就是调它,见 `src/js/ModuleUtils.js:40-46`),确认后端是否已把 description 配为搜索条件。**等用户提供接口返回值后再决定下一步**。

#### 场景 2:完全动态添加搜索项(后端不参与,**备用方案**)

> ⚠️ **这是备用方案**——一般情况**优先用场景 1(filter 思路)**,让后端在模型设计器配搜索条件。**只有当后端确实无法配置**(如临时调试、跨模型复用)时才用此方案。
>
> 使用前必须先确认:让用户提供 `listModule.do` 接口返回值,看 `searchCondition` 数组里确实没有 `id: 'keyword'` 这一项(没有就说明后端没配,才考虑用此方案)。

```js
afterModuleJSON: function (module) {
    // 不依赖后端模型设计器,纯前端动态加一个搜索项
    if (Array.isArray(module.searchCondition)) {
        module.searchCondition.push({
            name: '关键字',
            id: 'keyword',
            selectType: 1,
            isExtended: false
        })
    }
    return module
}
```

#### 场景 3:按角色改搜索项的 options / 类型

```js
afterModuleJSON: function (module) {
    // 把某个搜索项的 selectType 改一下,比如改成下拉多选
    let item = Array.isArray(module.searchCondition)
        ? module.searchCondition.find(i => i.id === 'categoryId')
        : null
    if (item) item.selectType = 0   // 0 = 下拉多选框
    return module
}
```

### 4.3 `selectType` 字典(常用)

来源:`src/views/common/modelDesigner/fieldDic.js:95-138`

| `selectType` | 组件 | 用途 |
|--------------|------|------|
| `0` | `search-multiple-select` | 下拉多选框(需要 `data` 数组配置 options) |
| `1` | `search-text` | **模糊搜索框**(文本字段用这个,最常见) |
| `5` | `search-date` | 时间选择器 |
| `6` | `search-num-range` | 数字区间 |
| `9` | `search-single-select` | 下拉单选框(需要 `data` 数组配置 options) |
| `11` | `search-year` | 年选择器 |
| `12` | `search-year-month` | 年月选择器 |
| `15` | `search-checkbox` | 复选框 |

> 没有 `data` 的搜索项(`searchType: 1`)不需要 options,直接 `value` 字符串即可;下拉类(`0` / `9`)必须有 `data: [{id, text}, ...]`。

### 4.4 流程图

```
listModuleCfg(mdCode)
   ↓ loadListCfg 返回字符串 searchCondition / selectorData
   ↓ Str_To_Obj 转数组
module = { searchCondition: [...], selectorData: [...], ... }
   ↓
afterModuleJSON(module)        ← 在这里改 searchCondition / selectorData
   ↓ (必须 return)
this.module = result
   ↓ 抛给父组件
ModuleList.mounted:
   _searchFieldList = GetSearchFieldList(this.searchCondition, this.selectorData)
```

### 4.5 常见问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 改了 searchCondition 但搜索栏没变化 | 忘了 `return module` | 必须在函数末尾 `return module` |
| 改了 searchCondition 但只过滤了一边,留下脏数据 | `GetSearchFieldList` 按 id 合并 `selectorData` | 两个数组同步 `filter` |
| 改 `module.searchCondition.push()` 不生效 | 当成字符串了(直接 `.push` 报错) | `module.searchCondition` 已是数组,可直接 `push`/`filter`(见 §4.1 关键事实) |
| 动态加的搜索项类型不对,渲染异常 | `selectType` 写错或缺失 | 参考 §4.3 的字典;下拉类要带 `data` |
| 想隐藏某个搜索项,但 `searchConditionChange` 没用 | 它只在用户**主动改**时触发,不会在初始化时跑 | 用 `afterModuleJSON` 在初始化时改 searchCondition |
| **filter 后搜索项还在(不消失)** | **后端没在模型设计器把该字段配为搜索条件** | **请用户提供 `listModule.do` 接口返回值(让用户在浏览器 Network 里看,或后端 `listModule` 接口),看 `searchCondition` 数组中是否有 `id: 'xxx'` 这一项。没有 → 让用户去后端模型设计器配;有 → 检查 filter 条件写对没** |

---

## 5. 关键事实

- `searchConditionChange` 内 `this` 是 **moduleList 实例**(可访问 `this.$axios`、`this.search()`、`this.searchReset()` 等)
- 触发时机:用户在搜索栏里**改动**了某个搜索项后(包括清空)
- `hideSearch` 只影响 UI,**不关功能**;数据请求依然会带搜索条件(如果业务方手动传)
- `searchConditionChange` 是**配置式**写法;如果需要更复杂逻辑,可以用 `searchBtns` 自定义按钮(详见 [module-list-buttons §5](../buttons/SKILL.md#5-searchbtns搜索栏按钮))
- **改单个搜索项的显隐/类型,用 `afterModuleJSON`**(本 skill §4);customSetting 没有针对单个搜索项显隐的专用 key

---

## 6. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| `searchConditionChange` 报 undefined | 误以为 this 是 mList | this 是 **moduleList**,改值直接操作 `searchFieldList` 数组(`item.value = xxx` 或 `item.value = null`),改完调 `this.search()` 触发搜索 |
| `searchConditionChange` 改了搜索项,搜索结果没变 | 改值后没触发搜索 | 框架只在用户**手动改**时触发;代码改值不会自动重新搜索,需手动调 `this.search()` |
| 动态 options 没生效 | options 字段名不对或组件没响应式 | 直接给 `searchFieldList` 对应项的 options / data 字段赋值,具体字段名按你们项目搜索组件实现调整 |
| 隐藏了搜索区,但业务上还有"传入搜索条件"的需求 | 用 `hideSearch: true` 后无法配置 | `hideSearch` 只关 UI,数据请求里依然会带搜索条件;或者在 `paramsBeforeRequest` 里手动加 |

---

## 7. 下一步去哪

- **按钮**(顶部/行/搜索栏按钮) → `module-list-buttons`
- **列渲染** → `module-list-render-field`
- **请求/数据流** → `module-list-data-flow`
- **选择 + 双击** → `module-list-selection-row`
- **表格外观** → `module-list-table-look`
- **导入导出** → `module-list-import-export`
- **回到总览** → `frontend-module-list`
- **表单页** → [frontend-module-edit](../../../frontend-module-edit/SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
