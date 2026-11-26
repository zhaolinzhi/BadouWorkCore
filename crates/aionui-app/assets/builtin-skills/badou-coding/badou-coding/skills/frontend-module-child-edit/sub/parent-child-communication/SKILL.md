---
name: frontend-module-child-edit-parent-child-communication
description: 八斗 Module 表单 customSetting — 关联子表与主表之间的**双向通信**(3 种 showType 全覆盖)。当用户问"子表怎么拿主表数据"、"子表怎么读主表字段"、"子表动态必填"、"父子表怎么联动"、"子表怎么通知主表"时触发。覆盖 4 条主→子通道(elseAttrs / addFormData / elseAttrs.mainScope / props 注入)、3 条子→主通道(mainScope 回调 / getExtendScope 反向通信)、3 种 showType 的具体取值方式与实战。

---

**⚠️ EventBus 在业务 JS 中不推荐**(详见 §3.2)— customSetting 不是 Vue 实例,无法清理监听会内存泄漏。

# 关联子表 — 父子表双向通信详解

> 本 skill 专门讲**子表与主表之间怎么传数据**——按 3 种 `showType` 分别讲"主表→子表"和"子表→主表"两条方向。
>
> **父 skill**:[frontend-module-child-edit](../SKILL.md)
>
> 其他 sub skill:[show-style](sub/show-style/SKILL.md)/ [layout-container](sub/layout-container/SKILL.md)/ [show-type](sub/show-type/SKILL.md)/ [child-tab-config](sub/child-tab-config/SKILL.md)

---

## 1. 一图看懂:父子表通信的 4 类通道

```
主表(ModuleEdit 实例)
    │
    │ ──── 主表 → 子表 ────
    │   ① elseAttrs(主表字段 / 主表作用域 / 主表 id / 关联字段值)
    │   ② addFormData(自动注入关联值,新增时生效)
    │   ③ showType=4 时 props 注入(mainFieldList / mainScope / id / scope / getExtendScope)
    │
    │ ──── 子表 → 主表 ────
    │   ④ mainScope.something()(调主表方法,主推)
    │   ⑤ ⚠️ EventBus —— 业务 JS 完全不用(framework 内部使用的内置事件,业务无法可靠触发;自定义事件无清理位置会内存泄漏),见 §3.2
    │   ⑥ getExtendScope()(仅 showType=4,反向让主表后续可调)
    └─────────────────────────────────
```

> ⚠️ **通道 ① 是核心**——3 种 showType 都会接收 `elseAttrs`,它包含主表所有"可暴露"的数据。
> **通道 ④ 是反向核心**——`mainScope` 让子表能调主表任何方法,包括 `getFormRef()` / `$emit('refreshForm')` / `$message` / `pushPage` 等组件实例方法。
> **通道 ⑤ EventBus 不推荐业务使用**——framework 内部用了 `setData` / `getChildTabData` 等事件,但那是 framework 自己用的;业务 JS 既不能可靠触发,自定义又会内存泄漏,详见 §3.2。
> **当前主表响应子表的全部姿势**:
> - `mainScope.xxx()` / `mainScope.$set()`(主推)
> - `getExtendScope()`(showType=4 反向通信)
> - EventBus 不在业务 JS 的可行范围

---

## 2. 4 条主表 → 子表通道详解

### 2.1 通道 ①:`elseAttrs`(主→子的统一通道)

> 来源:[ChildModuleEdit.vue:206-216](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L206-L216)。
> 接收方:`module-list`、`module-form`、`module-edit-code`(3 种组件都接收)。

#### 2.1.1 elseAttrs 内容

```js
elseAttrs: {
    mdCode: '子模块模型编码',
    mainId: '主表记录 id',
    moduleName: '子模块模型名称',
    mainFieldList: [/* 主表字段数组,每项含 name / value / type 等 */],
    mainScope: { /* 主表 ModuleEdit 实例,可调任何方法 */ },
    relationEntityField: '主表里指向子表的字段名',
    entityFieldValue: '主表关联字段的具体值'
}
```

#### 2.1.2 子表中读主表数据(3 种写法)

```js
// ✅ 写法 1:从 $attrs 取(适用于 ModuleList / ModuleForm / ModuleEditCode)
const mainFieldList = this.$attrs?.elseAttrs?.mainFieldList
const mainId = this.$attrs?.elseAttrs?.mainId
const mainScope = this.$attrs?.elseAttrs?.mainScope

// ✅ 写法 2:从 $attrs.elseAttrs 直接解构(更简洁)
const { mainFieldList, mainScope, entityFieldValue } = this.$attrs?.elseAttrs || {}

// ✅ 写法 3:从 fieldList 反查(更稳,formData 改了 fieldList 里字段的 value 也跟着变)
const orderField = mainFieldList?.find(f => f.name === 'orderId')
const orderId = orderField?.value
```

#### 2.1.3 this 在不同 key 下访问 elseAttrs 的差异

| this 类型 | 取法 |
|---|---|
| **moduleList**(子表列表组件) | `this.$attrs.elseAttrs.mainFieldList` |
| **moduleForm / mForm**(子表编辑表单) | `this.$attrs.elseAttrs.mainFieldList` |
| **moduleEditCode**(整个子表 Vue 实例) | `this.$attrs.elseAttrs.mainFieldList` |
| **子模块 customSetting**的 `valueChange` 等回调 | 回调参数 `formScope` 上挂 `elseAttrs`(因为子模块组件把这东西透传下去) |

> ⚠️ 注意 `moduleForm` 的 prop 有声明 `elseAttrs`,所以 `this.elseAttrs` **也能访问**(无需走 `$attrs`)。但走 `$attrs` 是更稳的写法,所有 3 种组件都通用。

---

### 2.2 通道 ②:`addFormData`(新增时自动注入)

> 来源:[ChildModuleEdit.vue:222-226](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L222-L226)。

#### 2.2.1 框架自动生成

```js
// 子表新增一条数据时,框架自动注入了:
addFormData = {
    [relationEntityField]: entityFieldValue  // 例如: { orderId: '主表orderId的值' }
}
```

#### 2.2.2 子模块用 customSetting 处理 addFormData

```js
// public/moduleJs/order_item/edit.js(子模块配置)
export default {
    afterModuleJSON (module) {
        // this 是 moduleEditCode 实例
        // addFormData 已经在 mounted 时注入到 formData 中
        // 在这里的 this.formData 里能看到
        return module
    }
}
```

#### 2.2.3 易错点

- `addFormData` **只在新增时生效**,编辑时不生效(编辑时走详情接口拿数据)
- `addFormData` 的 key 是 `relationEntityField`(可能 ≠ 主表真实字段名,要看 entityField 是否单独配)

---

### 2.3 通道 ③:`showType=4` 时的 props 注入

> 来源:[ChildModuleEdit.vue:240-264](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L240-L264)。

#### 2.3.1 框架自动注入的 props

| prop | 来源 | 说明 |
|---|---|---|
| `mainFieldList` | 主表字段列表 | 可读主表所有字段值 |
| `mainScope` | 主表 ModuleEdit 实例 | 可调主表任何方法 |
| `mainMdCode` | 主表模型编码 | 知道"我是谁家的子表" |
| `id` | 主表记录 id | 主表 id |
| `scope` | ChildModuleEdit 实例 | 拿到父组件能力 |
| `getExtendScope` | 函数 | 把当前作用域暴露给外部 |

#### 2.3.2 自定义页面取值示例

```vue
<template>
    <div>
        <p>主表 id: {{ id }}</p>
        <p>主表字段数: {{ mainFieldList.length }}</p>
    </div>
</template>

<script>
export default {
    props: {
        mainFieldList: Array,
        mainScope: Object,
        mainMdCode: String,
        id: String,
        scope: Object,
        getExtendScope: Function
    },
    mounted () {
        // 主表的字段值
        const mainOrderId = this.mainFieldList?.find(f => f.name === 'orderId')?.value
        // 调主表方法
        this.mainScope?.getFormRef?.()
    }
}
</script>
```

---

## 3. 3 条子表 → 主表通道详解

### 3.1 通道 ④:`mainScope.something()`(最常用)

> 通过 `elseAttrs.mainScope` 或 props 中的 `mainScope`(showType=4)拿到主表实例,直接调方法。

#### 3.1.1 主表暴露的常用方法(来自 `ModuleEdit/index.vue`)

| 方法 | 用途 | 来源 |
|---|---|---|
| `this.getFormRef()` | 拿到主表单的 mForm 实例,可调 `validateForm()` / `validateField()` / `resetFields()`(注意:**没有 setFieldValue**) | [ModuleEdit.vue:854-857](../../../../../src/components/frame/Module/ModuleEdit/index.vue#L854-L857) |
| `this.$emit('refreshForm')` | 通知主表刷新整个表单 | — |
| `this.detailId` | 主表 id | — |
| `this.formData` | 主表单值 | — |
| `this.fieldList` | 主表字段列表 | — |
| `this.$message.success(...)` | 消息提示 | — |
| `this.$router.push(...)` | 路由跳转 | — |
| `this.pushPage(...)` | 框架的 Tab 化跳转 | — |

#### 3.1.2 子表调用主表方法示例

```js
// 子表 customSetting 里(以 moduleList / moduleForm / moduleEditCode 为主)
const mainScope = this.$attrs?.elseAttrs?.mainScope

// 1. 拿到主表的表单引用
const formRef = mainScope?.getFormRef?.()

// 2. 触发主表刷新
mainScope?.$emit?.('refreshForm')

// 3. 主动滚动到主表某个字段(若主表组件实现了 scrollToField)
mainScope?.scrollToField?.('orderStatus')

// 4. 弹出一个确认框(用主表的 Element UI)
mainScope?.$confirm?.('确定操作?', '提示')
```

---

### 3.2 通道 ⑤:`this.$EventBus` 事件总线 ⚠️ 业务 JS **不用**

> 来源:[ChildModuleEdit.vue:266-270](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L266-L270)、[ModuleForm.vue:392](../../../../../src/components/frame/Module/ModuleForm/index.vue#L392)。

#### 3.2.1 ❌ 核心结论:业务模块 JS 完全不用 EventBus

> **验证证据**(grep 全 src + 全 public/moduleJs):
> - framework 用了几个 EventBus 监听(`EventBus.$on("setData", ...)` / `EventBus.$on("getChildTabData", ...)`),但**这些都是 framework 自己内部**用的,业务代码**没有**触发过它们
> - 业务模块(`public/moduleJs/`)中**所有 EventBus 用法都是 system 模块**(`sys_module_field_list.js` / `sys_md_module_edit.js` 等),用于**模块设计器**之间的数据传递(`setPageSetting` / `setFlowData` / `setLinkData` / `setBtnPowerData`),**不是普通业务模块的子表通信**
>
> **结论**:普通业务的子表通信**不需要 EventBus**——**framework 内置事件业务触发不了,业务自定义又无清理位置**。

#### 3.2.2 为什么不推荐业务 JS 用 EventBus(逐条理由)

| 风险 | 说明 |
|---|---|
| **`customSetting` 不是 Vue 实例** | 主表 / 子表 customSetting 里写 `mounted` / `beforeDestroy` **永不触发** |
| **没法清理监听** | 业务 JS 无法拿到合适的"组件销毁"时机去 `$off` 监听,导致:<br>· 监听重复挂载,回调被多次触发<br>· 监听持有被销毁组件的引用,**内存泄漏** |
| **没有接收方** | 主表 customSetting 写不了 `mounted` 接 EventBus,发出去的自定义信号"石沉大海" |
| **调试困难** | 事件链路跨多文件,出错难追 |

#### 3.2.3 真正可行的"主表响应子表"姿势

```js
// ✅ 推荐:用 mainScope 直接调主表动作(没有任何清理负担)
export default {
    valueChange: {
        itemType (formScope, fieldName, value) {
            const { mainScope } = this.$attrs?.elseAttrs || {}
            if (value === 'important' && mainScope) {
                // 改字段:直接 mainScope.$set
                const f = mainScope.tempFieldList?.find(x => x.name === 'riskLevel')
                if (f) mainScope.$set(f, 'value', 'high')

                // 调方法:直接 mainScope.xxx()
                mainScope.refreshTable?.()
                mainScope.$message?.success?.('主表已响应子表变更')
            }
        }
    }
}
```

> **总结**:业务模块 JS 中,**完全不用 EventBus**。需要通信就用 **`mainScope.xxx()`** 或 **`mainScope.$set()`** 直接调——这是 Vue 引用语义,即时同步,无清理负担。

#### 3.2.4 易错点

- **业务 JS 中不要 `$on` / `$emit` 任何 EventBus 事件**——既不能清理,也没有 framework 维护的接收方
- 即便你"看到 framework 监听了 setData",这个监听**由 ChildModuleEdit 内部使用**,外部业务模块不能可靠地触发它做"主表响应"
- `EventBus` 是**全局**的,**同名事件**所有页面都能收到 — 不要给自定义事件起通用名(避免全局污染)

---

### 3.3 通道 ⑥:`getExtendScope()`(showType=4 专属,反向通信)

> 来源:[ChildModuleEdit.vue:262-263](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L262-L263)。

#### 3.3.1 框架如何暴露

```js
// 在 ChildModuleEdit(父组件,Vue 实例)的 mounted 中执行
new Instance({
    propsData: {
        getExtendScope: (scope) => this.extendScope[this._key] = scope
    }
}).$mount(`#${this._key}`)
```

**机制**:
- 子模块**自己**调 `this.getExtendScope(this)` → 把自己的 Vue 实例**存**到 ChildModuleEdit 的 `extendScope['mountId0']` 里
- 后续任何组件**知道 Key(`'mountId0'`)** 的都能从这个字典里拿到子模块作用域

#### 3.3.2 使用场景

**业务场景:主表某个按钮,需要调"挂在某个子表"上的自定义页面里的某个方法**。

```js
// 自定义页面 mounted 时
mounted () {
    this.getExtendScope?.(this)  // 暴露自己
}

// 自定义页面提供方法
methods: {
    reload () {
        console.log('我被重新加载了')
    }
}

// ===== 主表单 customSetting =====
// 在主表某个按钮 click 里,反向调用
methods: {
    reloadChild () {
        // 找到 ChildModuleEdit 实例(通过 ref 或其他方式)
        const childInstance = this.$refs.someChild
        const childScope = childInstance?.extendScope?.['mountId0']
        childScope?.reload?.()
    }
}
```

#### 3.3.3 易错点

- **必须自己调** `getExtendScope(this)` 才会被存,**框架不会自动调**
- Key 是 `mountId${index}`,其中 `index` 是 ChildModuleEdit 的 `index` prop(由 ModuleEdit 传入)
- 如果不知道 key,可以用遍历:`Object.values(childInstance.extendScope)[0]`

---

## 4. showType=1(子表列表):拿主表数据 + 实战

### 4.1 基本拿法

```js
// 子表 customSetting(public/moduleJs/order_item/list.js)或子表按钮 click 里
const elseAttrs = this.$attrs?.elseAttrs || {}
const { mainFieldList, mainScope, entityFieldValue } = elseAttrs

// 主表某个字段值(推荐:从 mainFieldList 反查)
const mainOrderId = mainFieldList?.find(f => f.name === 'orderId')?.value
const mainOrderStatus = mainFieldList?.find(f => f.name === 'status')?.value
```

### 4.2 实战 1:列表新增按钮,根据主表状态决定是否可点

> ⚠️ **`isHide` 函数内的 `this` 指向 `btnObj`(按钮对象),不是 moduleList**——这一点在 `this` 指向中是常见陷阱(`frontend-module-tree-list SKILL §3` 也明确标注过)。
> 想在按钮配置里读列表实例,推荐改用 **`buttons: function(defaultBtnList) {}` 函数形式**,那个 `this` 指向 moduleList。

```js
// ✅ 推荐写法:用 buttons 函数形式(此时 this 指向 moduleList)
buttons: function (defaultBtnList) {
    const _btnList = [...defaultBtnList]
    const { mainFieldList } = this.$attrs?.elseAttrs || {}
    const mainStatus = mainFieldList?.find(f => f.name === 'status')?.value

    // 主表状态为"已完成"时,隐藏 add 按钮
    return _btnList.map(b => {
        if (b.id === 'add') {
            b.isHide = mainStatus === 'done'
        }
        return b
    })
}
```

```js
// ❌ 错误写法:isHide 函数内 this 是按钮对象,this.$attrs 是 undefined
buttons: [
    {
        id: 'add',
        isHide: function (btnObj) {
            // this = btnObj(按钮对象),没有 $attrs,会报 Cannot read property '$attrs' of undefined
            const { mainFieldList } = this.$attrs?.elseAttrs || {}  // ← 报错
            return mainFieldList?.find(f => f.name === 'status')?.value === 'done'
        },
        click (btnObj) {
            // ❌ this 也不是 moduleList,btnObj 没有 $router 等组件能力
        }
    }
]
```

```js
// ⚠️ 替代写法 1:用箭头函数 + 外层 closure 拿到 moduleList
// (但这种写法需要在 moduleList 实例上能引用到,可读性差)
```

```js
// ⚠️ 替代写法 2:用 disabled(若 isHide 不满足业务)
// disabled 的 this 同样指向 btnObj,且不支持函数式返回值,只能用静态 boolean
// 所以 disabled 场景下无法读主表字段——首选仍是 buttons 函数形式
```

### 4.3 实战 2:列表搜索栏默认值,根据主表过滤

```js
// 子表列表 customSetting
beforeRender (fieldList) {
    // this 是 mList 实例
    const { mainFieldList } = this.$attrs?.elseAttrs || {}
    const mainDeptId = mainFieldList?.find(f => f.name === 'deptId')?.value

    // 把搜索栏的 deptId 字段默认值设为主表的 deptId
    const deptField = this.fieldList?.find(f => f.name === 'deptId')
    if (deptField) {
        deptField.value = mainDeptId
    }
    return fieldList
}
```

### 4.4 实战 3:子表行点击 / 双击,跳转到主表

```js
// public/moduleJs/order_item/list.js
dblClick: function (row) {
    // this 是 moduleList 实例
    const { mainScope } = this.$attrs?.elseAttrs || {}
    // 跳到主表详情
    const mainId = mainScope?.detailId
    if (mainId) {
        this.$router.push({
            path: `/module/stander/edit/order_main/${mainId}`
        })
    }
}
```

---

## 5. showType=0/2(子表编辑表单):拿主表数据 + 实战

### 5.1 基本拿法(编辑表单内)

```js
// 子表编辑表单 customSetting(public/moduleJs/order_item/edit.js)
beforeRender (fieldList) {
    // this 是 moduleForm 实例
    // 字段值在 this.$attrs.formData 里(每个字段 .value 取值)
    const { mainFieldList, entityFieldValue } = this.$attrs?.elseAttrs || {}

    // 读主表某个字段值
    const mainOrderType = mainFieldList?.find(f => f.name === 'type')?.value

    // 反查到主表的关联字段值(就是 entityFieldValue)
    const mainOrderId = entityFieldValue

    return fieldList
}
```

### 5.2 实战 1:子表单动态必填(基于主表某字段)

```js
// public/moduleJs/order_item/edit.js
beforeRender (fieldList) {
    // this 是 moduleForm 实例
    const { mainFieldList } = this.$attrs?.elseAttrs || {}
    const mainOrderType = mainFieldList?.find(f => f.name === 'type')?.value

    // 主表是"特殊订单"时,子表的"specialReason"字段必填
    const reasonField = this.fieldList.find(f => f.name === 'specialReason')
    if (reasonField && mainOrderType === 'special') {
        reasonField.required = true
        reasonField.rules = [
            ...(reasonField.rules || []),
            { required: true, message: '特殊订单必须填写原因', trigger: 'blur' }
        ]
    }
    return fieldList
}
```

### 5.3 实战 2:子表单字段联动(基于主表值)

> ⚠️ **没有 `setFieldValue` 这个方法**——`mainFormRef`(`getFormRef()` 返回值)和 `mainScope` 上都没有。
>
> **核心结论:既然能拿到 `mainScope`,就能直接改主表的 `tempFieldList` —— 优于绕 EventBus**。
> 详细论述见 §3.2 (EventBus 在业务 JS 中不推荐)。

#### ✅ 推荐方案:直接改主表 `tempFieldList`

```js
// 子表 customSetting(public/moduleJs/order_item/edit.js)
valueChange: {
    // 子表单的 itemType 字段变化 → 直接改主表的 riskLevel
    itemType (formScope, fieldName, value) {
        // this 是 moduleForm 实例
        const { mainScope } = this.$attrs?.elseAttrs || {}
        if (value !== 'important' || !mainScope) return

        // ✅ 主表的响应式字段数据在 mainScope.tempFieldList
        // (mainScope.fieldList 是 props,不可变更;tempFieldList 才是真正响应式的 data)
        const targetField = mainScope.tempFieldList?.find(f => f.name === 'riskLevel')
        if (targetField) {
            // 用 mainScope 的 $set 触发响应式(等价于 this.$set 但走主表的 reactivity)
            mainScope.$set(targetField, 'value', 'high')
            // 字段对象是 mainScope.tempFieldList[i] 引用,Vue 自动更新 UI
        }
    }
}
```

> **原理**:`ChildModuleEdit` 把 `mainFieldList: this.tempFieldList`([ModuleEdit/index.vue:754](../../../../../src/components/frame/Module/ModuleEdit/index.vue#L754))传给子表——`mainFieldList` 与主表的 `tempFieldList` 是**同一个对象数组**(Vue 的引用语义)。改其中一个对象的属性,两边都看见。**不需要** `$emit('update:fieldList', ...)` 这种"通知主表重新拉"的操作。

> ⚠️ **EventBus 不是本场景的替代方案**——改字段**只有本节的直接修改姿势**真正可行(详见 §3.2 完整论述:业务 JS 中不能用自定义 EventBus,因为没法清理监听)。

### 5.4 实战 3:子表单保存后,通知主表刷新

```js
// public/moduleJs/order_item/edit.js(子表保存按钮重写)
export default {
    buttons: [
        {
            id: 'save',
            name: '保存',
            click (btnObj) {
                // ... 走默认保存(或自定义保存逻辑)
                // 保存成功后,通知主表
                const { mainScope } = this.$attrs?.elseAttrs || {}
                mainScope?.$emit?.('refreshForm')
            }
        }
    ]
}
```

> 注意:`refreshForm` 是**整个表单**(主表 + 所有子表)都刷新,可能太重;若只要刷主表某个字段,**首选 `mainScope.$set(targetField, 'value', newVal)`**(详见 §5.3,直接走主表的响应式)。

### 5.5 实战 4:子表单提交时校验主表状态

```js
// public/moduleJs/order_item/edit.js
validateRule (fieldList) {
    // 校验前先检查主表状态
    return [
        {
            validator: (rule, value, callback) => {
                const { mainFieldList } = this.$attrs?.elseAttrs || {}
                const mainStatus = mainFieldList?.find(f => f.name === 'status')?.value
                if (mainStatus === 'locked') {
                    callback(new Error('主表已锁定,子表无法保存'))
                } else {
                    callback()
                }
            },
            trigger: 'blur'
        }
    ]
}
```

---

## 6. showType=4(子表自定义页面):双向交互 + 实战

### 6.0 关于 `mounted` / `beforeDestroy` 的事实

> 来源:[ChildModuleEdit.vue:233-275](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L233-L275)。

| 钩子 | 谁触发 | 会不会被调 |
|---|---|---|
| `mounted()` | **Vue 自动触发**(`new Instance().$mount()` 后) | ✅ 会触发(前提:pageUrl 加载成功 + `export default {}` 是标准 Vue 组件) |
| `beforeDestroy()` | **ChildModuleEdit 手动调**:`this.pageInstance.beforeDestroy()`([L274](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L274)) | ✅ 会触发(前提:export default 里**显式定义**了此方法) |

**容易"看起来不调用"的常见原因**:
1. `pageUrl` 加载失败(require 报错,根本没生成 pageInstance)
2. 自定义页面**不是 `export default { ... }` 标准 Vue 组件**(比如纯 setup 写法 / 非 Vue SFC)
3. `beforeDestroy` 没在 export default 里**显式定义**——`pageInstance.beforeDestroy` 是 undefined

**最稳健的不依赖 Vue 生命周期的姿势**:把 EventBus 监听 / 清理写在 **ChildModuleEdit 的 mounted/beforeDestroy** 里(或通过 props 传 `onInit/onDestroy` 回调由 ChildModuleEdit 在正确时机调用,详见 §6.1 备选方案 B)。

---

### 6.1 主表 → 子表(通过 props)

#### 方案 A:标准 Vue 组件(注意生命周期触发条件)

```vue
<!-- src/views/business/customChildPage.vue -->
<template>
    <div>
        <h3>主表记录 id: {{ id }}</h3>
        <el-button @click="callMain">调主表方法</el-button>
        <el-button @click="notifyMain">通知主表刷新</el-button>
        <el-button @click="exposeMe">暴露自己给主表</el-button>
    </div>
</template>

<script>
export default {
    props: {
        mainFieldList: Array,
        mainScope: Object,
        mainMdCode: String,
        id: String,
        scope: Object,
        getExtendScope: Function
    },
    methods: {
        callMain () {
            const formRef = this.mainScope?.getFormRef?.()
            formRef?.validateForm?.().then(formData => {
                console.log('主表当前表单数据', formData)
            })
        },
        notifyMain () {
            // 改字段:直接走 mainScope.tempFieldList(无需 EventBus)
            const targetField = this.mainScope?.tempFieldList?.find(f => f.name === 'updatedByChild')
            if (targetField) {
                this.mainScope.$set(targetField, 'value', true)
            }
            // 通知主表动作:直接调 mainScope 方法(避免 EventBus 监听难清理的问题)
            this.mainScope?.refreshTable?.()
            this.mainScope?.$message?.success?.('主表已响应子组件调用')
        },
        exposeMe () {
            // 把当前作用域暴露给主表(后续主表可反向调用)
            this.getExtendScope?.(this)
        },
        reload () {
            console.log('自定义页面 reload 被主表触发')
            this.refresh()
        },
        refresh () {
            // 自定义的刷新逻辑
        }
    }
    // 注意:不在自定义页面中新增自定义 EventBus 监听,避免清理负担
    // 通信一律走 props 注入的 mainScope 直接调
}
</script>
```

#### ✅ 方案 B:更稳健的姿势——通过 props 传 `onInit` / `onDestroy` 回调

> **适用场景**:
> 1. 你的自定义页面不是标准 Vue 组件,生命周期不触发
> 2. 不确定 pageUrl 能否正确加载,但仍想稳妥地初始化与清理
> 3. 想让主表**主动控制**子页面的初始化时机

原理:**ChildModuleEdit 是父组件,它的 `mounted` / `beforeDestroy` 一定被触发**(标准 Vue 父子组件生命周期)。把子页面的初始化逻辑通过 props 传回调进来,由父组件在自己生命周期里调用,绕过子组件生命周期。

**步骤 1:扩展 `ChildModuleEdit` 注入新 prop**(后端模块设计器需要配 `onInit` / `onDestroy` 字段)

> ⚠️ 此方案需要项目里 `ChildModuleEdit.vue` 模板中给 `<component>` 加 `:onInit` / `:onDestroy` props,且透传到自定义页面。

**步骤 2:自定义页面用 props 接收回调**

```vue
<template>
    <div>
        <h3>主表 id: {{ id }}</h3>
        <el-button @click="notifyMain">通知主表</el-button>
    </div>
</template>

<script>
export default {
    props: {
        mainFieldList: Array,
        mainScope: Object,
        mainMdCode: String,
        id: String,
        scope: Object,
        getExtendScope: Function,
        // ✅ 新增:由 ChildModuleEdit.mounted 调用
        onInit: { type: Function, default: null },
        // ✅ 新增:由 ChildModuleEdit.beforeDestroy 调用
        onDestroy: { type: Function, default: null }
    },
    methods: {
        init () {
            // 框架调进来的初始化入口
            console.log('自定义页面 init 被 ChildModuleEdit 调用 ✅')
            // ⚠️ 不要在 init 中新增自定义 EventBus 监听——会引入清理负担
            // 通信一律走 props 注入的 mainScope
        },
        destroy () {
            // 框架调进来的清理入口
            console.log('自定义页面 destroy 被 ChildModuleEdit 调用 ✅')
            // 清理定时器 / 自定义资源(非 EventBus)
        },
        reload () {
            console.log('reload 被触发')
            this.refresh()
        },
        refresh () {},
        notifyMain () {
            // 改字段或通知主表(同 §5.3)
            const f = this.mainScope?.tempFieldList?.find(x => x.name === 'updatedByChild')
            if (f) this.mainScope.$set(f, 'value', true)
            // 调主表方法(替代 EventBus 通知)
            this.mainScope?.refreshTable?.()
        }
    },
    // 注意:**这里 mounted/beforeDestroy 是空操作或不存在**,全部由 props 回调处理
}
</script>
```

**步骤 3:`ChildModuleEdit.vue` 改造**(一次性的框架改造)

```vue
<!-- ChildModuleEdit.vue template 中 -->
<component
    :is="componentId"
    v-bind="..."
    :onInit="init"           <!-- 把 ChildModuleEdit 的 init 方法传进去 -->
    :onDestroy="destroy"     <!-- 把 ChildModuleEdit 的 destroy 方法传进去 -->
    @getInitForm="...">
</component>

<script>
export default {
    methods: {
        init () {
            // 统一由 ChildModuleEdit 处理:在 mounted 中调用,生命周期可靠
            console.log('[ChildModuleEdit] 子组件 init')
        },
        destroy () {
            // 统一由 ChildModuleEdit 处理:beforeDestroy 中调用
            console.log('[ChildModuleEdit] 子组件 destroy')
        }
    },
    // 这里可以加:在 self.mounted 中调用 this.init()(但需要拿到 pageInstance)
    mounted () {
        if (this.pageInstance?.init) this.pageInstance.init()
    },
    beforeDestroy () {
        if (this.pageInstance?.destroy) this.pageInstance.destroy()
        // 同时也兼容老的 beforeDestroy 调用
        typeof this.pageInstance?.beforeDestroy === 'function' && this.pageInstance.beforeDestroy()
    }
}
</script>
```

> 💡 这个改造是**框架级改动**,业务方**不能只改 JS 配置文件**——需要改 `ChildModuleEdit.vue`。如不能改框架,用方案 A,但务必保证 Vue 组件标准写法。

#### 方案 A vs B 速查

| 维度 | 方案 A:依赖 Vue 生命周期 | 方案 B:props 回调(ChildModuleEdit 控制) |
|---|---|---|
| **稳定程度** | ⚠️ 依赖 pageUrl 加载成功 + 标准 Vue 组件 | ✅ 父组件生命周期 100% 触发 |
| **业务方改造成本** | ✅ 只改 customChildPage.vue | ❌ 需改 ChildModuleEdit.vue 框架代码 |
| **适用场景** | 标准 Vue 组件 + 自定义页面可独立调试 | 复杂场景 / 子组件不能保证 Vue 标准写法 |

### 6.2 子表 → 主表(通过 3 种反向通道)

#### 6.2.1 反向通道 A:`mainScope` 调用主表方法

```js
// 自定义页面里
this.mainScope?.someMethod?.()
this.mainScope?.$emit?.('refreshForm')
```

#### 6.2.2 反向通道 B:EventBus ⚠️ 业务 JS 完全不用(见 §3.2)

> 业务模块(包括 showType=4 自定义页面)**完全不用 EventBus**——framework 内部用的内置事件(`setData` / `getChildTabData`)不是给业务模块触发的,业务自定义又无清理位置。
>
> 如需要"通知主表",**优先用 §6.2.1 `mainScope.xxx()` / `mainScope.$set()`** 直接调用(无清理负担)。

```js
// ❌ 不推荐:业务自定义 EventBus(无法清理监听)
// this.$EventBus?.$emit?.('someEvent', payload)
// this.$EventBus?.$on?.('someEvent', () => { ... })

// ✅ 推荐:用 mainScope 直接调
this.mainScope?.xxx?.()
this.mainScope?.refreshTable?.()
// 注意:framework 内置事件 (setData / getChildTabData) 业务不可靠触发,不算可用通道
```

#### 6.2.3 反向通道 C:getExtendScope + 主表反调

```js
// 自定义页面**初始化时**调(在 mounted 或 §6.1 方案 B 的 init() 里)
this.getExtendScope?.(this)
```

主表反调(**知道 `_key` 即可**,与生命周期无关):

```js
// 在主表某个按钮里
const childScope = this.$refs.childModuleEditInstance?.extendScope?.mountId0
childScope?.reload?.()
```

> ⚠️ 上面说"mounted 或 init()"——若用 §6.1 方案 A,需写在自定义 Vue 组件的 mounted 里(依赖 Vue 生命周期);若用方案 B,写在 init 回调里(由 ChildModuleEdit.mounted 调,稳定)。**业务方应根据"自定义页面是否是标准 Vue 组件"决定**。

---

## 7. 4 类通信通道速查矩阵

| 通信方向 | 通道 | 适用于 | 写法示例 |
|---|---|---|---|
| **主→子:传值** | `elseAttrs.mainFieldList` | 3 种 showType | `this.$attrs.elseAttrs.mainFieldList` |
| **主→子:取主表引用** | `elseAttrs.mainScope` | 3 种 showType | `this.$attrs.elseAttrs.mainScope` |
| **主→子:传 id** | `elseAttrs.mainId` | 3 种 showType | `this.$attrs.elseAttrs.mainId` |
| **主→子:关联字段值** | `elseAttrs.entityFieldValue` | 3 种 showType | `this.$attrs.elseAttrs.entityFieldValue` |
| **主→子:新增数据带关联** | `addFormData` | 仅 showType=0 | 框架自动注入 `{[relationField]: value}` |
| **主→子:showType=4 props** | props 注入 | 仅 showType=4 | `this.mainFieldList` / `this.mainScope` |
| **子→主:调主表方法** | `mainScope.xxx()` | 3 种 showType | `mainScope.$emit('refreshForm')` |
| **子→主:校验主表** | `mainScope.getFormRef().validateForm()` | 3 种 showType | `getFormRef().validateForm({ openValidate: false }).then(formData => ...)` |
| **子→主:修改主表字段** | 直接 `mainScope.$set()` 改字段对象 | 3 种 showType | ⭐ `const f = mainScope.tempFieldList.find(...); mainScope.$set(f, 'value', val)` (无需 $emit,引用共享) |
| **子→主:事件**(业务自定义) | ❌ **完全不推荐** | — | 详见 §3.2:无法清理监听,内存泄漏;framework 内置事件(`setData` / `getChildTabData`)业务不可靠触发 |
| **子→主:主表反调自定义页面** | `getExtendScope()` | 仅 showType=4 | `this.getExtendScope(this)` |

---

## 8. this 指向速查(子表通信相关)

| this 类型 | elseAttrs 在哪 | formData 在哪 | mainScope 在哪 |
|---|---|---|---|
| **子模块 moduleList** | `this.$attrs.elseAttrs` | — | `this.$attrs.elseAttrs.mainScope` |
| **子模块 moduleForm / mForm** | `this.$attrs.elseAttrs` 或 `this.elseAttrs`(声明了) | `this.$attrs.formData` | `this.$attrs.elseAttrs.mainScope` |
| **子模块 moduleEditCode** | `this.$attrs.elseAttrs` | `this.formData`(props 声明) | `this.$attrs.elseAttrs.mainScope` |
| **子模块 customSetting 回调**(valueChange 等) | 回调参数 `formScope` 上 | `formScope.formData` | `formScope.$attrs?.elseAttrs?.mainScope` |
| **showType=4 自定义页面** | — | — | `this.mainScope`(props 注入) |
| **主表 ModuleEdit** | 不会出现在主表 this 上 | `this.formData` | 即 `this` 本身 |

> 详细 this 速查 → [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)

---

## 9. 易错点

| 错误 | 现象 | 解决 |
|---|---|---|
| 子表 customSetting 里读 `this.formData` | undefined | 子表(列表/表单)的 formData 在 `this.$attrs.formData`(或 `this.$attrs.elseAttrs.mainFieldList` 取主表) |
| **业务 JS 中 `$on('自定义事件')`** ⚠️ | **内存泄漏**+ 重复触发 | ❌ **业务 JS 完全不要 `$on('自定义事件')**`——customSetting 是 plain object,无 `beforeDestroy` 时机清理监听;改用 `mainScope.xxx()` / `mainScope.$set()` 直接调(§3.1/§5.3) |
| 业务 JS 中 `$emit('自定义事件')` | 信号"石沉大海" | ❌ 主表 customSetting 接不住,且无清理时机 → 不用;改用 `mainScope` 直接调 |
| 业务 JS 用 `$emit('setData', ...)` 等 framework 内置事件 | 看似可调,实际**不可靠** | framework 内部用了 `setData` / `getChildTabData`,但**业务模块**没有可靠途径触发它们做"主表响应";这种用法是认知误区,详见 §3.2 |
| 用 `this.elseAttrs` 在 mList 里 | 部分组件能取,部分不能 | 统一用 `this.$attrs.elseAttrs`(所有 3 种 showType 都可) |
| `mainScope.xxx()` 后没判断返回值 | 主表可能没这个方法,报错 | 全部用 `mainScope?.xxx?.()`(可选链) |
| `getExtendScope()` 没在 `mounted` 调 | 主表拿不到自定义页面作用域 | showType=4 自定义页面是真实 Vue 组件,**在标准 mounted 调** |
| `mainScope.getFormRef()` 返回 undefined | 主表未初始化完成(子表先渲染) | 用 `this.$nextTick(() => mainScope?.getFormRef?.())` |
| 改主表字段用 `this.formData.xx = yy` | 不触发响应式 | ❌ 整个 src 没有 `setFieldValue` 方法;正确姿势见 §5.3(`mainScope.$set(field, 'value', val)` 直接改主表 tempFieldList 里的字段对象,引用共享自动响应式) |
| showType=4 自定义页面的 `mounted` / `beforeDestroy` "看起来不调用" | 真原因:`pageUrl` require 失败 / 自定义页面不是标准 Vue 组件 / `beforeDestroy` 没在 export default 中显式定义 | 见 §6.0 生命周期事实表;最稳妥方案见 §6.1 方案 B(props 传 `onInit` / `onDestroy` 回调由 ChildModuleEdit 触发) |
| showType=4 的 props 漏写 default | 子页 props 校验告警 | 全部默认值给 `default: () => []` 或 `default: null` |
| **`isHide` 函数内 `this` 指向 `btnObj`** ⚠️ | `this.$attrs` / `this.$store` undefined | 想读 moduleList 的字段/状态,改用 **`buttons: function(defaultBtnList) {}` 函数形式**——那个 `this` 才是 moduleList;`isHide` / `click` 内 this **都是 btnObj**(详见 [frontend-module-tree-list](SKILL.md) §3) |
| **主表 / 子表 customSetting 里写 `mounted` / `beforeDestroy`** ⚠️ | 这两个钩子**永远不会触发**——`customSetting` 不是 Vue 组件,framework 只当作配置对象消费;整 src 只有 `pageUrl` 自定义页面用 `Vue.extend`,业务模块 JS 永不通过 Vue.extend | 主表 customSetting 里能用的钩子见 §3.2.2 表格(`saveUrl` / `buttons` / `beforeModuleInitRender` 等);EventBus 监听**业务模块内无任何位置可挂**(主表 / 子表 customSetting 都不行) |

---

## 10. 验证 checklist

完成一个父子通信场景,过一遍:

- [ ] 子表能拿到主表字段值(`mainFieldList` 中能找到对应字段)
- [ ] 子表能调主表方法(用可选链避免主表未初始化错误)
- [ ] **业务 JS 中没有 `$on` 自定义 EventBus 事件**(无法清理监听,会内存泄漏)
- [ ] 业务 JS 中没有 `$emit` 自定义 EventBus 事件(主表 customSetting 接不住,石沉大海)
- [ ] 业务 JS 中**改主表字段一律用 `mainScope.$set(field, 'value', val)`**(§5.3)
- [ ] showType=4 自定义页面是真实 Vue 组件时,`mounted` / `beforeDestroy` 中挂载的 EventBus 监听**必须配对** `$on` / `$off`
- [ ] showType=4 自定义页面在 mounted 中调 `getExtendScope()`(若是标准 Vue 组件)
- [ ] showType=4 自定义页面的 props 都有 `default`
- [ ] 子表修改主表字段后,主表 UI 同步更新(走 `mainScope.$set(field, 'value', val)` 直接改 tempFieldList,而非 EventBus / 不存在的 `setFieldValue`)
- [ ] console 无 `Cannot read property 'mainScope' of undefined`
- [ ] 父子表双向通信链路在 Network / Vue DevTools 中能看到

---

## 11. 下一步去哪

- **showStyle 展示风格** → [sub/show-style/SKILL.md](show-style/SKILL.md)
- **排版容器 + CSS 布局** → [sub/layout-container/SKILL.md](layout-container/SKILL.md)
- **showType 渲染方式** → [sub/show-type/SKILL.md](show-type/SKILL.md)
- **childTab 字段配置 + 实战** → [sub/child-tab-config/SKILL.md](child-tab-config/SKILL.md)
- **总览** → [frontend-module-child-edit](../SKILL.md)