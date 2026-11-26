---
name: module-edit-module-config
description: 八斗 Module 表单 customSetting — 模型配置加载后/渲染前的定制(动态加按钮/加字段/改搜索条件/隐藏默认按钮/改表格视图)。当用户说"动态加按钮"、"加个新字段"、"隐藏 flow 按钮"、"按钮排序/改文案"、"表格视图"时触发。覆盖 afterModuleJSON / viewType / beforeModuleInitRender 共 3 个 key。
---

# Module 表单 — 模型配置加载后/渲染前定制

> 模型配置(module JSON)从后端拿回来之后、字段渲染之前这段时间的 3 个定制点。**先看 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

## 1. `afterModuleJSON`(模型配置加载后)— 高频

**签名**:`afterModuleJSON(module)` → **必须 return** 修改后的 module

**this 指向**:**moduleEditCode 实例**

**this 可用属性**:
- `this.formData` ✅(moduleEditCode 的 data,详情表单数据)
- `this.module` ✅(模型配置)
- `this.mdCode` / `this.detailId` / `this.BASEURL` ✅

> ⚠️ 这个 key 在 List 里也有,但**触发时机和 this 都不同**:
> - List 的 `afterModuleJSON` 在 `ModuleListCode.vue`(入口层)
> - Edit 的 `afterModuleJSON` 在 `ModuleEditCode.vue`(入口层)
> - this 指向一致:都是 moduleListCode/moduleEditCode 实例

### 1.1 动态加按钮

```js
afterModuleJSON: function (module) {
    if (!module.buttons) module.buttons = []
    module.buttons.push({
        id: 'myCustomBtn',
        name: '我的按钮',
        icon: 'custom',
        type: 'primary'
    })
    return module
}
```

### 1.2 动态加字段

```js
afterModuleJSON: function (module) {
    if (!module.fieldList) module.fieldList = []
    if (!module.fieldList.find(f => f.name === 'extraRemark')) {
        module.fieldList.push({
            name: 'extraRemark',
            display: '扩展备注',
            type: 'Textarea',
            required: false,
            width: '100%'
        })
    }
    return module
}
```

### 1.3 改搜索条件(虽然 Edit 不用搜,但 childTab 可能用)

```js
afterModuleJSON: function (module) {
    if (module.childTab) {
        module.childTab.forEach(tab => {
            if (tab.module === 'order_item') {
                tab.searchCondition = tab.searchCondition || []
            }
        })
    }
    return module
}
```

---

## 2. `viewType`(表格视图)

**类型**:`String`,默认 `'normal'`

**this 指向**:无(纯配置,后端模型设计器常配)

```js
export default {
    viewType: 'table'  // 表格视图(默认普通表单)
}
```

> 实际场景里 `viewType` 常在**后端模型设计器**配置,前端 customSetting 较少用。

---

## 3. `beforeModuleInitRender`(渲染前最后定制)

**签名**:`beforeModuleInitRender()` → 无返回值

**this 指向**:**moduleEdit 实例**

**触发时机**:获取到 tab/button 等后、按钮渲染前。可做"按钮隐藏 / 排序 / 改文案"等微调。

```js
beforeModuleInitRender: function () {
    // 隐藏某个默认按钮
    const btn = this.btnList.find(b => b.id === 'flow')
    if (btn) btn.isHide = true

    // 改按钮文案
    const submitBtn = this.btnList.find(b => b.id === 'submit')
    if (submitBtn) submitBtn.name = '提交申请'
}
```

---

## 下一步去哪

- 改详情请求/响应 → [detail-data](detail-data.md)
- 改保存地址/自定义按钮/暂存 → [save-and-buttons](save-and-buttons.md)
- 回到总览 → [frontend-module-edit](../../SKILL.md)
