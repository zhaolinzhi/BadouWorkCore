---
name: frontend-module-edit-fields
description: 八斗 Module 表单 customSetting — 字段值变更/联动/属性注入完整指南。当用户说"字段联动"、"字段 A 改了字段 B 跟着变"、"给某字段加额外属性"、"字段渲染前预处理"时触发。覆盖 valueChange / fieldChange(已废弃) / beforeFieldChange / fieldCustom 4 个 key。
---

# Module 表单 — 字段值变更 / 联动 / 属性注入

> 表单最常用的 4 个 key,业务方 80% 的"魔改"都从这里开始。**先看 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/edit.js` 的 `export default` 对象里。

**进入前必读**:mdCode + edit/add/view + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 5 个 key

| key | 类型 | 用途 | 频次 |
|------|------|------|------|
| `valueChange` | `Object<字段名, Function>` | 字段值变更事件(推荐) | ⭐⭐⭐⭐⭐ |
| `fieldChange` | `Function` | 字段值变更事件(已废弃) | ⚠️ 别用 |
| `beforeFieldChange` | `Function` | 字段渲染前预处理 | ⭐⭐⭐ |
| `fieldCustom` | `Object<字段名, Object>` | 给字段注入专属属性 | ⭐⭐⭐⭐ |
| `renderField`(查看时) | `Object<字段名, {formatter\|click\|render}>` | 查看页字段渲染 | ⭐⭐ |

---

## 2. `valueChange`(字段值变更)— 表单核心 ⭐⭐⭐⭐⭐

**签名**:`valueChange[fieldName](formScope, fieldName, value, fieldObj, ...rest)`

**this 指向**:**moduleForm 实例**(注意:不是 moduleEdit)

**this 可用属性**:
- `this.fieldList` ✅(props,字段列表)
- `this.$attrs.formData` ⚠️(**formData 不在 this 上**,要从 `$attrs` 取!)
- `this.$attrs.mdCode` / `this.$attrs.detailId` / `this.$attrs.isView` ✅
- `this.elseAttrs` ✅(关联子表场景:主表 id / 主表字段列表 / 主表作用域 / 实体关联名称 / 关联字段值 / 子模块模型名称 / 模型编码 等;**没有关联子表时是 undefined**)
- `this.$set` / `this.$emit` / `this.$nextTick` ✅(Vue 实例方法)

> ⚠️ **常见错误**:`this.formData` 在 moduleForm 里**是 undefined**(moduleForm 没声明 formData 为 prop)。要从 `this.$attrs.formData` 取。
> 详见 [frontend-module-edit §2.5 this 上下文速查表](../../SKILL.md#25-this-上下文速查表必读-)。

### 2.1 基本结构

```js
valueChange: {
    // key 是字段名(严格匹配后端 fieldList)
    status: function (formScope, fieldName, value, fieldObj) {
        // formScope 上有表单操作方法
        // 1. 改其它字段的值
        formScope.setFieldValue('relatedField', value === 1 ? 'on' : 'off')
        // 2. 改其它字段的显隐
        formScope.setFieldVisible('detailField', value === 1)
        // 3. 改其它字段的只读
        formScope.setFieldReadonly('detailField', value !== 1)
        // 4. 改其它字段的必填
        formScope.setFieldRequired('detailField', value === 1)
    }
}
```

### 2.2 实战:省市区联动

```js
valueChange: {
    province: function (formScope, fieldName, value) {
        // 清空下游
        formScope.setFieldValue('city', '')
        formScope.setFieldValue('area', '')
        // 重新拉市的数据
        formScope.setFieldOptions('city', `/api/city?province=${value}`)
    },
    city: function (formScope, fieldName, value) {
        formScope.setFieldValue('area', '')
        formScope.setFieldOptions('area', `/api/area?city=${value}`)
    }
}
```

### 2.3 实战:类型切换 → 字段切换

```js
valueChange: {
    type: function (formScope, fieldName, value) {
        // A 类型显示"金额",B 类型显示"数量"
        formScope.setFieldVisible('amount', value === 'A')
        formScope.setFieldVisible('quantity', value === 'B')
    }
}
```

### 2.4 实战:checkbox 勾选 → 解锁备注

```js
valueChange: {
    needRemark: function (formScope, fieldName, value) {
        formScope.setFieldRequired('remark', !!value)
        formScope.setFieldReadonly('remark', !value)
    }
}
```

### 2.5 实战:多个值一起联动(用到 `...rest` 参数)

```js
valueChange: {
    // 当多个字段一起改时,会一次性传过来
    a_b_c: function (formScope, fieldName, value, fieldObj, ...rest) {
        // rest 是其它被改的字段
    }
}
```

### 2.6 实战:checkbox 勾选 → 联动 radio 选项禁用

```js
valueChange: {
    checkboxf (formScope, fieldName, value) {
        // 1. checkbox 值是 "3,2,1" 字符串(逗号分隔),split 成数组
        const checkedValues = value ? String(value).split(',') : []
        // 2. this 指向 moduleForm,直接改 fieldList 里 radio 字段的 options
        const radioField = this.fieldList?.find(f => f.name === 'radiof')
        if (!radioField) return
        // 3. 保留原始 options(避免每次都基于已 disabled 的 options 再叠加)
        if (!radioField._originOptions) {
            radioField._originOptions = (radioField.options || []).map(o => ({ ...o }))
        }
        // 4. 基于原始 options 生成新 options,给已选值加 disabled
        radioField.options = radioField._originOptions.map(opt => ({
            ...opt,
            disabled: checkedValues.includes(String(opt.id))
                || checkedValues.includes(String(opt.value))
        }))
        // 5. 强制触发响应式更新(options 是引用类型,Vue 检测不到)
        this.$set(radioField, 'options', radioField.options)
    }
}
```

**关键点说明**:

| 点 | 说明 |
|---|---|
| **checkbox 值是字符串不是数组** | 后端 checkboxf 存的是 `"3,2,1"` 这种逗号分隔字符串,**不是 `['3','2','1']` 数组**,必须 split |
| **选项级 disabled** | Radio.vue L12 通过 `:disabled="i.disabled"` 控制单项禁用,只需在 options 里加 `disabled: true` 字段 |
| **绕过 formScope.setFieldOptions** | `formScope.setFieldOptions` 在源码里搜不到,实际写法是直接改 `this.fieldList` 里字段的 options + `$set` 触发响应式 |
| **保留原始 options** | 用 `_originOptions` 私有属性缓存,避免每次 valueChange 在已 disabled 的 options 上再叠加 disabled 判断 |
| **初次加载不会触发 valueChange** | 如果打开编辑页时 checkboxf 已经有值(如 `"3,2,1"`),需要 `beforeRender` 补充联动逻辑,否则初始不会禁用 radio 选项 |

### 2.7 实战:初次加载就联动(`beforeRender` + `valueChange` 配合)

```js
beforeRender (fieldList) {
    // 初次渲染时,如果有 checkboxf 值,手动跑一次联动
    const checkboxField = fieldList.find(f => f.name === 'checkboxf')
    if (checkboxField?.value) {
        const checkedValues = String(checkboxField.value).split(',')
        const radioField = fieldList.find(f => f.name === 'radiof')
        if (radioField?.options) {
            radioField.options = radioField.options.map(opt => ({
                ...opt,
                disabled: checkedValues.includes(String(opt.id))
            }))
        }
    }
    return fieldList
},
valueChange: {
    checkboxf (formScope, fieldName, value) {
        // 后续值变更时,跟初次加载逻辑保持一致(可抽成公共函数)
    }
}
```

---

## 3. `fieldChange`(已废弃,别用 ⚠️)

**签名**:`fieldChange(fieldName, value, fieldObj, formScope)`

**this 指向**:**moduleForm 实例**

> ⚠️ 这个 key **已经被 `valueChange` 替代**,新代码不要再用。
> 唯一作用:监听"被合并的多个字段一次变化"。

```js
// ⚠️ 不推荐,新代码请用 valueChange
fieldChange: function (fieldName, value, fieldObj, formScope) {
    // 老式写法
}
```

**迁移到 `valueChange`**:

```js
// 旧
fieldChange (fieldName, value, fieldObj, formScope) {
    if (fieldName === 'status') { ... }
}

// 新(更清晰、更快)
valueChange: {
    status (formScope, fieldName, value, fieldObj) {
        // ...
    }
}
```

---

## 4. `beforeFieldChange`(字段渲染前预处理)

**签名**:`beforeFieldChange(fieldObj)` → **建议 return** 修改后的 fieldObj(不 return 框架不接管)

**this 指向**:**moduleForm 实例**

> ⚠️ **同 valueChange**:`this.formData` 不存在,要从 `this.$attrs.formData` 取。

**触发时机**:表单 mounted 后,字段格式化**前**。可对每个字段的 `options`、`url`、`rules` 等做预处理。

### 4.1 动态注入 options URL

```js
beforeFieldChange: function (fieldObj) {
    // 给"城市"字段加动态 URL
    if (fieldObj.name === 'city') {
        fieldObj.url = function () {
            // this 是 moduleForm
            const province = this.formData.province
            return `/api/city?province=${province}`
        }
    }
    return fieldObj
}
```

### 4.2 改字段属性

```js
beforeFieldChange: function (fieldObj) {
    // 把所有必填字段都改成非必填
    if (fieldObj.required) {
        fieldObj.required = false
    }
    // 把某个字段改成只读
    if (fieldObj.name === 'id') {
        fieldObj.readonly = true
    }
    return fieldObj
}
```

### 4.3 实战:加 options 前先请求

> ⚠️ 一般**不**在 beforeFieldChange 里发请求(它是同步钩子)。如需异步,改用 `valueChange` 监听上游字段变化后再 setFieldOptions。

---

## 5. `fieldCustom`(注入字段专属属性)

**格式**:`{ [字段名]: { 任意属性 } }` — 会被 `getFieldCustom(name)` 合并到字段的 props 上。

**this 指向**:**moduleForm 实例**

> ⚠️ **同 valueChange**:`this.formData` 不存在,要从 `this.$attrs.formData` 取。

### 5.1 给 DialogList 注入弹窗参数

```js
fieldCustom: {
    // userSelector 是个 DialogList 类型
    userSelector: {
        initDialogParams (formScope) {
            return {
                orgId: formScope.formData.orgId
            }
        }
    }
}
```

### 5.2 给 ImagePicker 注入上传参数

```js
fieldCustom: {
    coverImage: {
        // ImagePicker 组件会读 uploadData
        uploadData: function (formScope) {
            return {
                bizType: 'cover',
                bizId: formScope.formData.id
            }
        }
    }
}
```

### 5.3 给字段加自定义方法(供字段内调用)

```js
fieldCustom: {
    remark: {
        // 字段组件内可通过 this.getExtra() 调用
        getExtra (formScope) {
            return formScope.formData.createTime
        }
    }
}
```

> 💡 `fieldCustom` 是**"给组件传任意 prop"**的万能插槽,具体能传什么看字段组件的 props。

---

## 6. `renderField`(查看时字段渲染)— 与 List 侧不同 ⭐⭐

> ⚠️ **重要**:List 侧 `renderField` 与 Edit 侧 `renderField` **签名不一样**!
> - List 侧:`formatter(row, column, cellValue, index, fieldObj)`(8 个参数,有 row/index)
> - Edit 侧:`formatter(value, fieldObj)`(2 个参数,**没有 row/index**)
>
> 共用 `edit.js` 时,`renderField` **只在查看(isView)页面生效**,编辑页面不生效。

### 6.1 真实签名(以 framework 代码为准)

**来源**:`src/components/frame/Common/MForm/index.vue:679,691,654,666`
```js
// formatter 调用
formatter.call(this, value, item)  // 仅 2 个参数

// click 调用
click.call(this, value, item)  // 仅 2 个参数

// render 调用
render.call(this, h, context, value, item)  // 仅 4 个参数(不是 8 个!)

// appendRender 调用
appendRender.call(this, h, context, value, item)  // 仅 4 个参数
```

**this 指向**:**MForm 实例**(即 moduleForm/index.vue 作用域)

### 6.2 基本结构

```js
renderField: {
    userName: {
        // this: mform/index 作用域
        formatter: function (value, fieldObj) {
            return `<span class="warningTag">${value}</span>`
        },
        click: function (value, fieldObj) {
            this.$message.warning('点击了')
            this.$router.push({ path: '/demo' })
        }
    }
}
```

### 6.3 实战:查看页加"查看详情"按钮

```js
import { Message } from 'element-ui'

export default {
    renderField: {
        customBtn: {
            render: function (h, context, value, fieldObj) {
                return (
                    <bd-button
                        type="text"
                        name="查看"
                        icon="view"
                        on-click={() => {
                            this.$message('点了查看')
                            this.$router.push({
                                path: `/demo/${fieldObj.name}`
                            })
                        }}
                    ></bd-button>
                )
            }
        }
    }
}
```

### 6.4 在编辑页 + 查看页同时生效

`renderField` 默认**只在查看页生效**。如果想在**编辑 + 查看**两态都渲染:
- 在编辑态用 `beforeRender` + `fieldCustom` 给字段注入 `render` 函数
- 或者自定义页面融合 → 见 ModelCommon.md "自定义页面表单如何融合到统一保存按钮"

```js
// 1. 在字段的 customOptions(view/edit 分支)里配
//    字段定义时:customOptions: JSON.stringify({ view: { ... }, edit: { ... } })
// 2. 或在 beforeRender 里:
beforeRender: function () {
    let xxField = this.fieldList.find(o => o.name === 'customBtn')
    // 1. formatter + click 方法
    xxField.formatter = function (value, field) {
        return '<span class="primaryC pointer">查看</span>'
    }
    xxField.click = function (value, field) {
        this.$message('点击了按钮')
    }
    // 2. render 可用全局组件
    let that = this
    xxField.render = function () {
        return (
            <bd-button type="text" name="查看" icon="view"
                on-click={() => that.$message('点击了')}></bd-button>
        )
    }
}
```

---

## 7. 关键事实

| 项 | 说明 |
|------|------|
| `valueChange` 触发时机 | 字段失焦或值真正变化时(不是输入中) |
| `valueChange` 的 formScope 方法集 | `setFieldValue` / `setFieldVisible` / `setFieldReadonly` / `setFieldRequired` / `setFieldOptions` / `getFieldValue` / `validateField` |
| `valueChange` 不触发 | 程序代码 `setFieldValue` 不会**再次**触发 valueChange(避免循环) |
| `fieldChange` 与 `valueChange` | 字段名要严格匹配后端 `fieldList.name` |
| `beforeFieldChange` 不 return | 框架用原 fieldObj,改的东西不生效 |
| `fieldCustom` 的字段名 | 也要严格匹配,字段没声明会静默忽略 |

---

## 8. 完整实战:省市区联动 + 类型切换 + 字段注入

```js
// public/moduleJs/order/edit.js
export default {
    // 1. 字段渲染前:给 city 字段绑定动态 URL
    beforeFieldChange: function (fieldObj) {
        if (fieldObj.name === 'city') {
            fieldObj.url = function () {
                const province = this.formData.province
                return `/api/city?province=${province}`
            }
        }
        return fieldObj
    },
    
    // 2. 字段值变更:省市区 + 订单类型
    valueChange: {
        province (formScope, fieldName, value) {
            formScope.setFieldValue('city', '')
            formScope.setFieldValue('area', '')
            formScope.setFieldOptions('city', `/api/city?province=${value}`)
        },
        city (formScope, fieldName, value) {
            formScope.setFieldValue('area', '')
            formScope.setFieldOptions('area', `/api/area?city=${value}`)
        },
        orderType (formScope, fieldName, value) {
            // 实体商品显示金额,虚拟商品显示兑换码
            formScope.setFieldVisible('amount', value === 'physical')
            formScope.setFieldVisible('redeemCode', value === 'virtual')
        }
    },
    
    // 3. 字段专属属性:给 DialogList 注入弹窗参数
    fieldCustom: {
        customerSelector: {
            initDialogParams (formScope) {
                return {
                    orgId: formScope.formData.orgId || 'default'
                }
            }
        }
    }
}
```

---

## 9. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| `valueChange` 写了没触发 | 字段名拼错 | 严格匹配后端 `fieldList.name`(不是 display) |
| 改了字段值 UI 没更新 | 用了 `formData.xxx = ...` 直接赋值 | 走 `formScope.setFieldValue(name, val)` |
| `setFieldValue` 改完又触发自己的 valueChange | 进入死循环 | 框架已避免此问题(只在 UI 输入时触发),如出现检查是否手动调了 setFieldValue |
| `beforeFieldChange` 改了字段没生效 | 忘了 return | 必须 return 修改后的 fieldObj |
| `fieldCustom` 没生效 | 字段类型不支持该属性 | 看字段组件的 props,`fieldCustom` 只能传 props 接受的字段 |
| `valueChange` 里 `this` 拿不到 formData | this 不是 moduleEdit | this 是 moduleForm,formData 在 `this.formData` |
| `renderField` 写了编辑页不生效 | 默认只在查看页生效 | 想编辑也生效,用 `beforeRender` + `field.render` 注入 |
| `renderField` 的 formatter 写了 4 个参数 | 误用 List 签名 | Edit 侧 formatter 只有 2 个参数:`(value, fieldObj)`,render 4 个:`(h, context, value, item)` |
| `appendRender` 写了 8 个参数 | 误用 List 签名 | appendRender 只有 4 个参数:`(h, context, value, item)` |

---

## 10. 下一步去哪

- **字段后追加 DOM / 整个表单重排版** → [module-edit-form-react](../form-react/SKILL.md)
- **校验规则 / 动态显隐** → [module-edit-validation](../validation/SKILL.md)
- **数据请求/保存** → [module-edit-submit-flow](../submit-flow/SKILL.md)
- **回到总览** → [frontend-module-edit](../../SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
