---
name: frontend-module-edit-form-react
description: 八斗 Module 表单 customSetting — 字段后追加 DOM / 整个表单重排版完整指南。当用户说"在字段旁边加按钮/说明"、"字段后插一个小图标/链接"、"完全自定义表单布局"、"DIY 表单排版"时触发。覆盖 appendDom / contentRender 2 个 key。
---

# Module 表单 — 字段后追加 DOM / 整个表单重排版

> 当业务方嫌"默认表单"不够用,要在字段旁边塞东西 / 整个表单自己排版时,用这两个 key。**先看 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/edit.js` 的 `export default` 对象里。

**进入前必读**:mdCode + edit/add/view + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 2 个 key

| key | 类型 | 用途 | 频次 |
|------|------|------|------|
| `appendDom` | `Object<字段名, { appendRender }>` | 字段后追加 DOM | ⭐⭐⭐ |
| `contentRender` | `Function` | 整个表单完全自定义排版 | ⭐⭐ |

---

## 2. `appendDom`(字段后追加 DOM)

**格式**:`{ [字段名]: { appendRender: function(h, context, value, fieldObj) } }`

**this 指向**:**moduleForm 实例**

**appendRender 签名**:接收 `h`(createElement)和字段信息,**必须 return VNode / JSX**

### 2.1 在"备注"字段后面加一个"参考模版"链接

```js
appendDom: {
    remark: {
        appendRender: function (h, context, value, fieldObj) {
            return (
                <a
                    style="margin-left: 8px; color: #409EFF;"
                    on-click={() => window.open('/template/remark.html', '_blank')}
                >
                    参考模版
                </a>
            )
        }
    }
}
```

### 2.2 在"金额"字段后显示"换算后的人民币"

```js
appendDom: {
    amount: {
        appendRender: function (h, context, value) {
            if (!value) return null
            const cny = (value * 7.2).toFixed(2)  // 假设汇率
            return (
                <span style="margin-left: 8px; color: #999;">
                    ≈ ¥{cny}
                </span>
            )
        }
    }
}
```

### 2.3 在"选择用户"字段后加一个"清空"按钮

```js
appendDom: {
    userSelector: {
        appendRender: function (h, context, value, fieldObj) {
            const _this = this
            return (
                <el-button
                    type="text"
                    style="margin-left: 8px;"
                    on-click={() => _this.$set(_this.formData, 'userSelector', null)}
                >
                    清空
                </el-button>
            )
        }
    }
}
```

### 2.4 JSX 5 条铁律(appendDom 也适用)

1. `return` 后面是 `()` 不是 `{}`
2. 标签不能写成字符串(不能 `'<span>'`,要写 `<span>`)
3. 必须有且仅有一个**根级标签**(不返回东西用 `return null`)
4. 变量用单花括号 `{value}`(不是 vue 模板的 `{{}}`)
5. 事件格式 `on-事件类型={fn}`,需要阻止冒泡用 `nativeOn-click`

---

## 3. `contentRender`(整个表单自定义排版)

**签名**:`contentRender(h, context, S, D)` → **必须 return VNode**(替换默认栅格布局)

**this 指向**:**DiyFormRender 实例**(MForm 通过 `<diy-form-render :render="contentRender" :slotList="...">` 调用,`this.render.call(this, ...)` 中的 this 是 DiyFormRender)

> ⚠️ **this 指向纠错 — 重要**:
> skill 早期版本写过"this 指向 moduleForm",**错的**。实际指向 DiyFormRender,所以:
> - `this.formData` / `this.fieldList` / `this.$attrs.formData` 全部是 undefined
> - 不要依赖 `this.$attrs` 拿 isView / formData(MForm 设置了 `inheritAttrs: false`,根本不传 attrs)
> - 需要字段值时:用参数 `D('fieldName').value`
> - 需要 isView 时:`this.$parent?.isView`(MForm 实例上的 prop)

**S / D 两个工具方法**(由 DiyFormRender 自动注入):
- `S(字段名)` → 返回该字段的**完整 el-form-item VNode**(带 label、表单控件、校验),可直接放到 JSX 里
- `D(字段名)` → 返回该字段的**数据对象**(`D('aa').label` 拿字段显示名,`D('aa').value` 拿值)

> ⚠️ 用了 `contentRender` 后,默认的栅格布局、字段排版、列数控制(`columnNum`)**全部失效**。所有排版由你负责。
> 包括 add / edit / view **三种模式**都会被 contentRender 接管——如果需要查看页和编辑页用不同布局,见 [§3.4 isView 判断](#34-区分查看页和编辑页)

### 3.1 基本骨架

```js
// ⚠️ 不要在内部再 import 或写 <diy-form-render>,framework 外层 MForm 已经包装了
//   (MForm/index.vue:34-37 用 <diy-form-render :render="contentRender"> 调用)
//   内部再包一层会双重包装,S(name) 找不到 children 直接返回空对象
contentRender: function (h, context, S, D) {
    return (
        <div>
            {/* 完全自己写排版,用 S('fieldName') 调用字段,用 D('fieldName') 取值 */}
            <el-row gutter={20}>
                <el-col span={12}>{S('userName')}</el-col>
                <el-col span={12}>{S('phone')}</el-col>
            </el-row>
        </div>
    )
}
```

> 💡 `S(name)` 返回完整的 el-form-item(含 label + 表单控件 + 校验),直接放到 JSX 里就行。
> 想跳过 S 自己渲染 input,可以用 `D(name).value` 取值,然后手动绑 input + formScope.setFieldValue 同步——但比较麻烦,优先用 S。

### 3.2 实战:分组 + 折叠面板

```js
contentRender: function (h, context, S, D) {
    return (
        <el-collapse>
            <el-collapse-item title="基本信息" name="base">
                <el-row gutter={20}>
                    <el-col span={12}>{S('userName')}</el-col>
                    <el-col span={12}>{S('phone')}</el-col>
                </el-row>
            </el-collapse-item>
            <el-collapse-item title="高级信息" name="advanced">
                <el-row gutter={20}>
                    <el-col span={24}>{S('remark')}</el-col>
                </el-row>
            </el-collapse-item>
        </el-collapse>
    )
}
```

### 3.3 实战:字段分组 + 标题分隔

```js
contentRender: function (h, context, S, D) {
    return (
        <div>
            <div class="form-section">
                <h3 class="section-title">基础信息</h3>
                <el-row gutter={20}>
                    <el-col span={12}>{S('userName')}</el-col>
                    <el-col span={12}>{S('phone')}</el-col>
                </el-row>
            </div>
            <div class="form-section">
                <h3 class="section-title">权限信息</h3>
                <el-row gutter={20}>
                    <el-col span={24}>{S('roleIds')}</el-col>
                </el-row>
            </div>
        </div>
    )
}
```

> ⚠️ **不要用 `this.renderField(name)`**:
> - `this` 是 DiyFormRender 实例,没有 `renderField` 方法
> - 字段渲染用 `S('name')` 返回的 el-form-item VNode,框架自动处理 label / 校验 / readonly
> - skill 早期版本的 `this.renderField('userName')` 写法是 moduleForm 的方法,这里调用会报错

### 3.4 区分查看页和编辑页

`contentRender` **完全替换**默认布局,add / edit / view **三种模式都生效**。如果查看页和编辑页要不同布局,必须自己在函数内分支判断。

**isView 取法**(踩坑经验):
```js
// ❌ 错误:this.$attrs.isView 永远是 undefined
const isView = this.$attrs.isView
// 原因:MForm 设置了 inheritAttrs:false,isView 不会传进 DiyFormRender 的 $attrs

// ❌ 错误:从 $attrs.formData.isView 读
const isView = this.$attrs?.formData?.isView  // formData 也没传进来,undefined

// ✅ 正确:this.$parent.isView 读 MForm 实例上的 prop
const isView = this.$parent?.isView || this.$attrs?.isView || false
```

**标准模式**:

```js
contentRender: function (h, context, S, D) {
    const isView = this.$parent?.isView || this.$attrs?.isView || false

    if (isView) {
        // 查看页:通常用纯文本 / 卡片 / 摘要
        return (
            <div class="bg-white border box-shadow padding" style="border-radius: 6px;">
                <span class="font14 color3">
                    {`《${D('name')?.value || '未命名'}》`}
                </span>
            </div>
        )
    }

    // 新增 / 编辑页:正常 input 表单(用 S() 嵌字段)
    return (
        <el-row gutter={20}>
            <el-col span={12}>{S('name')}</el-col>
            <el-col span={12}>{S('status')}</el-col>
        </el-row>
    )
}
```

> 💡 业务场景变种:
> - 只想查看页用 contentRender,编辑/新增走默认 → 仍要提供编辑分支(因为 contentRender 强制接管所有模式),但内容就是默认栅格
> - 三种模式都要不同布局 → 用 `this.$attrs?.detailId` 区分 add / edit(没有 detailId 是 add,有 detailId 是 edit,加 isView 是 view)

### 3.5 S() 嵌入一句话(inline 表单)— CSS 模板

把 `S('name')` 嵌到一句话里,默认 el-form-item 是 `display: block` + `height: 40px`,会换行 + 撑开 baseline。**必须** 配合限定 CSS 才能"嵌"进去。

**4 个必加的 CSS**(用唯一 className 限定作用域,避免污染全局):

```css
.${INLINE_CLASS} {                            /* 1. 外层统一 line-height + font-size */
    line-height: 28px;
    font-size: 14px;
}
.${INLINE_CLASS} .el-form-item {              /* 2. form-item 改 inline-flex,不再换行 */
    display: inline-flex !important;
    margin: 0 4px !important;
    vertical-align: middle !important;
}
.${INLINE_CLASS} .el-form-item__label {       /* 3. 隐藏 label,避免嵌进一句话出现"商品名称:" */
    display: none !important;
}
.${INLINE_CLASS} .el-form-item__content {     /* 4. content 改 flex + center,baseline 对齐 */
    display: flex !important;
    align-items: center !important;
}
.${INLINE_CLASS} .el-input__inner,            /* 5. input/select 高度压成 28px,跟外层一致 */
.${INLINE_CLASS} .el-textarea__inner {
    height: 28px !important;
    line-height: 28px !important;
    padding: 0 8px !important;
}
```

**完整实战** —— 「一句话卡片」:

```js
contentRender: function (h, context, S, D) {
    const isView = this.$parent?.isView || this.$attrs?.isView || false
    const INLINE_CLASS = 'wjx-goods-edit-inline-form'  // 唯一 className

    if (isView) {
        // 查看页:纯文本一句话
        const name = D('name')?.value || '未命名商品'
        return (
            <div class="bg-white border box-shadow padding" style="border-radius: 6px;">
                <span class="font14 color3" style="line-height: 1.8;">
                    {`《${name}》`}
                </span>
            </div>
        )
    }

    // 编辑页:一句话 + 嵌入式表单
    return (
        <div>
            <style>
                {`
                    .${INLINE_CLASS} { line-height: 28px; font-size: 14px; }
                    .${INLINE_CLASS} .el-form-item {
                        display: inline-flex !important;
                        margin: 0 4px !important;
                        vertical-align: middle !important;
                    }
                    .${INLINE_CLASS} .el-form-item__label { display: none !important; }
                    .${INLINE_CLASS} .el-form-item__content {
                        display: flex !important;
                        align-items: center !important;
                    }
                    .${INLINE_CLASS} .el-input__inner,
                    .${INLINE_CLASS} .el-textarea__inner {
                        height: 28px !important;
                        line-height: 28px !important;
                        padding: 0 8px !important;
                    }
                `}
            </style>
            <div
                class={`bg-white border box-shadow padding ${INLINE_CLASS}`}
                style="border-radius: 6px;"
            >
                《{S('name')}》{S('status')}
                <div class="marT-10">
                    <span class="color9 font12">描述:</span>
                    {S('description')}
                </div>
            </div>
        </div>
    )
}
```

> ⚠️ **textarea 要单独处理**:
> textarea 不能用 `height: 28px` 压扁(用户输入多行会撑不开),改成 `height: auto; min-height: 28px;` 让它自动撑开,放在一句话下方单独段而不是嵌进一句话里。

> ⚠️ **其他需要注意的边角**:
> - `el-select` / `el-cascader` / `el-date-picker` 内部也是 `el-input__inner`,上面的 CSS 同样生效
> - 单选/多选 radio/checkbox 组(`.el-radio-group` / `.el-checkbox-group`)默认是 inline,基本不需要额外 CSS,但 alignment 可能还差一点
> - `<style>` 每次 render 会重新插入到 DOM(Vue 2 不会去重),如果发现 style 重复堆叠,改成写到 `src/styles/commonAttr.scss` 作为全局工具类

---

## 4. 关键事实

| 项 | 说明 |
|------|------|
| `appendDom` 触发时机 | 字段渲染时(同字段同位置追加,不换行) |
| `appendDom` 不 return | 不报错,但也不显示任何东西 |
| `contentRender` 不 return | 表单空白(整个布局被你替换了) |
| `contentRender` 后,`columnNum` 失效 | 排版全在 contentRender 里自己控制 |
| `contentRender` 后,字段隐藏/只读 仍生效 | 通过 `setFieldVisible` 仍能控 |
| `appendDom` 内的 this | moduleForm,可访问 `this.formData` |

---

## 5. 完整实战:appendDom + contentRender 组合

```js
// public/moduleJs/order/edit.js
export default {
    // 1. 字段后追加"参考模版"链接
    appendDom: {
        remark: {
            appendRender (h, context, value) {
                return (
                    <a
                        style="margin-left: 8px;"
                        on-click={() => window.open('/template/remark.html')}
                    >
                        参考模版
                    </a>
                )
            }
        }
    },

    // 2. 整个表单分组排版
    contentRender (h, context, S, D) {
        return (
            <el-collapse>
                <el-collapse-item title="订单信息" name="base">
                    <el-row gutter={20}>
                        <el-col span={12}>{S('orderNo')}</el-col>
                        <el-col span={12}>{S('customer')}</el-col>
                    </el-row>
                    <el-row gutter={20}>
                        <el-col span={12}>{S('amount')}</el-col>
                        <el-col span={12}>{S('status')}</el-col>
                    </el-row>
                </el-collapse-item>
                <el-collapse-item title="备注" name="remark">
                    <el-row gutter={20}>
                        <el-col span={24}>{S('remark')}</el-col>
                    </el-row>
                </el-collapse-item>
            </el-collapse>
        )
    }
}
```

---

## 6. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| `appendDom` 写了没显示 | 字段名拼错 | 严格匹配 `fieldList.name` |
| `appendDom` 内 `this.formData` 是 undefined | 误用箭头函数绑错 this | 用普通 function,this 自动是 moduleForm |
| `contentRender` 后字段没显示 | 忘了在 JSX 里调 `S('name')` | 排版归你,字段也得你手动 render(用 S()) |
| `contentRender` 后列数乱了 | `columnNum` 失效了 | 排版完全自己控,用 `el-col span={N}` |
| `contentRender` 后校验规则丢了 | `validateRule` 还得用 | `validateRule` 是单独的 key,跟 contentRender 无关 |
| appendDom 里 `e.stopPropagation` 报错 | JSX 用了 vue 模板的事件语法 | 改 `on-click={fn}`,不是 `@click` |
| `contentRender` 内又写了 `<diy-form-render>` 嵌套 | `S(name)` 全部返回空对象,字段不显示 | 不要嵌套!外层 MForm 已经包装,直接 return JSX |
| `this.$attrs.isView` 永远是 undefined,查看页也走编辑分支 | MForm 设置了 `inheritAttrs: false`,isView 没传到 DiyFormRender 的 $attrs | 改用 `this.$parent?.isView`(见 [§3.4](#34-区分查看页和编辑页)) |
| `this.formData` / `this.fieldList` 在 contentRender 里是 undefined | this 是 DiyFormRender,不是 moduleForm | 字段值用 `D('name').value`,fieldList 在 contentRender 里不可用 |
| S() 嵌到一句话里,form-item 换行撑开 baseline | el-form-item 默认 `display: block; height: 40px` | 加 [§3.5 的 CSS 模板](#35-s-嵌入一句话inline-表单css-模板):`display: inline-flex` + 压扁高度 + `align-items: center` |
| S() 嵌到一句话里出现 "商品名称: [input]" 类似的 label | el-form-item__label 默认显示 | CSS 加 `.el-form-item__label { display: none }` |
| 拼接 status 字典时 statusText 显示成 `[object Object]` | STATUS_MAP 写成对象,模板字符串调 toString | 字典值直接用字符串:`{0: '在售'}` 而不是 `{0: {label: '在售'}}` |

---

## 7. 下一步去哪

- **字段值变更/联动** → [module-edit-fields](../fields/SKILL.md)
- **校验规则 / 动态显隐** → [module-edit-validation](../validation/SKILL.md)
- **数据请求/保存** → [module-edit-submit-flow](../submit-flow/SKILL.md)
- **回到总览** → [frontend-module-edit](../../SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
