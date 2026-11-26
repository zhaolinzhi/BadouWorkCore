---
name: frontend-module-list-request-flow
description: 八斗 Module 列表 customSetting — **请求配置层**(URL / 方法 / 参数 / 完全接管)。当用户说"改请求方法"、"加签"、"改请求 URL"、"请求前改参数"、"换 GET 请求"、"自定义请求完全接管" 时触发。覆盖 dataUrl / requestMethod / paramsBeforeRequest / diySearch 4 个 key。
---

# Module 列表 — 请求配置层

> 列表请求"发出去前的所有事"——URL、方法、参数、完全接管。本 skill 是 [data-flow index](../data-flow/SKILL.md) 的子章节。

> 📌 涉及的文件落点:**动手前先确认 JS 路径**(必读) → 详见 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 4 个 key

| key | 用途 | 频次 | 是否接管请求 |
|------|------|------|------|
| `dataUrl` | 自定义请求 URL(**必须是函数**) | ⭐⭐⭐⭐ | ❌ |
| `requestMethod` | 自定义 HTTP 方法(GET/POST) | ⭐⭐ | ❌ |
| `paramsBeforeRequest` | 请求前改参数(加签/补默认) | ⭐⭐⭐⭐⭐ | ❌ |
| `diySearch` | 完全接管请求 | ⭐⭐ | ✅ |

> 💡 前三个 key 简称**"三件套"**——能不写 diySearch 就不写。详见 [§7 决策速查](#7-决策速查三件套-vs-diysearch高频)。

> 💡 `requestMethod` 是 MList 组件的 prop,通过 `updateCustomSetting` 的 `...elseTableAttrs` 透传,**没在 §1 表里列**但实测有效。

---

## 2. `dataUrl`(自定义请求 URL)⭐⭐⭐

**来源**:[src/components/frame/Module/ModuleList/index.vue:450-451](../../../../components/frame/Module/ModuleList/index.vue#L450-L451)

**签名**:`dataUrl()` → `String`,**必须是函数**,返回请求 URL

**this 指向**:**moduleList 实例**(可通过 `this.BASEURL` / `this.mdCode` / `this.$store` 读)

```js
// 框架调用源码:
if (this.diy_dataUrl && typeof this.diy_dataUrl === 'function') {
    _url = this.diy_dataUrl.call(this)
}
```

> ⚠️ **必须是函数,字符串会被框架忽略**——`typeof === 'function'` 判断不通过,直接跳过走默认 URL。

### 2.1 基础用法(固定路径)

```js
dataUrl: function () {
    return '/assetsInfo/good/listJSON.do'
}
```

### 2.2 动态拼接 BASEURL / mdCode

```js
dataUrl: function () {
    return `${this.BASEURL}/jdbc/common/xxx/customList.do?mdCode=${this.mdCode}`
}
```

### 2.3 实战(摘自 `public/moduleJs/business/text/wjx_form_list.js:2-5`)

```js
exportUrl: function () {
    return `${this.BASEURL}/jdbc/common/basecommonlist/export.do?mdCode=${this.mdCode}`
}
```

> 💡 Edit 页的 `dataUrl` 同样必须是函数,但走的是表单详情接口,见 [module-edit-submit-flow](../../../../frontend-module-edit/sub/submit-flow/SKILL.md)。

---

## 3. `requestMethod`(自定义请求方法)⭐⭐

**来源**:`MList/index.vue` 第 266 行 `requestMethod: { type: String, default: 'post' }`

**签名**:`requestMethod` → `String`,直接写值,不接受函数

**透传机制**:customSetting 里**任意 MList / ModuleList 组件的 prop 名**(驼峰或短横线)都会通过 `updateCustomSetting` 的 `...elseTableAttrs` 透传给 MList(见 [ModuleList/index.vue:1015-1017](../../../../components/frame/Module/ModuleList/index.vue#L1015-L1017))

### 3.1 改 GET 请求(本项目实战 2026-06-24)

```js
requestMethod: 'get'
```

GET 请求下,`paramsBeforeRequest` 加的参数会以 **URL query string** 形式拼到 URL 后,**不会进 body**——这是从 POST 切 GET 最容易忽略的点。

### 3.2 为什么这个 key 在 SKILL 文档里不太显眼

它不在 6 个高频 key 之列(MList 有 60+ 个 prop,没法都列),但属于"**写 customSetting 时配 prop 名拼对就生效**"的那一类。常见一起配的 MList prop:

| 透传 prop | 作用 |
|------|------|
| `requestMethod` | GET/POST 等 HTTP 方法 |
| `optionResPath` | 响应中表格数据的字段路径(如 `'data.list'`) |
| `totalPath` | 响应中总条数的字段路径(如 `'data.total'`) |
| `requestConfig` | 额外 axios 配置(headers / timeout / cancelToken) |
| `usePagination` / `showPagination` | 启用/显示分页 |

---

## 4. `paramsBeforeRequest` ⭐⭐⭐⭐⭐(请求前改参数)

**来源**:`ModuleList/index.vue` 第 783-785 行

**签名**:`paramsBeforeRequest(params)` → **必须 return** 新参数对象

**this 指向**:**mList 实例**

### 4.1 通用:加签 / 补固定参数

```js
paramsBeforeRequest: function (params) {
    return {
        ...params,
        orgId: this.$store?.state?.user?.userInfo?.orgId,
        _t: Date.now(),  // 防缓存
        sign: this.$md5?.(JSON.stringify(params))  // 加签
    }
}
```

### 4.2 改分页

```js
paramsBeforeRequest: function (params) {
    return { ...params, page: 1, pageSize: 50 }
}
```

### 4.3 实战(摘自 `public/moduleJs/business/text/wjx_form_list.js:9-11`)

```js
paramsBeforeRequest: function (params) {
    return params
}
```

### 4.4 透传 + 强制追加

```js
paramsBeforeRequest: function (params) {
    return Object.assign({}, params, {
        // 强制覆盖
        clientType: 'web',
        token: this.$store?.state?.user?.token
    })
}
```

> ⚠️ **不 return = 啥也不生效**。多数"paramsBeforeRequest 没生效"都是忘了 return。

### 4.5 页码参数 `pageNo`(框架默认)

框架默认页码参数名是 `pageNo`,见 [src/setting/frame-const.js:162-170](../../../../setting/frame-const.js#L162-L170):

```js
pagination: {
    noName: 'pageNo',
    sizeName: 'perPageSize',
    ...
}
```

如业务后端字段名一致,**不用额外配 `paginationNameObj`**——直接用默认。

---

## 5. `diySearch`(完全自定义请求)⭐⭐

**签名**:`diySearch(requestConfig)` → `Boolean`(return `true` 表示"已处理,别走默认请求")

**this 指向**:**mList 实例**

```js
diySearch: function (requestConfig) {
    // requestConfig = { url, method, params, ... }
    // this 指向 mList
    
    this.$axios({
        url: '/my/custom/api',
        method: 'post',
        data: this.finalListParams
    }).then(res => {
        this.temp_data = res.data.list
        this.temp_total = res.data.total
    })
    
    return true  // 告诉框架"我已经处理了"
}
```

> ⚠️ 谨慎使用:它**完全绕过**默认请求、loading、分页等。

> 💡 **核心原则**:**能用三件套搞定的,坚决别用 `diySearch`**——详见 [§7 决策速查](#7-决策速查三件套-vs-diysearch高频)。

---

## 6. 关键事实

| 函数 | 不 return 后果 |
|------|---------------|
| `dataUrl` | 自定义 URL 不生效(回退默认) |
| `paramsBeforeRequest` | 啥也不生效 |
| `diySearch` | `return true` 表示已处理,否则走默认 |

**this 指向差异**:`dataUrl` 在 moduleList;`paramsBeforeRequest` / `diySearch` 在 mList。

---

## 7. 决策速查:三件套 vs `diySearch`(高频)

> **何时用本节**:用户要做"换 URL / 换方法 / 加签 / 换参数",你先判断**该不该直接用 `diySearch` 完全接管**——大多数情况**三件套就够了,别上 `diySearch`**。

### 7.1 对比表(快速决策)

| 维度 | 三件套 `dataUrl` + `requestMethod` + `paramsBeforeRequest` | `diySearch`(完全接管) |
|------|------|------|
| 配置量 | **3~5 行** | **20~40 行** |
| 是否接管请求 | ❌ 不接管,框架继续发请求 | ✅ `return true` 跳过默认请求 |
| 是否接管响应 | ❌ 不接管,走 `afterListJSON` | ✅ 自己塞 `temp_data` / `temp_total` |
| 分页 | ❌ 框架默认(`pageNo`/`perPageSize`) | ⚠️ 手动维护 `temp_params`,翻页自己 `this.init()` |
| loading / 错误提示 | ❌ 框架默认 | ⚠️ 框架的 axios 拦截器仍生效,但 loading/alert 都得自己写 |
| sort 字段 | ❌ 框架按 `column.property` 拼 | ⚠️ 自己在 `temp_params` 里拼 |
| 响应路径 | ❌ 配 `optionResPath` / `totalPath` prop | ⚠️ 自己 `Get_Data_By_Path` 解析 |
| 加签 / Token | ✅ 自动走 axios 拦截器 | ✅ axios 拦截器仍生效,但容易漏 |
| this 指向 | `dataUrl`→moduleList,其余→mList | mList |

### 7.2 决策树(直接照抄)

| 你的需求 | 怎么配 | 用什么 key |
|---------|--------|-----------|
| 只换 URL | `dataUrl: function () { return '/my.do' }` | `dataUrl` |
| 只换方法(GET ↔ POST) | `requestMethod: 'get'` | `requestMethod`(MList prop,通过 `elseTableAttrs` 透传,**§1 没列但实测有效**) |
| 加签 / 补参数 / 默认筛选 | `paramsBeforeRequest: function (p) { return { ...p, sign: ... } }` | `paramsBeforeRequest` |
| **三件组合**(URL + 方法 + 参数,如本次实战) | 同时配上面 3 个 key | **三件套** |
| 默认响应路径不对 | 配 `optionResPath` / `totalPath` prop | `elseTableAttrs` 透传 |
| 加自定义 `headers` / `timeout` | 配 `requestConfig` prop | `elseTableAttrs` 透传 |
| 自定义 body(`data` 而非 `params`) | 配 `requestConfig.data` 或 `diySearch` | 半接管或全接管 |
| 完全非 RESTful(GraphQL / gRPC-Web / RPC) | — | **必须 `diySearch`** |
| SSE / WebSocket 上行 / 流式上传 | — | **必须 `diySearch`** |
| 后端接口一个请求要触发多次列表更新 | — | **`diySearch` + 自己管 state** |
| **穷举:什么时候非 `diySearch` 不可** | 上面 3 行打勾才算 | — |

### 7.3 `diySearch` 的 5 个易错点(失效模式清单)

写 `diySearch` 时**逐一对照**,漏一个就埋雷:

1. **必须 `return true`** —— 不 return 框架还会再发一次默认请求,**请求发 2 次**,后端收到重复请求可能报错/数据错乱
2. **必须手动设置 `this.temp_data`** —— 表格数据源,没设置就空白
3. **必须手动设置 `this.temp_total`** —— 总条数,没设置分页器会显示 0 / 翻页无效
4. **必须自己 `this.$loading`** 或类似 —— 框架的 loading 不会因为你接管请求就停,可能转圈一直转/不转
5. **必须自己处理 sort / 分页参数** —— 用户点排序、翻页时,你需要自己监听并重发请求

外加:

- **响应错误处理** 框架默认 toast 会绕过,自己写 `$message.error`
- **导出/导入按钮** 默认按钮走的是 `exportUrl` / `importUrl`,跟 `diySearch` 无关,不用接管
- **`afterListJSON`** 在 `diySearch` 里**仍会执行**(因为 `temp_data` 被赋值后会触发),所以 `afterListJSON` 该写还得写

### 7.4 本次实战(2026-06-24,wjx_goods_list)

**需求**:
- URL 改 `/project/goods/getListJSON.do`
- 方法改 GET
- 页码参数 `pageNo`

**方案**:三件套,**3 行搞定**(没用 `diySearch` 写 25 行)

```js
dataUrl: function () {
    return '/project/goods/getListJSON.do'
},
requestMethod: 'get',  // MList prop,通过 updateCustomSetting 的 ...elseTableAttrs 透传
paramsBeforeRequest: function (params) {
    return { ...params, deleteFlg: 0 }
}
```

**为什么不用 `diySearch`**:

- ✅ 框架默认 `pageNo` 字段就是对的(见 [src/setting/frame-const.js:167](../../../../setting/frame-const.js#L167) `noName: 'pageNo'`),不用自己拼分页参数
- ✅ `afterListJSON` 还能沿用,不用自己解析 `temp_data`
- ✅ `loading` / 错误提示 / 翻页 / 排序 / 多选 全部免费送
- ✅ 3 行 vs 25 行,后续维护差 10 倍

**`requestMethod` 这个 key 为什么在 §1 没列但实测有效**:

- 它是 MList 组件的 prop(见 [src/components/frame/Common/MList/index.vue:266](../../../../components/frame/Common/MList/index.vue#L266) `requestMethod`)
- ModuleList 的 `updateCustomSetting` 用 `...elseTableAttrs` 模式(见 [ModuleList/index.vue:1015-1017](../../../../components/frame/Module/ModuleList/index.vue#L1015-L1017))把 customSetting 里没显式声明的 key 全透传给 MList
- 结论:任何 MList/ModuleList 组件的 prop,理论上都能在 customSetting 里配,只要 prop 名拼对(驼峰或短横线)

### 7.5 常见组合模板(收藏)

**模板 A:换 URL + GET + 加签**(三件套最常见用法)

```js
dataUrl: function () {
    return `${this.BASEURL}/project/xxx/getListJSON.do`
},
requestMethod: 'get',
paramsBeforeRequest: function (params) {
    return {
        ...params,
        sign: this.$md5?.(JSON.stringify(params)),
        _t: Date.now()
    }
}
```

**模板 B:POST + 补默认查询 + 字段名翻译**(纯 paramsBeforeRequest)

```js
paramsBeforeRequest: function (params) {
    return {
        ...params,
        // 1. 默认只查未删除
        deleteFlg: 0,
        // 2. 字段名翻译(后端要的字段名跟页面不一样)
        statusFilter: params.statusDesc
    }
}
```

**模板 C:`diySearch` 最小可用**(迫不得已时,缺一项就报错)

```js
diySearch: function (requestConfig) {
    this.$axios({
        url: '/graphql',
        method: 'post',
        data: {
            query: `query { goods { id name status } }`,
            variables: this.finalListParams
        }
    }).then(res => {
        this.temp_data = res.data?.data?.goods || []   // 1
        this.temp_total = res.data?.data?.goods?.length || 0  // 2
        this.$loading?.close?.()                       // 3
    }).catch(err => {
        this.$message.error(err.message)               // 4
        this.temp_data = []
        this.temp_total = 0
    })
    return true   // 5 必须
}
```

### 7.6 ⚠️ 联动影响(用了三件套时容易出问题)

- **GET 请求**:`paramsBeforeRequest` 里加的参数(本例 `deleteFlg: 0`)会以 **URL query string** 形式拼到 URL 后,**不会进 body**。如果后端只读 body,从 GET 改 POST 时这个差异要重新检查
- **字段名变化**:后端换接口可能字段名也跟着变(如 `deleteFlg` 改成 `isDeleted`),只改 `dataUrl` 不改 `paramsBeforeRequest` 会送出错的字段名,**两个 key 联动检查**
- **`searchCondition` 字段**:搜索栏的参数 key 是后端模型设计器配的(在 `searchCondition` 里),跟页码参数(`pageNo`)是两套,**不要混**——`pageNo` 改 `page` 跟搜索栏 key 无关
- **`requestConfig` prop**:MList 还有 `requestConfig: { type: Object, default: () => {} }`,跟 `dataUrl` / `requestMethod` 是叠加关系,可以同时配(headers/timeout/cancelToken 等)

### 7.7 决策一句话总结

> **能用 dataUrl / requestMethod / paramsBeforeRequest 三个 key 解决 → 三件套;非 `diySearch` 不可的(GraphQL/SSE/完全接管响应) → diySearch;两者都行 → 优先三件套(代码短 10 倍,bug 少 5 倍)**。

---

## 8. 常见问题(请求配置)

| 问题 | 现象 | 解决 |
|---|------|------|
| 改完 paramsBeforeRequest 没生效 | 忘了 return | 必须 return 新对象 |
| Network 看不到新参数 | paramsBeforeRequest 里 `return` 写成函数表达式 | 用 `return { ...params, ... }` |
| 改 `dataUrl` 不生效 | 写成字符串形式 `dataUrl: '/xxx.do'` | **必须是函数** `dataUrl: function () { return '/xxx.do' }`,框架在 ModuleList/index.vue:450 用 `typeof === 'function'` 判断,字符串直接被跳过走默认 URL |
| `requestMethod` 不生效 | name 拼错(写成 `'GET'` 大写) | axios 默认小写,建议都用 `'get'` / `'post'` |
| `paginationNameObj` 想改页码名 | 这个 prop 不在 customSetting 6 个高频 key 里,要透传到 MList 也得用 elseTableAttrs,但 pageNo 已经是默认,通常不用配 | 见 §4.5 框架默认配置 |

---

## 9. 下一步去哪

- **响应处理**(数据返回后怎么处理) → [response-flow](../response-flow/SKILL.md)
- **模型配置变更**(改 fieldList / searchCondition 等) → [module-config-mutation](../module-config-mutation/SKILL.md)
- **回到入口** → [data-flow index](../data-flow/SKILL.md)
- **回到列表 customSetting 总览** → [frontend-module-list](../../SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)

---

## 10. 修订记录

- **2026-06-24**:从原 data-flow/SKILL.md 拆出,合并 §2 dataUrl + §3 paramsBeforeRequest + §4 diySearch + §11 决策速查,并独立加 §3 requestMethod(原 §11 间接提到的)
