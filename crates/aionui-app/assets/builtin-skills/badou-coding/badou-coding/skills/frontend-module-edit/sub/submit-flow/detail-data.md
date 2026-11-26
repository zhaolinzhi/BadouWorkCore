---
name: module-edit-detail-data
description: 八斗 Module 表单 customSetting — 详情数据请求/响应处理(edit 进入页面时拉详情数据那条线)。当用户说"改详情接口 URL"、"改详情返回结构路径"、"详情请求参数加签"、"详情数据回来再处理/转格式"时触发。覆盖 dataUrl / valuePath / paramsBeforeRequest / afterEditJSON 共 4 个 key。
---

# Module 表单 — 详情数据请求/响应

> 编辑页进入时拉详情数据这条线的 4 个 key。**先看 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

## 1. 详情请求流程(只对 edit/view 生效,add 跳过)

**本节 4 个 key (`dataUrl` / `valuePath` / `paramsBeforeRequest` / `afterEditJSON`) 的 `this` 统一指向 moduleEditCode 实例**,可访问:
- `this.formData` ✅(详情表单数据)
- `this.module` ✅(模型配置)
- `this.mdCode` / `this.detailId` / `this.BASEURL` / `this.$store` ✅

详见 [frontend-module-edit §2.5 this 上下文速查表](../../SKILL.md#25-this-上下文速查表必读-)。

```
用户进入编辑页
  ↓
dataUrl() → URL                ← 改 URL(可选,默认走 /jdbc/common/basecommonedit/editJSON.do)
  ↓
paramsBeforeRequest(params)     ← 改请求参数(可选)
  ↓
请求发到后端 → 后端直接返回 fieldObj 平铺(标准)
  ↓
【标准场景】框架按 valuePath='value' 从每个 fieldObj 里取显示值
【非标准场景】valuePath 自定义            ← fieldObj 内"值"属性名不是 value 时配
  ↓
afterEditJSON(formData)         ← 字段值二次处理(可选)
  ↓
回填到 formData
```

---

## 2. `dataUrl`(详情请求 URL)

**签名**:`dataUrl()` → `String` (必须 return)

**this 指向**:**moduleEditCode 实例**

**this 可用属性**:
- `this.formData` ✅(moduleEditCode 的 data,详情表单数据)
- `this.module` ✅(模型配置)
- `this.mdCode` ✅(模型编码)
- `this.detailId` ✅(编辑时的数据 ID)
- `this.BASEURL` ✅(请求前缀)
- `this.$store` ✅(Vuex,常用于取登录用户信息)

```js
dataUrl: function () {
    // this.BASEURL = '/jdbc'
    return `${this.BASEURL}/common/${this.mdCode}/getEdit.do`
    // 或:return '/jdbc/common/user_info/getEdit.do'
}
```

**实战**(常见模式):
```js
dataUrl () {
    return `${this.BASEURL}/common/${this.mdCode}/getEditCustom.do`
}
```

> 💡 **新接口必须按标准结构返回**:标准响应 = 直接 fieldObj 平铺(无外层包装,无 hasOk/bean/code/data)。
> 如果新接口是标准响应,只需要 dataUrl,不需要配 valuePath/afterEditJSON;
> 如果新接口有外层包装或字段值需要二次处理,才需要配 [§3 valuePath](#3-valuepath详情数据路径) 或 [§5 afterEditJSON](#5-aftereditjson详情数据处理)。

---

## 3. `valuePath`(fieldObj 内部属性路径)

**类型**:`String`(用 `,` 分隔的路径)

**this 指向**:**moduleEditCode 实例**

**默认行为**:框架从每个 fieldObj 里取 `.value` 属性作为显示值(标准 fieldObj 形如 `{ value, fieldId }`)。

**何时需要 valuePath**:**仅当 fieldObj 内"值"的属性名不是 `value` 时**(标准场景不需要)。

```js
// 标准 fieldObj: { value: '11:3', fieldId: '...' }
// 默认取 .value,不需要写 valuePath

// 业务场景 1: 后端把"值"属性名改成了 id
// fieldObj: { id: '11:3', fieldId: '...' }
valuePath: 'id',
```

**实战:嵌套路径**
```js
// fieldObj: { data: { value: '11:3' }, fieldId: '...' }
// 用 , 分隔多层路径
valuePath: 'data,value',
```

> ⚠️ **常见误解**:valuePath **不是**响应外层穿透路径。
> 不要写成 `valuePath: 'bean'` / `valuePath: 'data.body.form'` 这种形式——那是错误用法。
> 标准响应外层没有 hasOk/bean/code/data 等包装,框架直接把整个响应当 formData。

---

## 4. `paramsBeforeRequest`(详情请求参数)

**签名**:`paramsBeforeRequest(params)` → **必须 return** 新参数对象(async 也可)

**this 指向**:**moduleEditCode 实例**

```js
paramsBeforeRequest: function (params) {
    return {
        ...params,
        _t: Date.now(),
        orgId: this.$store?.state?.user?.userInfo?.orgId
    }
}
```

**实战(异步加签)**:
```js
paramsBeforeRequest: async function (params) {
    const sign = await this.$axios.get('/api/sign', { params })
    return { ...params, sign: sign.data }
}
```

---

## 5. `afterEditJSON`(详情数据处理)

**签名**:`afterEditJSON(formData)` → **必须 return** 处理后的 formData

**this 指向**:**moduleEditCode 实例**

### 5.1 转码 / 转格式

```js
afterEditJSON: function (formData) {
    // 后端给的是"0/1",前端要显示"禁用/启用"
    formData.statusText = formData.status === 1 ? '启用' : '禁用'
    // 时间戳转日期
    formData.createTime = this.$moment?.(formData.createTime).format('YYYY-MM-DD HH:mm:ss')
    return formData
}
```

### 5.2 默认值兜底

```js
afterEditJSON: function (formData) {
    // 后端没返回的字段,前端给个默认值
    return {
        ...formData,
        needRemark: formData.needRemark ?? false,
        tags: formData.tags || []
    }
}
```

### 5.3 字段重命名(后端字段名跟前端不一致时)

```js
afterEditJSON: function (formData) {
    return {
        ...formData,
        userName: formData.user_name,  // 后端 snake_case → 前端 camelCase
        phone: formData.mobile
    }
}
```

---

## 下一步去哪

- 改模型配置(加按钮/字段) → [module-config](module-config.md)
- 改保存地址/自定义按钮/暂存 → [save-and-buttons](save-and-buttons.md)
- 回到总览 → [frontend-module-edit](../../SKILL.md)
