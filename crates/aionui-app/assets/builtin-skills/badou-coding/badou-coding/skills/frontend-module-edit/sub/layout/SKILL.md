---
name: frontend-module-edit-layout
description: 八斗 Module 表单 customSetting — 布局(列数 / 渲染前) / 标题栏右侧完整指南。当用户说"改表单列数"、"表单 mounted 时改字段"、"在标题旁边加按钮"、"上一条下一条切换"时触发。覆盖 columnNum / beforeRender / titleRightSlot 3 个 key。
---

# Module 表单 — 布局 / 标题栏右侧

> 3 个"改外观/位置"的 key,简单但高频。**先看 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/edit.js` 的 `export default` 对象里。

**进入前必读**:mdCode + edit/add/view + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 3 个 key

| key | 类型 | 用途 | 频次 |
|------|------|------|------|
| `columnNum` | `Number` | 表单栅格列数 | ⭐⭐ |
| `beforeRender` | `Function` | 字段已构造完、渲染前 | ⭐⭐⭐⭐ |
| `titleRightSlot` | `Function` | 标题栏右侧插槽 | ⭐⭐ |

---

## 2. `columnNum`(表单栅格列数)

**类型**:`Number`(默认从 `GlobalConst.form.columnNum` 取,一般是 2)

**this 指向**:无(纯配置)

```js
// 每行 1 列
columnNum: 1,

// 每行 3 列
columnNum: 3,
```

**实战**:
```js
// public/moduleJs/order/edit.js
export default {
    columnNum: 2,  // 一行 2 个字段(适合订单的字段不太宽)
    
    // public/moduleJs/user_info/edit.js
    // columnNum: 1  // 一行 1 个字段(适合长字段如地址、备注)
}
```

> ⚠️ 如果用了 `contentRender` 自定义排版,`columnNum` 失效(排版归你控)。

---

## 3. `beforeRender`(字段已构造完、渲染前)

**签名**:`beforeRender(fieldList)` → **必须 return** 修改后的 fieldList

**this 指向**:**moduleForm 实例**

**触发时机**:`afterModuleJSON` 之后,字段已经全部构造好,但**还没渲染到 DOM**。这是改字段的最后/最方便时机。

### 3.1 改字段属性

```js
beforeRender: function (fieldList) {
    return fieldList.map(f => {
        // 1. 改文案
        if (f.name === 'userName') {
            f.display = '用户名(必填)'
        }
        // 2. 加 placeholder
        if (f.name === 'phone') {
            f.placeholder = '请输入 11 位手机号'
        }
        // 3. 改宽度
        if (f.name === 'remark') {
            f.width = '100%'  // 跨整行
        }
        // 4. 改 type
        if (f.name === 'description') {
            f.type = 'RichText'  // 升级成富文本
        }
        return f
    })
}
```

### 3.2 加字段(动态插入)

```js
beforeRender: function (fieldList) {
    if (!fieldList.find(f => f.name === 'extraField')) {
        fieldList.push({
            name: 'extraField',
            display: '扩展字段',
            type: 'Text',
            required: false
        })
    }
    return fieldList
}
```

### 3.3 删字段(根据业务逻辑)

```js
beforeRender: function (fieldList) {
    // add 模式才显示"密码",edit 模式不显示
    if (this.viewType === 'edit') {
        return fieldList.filter(f => f.name !== 'password')
    }
    return fieldList
}
```

### 3.4 改字段顺序

```js
beforeRender: function (fieldList) {
    // 把"备注"放到最前面
    const remark = fieldList.find(f => f.name === 'remark')
    if (remark) {
        return [remark, ...fieldList.filter(f => f.name !== 'remark')]
    }
    return fieldList
}
```

### 3.5 根据 formData 已有值动态显隐

```js
beforeRender: function (fieldList) {
    const type = this.formData.type
    return fieldList.map(f => {
        // type === 'A' 时只显示 amount
        if (f.name === 'amount' && type !== 'A') f.isShow = false
        if (f.name === 'quantity' && type !== 'B') f.isShow = false
        return f
    })
}
```

### 3.6 实战:加 options URL

```js
beforeRender: function (fieldList) {
    return fieldList.map(f => {
        if (f.name === 'city') {
            f.url = function () {
                return `/api/city?province=${this.formData.province}`
            }
        }
        if (f.name === 'productType') {
            // 直接给 options
            f.options = [
                { value: 'A', label: '类型 A' },
                { value: 'B', label: '类型 B' }
            ]
        }
        return f
    })
}
```

### 3.7 `beforeFieldChange` vs `beforeRender` 区别

| 维度 | `beforeFieldChange` | `beforeRender` |
|------|--------------------|--------------|
| 触发时机 | 字段格式化**前** | 字段格式化**后**、渲染**前** |
| 接收 | 单个 fieldObj | 整个 fieldList |
| 适合 | 改字段的 options/url | 改字段的 display/width/顺序,加/删字段 |
| 推荐度 | ⭐⭐ | ⭐⭐⭐⭐ |

**推荐**:能用 `beforeRender` 解决的不要用 `beforeFieldChange`(更清晰、更高效)。

---

## 4. `titleRightSlot`(标题栏右侧插槽)

**签名**:`titleRightSlot()` → **(h) => VNode / JSX**(必须返回一个函数,不是 VNode)

**this 指向**:**moduleEdit 实例**(仅外层函数,内层 `(h) => ...` 是普通函数,需通过闭包捕获)

**用途**:在表单标题右侧(右上角)插入自定义内容,如"上一条/下一条"切换、外部跳转、统计信息等。

> ⚠️ **必须返回函数,不是 JSX**——框架内部 `RenderFun` 函数式组件只接受函数(见 [src/components/frame/RenderFun.vue:15-19](../../../../../src/components/frame/RenderFun.vue#L15-L19)):先把 `customSetting.titleRightSlot.call(this)` 执行一遍,返回值再传给 `RenderFun` 的 `:render` prop。
>
> **错误写法**(直接返回 JSX):`RenderFun` 收到 VNode 对象,`typeof !== 'function'` → 什么都不渲染。
>
> **正确写法**:`return (h) => <span>...</span>`,JSX 在内层函数中编译,此时 `h` 由 `RenderFun` 注入。

### 4.1 加"上一条/下一条"按钮

```js
titleRightSlot () {
    const _this = this  // 闭包捕获外层 this(moduleEdit)
    return (h) => (
        <div style="float: right;">
            <el-button
                size="small"
                icon="el-icon-arrow-left"
                on-click={() => _this.loadPrev()}
            >
                上一条
            </el-button>
            <el-button
                size="small"
                on-click={() => _this.loadNext()}
            >
                下一条
                <i class="el-icon-arrow-right" style="margin-left: 4px;"></i>
            </el-button>
        </div>
    )
}
```

### 4.2 加"外部跳转"链接

```js
titleRightSlot () {
    const _this = this
    return (h) => (
        <a
            style="float: right; margin-right: 12px; line-height: 32px;"
            on-click={() => window.open(`/external/${_this.formData.id}`)}
        >
            查看外部数据 →
        </a>
    )
}
```

### 4.3 加"统计"信息

```js
titleRightSlot () {
    const _this = this
    return (h) => (
        <span style="float: right; margin-right: 12px; line-height: 32px; color: #999;">
            共 {_this.formData.totalCount || 0} 条
        </span>
    )
}
```

---

## 5. 关键事实

| 项 | 说明 |
|------|------|
| `columnNum` 范围 | 1-4(超过 4 不好看) |
| `columnNum` 无效 | 用了 `contentRender` 自定义排版 |
| `beforeRender` 不 return | 字段全丢,白屏 |
| `beforeRender` 改的字段 | 渲染前的最后机会,之后改不动 |
| `titleRightSlot` 的 this | moduleEdit(外层),可访问 `this.formData` / `this.mdCode` / `this.pushPage` |
| `titleRightSlot` 必须返回函数 | ⚠️ **返回 `(h) => VNode`,不能直接返回 JSX**——直接返回 VNode 会被 `RenderFun` 当成非函数丢掉 |
| `titleRightSlot` 不 return 函数 | 标题栏右侧空白(不报错,默默失败) |

---

## 6. 完整实战:列数 + beforeRender + titleRightSlot 组合

```js
// public/moduleJs/order/edit.js
export default {
    // 1. 列数
    columnNum: 2,
    
    // 2. 字段调整
    beforeRender: function (fieldList) {
        return fieldList.map(f => {
            // 改文案
            if (f.name === 'orderNo') f.display = '订单编号(必填)'
            // 加 placeholder
            if (f.name === 'amount') f.placeholder = '请输入金额'
            // 跨整行
            if (f.name === 'remark') f.width = '100%'
            // 升级成富文本
            if (f.name === 'description') f.type = 'RichText'
            return f
        })
    },
    
    // 3. 标题右侧
    titleRightSlot () {
        const _this = this
        return (h) => (
            <div style="float: right;">
                <el-button
                    size="small"
                    icon="el-icon-arrow-left"
                    on-click={() => _this.loadPrev()}
                >
                    上一条
                </el-button>
                <el-button
                    size="small"
                    on-click={() => _this.loadNext()}
                >
                    下一条
                </el-button>
            </div>
        )
    }
}
```

---

## 7. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| `columnNum` 不生效 | 用了 contentRender | contentRender 模式下 columnNum 失效,自己控 el-col span |
| `beforeRender` 改了字段没显示 | 忘了 return | 必须 return fieldList |
| `beforeRender` 改 fieldList 后白屏 | 字段全删了 | 检查 filter/map 逻辑 |
| `beforeRender` 改了 formData | 误以为能改值 | `beforeRender` 只能改 fieldList(字段定义),改 formData 用 `valueChange` |
| `titleRightSlot` 写了不显示 | ⚠️ **直接返回了 JSX 而非函数** | 必须返回 `(h) => VNode`,见 §4 顶部说明 |
| `titleRightSlot` 的按钮点了没反应 | 用了箭头函数绑错 this | 用 `const _this = this` 在外层捕获,内层用 `_this.xxx` |
| `titleRightSlot` 的元素叠在一起 | 没浮动 / flex | 加 `float: right` 或 flex 容器 |
| `titleRightSlot` 里 pushPage 没反应 | 误用 `this.$router.push` | 用 `_this.pushPage`(框架方法,自动加 tab) |

---

## 8. 下一步去哪

- **字段值变更/联动** → [module-edit-fields](../fields/SKILL.md)
- **字段后追加 DOM / 重排版** → [module-edit-form-react](../form-react/SKILL.md)
- **数据请求/保存** → [module-edit-submit-flow](../submit-flow/SKILL.md)
- **Tab 切换 / 子表** → [module-edit-tab-nav](../tab-nav/SKILL.md)
- **回到总览** → [frontend-module-edit](../../SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
