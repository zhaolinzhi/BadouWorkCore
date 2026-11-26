---
name: frontend-module-child-edit-show-style
description: 八斗 Module 表单 customSetting — 关联子表的 `showStyle` 3 种展示风格详解。当用户问"showStyle 怎么配"、"平级 Tab 和子 Tab 的区别"、"按顺序展示是什么意思"、"子表 Tab 怎么合并"时触发。覆盖 showStyle=1(平级 Tab) / showStyle=2(子 Tab) / showStyle=3(顺序展示) 三种风格 + tabName 合并机制 + 后端 toggle_TabName 联动规则。
---

# 关联子表 — `showStyle` 3 种展示风格详解

> 来源:[ModuleEdit/index.vue:520-547](../../../../../src/components/frame/Module/ModuleEdit/index.vue#L520-L547) 的 switch + [sys_module_link_edit.js:163-186](../../../../../public/moduleJs/frame/modelDesign/sys_module_link_edit.js#L163-L186) 的 `toggle_TabName`。
>
> **父 skill**:[frontend-module-child-edit](../SKILL.md)

---

## 1. 三种风格一览

| 值 | 名称 | 视觉效果 | 适用场景 |
|---|---|---|---|
| `1`(默认) | **平级 Tab** | 主表与子表**并列成 Tab**,首个 Tab 是主表 | 主表 + 子表数据都比较独立,适合分开查看 |
| `2` | **子 Tab** | **主表在上**,**子表在主表下方组成 Tab** | 主表是核心,子表是辅助信息 |
| `3` | **按顺序展示** | 主表 + 子表**从上往下垂直堆叠**,无 Tab | 多个关联模块都重要,需要一屏看完 |

> ⚠️ `showStyle` 为空字符串 / `undefined` / `null` → 默认按风格 1 处理。

---

## 2. 风格 1(默认):平级 Tab

### 2.1 配置示例

```js
// 后端 sys_module_link 配置示意
{
    module: 'order_item',
    title: '订单明细',
    showTab: '1',
    showStyle: 1,             // ← 平级 Tab
    showType: 1,
    tabName: '订单明细',
    relationEntityField: 'orderId'
}
```

### 2.2 渲染结果

```
┌────────────────────────────────────────┐
│ [主表] [订单明细] [物流信息] [售后]    │  ← Tab 头
├────────────────────────────────────────┤
│                                        │
│           当前 Tab 内容                │
│                                        │
└────────────────────────────────────────┘
```

**特点**:
- 主表作为 `mainTab[0]`(首个 Tab)
- 所有 `showStyle=1` 的关联子表合并到 `mainTab` 后续 Tab 项
- `tabName` 相同的会**合并到同一 Tab 内**(见 §5)

---

## 3. 风格 2:子 Tab

### 3.1 配置示例

```js
{
    module: 'order_log',
    title: '操作日志',
    showStyle: 2,             // ← 子 Tab
    showType: 1,
    tabName: '操作日志',
    relationEntityField: 'orderId'
}
```

### 3.2 渲染结果

```
┌────────────────────────────────────────┐
│                                        │
│            主表字段区                  │
│                                        │
├────────────────────────────────────────┤
│ [操作日志] [附件] [评价]               │  ← 主表下方的子 Tab
├────────────────────────────────────────┤
│           当前子 Tab 内容              │
└────────────────────────────────────────┘
```

**特点**:
- **主表在上**(作为 `mainDefault[0]`,独立模块)
- **子表在主表下方**组成 `linkTab`(二维结构)
- 所有 `showStyle=2` 的关联子表合并到 `linkTab` 的子 Tab 项

---

## 4. 风格 3:按顺序展示

### 4.1 配置示例

```js
{
    module: 'order_address',
    title: '收货地址',
    showStyle: 3,             // ← 按顺序展示
    showType: 0,
    tabName: '',              // ← ⚠️ 必须为空(后端 toggle_TabName 会强制清空)
    relationEntityField: 'orderId'
}
```

### 4.2 渲染结果(无 Tab)

```
┌────────────────────────────────────────┐
│            主表字段区                  │
├────────────────────────────────────────┤
│            收货地址(独立模块)          │
├────────────────────────────────────────┤
│            发票信息(独立模块)          │
├────────────────────────────────────────┤
│            备注信息(独立模块)          │
└────────────────────────────────────────┘
```

### 4.3 关键规则:从顶到底依次填入 3 类容器

```js
// ModuleEdit/index.vue:533-540
case 3:
    if ([..._res.mainTab, ..._res.defaultB, ..._res.linkTab, ..._res.defaultC].length === 0) {
        _res.mainDefault.push(_linkItem)        // 1. 第一个 → mainDefault(主表之后)
    } else if ([..._res.linkTab, ..._res.defaultC].length === 0) {
        _res.defaultB.push(_linkItem)           // 2. 中间 → defaultB(平级 Tab 之后,子 Tab 之前)
    } else {
        _res.defaultC.push(_linkItem)           // 3. 末尾 → defaultC(子 Tab 之后)
    }
    break
```

**口诀**:**顺序展示(showStyle=3)的模块,从上往下依次填 mainDefault → defaultB → defaultC,被中间的平级 Tab / 子 Tab 截断**。

---

## 5. tabName 合并机制(核心)

> 来源:[ModuleEdit/index.vue:669-692](../../../../../src/components/frame/Module/ModuleEdit/index.vue#L669-L692) 的 `addTabItem`。

### 5.1 合并规则

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

### 5.2 合并实战

```js
// 后端 childTab 配置
[
    { module: 'order_item',   title: '订单明细', tabName: '订单信息', showStyle: 1, showType: 1, relationEntityField: 'orderId' },
    { module: 'order_log',    title: '操作日志', tabName: '订单信息', showStyle: 1, showType: 1, relationEntityField: 'orderId' },  // ← tabName 同上,会合并
    { module: 'order_pay',    title: '支付信息', tabName: '支付信息', showStyle: 1, showType: 1, relationEntityField: 'orderId' },
    { module: 'order_refund', title: '退款记录', tabName: '售后',     showStyle: 1, showType: 1, relationEntityField: 'orderId' }
]
```

**渲染**:`[主表] [订单信息(订单明细 + 操作日志)] [支付信息] [售后(退款记录)]`

---

## 6. 后端联动规则

### 6.1 `toggle_TabName`(showStyle 切换时联动 tabName 显隐)

```js
// sys_module_link_edit.js:163-186
function toggle_TabName (fieldList) {
    let _tabNameField = getField(fieldList, 'tabName')
    let _showStyleField = getField(fieldList, 'showStyle')
    switch (_showStyleField.value && parseInt(_showStyleField.value) || 1) {
        case 3:
            // 顺序展示:tabName 字段隐藏,值清空
            this.$set(_tabNameField, 'hidden', true)
            _tabNameField.value = ''
            break
        case 1:
        case 2:
        default:
            // 平级 Tab / 子 Tab:tabName 字段显示,值 = displayName 或保留原值
            let _displayNameField = getField(fieldList, 'displayName')
            this.$set(_tabNameField, 'hidden', false)
            _tabNameField.value = _tabNameField.value || _displayNameField.value
    }
}
```

**关键事实**:
- `showStyle=3` 时 → 后端**强制清空** tabName → 前端拿不到
- `showStyle=1/2` 时 → tabName 字段显示,值为 `displayName` 兜底

### 6.2 `setField_ShowType_Options`(联动 showType 可选项)

`showType` 的可选项**受 type(1v1/1vN) 和 isEdit 限制**:

| type | isEdit | showType 可选 |
|---|---|---|
| 1(1v1) | 1(是) | 只显示 0(编辑表单) |
| 1(1v1) | 0(否) | 只显示 2(查看表单) |
| 2(1vN) | — | 只显示 1(列表) |
| 3(多对多) | — | — |

详见 [sub/show-type/SKILL.md](SKILL.md)。

---

## 7. 易错点

| 错误 | 现象 | 解决 |
|---|---|---|
| `showStyle=3` 时还配 `tabName` | 后端清空 tabName 后,模块**单独显示**而非合并 | showStyle=3 不需要 tabName,直接清空 |
| `showStyle=1` 但 tabName 是空 | 多个模块都生成各自的 Tab 头(Tab 名 = title) | 平级 Tab 必填 tabName |
| 同一 tabName 但 showStyle 不同 | **不会合并**(`addTabItem` 同时校验 showStyle) | 保持 showStyle 一致 |
| 改了 showStyle 没生效 | 前端刷新也没用 | showStyle 是**后端配置**,改完保存后刷新即可 |
| 期望子 Tab 但渲染成平级 Tab | showStyle 写成字符串 `"2"` 而非数字 `2` | 后端 select 组件返回字符串,前端 `parseInt(i.showStyle)` 转数字 |

---

## 8. 下一步去哪

- **父子表通信** → [sub/parent-child-communication/SKILL.md](parent-child-communication/SKILL.md)
- **showType 4 类渲染方式** → [sub/show-type/SKILL.md](show-type/SKILL.md)
- **排版容器 + CSS 布局** → [sub/layout-container/SKILL.md](layout-container/SKILL.md)
- **childTab 完整字段配置 + 实战** → [sub/child-tab-config/SKILL.md](child-tab-config/SKILL.md)
- **总览** → [frontend-module-child-edit](../SKILL.md)