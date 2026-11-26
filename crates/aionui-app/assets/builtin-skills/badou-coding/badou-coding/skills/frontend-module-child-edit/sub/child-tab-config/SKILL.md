---
name: frontend-module-child-edit-child-tab-config
description: 八斗 Module 表单 customSetting — `childTab` 12 项字段完整速查表 + 5 种典型实战配置 + `afterModuleJSON` 改 childTab 的两种用法 + 不要碰的字段清单。当用户问"childTab 字段有哪些"、"relationEntityField 怎么配"、"子表怎么合并到同一个 Tab"、"用 customSetting 改子表行不行"、"怎么动态切换子表"时触发。
---

# 关联子表 — `childTab` 字段配置 + 实战

> 来源:[ChildModuleEdit.vue:91-166](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L91-L166) 的 props + [ModuleEdit/index.vue:750-770](../../../../../src/components/frame/Module/ModuleEdit/index.vue#L750-L770) 的 `getChildModuleAttr` + 业务实战案例。
>
> **父 skill**:[frontend-module-child-edit](../SKILL.md)

---

## 1. childTab 12 项字段速查表

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `module` | String | ✅ | 子模块模型编码(mdCode) |
| `moduleName` | String | ❌ | 子模块模型名称(显示用,fallback 到 `title`) |
| `title` | String | ❌ | 关联模块的展示标题(显示在 Tab 头或独立模块标题) |
| `tabName` | String | ❌ | **所属 Tab 名称**(同 tabName 的多个子模块合并到同一 Tab;showStyle=3 时清空) |
| `showTab` | String | ✅ | **是否展示**:`'0'`=隐藏 / `'1'`=展示 |
| `showStyle` | Number | ❌ | 展示风格:`1`=平级 Tab / `2`=子 Tab / `3`=顺序展示(默认 1) |
| `showType` | Number | ❌ | 展示类型:`0`=编辑表单 / `1`=列表 / `2`=查看表单 / `4`=自定义页面(默认 1) |
| `relationEntityField` | String | ✅ | **关联字段名**(主表里关联子表的字段,如 `orderId`) |
| `pageUrl` | String | ❌ | 仅 `showType=4` 时需要,指向 `src/views/{pageUrl}.vue` |
| `viewType` | String | ❌ | 表格视图(后端常配) |
| `isView` | Boolean | ❌ | 是否查看模式(覆盖父级 isView) |
| `entityField` | String | ❌ | 主表里作为关联值的字段名(若不填,默认 = `relationEntityField`) |

---

## 2. 三个核心字段的关系

```
主表有字段 orderId(主键) ←─────────────┐
                                        │ relationEntityField
                                        │ (主表里的字段名,
                                        │  框架会自动取其值作为子表的过滤条件)
关联子表配置.childTab.relationEntityField
                                        │
                                        │ = 主表里"指向子表"的字段名
                                        │
子表请求列表时                          │
params.defaultSearchParam 自动过滤        │
[{ name: 'orderId', value: 主表orderId的值, type: ... }] ← defaultParamsObj 由 ChildModuleEdit 自动生成
```

> 详细机制见 [ChildModuleEdit.vue:206-226](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L206-L226)。

### 2.1 relationEntityField vs entityField

| 字段 | 含义 | 默认值 |
|---|---|---|
| `relationEntityField` | **配置上**填的"关联字段名"(后端配置项) | 必填 |
| `entityField` | **主表里**作为关联值的字段名(运行时从主表读) | 不填则 = `relationEntityField` |

**实战场景**:
- 主表字段名 = 子表配置里写的关联名 → `entityField` 不用填
- 主表字段名 ≠ 子表配置里写的关联名(比如主表改了字段名) → 需要分别配

---

## 3. 5 种典型实战配置

### 3.1 订单主表 + 1 个明细列表(最常见)

```js
// 后端 childTab 配置
{
    module: 'order_item',
    title: '订单明细',
    tabName: '明细',
    showTab: '1',
    showStyle: 1,             // 平级 Tab
    showType: 1,              // 列表
    relationEntityField: 'orderId'
}
```

**渲染**:`[主表] [明细]`

### 3.2 主表 + 多 Tab(每个 Tab 多个子表)

```js
[
    { module: 'order_item',  title: '订单明细',  tabName: '订单信息', showTab: '1', showStyle: 1, showType: 1, relationEntityField: 'orderId' },
    { module: 'order_log',   title: '操作日志',  tabName: '订单信息', showTab: '1', showStyle: 1, showType: 1, relationEntityField: 'orderId' },
    { module: 'order_pay',   title: '支付信息',  tabName: '支付信息', showTab: '1', showStyle: 1, showType: 1, relationEntityField: 'orderId' },
    { module: 'order_refund', title: '退款记录', tabName: '售后',     showTab: '1', showStyle: 1, showType: 1, relationEntityField: 'orderId' }
]
```

**渲染**:`[主表] [订单信息(订单明细 + 操作日志)] [支付信息] [售后(退款记录)]`

### 3.3 主表 + 1 个编辑表单子表(1v1 关联)

```js
{
    module: 'order_address',
    title: '收货地址',
    tabName: '地址',
    showTab: '1',
    showStyle: 2,             // 子 Tab(主表在上)
    showType: 0,              // ⚠️ 1v1 用编辑表单
    relationEntityField: 'orderId'
}
```

> `showType=0` 时 `relationEntityField` 用来**定位子表单**(`addFormData` 自动注入,实现"主表保存后子表单自动带出")。

### 3.4 主表 + 顺序展示多个独立块(无 Tab)

```js
[
    { module: 'order_address', title: '收货地址', showTab: '1', showStyle: 3, showType: 0, relationEntityField: 'orderId' },
    { module: 'order_invoice', title: '发票信息', showTab: '1', showStyle: 3, showType: 0, relationEntityField: 'orderId' },
    { module: 'order_remark',  title: '订单备注', showTab: '1', showStyle: 3, showType: 2, relationEntityField: 'orderId' }
]
```

**渲染**(从上往下):
```
主表
收货地址(编辑表单)
发票信息(编辑表单)
订单备注(查看表单)
```

### 3.5 主表 + 平级 Tab + 顺序展示混合

```js
[
    // 第一个顺序展示 → mainDefault[1](主表是 mainDefault[0])
    { module: 'order_basic', title: '基本信息', showTab: '1', showStyle: 3, showType: 0, relationEntityField: 'orderId' },
    // 平级 Tab → mainTab 后续项
    { module: 'order_item',  title: '订单明细', tabName: '明细', showTab: '1', showStyle: 1, showType: 1, relationEntityField: 'orderId' },
    { module: 'order_log',   title: '操作日志', tabName: '日志', showTab: '1', showStyle: 1, showType: 1, relationEntityField: 'orderId' },
    // 末尾顺序展示 → defaultC
    { module: 'order_remark', title: '订单备注', showTab: '1', showStyle: 3, showType: 2, relationEntityField: 'orderId' }
]
```

**渲染**(从上往下):
```
主表(平级 Tab 头 + 实际内容)
基本信息(独立块,默认背景)
[明细] [日志]  ← 平级 Tab 内容
订单备注(独立块,默认背景)
```

### 3.6 主表 + 自定义页面子表(showType=4)

> 自定义页面 = **不是表单/列表/查看,而是任何自定义 Vue 组件**(图表、看板、3D 视图、流程图、外部 iframe 嵌入等)。

#### 3.6.1 后端 childTab 配置

```js
{
    module: 'business_a_item',          // mdCode 必填(框架会用它,但渲染不走 module-list/module-edit)
    title: '业务自定义视图',
    showTab: '1',
    showStyle: 1,                       // 排版风格与其他子表一致(平级 Tab)
    showType: 4,                        // ← 关键:自定义页面
    pageUrl: 'business/customChildPage', // ← 关键:指向 src/views/business/customChildPage.vue
    relationEntityField: 'parentId'      // 必填,但实际不会被过滤(列表行为)
}
```

> ⚠️ `pageUrl` 路径规则:
> - 相对于 `src/views/`,**不要**写 `@/views/` 前缀
> - **不要**写 `.vue` 后缀
> - 例如:`'business/customChildPage'` → `src/views/business/customChildPage.vue`

#### 3.6.2 自定义页面 Vue 文件

```vue
<!-- src/views/business/customChildPage.vue -->
<template>
    <div class="custom-child-page">
        <h3>主表记录: {{ id }}</h3>
        <p>主表字段数: {{ mainFieldList.length }}</p>
        <el-button @click="callMain">调用主表方法</el-button>
        <el-button @click="sendToParent">向主表发数据</el-button>
    </div>
</template>

<script>
export default {
    name: 'custom-child-page',
    props: {
        // ===== 框架自动注入的 props =====
        mainFieldList: { type: Array, default: () => [] },  // 主表字段列表
        mainScope: { type: Object, default: () => ({}) },    // 主表 ModuleEdit 实例
        mainMdCode: { type: String, default: '' },          // 主表模型编码
        id: { type: String, default: '' },                  // 主表记录 id
        scope: { type: Object, default: () => ({}) },       // ChildModuleEdit 实例
        getExtendScope: { type: Function, default: null },  // 暴露当前作用域给外部
        // ===== 后端 childTab 的其余字段透传 =====
        // 例如:title / showTab / relationEntityField 等
    },
    methods: {
        callMain () {
            // 调主表 ModuleEdit 的方法
            this.mainScope?.someMethod?.()
        },
        sendToParent () {
            // 通过 EventBus 通知主表
            this.$EventBus?.$emit('setData', { foo: 'bar' }, 'xxx')
        }
    },
    mounted () {
        // 把当前作用域暴露给父组件
        this.getExtendScope?.(this)
    },
    beforeDestroy () {
        // 清理逻辑(EventBus 监听、定时器、订阅等)
        // 框架在 ChildModuleEdit.beforeDestroy 中会自动调用
    }
}
</script>

<style scoped>
.custom-child-page {
    padding: 16px;
}
</style>
```

#### 3.6.3 实战:自定义页面调主表方法

业务场景:主表单保存后,通知"自定义页面"刷新数据。

```js
// 主表单的 customSetting(public/moduleJs/main/edit.js)
export default {
    buttons: [
        {
            id: 'save',
            name: '保存',
            click (btnObj) {
                // ... 框架默认保存逻辑
                // 保存成功后,通知所有挂载的"自定义页面"刷新
                this.$EventBus.$emit('refreshCustomChild', { mainId: this.detailId })
            }
        }
    ]
}
```

```js
// 自定义页面 mounted 中监听
mounted () {
    this.$EventBus.$on('refreshCustomChild', (data) => {
        this.refresh(data)
    })
}

beforeDestroy () {
    // 必须清理 EventBus 监听,否则会内存泄漏
    this.$EventBus.$off('refreshCustomChild')
}
```

#### 3.6.4 4 种典型自定义页面用途

| 用途 | pageUrl 示例 | 说明 |
|---|---|---|
| 业务图表/看板 | `'dashboard/orderDashboard'` | 用 echarts / 图表库展示主表相关的聚合数据 |
| 流程图/状态图 | `'flow/orderFlowChart'` | 渲染主表当前进度/审批流 |
| 外部 iframe 嵌入 | `'iframe/embedPage'` | 嵌入第三方页面,iframe 内通过 query 传主表 id |
| 富交互业务组件 | `'business/complexEditor'` | 复杂编辑器(如富文本、画板)框架默认表单不支持 |

#### 3.6.5 易错点

| 错误 | 现象 | 解决 |
|---|---|---|
| `pageUrl` 写 `@/views/xxx.vue` | 报错 `Cannot find module '@/views/@/views/xxx.vue'` | 路径**只写中间部分**:`'xxx'` |
| `pageUrl` 写 `xxx.vue` | 报错找不到 `.vue.vue` | 后缀省略 |
| 自定义页面刷新后报错 | 父组件销毁但 EventBus 监听未清理 | `beforeDestroy` 中 `$off` 监听 |
| 想读主表字段值用 `this.formData` | undefined | 主表字段值在 `this.mainFieldList` 中,或在子模块内走 `this.$attrs.elseAttrs` |
| 自定义页面没有滚动条 | 内容超出但显示不全 | 外层容器 `.custom-child-page` 加 `height: 100%; overflow: auto` |
| 修改 pageUrl 后没生效 | 页面还是旧的 | 自定义页面是**运行时 require**,改完**刷新页面**即可 |

---

## 4. 最小化 childTab 配置示例

```js
// 后端 sys_module_link 模型里一条记录的 JSON 示意
{
    "module": "wjx_form_item",       // 子模块 mdCode
    "title": "测试明细",
    "tabName": "明细",
    "showTab": "1",                  // 展示
    "showStyle": 1,                  // 平级 Tab
    "showType": 1,                   // 列表
    "relationEntityField": "formId"  // 关联主表的 formId 字段
}
```

---

## 5. customSetting 真的需要碰 childTab 吗?(90% 场景不需要)

### 5.1 90% 场景:走 `afterModuleJSON` 改 childTab

```js
// public/moduleJs/order_main/edit.js
export default {
    afterModuleJSON (module) {
        // this 是 moduleEditCode 实例
        if (module.childTab) {
            module.childTab.forEach(tab => {
                if (tab.module === 'order_item') {
                    tab.title = '订单明细(必填)'           // 改标题
                    tab.tabName = '订单'                   // 改 tabName 触发合并
                    tab.showStyle = 2                      // 改成子 Tab
                    tab.showType = 1                       // 改成列表
                }
            })
        }
        return module
    }
}
```

> 业务方写 customSetting 改 childTab,**用 `afterModuleJSON`**,**不是**直接 return 一个新对象。

### 5.2 极少数场景:动态增删子表

```js
// 比如:根据主表的"业务类型"字段,动态切换不同的关联子表
afterModuleJSON (module) {
    const businessType = this.formData?.businessType?.value
    if (businessType === 'A') {
        module.childTab = [
            { module: 'business_a_item', title: 'A 类明细', showTab: '1', showStyle: 1, showType: 1, relationEntityField: 'parentId', tabName: '明细' }
        ]
    } else {
        module.childTab = [
            { module: 'business_b_item', title: 'B 类明细', showTab: '1', showStyle: 1, showType: 1, relationEntityField: 'parentId', tabName: '明细' }
        ]
    }
    return module
}
```

---

## 6. 不要碰的字段

| 字段 | 原因 |
|---|---|
| `module` | 改错了**子模块加载不出来**,且前端难以验证 |
| `relationEntityField` | 必须与主表实际字段一致,改错**请求列表返回空数据** |
| `showType=3` | 根本不存在,框架不会渲染(被忽略) |
| `tabName` 当 `showStyle=3` | 后端强制清空,前端赋值无效 |

---

## 7. tabName 合并机制详解

> 来源:[ModuleEdit/index.vue:669-692](../../../../../src/components/frame/Module/ModuleEdit/index.vue#L669-L692) 的 `addTabItem`。

```js
addTabItem (tabList, addItem, option) {
    let { tabName, showStyle = 1 } = addItem
    let _tabIndex = tabList.findIndex(i => i.tabName === tabName && i.showStyle === showStyle)
    if (~_tabIndex) {
        // 找到同名 tab → 往该 tab 的 children 里 push
        tabList[_tabIndex].children[_operate](addItem)
        return
    }
    // 找不到 → 新建一个 tab 项
    tabList[_operate]({
        [this.tabKey.text]: tabName,
        showStyle,
        children: [addItem]
    })
}
```

**口诀**:**tabName 相同的子表 + 相同 showStyle → 合并到同一 Tab 内**。

### 7.1 同 tabName + 不同 showStyle 不会合并

```js
[
    { module: 'item', title: 'A', tabName: '同一名', showStyle: 1, ... },  // ← 进入 mainTab
    { module: 'item', title: 'B', tabName: '同一名', showStyle: 2, ... }   // ← 进入 linkTab(不合并!)
]
```

---

## 8. 关键事实速查

| 项 | 说明 |
|---|---|
| `showTab='0'` | 该子模块**完全隐藏**,不走任何容器 |
| tabName 合并规则 | 同 tabName + 同 showStyle 的子模块**合并到同一 Tab 内** |
| 主表始终在 mainDefault[0] | 即使存在平级 Tab,主表也会同时作为 `mainTab[0]` 的内容 |
| `isInLink=true` | ChildModuleEdit 传给子模块,让按钮事件**过滤掉不允许在子模块出现的按钮** |
| `addFormData` 自动注入 | ChildModuleEdit 自动生成 `{[relationEntityField]: 主表关联字段值}`,实现"新增子表数据自动带上主表 id" |
| `elseAttrs` 注入 | 传给子模块,让子模块能取到主表字段列表、主表作用域、关联字段值等 |

---

## 9. 常见问题

| 问题 | 现象 | 原因 / 解决 |
|---|---|---|
| 子表没显示 | 页面只有主表 | 后端 `showTab` 没配成 `'1'`,或子模块模型编码(`module`)写错 |
| 子表请求列表返回空 | 列表没数据 | `relationEntityField` 配错,**主表里没有该字段**会发警告 `关联字段X在主表中找不到` |
| Tab 头出现但内容空 | tab 配置了但没渲染 | 后端 `module` 字段写错(子模块 mdCode 不存在) |
| 子表 Tab 顺序不对 | Tab 顺序与预期不符 | Tab 顺序由**后端 sort 字段**决定,前端无法控制 |
| 想"主表不带标题" | 主表有标题 | 子表自带标题隐藏规则对主表不生效,主表标题 = `this.name`(`ModuleEdit` prop) |
| 想让子模块按钮也出现在主模块 | 主模块按钮区没该按钮 | `isInLink` 过滤了——子模块的按钮**只在子模块内可见**,不会上升到主模块 |
| 改了 `showStyle=3` 但页面还是有 Tab | 配置没生效 | 检查 `childTab` 里是否同时存在 `showStyle=1` 的项——只要有 1 个平级 Tab,整页就有 Tab 头 |
| `showType=4` 没渲染 | 自定义页面没出来 | 检查 `pageUrl` 是否正确(指向 `src/views/{pageUrl}.vue`),且 export default 必须是 Vue 组件 |
| 想在主表和子表之间加自定义内容 | 主表下、子表上有"空隙" | 不能在框架内置结构中插入,**只能**通过 `contentRender` 改主表自身;或在主模块后追加一个 `showStyle=3 + showType=0` 的"伪装子表" |

---

## 10. 下一步去哪

- **父子表通信**(子表如何拿主表数据 / 通知主表 / 自定义页面交互)→ [sub/parent-child-communication/SKILL.md](parent-child-communication/SKILL.md)
- **showStyle 展示风格** → [sub/show-style/SKILL.md](show-style/SKILL.md)
- **showType 渲染方式** → [sub/show-type/SKILL.md](show-type/SKILL.md)
- **排版容器 + CSS 布局** → [sub/layout-container/SKILL.md](layout-container/SKILL.md)
- **总览** → [frontend-module-child-edit](../SKILL.md)