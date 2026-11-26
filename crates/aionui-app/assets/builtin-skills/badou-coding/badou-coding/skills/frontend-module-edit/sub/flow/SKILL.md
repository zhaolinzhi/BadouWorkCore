---
name: frontend-module-edit-flow
description: 八斗 Module 流程表单 customSetting — 流程专属按钮 + Save/Submit 原理。当用户说"流程表单"、"flowButtons"、"审批提交"、"重写流程保存"、"重写流程提交"、"审批弹窗"时触发。覆盖 flowButtons / Save / Submit 三个核心机制。
---

# Module 表单 — 流程表单

> 流程表单(审批流)的 customSetting 与普通表单**有专属差异**——多了 `flowButtons`、要走 `Save`/`Submit` 函数。**先看 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/edit.js` 的 `export default` 对象里。

**进入前必读**:mdCode + edit/add/view + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 3 个核心机制

| 机制 | 类型 | 用途 | 频次 |
|------|------|------|------|
| `flowButtons` | `Array\|Function` | 流程页面的自定义按钮(非保存按钮) | ⭐⭐⭐ |
| `Save` | `Function` (从 `@/components/frame/Module/BtnBaseFun/flow-edit` 引入) | 流程页面的"保存"按钮事件 | ⭐⭐⭐ |
| `Submit` | `Function` (从 `@/components/frame/Module/BtnBaseFun/flow-edit` 引入) | 流程页面的"提交/审批"按钮事件 | ⭐⭐⭐ |

> ⚠️ 流程表单用 `flowButtons` 而不是 `buttons`(虽然 `buttons` 也能用,但流程侧推荐 `flowButtons`)。

---

## 2. `flowButtons`(非保存按钮)

**类型**:`Array<ButtonObj>` 或 `Function(data) => Array`

**this 指向**:**moduleEdit 实例**

```js
export default {
    flowButtons: [
        {
            id: 'new',
            name: '新增流程',
            icon: 'import',
            type: 'primary',
            click: function (btnObj) {
                let _formRef = this.getFormRef()
                // _formRef.dataForm  → 表单数据
                // _formRef.dataList  → 字段列表
                this.pushPage({
                    path: '/module/stander/add/xxx',
                    title: '新增流程'
                })
            }
        }
    ]
}
```

> 与普通 `buttons` 区别:`flowButtons` 的按钮只出现在**流程页面**,且**不参与默认保存流程**。

---

## 3. `Save`(重写"保存"按钮 + 4 个事件插入点) ⭐⭐⭐

**适用场景**:你想**保留默认保存逻辑**,只在某些节点插入自己的业务判断。

**来源**:`src/components/frame/Module/BtnBaseFun/flow-edit.js` 的 `Save` 函数

```js
import { Save } from '@/components/frame/Module/BtnBaseFun/flow-edit'

export default {
    flowButtons: [
        {
            id: 'save',
            name: '保存',
            icon: 'save',
            type: 'primary',
            loading: false,
            click: function (btnObj) {
                // 1. 获取表单 ref
                let _formRef = this.getFormRef()
                
                // 2. 调用框架 Save,在 4 个节点插入业务逻辑
                return Save.call(this, btnObj, {
                    // 校验前(resolve?, formRef)
                    beforeValidate: function (resolve, formRef) {
                        // 不写 resolve 视为同步,直接执行
                        // 写了 resolve 必须调 resolve() 才继续
                    },
                    // 提交前(resolve?, formData, formRef)
                    before: function (resolve, formData, formRef) {
                        // 提交前可以改 formData
                        formData.extraField = 'someValue'
                        resolve()
                    },
                    // 响应后(resolve?, formRef, res)
                    after: function (resolve, formRef, res) {
                        // res 是接口响应
                        this.$message.success('保存成功')
                        resolve()
                    },
                    // 关联表单的最终保存后(resolve?, formRef)
                    finally: function (resolve, formRef) {
                        // 所有子表都保存完成后触发
                        this.$emit('refreshForm')
                        resolve()
                    }
                })
            }
        }
    ]
}
```

**Save 与 Submit 区别**:
- **Save** 用于"保存"按钮,只走保存接口
- **Submit** 用于"提交/审批"按钮,保存 + 走审批流(打开审批弹窗)

---

## 4. `Submit`(重写"提交/审批"按钮 + 8 个事件插入点) ⭐⭐⭐

**适用场景**:重写"提交"按钮,在保存、打开弹窗、提交审批等节点插入业务。

**签名**:
```js
import { Submit } from '@/components/frame/Module/BtnBaseFun/flow-edit'

flowButtons: function (data) {
    // data 是流程路由按钮数组
    // 找"提交"按钮(根据名称或 id)
    let submitbtn = data.find(o => o.name === '提交')
    if (submitbtn) {
        submitbtn.click = function (btnObj) {
            Submit.call(this, btnObj, {
                // 1. 页面表单校验前(resolve?, formRef)
                beforeValidate: function (resolve, formRef) {
                    setTimeout(() => {
                        this.$message.warning('开始校验')
                        resolve()
                    }, 1000)
                },
                // 2. 提交前(resolve?, formData, formRef)
                beforeSave: function (resolve, formData, formRef) {
                    // 改提交参数
                    formData.aa = '审批接口自定义新增参数'
                    resolve()
                },
                // 3. 提交响应后(resolve?, formRef, res)
                afterSave: function (resolve, formRef, res) {
                    this.$message.success('保存成功')
                    resolve()
                },
                
                // 4. 打开审批弹窗前(resolve?, dialogConfig)
                beforeDialog: function (resolve, dialogConfig) {
                    // dialogConfig 是传入审批弹窗组件的参数,可定制弹窗按钮
                    dialogConfig.title = '初始提交流程[单独定制标题]'
                    resolve()
                },
                // 5. 审批弹窗表单校验前(resolve?, resolve)
                beforeDialogValidate: function (resolve) {
                    setTimeout(() => {
                        this.$message.warning('审批表单:校验开始')
                        resolve()
                    }, 1000)
                },
                // 6. 执行审批前(resolve?, params)
                beforeSubmit: function (resolve, params) {
                    // 改审批提交参数
                    params.aa = '审批接口自定义新增参数'
                    resolve()
                },
                // 7. 审批成功后(resolve?)
                afterSubmit: function (resolve) {
                    this.$message.warning('审批表单:提交成功')
                    resolve()
                }
            })
        }
    }
    return data
}
```

**注意**:
- `flowButtons: function (data)` 这种**函数形式**是**重构版流程提交**的写法,后续待改进(目前是唯一支持的方式)
- `flowButtons: [array]` 数组形式只支持**简单按钮**,不支持"提交"按钮的事件重写

---

## 5. 关键事实

| 项 | 说明 |
|------|------|
| `flowButtons` vs `buttons` | `flowButtons` 是流程页面专属,`buttons` 在普通表单里用 |
| `Save` 与 `Submit` 引入路径 | 都从 `@/components/frame/Module/BtnBaseFun/flow-edit` 引入 |
| `Save` 的 4 个事件节点 | beforeValidate / before / after / finally |
| `Submit` 的 8 个事件节点 | beforeValidate / beforeSave / afterSave + beforeDialog / beforeDialogValidate / beforeSubmit / afterSubmit |
| 事件函数有 `resolve` | 必须 `resolve()` 才往后走,不调就阻塞 |
| 事件函数无 `resolve` | 视为同步,直接执行 |
| `flowButtons` 函数形式 | 用于"提交"按钮重写,数组形式只支持简单按钮 |
| 全局开关 | `GlobalSetting.flow.buttonType = 1` 时,自定义按钮默认放弹窗 tab;`isPage: true` 强制放页面底部 |

---

## 6. 完整实战:流程"提交"按钮插入业务

```js
// public/moduleJs/order/edit.js
import { Submit } from '@/components/frame/Module/BtnBaseFun/flow-edit'

export default {
    // 流程页底部"提交"按钮 + 8 个事件节点
    flowButtons: function (data) {
        let submitBtn = data.find(o => o.name === '提交')
        if (submitBtn) {
            submitBtn.click = function (btnObj) {
                return Submit.call(this, btnObj, {
                    beforeValidate: (resolve) => {
                        // 校验前,比如检查某个业务前提
                        if (!this.formData.customer) {
                            this.$message.error('请先选客户')
                            return  // 不调 resolve 阻塞
                        }
                        resolve()
                    },
                    beforeSave: (resolve, formData) => {
                        // 提交保存前补参
                        formData.submitTime = Date.now()
                        resolve()
                    },
                    beforeDialog: (resolve, dialogConfig) => {
                        // 自定义审批弹窗标题
                        dialogConfig.title = `提交订单:${this.formData.orderNo}`
                        resolve()
                    },
                    beforeSubmit: (resolve, params) => {
                        // 给审批接口加业务参数
                        params.urgentLevel = this.formData.urgent || 'normal'
                        resolve()
                    },
                    afterSubmit: (resolve) => {
                        this.$message.success('已成功发起审批')
                        // 跳回列表
                        this.pushPage({
                            path: `/module/stander/list/order/0`,
                            title: '订单列表',
                            replace: true
                        })
                        resolve()
                    }
                })
            }
        }
        return data
    }
}
```

---

## 7. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| 写 `flowButtons: [{...}]` 数组想重写"提交"按钮,没生效 | 数组形式只支持简单按钮 | 改用 `flowButtons: function (data) {...}`,在里面找按钮重写 click |
| 调 `Save` / `Submit` 没引 | import 路径错 | 必须从 `@/components/frame/Module/BtnBaseFun/flow-edit` 引入,不是 `@/service/event-expand` |
| 写 `flowButtons` 时用了 `Save` | Save 用于普通表单,流程用 `Save` (flow-edit) | 走 `import { Save } from '@/components/frame/Module/BtnBaseFun/flow-edit'` |
| 事件函数有 `resolve` 但没调 | 流程卡住,不往下走 | 调 `resolve()` 才会继续;异步场景必须 `await` 完再调 |
| 事件函数没 `resolve` 参数,但想异步阻塞 | 不支持 | 加 `resolve` 参数并 `await ...; resolve()` |
| 流程按钮没出现在页面底部 | 后端配置 `GlobalSetting.flow.buttonType = 1` | 加上 `isPage: true` 强制放页面底部 |
| "提交"按钮没找到 | 按钮 name 不是"提交" | 流程按钮名称因后端配置而异,看后端或列表打印 data |

---

## 8. 与 Submit/Save 的关系(状态机)

```
用户在流程页底部点"提交"
  ↓
Submit.call(this, btnObj, {
  beforeValidate:  → 主表单校验
  beforeSave:       → 保存主表单(走保存接口)
  afterSave:        → 主表单保存完成
  beforeDialog:     → 打开审批弹窗
  beforeDialogValidate:  → 审批弹窗校验
  beforeSubmit:     → 提交审批
  afterSubmit:      → 审批提交完成
})
```

---

## 9. 下一步去哪

- **普通表单的提交/保存** → [module-edit-submit-flow](../submit-flow/SKILL.md)
- **字段值变更/联动** → [module-edit-fields](../fields/SKILL.md)
- **回到总览** → [frontend-module-edit](../../SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
