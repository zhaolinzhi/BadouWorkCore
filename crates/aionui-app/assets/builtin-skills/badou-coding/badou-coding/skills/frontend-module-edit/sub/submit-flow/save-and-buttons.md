---
name: module-edit-save-and-buttons
description: 八斗 Module 表单 customSetting — 保存流程/按钮覆盖(改保存接口/开保存后新增/自定义按钮/按钮事件插入点/暂存按钮/流程页 tab 渲染)。当用户说"改保存接口"、"加自定义按钮"、"按钮重写"、"按钮拦截"、"保存前确认"、"加暂存/草稿按钮"、"流程按钮 tab"时触发。覆盖 saveUrl / openBtnSaveAndAdd / buttons / beforeApproveRender 共 4 个 key。
---

# Module 表单 — 保存流程/按钮覆盖

> 保存流程 + 按钮相关的 4 个 key(最大的一块)。**先看 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

## 1. `saveUrl`(保存接口 URL)

**签名**:`saveUrl(mdCode)` → `String`(必须 return)

**this 指向**:**moduleEdit 实例**

**this 可用属性**:
- `this.formData` ✅(moduleEdit 的 props,详情表单数据)
- `this.fieldList` ✅(props)
- `this.mdCode` ✅ / `this.detailId` ✅
- `this.BASEURL` ✅ / `this.$store` ✅

```js
saveUrl: function (mdCode) {
    return `${this.BASEURL}/common/${mdCode}/saveCustom.do`
}
```

**实战:动态 mdCode**
```js
saveUrl (mdCode) {
    // 不同 mdCode 走不同接口
    if (mdCode === 'order_v2') {
        return `${this.BASEURL}/common/order/saveV2.do`
    }
    return `${this.BASEURL}/common/${mdCode}/save.do`
}
```

---

## 2. `openBtnSaveAndAdd`(开启"保存后新增")

**类型**:`Boolean`

**this 指向**:无(纯配置)

```js
openBtnSaveAndAdd: true,   // 显示"保存并新增"按钮
```

> 默认 false。设为 true 后,编辑页底部出现"保存并新增"按钮,保存成功后清空 formData 而不是关闭。

> ⚠️ 如果你**重写了默认 save 按钮事件**,需要在保存成功逻辑中加 `Event_Expand.call(this, 'after', arguments[1])` —— 钩子名叫 **`after`**(不是 `afterSave`)。
>
> **历史背景**(框架内现已统一为 `after`):
>
> - `BtnBaseFun/edit.js` 的 `Save` 函数内部只触发 `'after'` 这一种钩子
> - 同文件的 `SaveAndNew` 函数早期写的是 `afterSave`,**两边钩子名不一致会导致"保存后新增"看起来按钮可用、保存却没跳转**
> - **项目已修复**:本仓库 `BtnBaseFun/edit.js:239` 在 2026-07-10 的 commit `82cdacf6` 把 `SaveAndNew` 里写错的 `afterSave` 改成了 `after`
> - 如果你升级到官方新版 `badou-frontend-framework` 包,务必确认 `SaveAndNew` 传的钩子是 **`after`** —— 老教程/老 chat 还会引用 `afterSave`,这个是错的
>
> 完整写法见 §3.6。

---

## 3. `buttons`(自定义按钮)— 高频 ⭐⭐⭐⭐⭐

**类型**:`Array<ButtonObj>` 或 `Function(defaultBtnList) => Array`

**this 指向**:**moduleEdit 实例**

> 💡 **同 saveUrl**:`this.formData` / `this.fieldList` / `this.mdCode` 都能直接用(this 是 moduleEdit 实例,formData 是 props)。

### 3.1 数组形式(简单)

```js
buttons: [
    {
        id: 'myBtn',
        name: '我的按钮',
        icon: 'custom',
        type: 'primary',
        click: function () {
            // this 是 moduleEdit
            this.$message.success('点击了')
        }
    }
]
```

### 3.2 函数形式(覆盖默认按钮)

```js
buttons: function (defaultBtnList) {
    // defaultBtnList 是框架提供的默认按钮(保存/取消/...)
    // 可以修改、过滤、追加
    return [
        ...defaultBtnList,  // 保留默认
        {
            id: 'preview',
            name: '预览',
            icon: 'view',
            type: 'primary',
            click () {
                this.pushPage({
                    path: `/module/view/view/${this.mdCode}/${this.formData.id}`,
                    title: '预览'
                })
            }
        }
    ]
}
```

### 3.3 实战:覆盖默认"保存"按钮 + 拦截

```js
buttons: function (defaultBtnList) {
    return defaultBtnList.map(btn => {
        if (btn.id === 'save') {
            // 保留原 click,但加一个"保存前确认"
            const originalClick = btn.click
            btn.click = function () {
                if (!this.formData.userName) {
                    this.$message.warning('请先填用户名')
                    return
                }
                originalClick.call(this)
            }
        }
        return btn
    })
}
```

### 3.4 按钮事件注入:`Event_Expand`

> **核心机制**:`buttons[].click` 函数内 this 是 moduleEdit,可以调 `Event_Expand` 在保存生命周期的不同节点注入逻辑。

```js
import { Event_Expand } from '@/components/frame/Module/BtnBaseFun/edit'

buttons: [
    {
        id: 'save',
        name: '保存',
        click () {
            // 1. 校验前
            Event_Expand.call(this, 'beforeValidate', this._saveBtn, () => {
                console.log('校验前')
            })
            // 2. 提交前
            Event_Expand.call(this, 'before', this._saveBtn, () => {
                console.log('提交前')
            })
            // 3. 保存成功
            Event_Expand.call(this, 'after', this._saveBtn, (res) => {
                console.log('保存成功', res)
            })
            // 4. 最终
            Event_Expand.call(this, 'finally', this._saveBtn, () => {
                console.log('最终')
            })
        }
    }
]
```

> 💡 实际场景里**很少直接用 Event_Expand**——大部分拦截需求用 `validateRule` + `afterEditJSON` + `saveUrl` 就能搞定。只有在"框架默认保存流程满足不了"的复杂场景才用。

### 3.5 按钮属性全集

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | String | 唯一标识 |
| `name` | String | 按钮文案 |
| `icon` | String | 图标名(Element UI 图标) |
| `type` | String | `primary` / `success` / `warning` / `danger` / `text` |
| `click` | Function | 点击事件(this 是 moduleEdit) |
| `isHide` | Boolean | 隐藏 |
| `isEdit` | Boolean | **只在编辑模式显示**(不传 = 编辑+查看都显示) |
| `isView` | Boolean | **只在查看模式显示** |
| `isPage` | Boolean | 流程页面:把流程按钮强行放在页面底部(默认放在"下一步"弹窗 tab) |
| `loading` | Boolean | loading 状态(框架自动维护) |
| `disabled` | Boolean | 禁用 |
| `priority` | Number | 排序(数字越小越前,默认 999999) |

**`isEdit` / `isView` 实战**:编辑和查看共用一份 edit.js,有时只想给某一态加按钮。

```js
buttons: [
    { id: 'onlyEdit', name: '只有编辑出现', type: 'success', isEdit: true },
    { id: 'onlyView', name: '只有查看出现', type: 'success', isView: true }
]
```

> 来源:`ModuleEdit/index.vue:723-732` 根据 `isView` 自动判断 `isEdit`/`isView` 是否生效。

### 3.6 按钮事件插入点:`Save.call(this, btnObj, {...})` ⭐⭐⭐

**核心机制**:与 List 侧 `getBaseBtnFun` 类似,Edit 侧有 `Save` 函数(从 `@/components/frame/Module/BtnBaseFun/edit` 引入),它在 4 个生命周期节点埋了钩子。

**来源**:`src/components/frame/Module/BtnBaseFun/edit.js:1 Save` 函数

```js
import { Save } from '@/components/frame/Module/BtnBaseFun/edit'

buttons: [
    {
        id: 'save',
        click: function (btnObj) {
            // 调用框架默认保存,在 4 个节点插入业务逻辑
            return Save.call(this, btnObj, {
                // 1. 校验前(resolve?, formRef)
                beforeValidate: function (resolve, formRef) {
                    // 同步:不写 resolve,直接执行
                    console.log('校验前', formRef)
                },
                // 异步:有 resolve 必调 resolve() 才会继续
                // beforeValidate: function (resolve, formRef) {
                //     setTimeout(() => {
                //         this.$message.warning('正在校验')
                //         resolve()
                //     }, 1000)
                // },

                // 2. 提交前(resolve?, formData, formRef)
                before: function (resolve, formData, formRef) {
                    // formData 是校验通过后的数据
                    if (formData.amount <= 0) {
                        this.$message.error('金额必须大于 0')
                        return  // 不调 resolve 就阻塞
                    }
                    resolve()  // 调了才往下走
                },

                // 3. 提交响应后(resolve?, formRef, res)
                after: function (resolve, formRef, res) {
                    console.log('保存成功响应', res)
                    resolve()  // 必须调
                },

                // 4. 关联表单的最终保存后(resolve?, formRef)
                finally: function (resolve, formRef) {
                    // 保存完干点啥
                    console.log('最终保存完毕')
                    resolve()
                }
            })
        }
    }
]
```

**Event_Expand 内部原理**(供高级场景):

`Save` 函数内部调的是 `Event_Expand.call(this, 'beforeValidate', arguments[1], ...)`,而 `Event_Expand` 在 `@/service/event-expand`:

```js
import { Event_Expand } from '@/service/event-expand'
// Event_Expand.call(this, 'eventName', evtObj, ...busiParams)
// 1. evtObj 必须是对象
// 2. evtName 是 evtObj 的一个 key
// 3. evtObj[evtName] 是 handler
// 4. handler 第一个参数是 resolve(若有,等待 resolve 调用)
```

> ⚠️ **业务方一般不需要直接用 Event_Expand**。**用 Save.call(this, btnObj, {...}) 这个上层 API** 即可。
> 直接用 Event_Expand 的场景:重写 Save 内部逻辑、自己控制时序时。

### 3.7 拿表单对象的官方 API:`getFormRef()` ⭐⭐

**获取表单 ref**:
```js
click: function (btnObj) {
    let formRef = this.getFormRef()
    // formRef.dataForm  → 完整 formData
    // formRef.dataList  → 字段列表
    formRef.validateForm().then((formData) => {
        // formData 校验通过后的数据
        this.postFile(this._saveUrl, formData, (isSuccess, res) => {
            // ...
        })
    })
}
```

**关闭校验(直接拿数据)**:
```js
click: function (btnObj) {
    let formRef = this.getFormRef()
    // { openValidate: false } 关闭校验,直接返回 formData
    formRef.validateForm({ openValidate: false }).then((formData) => {
        // formData 不一定校验过
        // 用于"保存草稿"等不要求必填的场景
    })
}
```

### 3.8 `getBaseBtnFun()` 拿默认按钮事件

**用于**:保留原按钮行为,在前后插入逻辑。

```js
buttons: [
    {
        id: 'save',
        click: function (btnObj) {
            let _fun = this.getBaseBtnFun('save')
            _fun.call(this, btnObj, {
                before: function (formData, formRef) {
                    alert('即将保存')
                }
            })
        }
    }
]
```

> 跟 List 侧 `getBaseBtnFun` 用法一致。

### 3.9 刷新表单:`this.$emit('refreshForm')` ⭐⭐

> 刷新**除模型配置外**的所有数据(表单、按钮、子表)。**`afterModuleJSON` 内不能调**(模型还没加载完)。

```js
buttons: [
    {
        id: 'refresh',
        name: '刷新表单',
        type: 'success',
        icon: 'refresh',
        click (btnObj) {
            this.$emit('refreshForm')
        }
    }
]
```

### 3.10 暂存/草稿按钮:跳过校验直接保存 ⭐⭐⭐

> 用户语义:"加个暂存/草稿按钮,允许未填完必填项就保存"。
> 核心原理:用 `getFormRef().validateForm({ openValidate: false })` 关闭校验拿 formData,再走默认 `Save_Module_Form` 提交。

**完整可复制模板**:

```js
import { Save_Module_Form } from '@/api/frame/common'

export default {
    buttons: [
        // 暂存按钮 - 跳过表单校验,直接保存(走默认 save.do)
        {
            id: 'draft',
            name: '暂存',
            type: 'warning',
            icon: 'save',
            loading: false, // 必加:声明初始 loading 状态,防止框架响应式追踪不到 btnObj.loading
            click (btnObj) {
                const formRef = this.getFormRef()
                // openValidate: false 关闭校验,直接 resolve 当前 formData
                formRef.validateForm({ openValidate: false }).then(formData => {
                    btnObj.loading = true
                    Save_Module_Form(formData, this._saveUrl).then(saveRes => {
                        btnObj.loading = false
                        if (saveRes?.hasOk) {
                            this.$message.success('暂存成功')
                        } else {
                            this.$message.error(`暂存失败！${saveRes?.message || ''}`)
                        }
                    }).catch(() => {
                        btnObj.loading = false
                    })
                })
            }
        }
    ]
}
```

**4 个关键点(必须遵守的约定)**:

1. **`loading: false` 必须显式声明在按钮对象上**(不是只写在 click 里)。
   - 原因:btnObj 是 Vue 按钮实例的响应式属性,**未声明的字段在 `click` 回调里被赋值时,部分框架版本不会触发响应式更新**,按钮 spinner 不显示。
   - 解决:在按钮定义里和 `loading` 同级写 `loading: false`,让 Vue 把它挂到响应式系统里。
2. **`{ openValidate: false }` 是 MForm 关闭校验的唯一入口**。
   - 原理:见 [MForm/index.vue:783-812](../../../Common/MForm/index.vue#L783-L812),`openValidate: false` 时直接 `resolve(this._formData)`,不走 `this.$refs[this.id].validate()`。
   - **注意**:不能自己写 `formRef.dataForm` 直接拿 —— 表单数据组装、字段清洗逻辑都在 `validateForm` 内部,**不走它会拿到脏数据**。
3. **`this._saveUrl` 是解析后的最终保存地址**(可能由 `saveUrl` 覆盖过)。
   - 不要再用 `this.mdCode` 拼 URL,直接传 `this._saveUrl` 即可。
4. **暂存成功后不要 `this.goBack()`**,留在当前页;如果需要更新路由 id(新增暂存场景),让后端返回新 id 后由业务方决定是否跳转。

**变体:用 `postFile` 走文件上传接口**(如果暂存接口支持附件):

```js
click (btnObj) {
    const formRef = this.getFormRef()
    formRef.validateForm({ openValidate: false }).then(formData => {
        btnObj.loading = true
        this.postFile(this._saveUrl, formData, (isSuccess, res) => {
            btnObj.loading = false
            if (isSuccess) {
                this.$message.success('暂存成功')
            } else {
                this.$message.error('暂存失败')
            }
        })
    })
}
```

**变体:暂存走单独接口**(不共用 save.do):

```js
saveUrl (mdCode) {
    // 默认保存仍走 save.do
    return `${this.BASEURL}/common/${mdCode}/save.do`
},

buttons: [
    {
        id: 'draft',
        name: '暂存',
        type: 'warning',
        icon: 'save',
        loading: false,
        click (btnObj) {
            const formRef = this.getFormRef()
            formRef.validateForm({ openValidate: false }).then(formData => {
                btnObj.loading = true
                // 暂存走专门接口,不污染 _saveUrl
                const draftUrl = `${this.BASEURL}/common/${this.mdCode}/saveDraft.do`
                Save_Module_Form(formData, draftUrl).then(saveRes => {
                    btnObj.loading = false
                    if (saveRes?.hasOk) {
                        this.$message.success('暂存成功')
                    } else {
                        this.$message.error(`暂存失败！${saveRes?.message || ''}`)
                    }
                }).catch(() => {
                    btnObj.loading = false
                })
            })
        }
    }
]
```

**适用场景**:
- 流程表单中途保存草稿(必填项未填完)
- 长表单分多次填写
- 临时存盘,稍后继续编辑

**不适用场景**:
- 必须保证数据完整性的保存(用默认保存按钮)
- 关联子表嵌套保存(走 [tab-nav](../tab-nav/SKILL.md) 的 `scopeSave` 机制)

---

## 4. `beforeApproveRender`(流程按钮 tab 渲染前) ⭐

> ⚠️ 此方法**仅针对流程页面**的"下一步"弹窗。
> 流程页面 `GlobalSetting.flow.buttonType = 1` 时,自定义按钮默认放在弹窗 tab 上;用 `beforeApproveRender` 可控制 tab 显示。

**this 指向**:**弹窗页面作用域**(不是 moduleEdit)

```js
export default {
    beforeApproveRender () {
        // 获取页面作用域
        let pageScope = this.mainScope
        // 操作弹窗上的 tab
        // this.tempBtnList.splice(0, 1)  // 删除第一个 tab
        // this.tempBtnList.forEach(b => {
        //     if (b.id === 'submit') b.isHide = true
        // })
    }
}
```

**来源**:`ModuleEditCode.vue` 流程相关逻辑。

---

## 5. 完整实战:数据流 + 按钮全定制

```js
// public/moduleJs/order/edit.js
import { Event_Expand } from '@/components/frame/Module/BtnBaseFun/edit'
import { Message } from 'element-ui'

export default {
    // 1. 详情请求
    dataUrl () {
        return `${this.BASEURL}/common/${this.mdCode}/getEditCustom.do`
    },
    paramsBeforeRequest (params) {
        return { ...params, _t: Date.now() }
    },
    valuePath: 'data.result',
    afterEditJSON (formData) {
        formData.statusText = formData.status === 1 ? '启用' : '禁用'
        return formData
    },

    // 2. 模型配置
    afterModuleJSON (module) {
        // 动态加按钮
        if (!module.buttons) module.buttons = []
        module.buttons.push({
            id: 'audit',
            name: '送审',
            type: 'warning'
        })
        return module
    },
    beforeModuleInitRender () {
        // 隐藏 flow 按钮
        const flow = this.btnList.find(b => b.id === 'flow')
        if (flow) flow.isHide = true
    },

    // 3. 保存
    saveUrl (mdCode) {
        return `${this.BASEURL}/common/${mdCode}/saveOrder.do`
    },
    openBtnSaveAndAdd: true,
    buttons (defaultBtnList) {
        return [
            ...defaultBtnList,
            {
                id: 'preview',
                name: '预览',
                icon: 'view',
                type: 'primary',
                click () {
                    this.pushPage({
                        path: `/module/view/view/${this.mdCode}/${this.formData.id}`,
                        title: '预览订单'
                    })
                }
            },
            {
                id: 'audit',
                name: '送审',
                icon: 'check',
                type: 'warning',
                click () {
                    Message.success('已送审')
                }
            }
        ]
    }
}
```

---

## 下一步去哪

- 改详情请求/响应 → [detail-data](detail-data.md)
- 改模型配置(加按钮/字段) → [module-config](module-config.md)
- 回到总览 → [frontend-module-edit](../../SKILL.md)
