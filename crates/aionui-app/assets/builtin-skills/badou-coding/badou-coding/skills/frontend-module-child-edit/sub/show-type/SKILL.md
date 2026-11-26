---
name: frontend-module-child-edit-show-type
description: 八斗 Module 表单 customSetting — 关联子表的 `showType` 4 类渲染方式详解(0=编辑表单 / 1=列表 / 2=查看表单 / 4=自定义页面)。当用户问"showType 怎么配"、"子表用编辑表单还是列表"、"1v1 关联怎么配"、"showType=4 怎么用 pageUrl"、"自定义页面怎么挂载"时触发。覆盖 ChildModuleEdit 的 4 个 template 分支 + 关键 props(isInLink / addFormData / elseAttrs / isView)+ pageUrl 自动挂载机制。
---

# 关联子表 — `showType` 4 类渲染方式详解

> 来源:[ChildModuleEdit.vue:1-73](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L1-L73) 的 template 分支 + [sys_module_link_edit.js:90-157](../../../../../public/moduleJs/frame/modelDesign/sys_module_link_edit.js#L90-L157) 的 `setField_ShowType_Options`。
>
> **父 skill**:[frontend-module-child-edit](../SKILL.md)

---

## 1. 4 类 showType 一览

| 值 | 名称 | 渲染组件 | props 关键点 | 适用场景 |
|---|---|---|---|---|
| `0` | **编辑表单** | `module-edit-code`(`ModuleEditCode`) | `:isInLink="true"` `:hideBtn="false"` | 1v1 关联(主表+子表单) |
| `1` | **列表**(默认) | `module-list-code`(`ModuleListCode`) | `:fullHeight="true"` `:defaultParamsObj` | 1vN 关联(主表+多条子数据) |
| `2` | **查看表单** | `module-edit-code`(强制 `isView`) | `:isView` 强制 true | 1v1 关联的只读视图 |
| `4` | **自定义页面** | 动态挂载的 Vue 组件 | 用 `pageUrl` 字段 | 关联模块是自定义业务页面 |

> ⚠️ `showType=3` 不存在(框架无对应渲染分支)。

---

## 2. `showType` 与 type / isEdit 的联动规则

> 来源:[sys_module_link_edit.js:90-157](../../../../../public/moduleJs/frame/modelDesign/sys_module_link_edit.js#L90-L157) 的 `setField_ShowType_Options`。

| type(关联类型) | isEdit | showType 可选项 |
|---|---|---|
| `1`(1v1) | `1`(是) | 只显示 `0`(编辑表单) |
| `1`(1v1) | `0`(否) | 只显示 `2`(查看表单) |
| `2`(1vN) | — | 只显示 `1`(列表) |
| `3`(多对多) | — | — |

**关键事实**:
- **1v1 关联**:只能是编辑表单或查看表单(二选一)
- **1vN 关联**:只能是列表
- 后端 select 组件会根据 type 动态过滤 showType 的可选项

---

## 3. showType=0:编辑表单(1v1 关联)

### 3.1 完整 template

```vue
<!-- ChildModuleEdit.vue:11-30 -->
<component
    :is="componentId"
    ref="moduleEditCode"
    :title="title"
    :noTitle="noTitle"
    :hideBtn="false"
    :isInLink="true"           <!-- 关键:告诉子模块"我是子模块" -->
    :isView="isView"
    btn-placement="top"
    :mdCode="mdCode"
    :defaultParamsObj="defaultParamsObj"
    :addFormData="_addFormData"  <!-- 关键:自动注入关联字段值 -->
    :fullHeight="fullHeight"
    :class="_linkClass"
    :elseAttrs="elseAttrs"
    :viewType="viewType"
    :historyData="historyData">
</component>
```

### 3.2 关键 props 解析

| prop | 值 | 作用 |
|---|---|---|
| `:isInLink="true"` | 固定 true | 让按钮事件知道"我是子模块",框架会**过滤掉不允许在子模块出现的按钮**(如某些只在主模块才有的批量操作) |
| `:hideBtn="false"` | 固定 false | 不隐藏按钮(子模块要保留保存按钮) |
| `btn-placement="top"` | 固定 top | 按钮放顶部,不影响容器高度 |
| `:addFormData="_addFormData"` | 自动注入 `{[relationEntityField]: 主表关联值}` | 新增子表数据时**自动带上主表 id** |
| `:elseAttrs="elseAttrs"` | 注入主表字段列表、主表作用域等 | 见 §6.2 |

### 3.3 `_addFormData` 自动生成逻辑

```js
// ChildModuleEdit.vue:222-226
_addFormData () {
    return {
        [this.relationEntityField]: this._entityFieldValue,
    }
}
```

其中 `_entityFieldValue` 从**主表的 `entityField` 字段读取**:

```js
// ChildModuleEdit.vue:194-205
_entityFieldValue () {
    let _field = (this.mainFieldList || []).find(i => i.name === this.entityField)
    if (!_field) {
        let errorTip = `关联字段${this.relationEntityField}在主表中找不到，请检查字段名是否正确,以及在主表中是否存在该字段`
        console.error(errorTip)
        this.$message.warning(errorTip)
        return
    }
    return _field.value
}
```

---

## 4. showType=1:列表(1vN 关联,最常用)

### 4.1 完整 template

```vue
<!-- ChildModuleEdit.vue:33-46 -->
<module-list-code
    ref="list"
    :title="title"
    :noTitle="noTitle"
    :defaultBtnList="_defaultBtnList"
    :mdCode="mdCode"
    :defaultParamsObj="defaultParamsObj"  <!-- 自动按 relationEntityField 过滤 -->
    :elseAttrs="elseAttrs"
    :isView="isView"
    :fullHeight="true"
    :class="_linkClass">
</module-list-code>
```

### 4.2 关键点

- `:defaultParamsObj` 由框架**自动生成**:

```js
// ChildModuleEdit.vue:218-221
defaultParamsObj () {
    let defaultSearchParam = `[{"name":"${this.relationEntityField}","value":"${this._entityFieldValue}","type":"${GlobalConst.searchBar.type}"}]`
    return { defaultSearchParam }
}
```

- **过滤机制**:列表请求时,自动带上 `relationEntityField` = 主表关联值作为过滤条件
- `:fullHeight="true"` 列表**铺满容器**
- 列表高度由外层 `h-auto` / `h-per-100` 决定

### 4.3 列表高度自动计算

```js
// ChildModuleEdit.vue:233-235
async mounted () {
    // 根据设备可视高度,动态计算模型列表的展示高度
    this.listHeight = `${document.body.clientHeight - 200}px`
    ...
}
```

---

## 5. showType=2:查看表单(1v1 关联的只读视图)

### 5.1 完整 template

```vue
<!-- ChildModuleEdit.vue:49-68 -->
<component
    isView                        <!-- 关键:强制查看模式 -->
    :is="componentId"
    ref="moduleEditCode"
    :title="title"
    :noTitle="noTitle"
    :hideBtn="false"
    :isInLink="true"
    :mdCode="mdCode"
    :defaultParamsObj="defaultParamsObj"
    :addFormData="_addFormData"
    :fullHeight="fullHeight"
    :class="_linkClass"
    :elseAttrs="elseAttrs"
    :viewType="viewType"
    :historyData="historyData">
</component>
```

### 5.2 与 showType=0 的区别

| 项 | showType=0 | showType=2 |
|---|---|---|
| `isView` | 跟随父级 | **强制 true** |
| 用途 | 1v1 编辑场景 | 1v1 只读场景 |
| 按钮 | 子模块完整按钮 | 受 isView 限制 |
| 后端联动 | type=1, isEdit=1 | type=1, isEdit=0 |

---

## 6. showType=4:自定义页面 ⭐

### 6.1 完整 template

```vue
<!-- ChildModuleEdit.vue:70-72 -->
<template v-if="showType === 4">
    <div class="per-100" :id='_key'></div>
</template>
```

### 6.2 pageUrl 自动挂载机制

```js
// ChildModuleEdit.vue:236-265
async mounted () {
    let { pageUrl } = this.childData
    if (pageUrl) {
        let pageVue = await require(`@/views/${pageUrl}`).default
        const Instance = Vue.extend({
            ...pageVue,
            router,
            store,
        })
        this.pageInstance = new Instance({
            propsData: {
                ...this.childData,         // 原 childTab 配置
                mainFieldList: this.mainFieldList,  // 主表字段列表
                mainScope: this.mainScope,         // 主表作用域
                mainMdCode: this.mainMdCode,       // 主表模型编码
                id: this.mainId,                  // 主表 id
                scope: this,                      // 当前 ChildModuleEdit 实例
                getExtendScope: (scope) => this.extendScope[this._key] = scope
            }
        }).$mount(`#${this._key}`)
    }
}
```

### 6.3 自动注入的 propsData

| 属性 | 来源 | 说明 |
|---|---|---|
| `{...childData}` | 后端 childTab 配置 | 原配置全部透传 |
| `mainFieldList` | 主表字段列表 | 可读主表字段值 |
| `mainScope` | 主表 `ModuleEdit` 实例 | 可调用主表方法 |
| `mainMdCode` | 主表 mdCode | 知道"我是谁家的子表" |
| `id` | 主表 id | 主表记录 id |
| `scope` | 当前 ChildModuleEdit 实例 | 拿到父组件能力 |
| `getExtendScope` | 函数 | 让外部能拿到自定义页面作用域 |

### 6.4 自定义页面 Vue 文件示例

```vue
<!-- src/views/business/customChildPage.vue -->
<template>
    <div class="custom-child-page">
        <h3>主表 id: {{ id }}</h3>
        <p>主表字段列表: {{ mainFieldList.length }} 个字段</p>
        <el-button @click="callMainMethod">调用主表方法</el-button>
    </div>
</template>

<script>
export default {
    name: 'custom-child-page',
    props: {
        mainFieldList: Array,
        mainScope: Object,
        mainMdCode: String,
        id: String,
        scope: Object,
        getExtendScope: Function
    },
    methods: {
        callMainMethod () {
            // 调用主表 ModuleEdit 的方法
            this.mainScope.someMethod?.()
        }
    },
    mounted () {
        // 把当前作用域暴露给父组件
        this.getExtendScope?.(this)
    }
}
</script>
```

### 6.5 后端配置示例

```js
{
    module: 'business_a_item',
    showType: 4,              // ← 自定义页面
    pageUrl: 'business/customChildPage',  // ← 指向 src/views/business/customChildPage.vue
    relationEntityField: 'parentId'
}
```

> ⚠️ `pageUrl` 路径**省略 `@/views/` 前缀和 `.vue` 后缀**。

### 6.6 beforeDestroy 处理

```js
// ChildModuleEdit.vue:272-275
beforeDestroy () {
    // 由于挂载页面无法监听组件被销毁,所以将其放到挂载页面的methods方法中定义,手动调用
    typeof this.pageInstance?.beforeDestroy === 'function' && this.pageInstance.beforeDestroy()
}
```

> ⚠️ 自定义页面若需要在销毁时清理,**必须定义 `beforeDestroy` 方法**——框架会手动调用。

---

## 7. elseAttrs 注入(子模块拿主表信息的统一通道)

> 来源:[ChildModuleEdit.vue:206-216](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L206-L216)。

```js
elseAttrs () {
    return {
        mdCode: this.mdCode,                     // 子模块模型编码
        mainId: this.mainId,                     // 主表 id
        moduleName: this.moduleName,             // 子模块模型名称
        mainFieldList: this.mainFieldList,       // 主表字段列表
        mainScope: this.mainScope,               // 主表作用域(可调用主表方法)
        relationEntityField: this.relationEntityField,  // 关联字段名
        entityFieldValue: this._entityFieldValue, // 主表关联字段值
    }
}
```

**子模块中如何读**:

```js
// 在子模块 customSetting 的某个回调里(以子模块 moduleForm 为例)
const mainId = this.$attrs?.elseAttrs?.mainId
const mainScope = this.$attrs?.elseAttrs?.mainScope
const entityFieldValue = this.$attrs?.elseAttrs?.entityFieldValue
```

---

## 8. 易错点

| 错误 | 现象 | 解决 |
|---|---|---|
| `showType=3` | 框架无对应渲染,子模块不显示 | 改成 0/1/2/4 之一 |
| 1v1 关联配 showType=1 | 后端 select 不允许,前端不会渲染列表 | 改成 0 或 2 |
| `showType=4` 没配 `pageUrl` | 节点存在但内容为空 | 必填 `pageUrl` 指向 `src/views/{pageUrl}.vue` |
| `pageUrl` 路径写错 | 报错 `Cannot find module` | 路径**省略 `@/views/` 前缀和 `.vue` 后缀** |
| `showType=4` 自定义页面刷新失效 | 父组件销毁时未清理 | 自定义页面**必须定义 `beforeDestroy` 方法** |
| `entityField` 配错 | 主表里找不到该字段,出现警告 `关联字段X在主表中找不到` | 确保 `entityField` 是主表实际字段名 |

---

## 9. 下一步去哪

- **父子表通信**(子表如何拿主表数据 / 通知主表 / 自定义页面交互)→ [sub/parent-child-communication/SKILL.md](parent-child-communication/SKILL.md)
- **showStyle 展示风格** → [sub/show-style/SKILL.md](show-style/SKILL.md)
- **排版容器 + CSS 布局** → [sub/layout-container/SKILL.md](layout-container/SKILL.md)
- **childTab 字段配置 + 实战** → [sub/child-tab-config/SKILL.md](child-tab-config/SKILL.md)
- **总览** → [frontend-module-child-edit](../SKILL.md)