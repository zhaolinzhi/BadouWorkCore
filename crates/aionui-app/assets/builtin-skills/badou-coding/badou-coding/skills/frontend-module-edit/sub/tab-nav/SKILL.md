---
name: frontend-module-edit-tab-nav
description: 八斗 Module 表单 customSetting — Tab 切换 / 关联子表(嵌套表单)完整指南。当用户说"tab 切换拦截"、"tab 切换前判断未保存"、"关联子表"、"嵌套表单"、"子表单自定义保存"时触发。覆盖 beforeTabLeave / tabClick / tabChange / isChangeInfo / childTab / scopeSave 6 个 key。
---

# Module 表单 — Tab 切换 / 关联子表(嵌套)

> 表单有多个 tab 时的切换控制 + 关联子模块(嵌套表单)的高级定制。**先看 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/edit.js` 的 `export default` 对象里。

**进入前必读**:mdCode + edit/add/view + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 6 个 key

| key | 类型 | 用途 | 频次 |
|------|------|------|------|
| `beforeTabLeave` | `Function` | tab 切换前拦截 | ⭐⭐⭐⭐ |
| `tabClick` | `Function` | tab 点击(切换前) | ⭐⭐ |
| `tabChange` | `Function` | tab 切换成功 | ⭐⭐ |
| `isChangeInfo` | `Object` | 子模块变更标记 | ⭐⭐ |
| `childTab` | `Array` | 关联子模块配置 | ⭐⭐⭐ |
| `scopeSave` | `Function` | 子模块自定义保存 | ⭐⭐ |

---

## 2. `beforeTabLeave`(tab 切换前拦截)— 最重要

**签名**:`beforeTabLeave(activeName, oldActiveName)` → `false` 阻止切换 / `Promise.reject()` 阻止 / 否则允许

**this 指向**:**moduleEdit 实例**

### 2.1 基础拦截:有未保存就提示

```js
beforeTabLeave: function (activeName, oldActiveName) {
    // 检测当前 tab 是否有未保存
    if (this.isChange) {
        return this.$confirm('当前 tab 有未保存修改,确认离开?')
            .then(() => true)
            .catch(() => false)
    }
    return true
}
```

### 2.2 return false 直接阻止

```js
beforeTabLeave (activeName, oldActiveName) {
    // 状态是"审批中"时禁止切换 tab
    if (this.formData.status === 'approving') {
        this.$message.warning('审批中的表单不能切换 tab')
        return false
    }
    return true
}
```

### 2.3 实战:子模块有未保存也拦截

```js
beforeTabLeave: function (activeName, oldActiveName) {
    // isChangeInfo: { mdCode: Boolean } 由子模块的 fieldChange 自动维护
    const hasChildChange = Object.values(this.isChangeInfo || {}).some(v => v)
    if (this.isChange || hasChildChange) {
        return this.$confirm('有未保存修改,确认离开?')
            .then(() => true)
            .catch(() => false)
    }
    return true
}
```

### 2.4 实战:异步校验后拦截

```js
beforeTabLeave: async function (activeName, oldActiveName) {
    try {
        await this.$refs.moduleForm.validate()
        return true
    } catch (e) {
        this.$message.warning('请先完成必填字段')
        return false
    }
}
```

---

## 3. `tabClick` / `tabChange`

### 3.1 `tabClick`(tab 被点击时,不一定切换成功)

**签名**:`tabClick(tab)`

**this 指向**:**moduleEdit 实例**

```js
tabClick: function (tab) {
    console.log('tab 被点击:', tab.name)
    // 做一些"点击即触发"的事,不管切换成功没
}
```

### 3.2 `tabChange`(tab 切换成功)

**签名**:`tabChange(activeName, oldActiveName)`

**this 指向**:**moduleEdit 实例**

```js
tabChange: function (activeName, oldActiveName) {
    // tab 切换成功后才触发,适合做"加载数据"
    if (activeName === 'detail') {
        this.$nextTick(() => {
            this.loadDetailData()
        })
    }
}
```

### 3.3 实战:tab 切换后刷新数据

```js
tabChange: function (activeName) {
    if (activeName === 'history') {
        // 切到"历史记录"tab 时拉数据
        this.loadHistory()
    }
    if (activeName === 'attachment') {
        // 切到"附件"tab 时拉附件
        this.loadAttachments()
    }
}
```

---

## 4. `isChangeInfo`(子模块变更标记)

**类型**:`{ [子模块mdCode]: Boolean }`

**this 指向**:**moduleEdit 实例**

**自动维护**:`fieldChange` 会自动更新 `isChangeInfo[mdCode] = true`,子模块保存成功后置 false。

**使用场景**:在 `beforeTabLeave` 里检查"子模块有没有未保存"。

```js
// 子模块保存成功后,框架会自动:
// this.isChangeInfo['order_item'] = false

// 在 beforeTabLeave 里:
beforeTabLeave (activeName, oldActiveName) {
    const hasChildChange = Object.values(this.isChangeInfo || {}).some(v => v)
    if (hasChildChange) {
        return this.$confirm('子模块有未保存修改,确认离开?')
            .then(() => true)
            .catch(() => false)
    }
    return true
}
```

---

## 5. `childTab`(关联子模块配置)

**类型**:`Array<ChildTabConfig>`

**this 指向**:无(纯配置,后端也常配)

**一般后端配**(`module.json` 里的 `childTab` 字段),前端 customSetting 不太碰它。

```json
[
    {
        "module": "order_item",
        "title": "订单明细",
        "showTab": "1",
        "showType": 0,            // 0=编辑表单, 1=列表, 2=查看表单
        "relationEntityField": "orderId",
        "tabName": "items"
    }
]
```

**前端用 customSetting 改 childTab**(极少用):
```js
afterModuleJSON: function (module) {
    // 改 childTab
    if (module.childTab) {
        module.childTab.forEach(tab => {
            if (tab.module === 'order_item') {
                tab.title = '订单明细(必填)'
            }
        })
    }
    return module
}
```

> 推荐:childTab 走后端 module JSON 配置,customSetting 不碰。

---

## 6. `scopeSave`(子模块自定义保存)— 高级

**签名**:`async scopeSave()`

**this 指向**:子模块的 `mForm/index.vue` 作用域

**用途**:当默认保存逻辑不满足子模块需求时,完全接管子表单的提交。

**示例:子模块"订单明细"需要批量保存到外部 API**

```js
// public/moduleJs/order_item/edit.js
export default {
    scopeSave: async function () {
        // this 指向子模块的 mForm 作用域
        const list = this.formData.list || []
        
        // 校验
        if (!list.length) {
            this.$message.warning('请先添加明细')
            throw new Error('empty')  // 阻止默认保存
        }
        
        // 调外部 API
        try {
            await this.$axios.post('/api/order_item/batchSave', { list })
            this.$message.success('保存成功')
            this.isChangeInfo[this.mdCode] = false  // 标记为已保存
        } catch (e) {
            this.$message.error('保存失败')
            throw e
        }
    }
}
```

> ⚠️ `scopeSave` 是高级 API,只有"框架默认保存流程完全满足不了"时才用。

---

## 7. 关键事实

| 项 | 说明 |
|------|------|
| `beforeTabLeave` return false | 阻止切换 |
| `beforeTabLeave` return Promise.reject | 阻止切换 |
| `beforeTabLeave` return Promise.resolve | 允许切换 |
| `beforeTabLeave` 不 return | 视为允许(老版本可能不兼容) |
| `tabClick` vs `tabChange` | click 一定会触发(不管切换成功没),change 只在成功后 |
| `isChangeInfo` 自动维护 | 子模块 fieldChange 自动置 true,保存后置 false |
| `childTab` 优先后端配 | 前端 customSetting 改它少见 |

---

## 8. 完整实战:tab 拦截 + 关联子表 + 子模块自定义保存

### 8.1 父表单(main order)

```js
// public/moduleJs/order/edit.js
export default {
    // tab 切换前拦截
    beforeTabLeave: function (activeName, oldActiveName) {
        const hasChange = this.isChange
        const hasChildChange = Object.values(this.isChangeInfo || {}).some(v => v)
        
        if (hasChange || hasChildChange) {
            return this.$confirm('有未保存修改,确认切换?', '提示', {
                type: 'warning'
            })
                .then(() => true)
                .catch(() => false)
        }
        return true
    },
    
    // tab 切换后加载数据
    tabChange: function (activeName) {
        if (activeName === 'history') this.loadHistory()
        if (activeName === 'attachment') this.loadAttachments()
    },
    
    // 模型配置:加 tab
    afterModuleJSON: function (module) {
        // 后端 childTab 已配 'order_item' 子模块
        // 这里可以追加自定义 tab
        return module
    }
}
```

### 8.2 子模块(order_item)— 完全自定义保存

```js
// public/moduleJs/order_item/edit.js
import { Message } from 'element-ui'

export default {
    scopeSave: async function () {
        // this 是子模块的 mForm 作用域
        const items = this.formData.items || []
        
        // 1. 校验
        if (!items.length) {
            Message.warning('请先添加明细')
            throw new Error('empty')
        }
        for (let i = 0; i < items.length; i++) {
            if (!items[i].productId) {
                Message.warning(`第 ${i + 1} 行未选择商品`)
                throw new Error('invalid')
            }
        }
        
        // 2. 调批量保存 API
        try {
            const res = await this.$axios({
                url: '/api/order_item/batchSave',
                method: 'post',
                data: {
                    orderId: this.$route.params.id,
                    items
                }
            })
            Message.success('保存成功')
            this.isChangeInfo[this.mdCode] = false
            return res
        } catch (e) {
            Message.error('保存失败: ' + (e.message || ''))
            throw e
        }
    }
}
```

---

## 9. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| `beforeTabLeave` 写了不拦截 | return undefined | 显式 return true / false |
| `beforeTabLeave` 异步不生效 | 用了同步 return | 改成 async,return Promise |
| `isChangeInfo` 一直是 true | 子模块没走"成功保存" | 走 `scopeSave` 的话手动置 false |
| `tabClick` 触发了 `tabChange` 没触发 | beforeTabLeave 拦截了 | 拦截后 tabChange 不会触发,正常 |
| `childTab` 改了不显示 | 后端没配 | childTab 优先后端 module JSON |
| `scopeSave` 写完没生效 | 没在子模块的 edit.js 写 | scopeSave 是子模块 customSetting,不是父表单的 |
| `scopeSave` 抛错没阻断 | catch 里没 rethrow | 必须在 catch 里 `throw e` |

---

## 10. 下一步去哪

- **字段值变更/联动** → [module-edit-fields](../fields/SKILL.md)
- **数据请求/保存** → [module-edit-submit-flow](../submit-flow/SKILL.md)
- **布局** → [module-edit-layout](../layout/SKILL.md)
- **回到总览** → [frontend-module-edit](../../SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
