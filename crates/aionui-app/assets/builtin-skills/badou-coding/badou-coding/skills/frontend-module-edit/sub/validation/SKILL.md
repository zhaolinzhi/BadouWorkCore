---
name: frontend-module-edit-validation
description: 八斗 Module 表单 customSetting — 校验规则 / 动态显隐 / 动态只读完整指南。当用户说"加自定义校验"、"字段动态显隐"、"动态只读"、"动态必填"、"唯一性校验"时触发。覆盖 validateRule + 显隐/只读/必填的所有方式(valueChange 联动 / fieldObj.fieldChange 后端配置 / controlShowAndHide)。
---

# Module 表单 — 校验 / 动态显隐 / 动态只读

> 表单"控制"类的全部手段:校验、显隐、只读、必填。**先看 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/edit.js` 的 `export default` 对象里。

**进入前必读**:mdCode + edit/add/view + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的内容

| 主题 | 涉及 key | 频次 |
|------|---------|------|
| 自定义校验规则 | `validateRule` | ⭐⭐⭐⭐ |
| 动态显隐 | `valueChange` + `setFieldVisible` / 后端 `fieldChange` 配置 | ⭐⭐⭐⭐⭐ |
| 动态只读 | `valueChange` + `setFieldReadonly` | ⭐⭐⭐⭐ |
| 动态必填 | `valueChange` + `setFieldRequired` | ⭐⭐⭐⭐ |
| 唯一性校验 | `Value_Unique_Fun`(系统方法) | ⭐⭐⭐ |

---

## 2. `validateRule`(自定义校验规则)

**签名**:`validateRule(fieldList)` → **必须 return** `{ [字段名]: [Rule数组] }`

**this 指向**:**moduleForm 实例**

> ⚠️ **`this.formData` 不存在**,要从 `this.$attrs.formData` 取(动态校验要根据其它字段值时尤其注意)。

### 2.1 基本结构

```js
import { validatePhone, validateIdCard } from '@/utils/validators'

validateRule: function (fieldList) {
    return {
        // 字段名: 规则数组
        userName: [
            { required: true, message: '用户名必填', trigger: 'blur' },
            { min: 3, max: 20, message: '长度 3-20', trigger: 'blur' }
        ],
        phone: [
            { required: true, message: '手机号必填', trigger: 'blur' },
            { validator: validatePhone, trigger: 'blur' }
        ],
        idCard: [
            { validator: validateIdCard, trigger: 'blur' }
        ]
    }
}
```

### 2.2 规则简写:字符串形式

```js
validateRule: function (fieldList) {
    return {
        // 字符串:会被识别为"该字段名必填"
        userName: 'required',
        // 字符串 + 对象混用
        phone: [
            'required',
            { validator: validatePhone, trigger: 'blur' }
        ]
    }
}
```

### 2.3 实战:动态校验(根据其它字段值决定)

```js
validateRule: function (fieldList) {
    const _this = this
    return {
        amount: [
            { required: true, message: '金额必填', trigger: 'blur' },
            {
                validator: function (rule, value, callback) {
                    if (_this.formData.orderType === 'A' && value <= 0) {
                        callback(new Error('A 类订单金额必须大于 0'))
                    } else {
                        callback()
                    }
                },
                trigger: 'blur'
            }
        ]
    }
}
```

### 2.4 实战:加自定义异步校验(用户名唯一性)

```js
import { uniqueCheck } from '@/api/user'

validateRule: function (fieldList) {
    const _this = this
    return {
        userName: [
            { required: true, message: '必填', trigger: 'blur' },
            {
                validator: function (rule, value, callback) {
                    if (!value) {
                        callback()
                        return
                    }
                    uniqueCheck({ userName: value, excludeId: _this.detailId })
                        .then(res => {
                            if (res.data.exists) {
                                callback(new Error('用户名已存在'))
                            } else {
                                callback()
                            }
                        })
                        .catch(() => callback())
                },
                trigger: 'blur'
            }
        ]
    }
}
```

### 2.5 手动触发校验

```js
// 在 valueChange 里校验其它字段
valueChange: {
    type (formScope, fieldName, value) {
        formScope.validateField('amount')  // 立即校验 amount 字段
    }
}
```

---

## 3. 动态显隐(3 种方式)

### 3.1 方式 A:`valueChange` 里调 `setFieldVisible`(推荐)

```js
valueChange: {
    type (formScope, fieldName, value) {
        formScope.setFieldVisible('amount', value === 'A')
        formScope.setFieldVisible('quantity', value === 'B')
    }
}
```

**优势**:逻辑集中在 customSetting,后端不需要配。
**适用**:联动规则跟业务强相关、需要前端写代码。

### 3.2 方式 B:后端 module JSON 的 `fieldChange` 配置(纯配置,免代码)

后端在字段上配 `fieldChange`:

```json
{
    "name": "type",
    "fieldChange": {
        "A": { "showFields": ["amount"], "hiddenFields": ["quantity"] },
        "B": { "showFields": ["quantity"], "hiddenFields": ["amount"] }
    }
}
```

**优势**:业务方改规则不用发版。
**适用**:规则简单、不需要发请求。

### 3.3 方式 C:`beforeRender` 初始化时根据已有值显隐

```js
beforeRender: function (fieldList) {
    // 初始时根据 formData.type 显隐
    const type = this.formData.type
    fieldList.forEach(f => {
        if (type === 'A' && f.name === 'amount') f.isShow = true
        if (type === 'A' && f.name === 'quantity') f.isShow = false
    })
    return fieldList
}
```

---

## 4. 动态只读 / 动态必填

> 语法跟"动态显隐"完全一样,只是方法名不同。

```js
valueChange: {
    // 1. 选了 A → 锁定 amount;选 B → 锁定 quantity
    type (formScope, fieldName, value) {
        formScope.setFieldReadonly('amount', value !== 'A')
        formScope.setFieldReadonly('quantity', value !== 'B')
    },
    
    // 2. 勾选"需要备注" → 备注必填 + 可填
    needRemark (formScope, fieldName, value) {
        formScope.setFieldRequired('remark', !!value)
        formScope.setFieldReadonly('remark', !value)
    },
    
    // 3. 状态变成"已审核" → 所有字段只读
    status (formScope, fieldName, value) {
        const readonly = value === 'approved'
        formScope.fieldList.forEach(f => {
            formScope.setFieldReadonly(f.name, readonly)
        })
    }
}
```

**formScope 完整方法集**:
- `setFieldValue(name, val)` — 改值
- `setFieldVisible(name, bool)` — 显隐
- `setFieldReadonly(name, bool)` — 只读
- `setFieldRequired(name, bool)` — 必填
- `setFieldOptions(name, options | url)` — 改 options
- `getFieldValue(name)` — 取值
- `validateField(name)` — 校验单个字段
- `validateForm()` — 校验整个表单

---

## 5. 地址本 / 弹窗选列表 特殊赋值(`beforeRender` + `extraValueObj`)

> 字段类型是 `addressBook`(地址本)或 `dialogList`(弹窗选列表)时,赋值跟普通字段不一样。
> 因为它们内部存的是"类型!@!名称!@!id"这种特殊格式。

### 5.1 地址本赋值(2 种方式)

```js
beforeRender: function () {
    // 找到地址本字段
    let xxField = this.fieldList.find(f => f.name === 'addressBook')
    
    // 方式 1:用 extraValueObj(冗余字段一致时)
    // xxId, xxName 分别是地址本配置【保存Key值给】【保存Value给】所填写的字段名
    xxField.extraValueObj = {
        xxId: '123',
        xxName: '名称'
    }
    xxField.value = '123'
    
    // 方式 2:用 value 字符串
    // 格式:地址本类型!@!选中值显示文本!@!选中值id
    xxField.value = '1!@!运维管理!@!2c9fdee666f125010166f148970f0018'
}
```

### 5.2 弹窗选列表赋值

```js
beforeRender: function () {
    // 假设字段 __A 配置为弹窗选择列表的类型
    let __A = this._fieldList.find(i => i.name === '__A')
    // id 值
    __A.value = '833172f5f81842b9864c95ba4c0e2672058617b1497f47819c038f3b267417c9'
    // 文本值
    __A.valueText = '测试弹窗级联'
}
```

### 5.3 地址本动态修改 config(tree / options 过滤)

```js
// 工具方法
function setConfig (dataList, fieldName, fieldValue) {
    let addressbookField = dataList.find(i => i.name === fieldName)
    let params = [{ name: 'name', value: fieldValue, type: 'text-query', tagName: '' }]
    addressbookField.config = {
        treeDefaultParams: JSON.stringify(params),
        optionDefaultParams: JSON.stringify(params)
    }
}

export default {
    // 1. 渲染前过滤
    beforeRender: function () {
        setConfig(this._fieldList, 'addressBook', '哇咔咔')
    },
    // 2. valueChange 联动过滤
    valueChange: {
        addressBook: function (formScope, fieldName, value, fieldObj) {
            setConfig(formScope.dataList, 'addressBook', '哇咔咔2')
        }
    }
}
```

### 5.4 弹窗选列表加默认参数(`fieldCustom.initDialogParams`)

```js
fieldCustom: {
    dialogB: {
        /**
         * 弹窗初始默认参数
         * @param {Object} formData 表单数据对象
         */
        initDialogParams: function ({ formData }) {
            return {
                // 显示在搜索框
                searchParam: { code: 'wjx' },
                // 默认查询参数
                defaultParamsObj: { tableName: 'wj' }
            }
        }
    }
}
```

---

## 7. 关键事实

| 项 | 说明 |
|------|------|
| `validateRule` 不 return | 校验规则丢失(走默认) |
| `validateRule` 字段名拼错 | 该字段无规则(不影响其它字段) |
| 动态显隐不会触发 valueChange | setFieldVisible 不算"值变化" |
| 动态只读 + 显隐 同时设置 | 都生效(只读不显示也没问题) |
| 字段 required = true 但不可见 | 框架仍会校验,可能校验失败 — 业务方自己协调 |
| `fieldList` 里有但 `setFieldVisible(false)` | 字段从 DOM 消失,且不参与校验 |

---

## 8. 完整实战:联动 + 校验 + 显隐/只读/必填 组合

```js
// public/moduleJs/order/edit.js
import { validatePhone, uniqueCheck } from '@/api/order'

export default {
    // 1. 字段联动
    valueChange: {
        // 选 A/B 类型 → 字段切换
        type (formScope, fieldName, value) {
            formScope.setFieldVisible('amount', value === 'A')
            formScope.setFieldVisible('quantity', value === 'B')
            formScope.setFieldVisible('redeemCode', value === 'C')
            
            // 锁定非当前类型的字段
            formScope.setFieldReadonly('amount', value !== 'A')
            formScope.setFieldReadonly('quantity', value !== 'B')
        },
        
        // 勾选"需要备注" → 备注必填
        needRemark (formScope, fieldName, value) {
            formScope.setFieldRequired('remark', !!value)
            formScope.setFieldReadonly('remark', !value)
        },
        
        // 状态变成"已审核" → 锁全部
        status (formScope, fieldName, value) {
            if (value === 'approved') {
                formScope.fieldList.forEach(f => {
                    formScope.setFieldReadonly(f.name, true)
                })
            }
        }
    },
    
    // 2. 校验规则
    validateRule: function (fieldList) {
        const _this = this
        return {
            orderNo: [
                { required: true, message: '订单号必填' }
            ],
            customer: [
                { required: true, message: '客户必填' }
            ],
            amount: [
                {
                    validator: function (rule, value, callback) {
                        if (_this.formData.type === 'A' && (!value || value <= 0)) {
                            callback(new Error('A 类订单金额必须大于 0'))
                        } else {
                            callback()
                        }
                    },
                    trigger: 'blur'
                }
            ],
            // 唯一性校验
            orderCode: [
                { required: true, message: '必填' },
                {
                    validator: function (rule, value, callback) {
                        if (!value) return callback()
                        uniqueCheck({ orderCode: value, excludeId: _this.detailId })
                            .then(res => {
                                res.data.exists
                                    ? callback(new Error('订单号已存在'))
                                    : callback()
                            })
                            .catch(() => callback())
                    },
                    trigger: 'blur'
                }
            ]
        }
    }
}
```

---

## 9. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| `validateRule` 不生效 | 忘了 return | 必须 return `{ [field]: [Rule] }` |
| 动态校验的 this 是 undefined | 用了箭头函数 | 用普通 function,或 `_this = this` 缓存 |
| 字段 hidden 仍报错 | hidden 字段未参与校验? | 框架规则:hidden 字段不参与校验,检查是否手动 validateField |
| setFieldVisible(false) 后字段 required 仍校验 | 必填规则没撤 | 显隐时同时 `setFieldRequired(false)` |
| `fieldChange` 后端配置不生效 | 格式写错 | 严格 `{value: {showFields: [...], hiddenFields: [...]}}` |
| 动态必填改了 UI 没反应 | 没在 valueChange 里 setFieldRequired | valueChange 必走 |
| 异步校验 callback 多次调用 | 没防抖 | 用 `setTimeout` + clearTimeout,或用 lodash.debounce |

---

## 10. 下一步去哪

- **字段值变更/联动基础** → [module-edit-fields](../fields/SKILL.md)
- **字段后追加 DOM / 重排版** → [module-edit-form-react](../form-react/SKILL.md)
- **数据请求/保存** → [module-edit-submit-flow](../submit-flow/SKILL.md)
- **回到总览** → [frontend-module-edit](../../SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
