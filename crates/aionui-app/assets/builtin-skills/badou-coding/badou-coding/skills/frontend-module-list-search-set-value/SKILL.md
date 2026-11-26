---
name: frontend-module-list-search-set-value
description: Use when 用代码主动设置/修改 Module 列表页搜索项的值(运行时动态改、初始化默认值、按钮触发、联动赋值、重置清空)。常见触发:"更新搜索条件"、"设置时间范围"、"给搜索栏赋值"、"批量预填"、"打开页面默认选中"、"清空搜索项"、"在过去的 N 天之内"、"超过 N 天之前"、"如何给搜索项赋值"。
---

# Module 列表 — 如何主动设置/修改搜索项的值

> 用代码**主动控制**列表页某个搜索项的值(运行时 / 初始化 / 联动 / 清空)。**核心就 3 行代码**,所有场景都适用。
>
> 📌 **本 skill 的核心**:每个搜索项类型都有**特定的值格式** — 设错格式组件不会报错,但 UI 不显示 / 后端过滤失效。

---

## 1. 何时调用本 skill

✅ **进入**:用户说...
- "更新搜索条件"、"设置时间范围"、"给搜索栏赋值"、"搜索项默认值"
- "批量预填"、"打开页面默认选中"
- "清空搜索项"、"重置搜索项"
- "改了 X 自动给 Y 赋值"、"搜索项联动"
- "在过去的 N 天之内"、"超过 N 天之前"(Date 组件的模式 2/3)
- "如何修改/设置某个搜索项"

❌ **不进入**:
- 后端模型设计器配置 → 走 model designer
- 只读搜索项的值 → [module-list-search §2](../frontend-module-list/sub/search/SKILL.md)
- 按角色显隐搜索项 / 改 selectType / 动态加搜索项 → [module-list-search §4](../frontend-module-list/sub/search/SKILL.md)

---

## 2. 核心:3 行代码设值

**不管什么场景,主动设置/修改搜索项的值都是这 3 行:**

```js
// 1. 定位:在 searchFieldList 里找到对应项(按 id)
let item = this.searchFieldList.find(i => i.id === 'updateTime')

// 2. 赋值:直接改 item.value(格式见 §3,按类型)
item.value = { dateType: '0', startTime: '2025-01-01', endTime: '2025-12-31' }

// 3. 触发搜索(框架不会自动搜,必须手动 this.search())
this.search()
```

**关键事实**:
- `this.searchFieldList` 是 **moduleList 实例**上的属性(详见 §6 总表)
- 它是搜索栏 UI 的实时引用,改完 UI **立刻更新**
- 改完值**不会自动搜索**,必须 `this.search()`
- 在 `searchConditionChange` 函数里 `searchFieldList` 是参数(同一引用),可直接用

---

> ⚠️ **阅读 §3 之前,先看这 3 条最高频易错点**(每条都让"代码改了但什么也没发生"):
>
> | # | 问题 | 一句话解法 |
> |---|---|---|
> | 1 | 改了 Date 的 `value` 但 **UI 没切换模式** | value 必须带 `dateType: '0'`/`'1'`/`'2'`,和 UI 当前 radio 模式**严格匹配**(详见 §3.1) |
> | 2 | 改了 `item.value` 但 **UI 没变化** | 必须用 `this.searchFieldList.find()` 走**引用**;禁止 `JSON.parse(JSON.stringify(...))` / 浅拷贝 / `Object.freeze` |
> | 3 | 改了值但 **列表没刷新** | 改完手动 `this.search()`(框架不会自动搜) |
>
> 完整 12 条见 §7。

---

## 3. 各搜索项类型的值格式(必读,核心)

### 3.1 时间选择器 `selectType: 5` — 3 种模式

> 来源:`src/components/frame/Common/MSearch/components/Date.vue` 第 268-300 行 `updateValue` 方法

#### 🎯 先选模式,再写 value(决策树)

```
用户的需求是?
├─ "显示具体起止日期"(如合同时间、财报日期) → 模式 1(时间段)
├─ "近 N 天/月/年"(自然语义,如报表默认)   → 模式 2(过去 N [单位] 内)
└─ "超过 N 天/月/年 之前"(如 30 天前订单)  → 模式 3(超出 N [单位] 前)
```

**反向选择**(两种都能过滤相同数据,但 UI 体验不同):

| 场景 | 推荐模式 | UI 效果 |
|---|---|---|
| 财报 / 合同 / 订单详情,**用户期望看到具体日期** | 模式 1 | `2025-01-01 至 2025-12-31` |
| 报表 / 仪表盘,**模糊语义就够** | 模式 2 | `在过去的 1 年之内` |
| 风控 / 滞留数据,**强调"超过"** | 模式 3 | `超过 30 天之前` |

⚠️ **错选了模式不会报错**:同一段数据,模式 1 显示"2025-07-02 至 2026-07-02",模式 2 显示"在过去的 1 年之内"——**都能过滤,但用户看到的界面不一样**。先想清楚 UI 文案再选模式。

时间搜索项有 **3 种模式**,每种模式的 `value` 格式**完全不同**:

| 模式 | UI 表现 | value 格式 | dateType |
|------|---------|-----------|----------|
| **模式 1:时间段** | 开始日期 至 结束日期 | `{ dateType: '0', startTime: '2025-01-01', endTime: '2025-12-31' }` | `'0'` |
| **模式 2:相对时间(过去)** | 在过去的 N 天/周/月/年 之内 | `{ dateType: '1', afterTime: 7, measurement: 'd' }` | `'1'` |
| **模式 3:相对时间(之前)** | 超过 N 天/周/月/年 之前 | `{ dateType: '2', beforeTime: 7, measurement: 'd' }` | `'2'` |

#### 模式 1:时间段(开始日期 至 结束日期)

```js
item.value = {
    dateType: '0',
    startTime: '2025-01-01',  // 格式:yyyy-MM-dd(注意是字符串,不是 Date 对象)
    endTime: '2025-12-31'
}
```

#### 模式 2:在过去的 N [单位] 之内

```js
item.value = {
    dateType: '1',
    afterTime: 7,           // 数字(整数)
    measurement: 'd'        // 单位:'d' = 天 / 'w' = 周 / 'month' = 月 / 'y' = 年
}
```

**常见组合**:
- 近 7 天:`{ dateType: '1', afterTime: 7, measurement: 'd' }`
- 近 1 个月:`{ dateType: '1', afterTime: 1, measurement: 'month' }`
- 近 1 年:`{ dateType: '1', afterTime: 1, measurement: 'y' }`

#### 模式 3:超过 N [单位] 之前

```js
item.value = {
    dateType: '2',
    beforeTime: 7,          // 数字(整数)
    measurement: 'd'        // 单位同上
}
```

**常见组合**:
- 超过 7 天前:`{ dateType: '2', beforeTime: 7, measurement: 'd' }`
- 超过 1 年前:`{ dateType: '2', beforeTime: 1, measurement: 'y' }`

#### 清空时间搜索项

```js
item.value = ''  // 或 null
```

⚠️ **关键事实**:
- `dateType` 是**字符串** `'0'`/`'1'`/`'2'`,**不是数字**
- `startTime` / `endTime` 格式是 `yyyy-MM-dd` 字符串(从 Date.vue 第 18 行 `value-format="yyyy-MM-dd"`)
- `measurement` 注意是 `'month'` 而不是 `'m'`(从 Date.vue 第 103 行)
- 设错格式组件不会报错,但 UI 不显示 / 后端过滤失效

---

### 3.2 各类型完整对照表(type → 组件 → value)

> **数据源**:`src/views/common/modelDesigner/fieldDic.js:95-138` `otherDic.searchType`
> **注册位置**:`src/components/frame/Common/MSearch/index.vue:60-82`
> **关键查找逻辑**:`MSearch/index.vue:147`
> ```js
> o.componentName = otherDic.searchType.find(i => parseInt(i.id) === parseInt(o.type))?.componentName || 'search-text'
> ```

| 搜索项类型 | type / selectType | Component name | value 格式 | value 示例 |
|---|---|---|---|---|
| **下拉多选** | `0` | `search-multiple-select` | `String`,`id;id;id`(默认 `;` 分隔) | `'1;2;3'` |
| **模糊搜索** | `1` | `search-text` | `String` | `'abc'` |
| **时间选择器** | `5` | `search-date` | 见 §3.1 三模式 | `{dateType:'0', startTime:'2025-01-01', endTime:'2025-12-31'}` |
| **数字区间** | `6` | `search-num-range` | `{startNum, endNum}`(**支持单边**) | `{startNum: 10, endNum: 100}` |
| **下拉单选** | `9` | `search-single-select` | `String`(选项 `id`,不是 `text`) | `'option-id-1'` |
| **年选择器** | `11` | `search-year` | `'yyyy'` | `'2026'` |
| **年月选择器** | `12` | `search-year-month` | `'yyyy-MM'` | `'2026-07'` |
| **复选框** | `15` | `search-checkbox` | `Boolean`(`true` / `false`,**非字符串**) | `true` |
| **清空(通用)** | — | — | `null` 或 `''` | `item.value = null` |

> ⚠️ `type` 比较用 `parseInt(...)`,**字符串 `'5'` 和数字 `5` 都匹配**——看到哪种不用纠结。
> ⚠️ 找不到匹配 `type` 时 **default 是 `search-text`(模糊搜索)**;老旧接口偶发返未知 type 不会崩,只是 UI 可能不是预期。
> 旧路径引用:`selectType` 字典见 [module-list-search §4.3](../frontend-module-list/sub/search/SKILL.md#43-selecttype-字典常用)。

### 3.3 拿到一段 searchFieldList 怎么读 type / 选组件

后端 `listModule.do` 返回的 `searchCondition` 数组(框架内最终叫 `searchFieldList` / `dataList`)每项长这样:

```js
[
    {
        id: 'createTime',       // 字段 id(代码用 .find(i => i.id === 'createTime') 定位)
        name: '创建时间',        // UI 显示的 label
        type: '5',              // ← selectType,决定渲染哪个组件(查 §3.2 表)
        value: {                // 当前 UI 值,格式见 §3.2
            dateType: '0', startTime: '2025-07-02', endTime: '2026-07-02'
        },
        defaultValue: null,     // 「重置」按钮回退值
        isMulti: false,         // true → 进右上「更多」下拉,不在主搜索栏显示
        isSelect: true,         // 当前是否在搜索栏可见;false 时被 dataList 过滤掉
        sortIndex: 0,           // 搜索项排序权重
        option: [...],          // 仅 type=0/9,下拉选项 [{id, text}]
        optionUrl: '/dict/list' // 仅 type=0/9,下拉数据接口(动态字典)
    }
    // ...
]
```

#### 5 秒判定 type → 组件(控制台调试小工具)

```js
import { otherDic } from '@/views/common/modelDesigner/fieldDic'
console.log(
    this.searchFieldList.map(i => ({
        id: i.id,
        type: i.type,
        组件: otherDic.searchType
            .find(d => parseInt(d.id) === parseInt(i.type))
            ?.componentName || 'search-text',
        value: i.value
    }))
)
// → [{id, type, 组件, value}] 一目了然
```

#### 已知边界情况

| 现象 | 原因 | 处理 |
|---|---|---|
| `type` 字段是字符串或数字交替出现 | 后端字段命名不统一 / 老接口 | `parseInt` 比较,无需处理 |
| 下拉只有 `id` 没 `text` 显示 | 后端 `option` 数组为空 / 没返 `optionUrl` | Network 看 listModule.do 响应,确认 `searchCondition[i].option` 是否有数据 |
| 某个搜索项完全不显示 | `isSelect: false` 或 `isHide: true` 被 dataList 过滤 | 看返回的 item 字段、查 `afterModuleJSON` 是否有过滤逻辑 |
| 在「更多」弹层里 | `isMulti: true` 时进 `extendList`(`MSearch/index.vue:39-55`) | 右上角「更多」按钮点击即可看到 |
| 改了 type 字段但 UI 没切组件 | type 是只读字段,改 type 无效 | 改后端 model designer 配置 |

#### 反向查找(知道组件 → 反推 type)

有时你从 stack trace 看到 `search-multiple-select` 报错,想反查它对应什么 type:

```js
import { otherDic } from '@/views/common/modelDesigner/fieldDic'
otherDic.searchType.find(d => d.componentName === 'search-multiple-select')
// → { id: '0', text: '下拉多选框', componentName: 'search-multiple-select', value: '{"value":null,...}' }
```

> 留意:返回的对象里有个 `value` 字段,是该 type 在后端模型设计器里的**默认 value 模板**(包含 `selectType`、`isExtended` 等默认值)。调试后端默认值时这条很有用——比如想知道"后端给 type=5 时间搜索项返的默认 value 长什么样",看这里就行。

---

## 4. 触发时机(代码写在哪)

| 场景 | 写在哪 | this 指向 | 能否用 `this.searchFieldList` |
|------|--------|-----------|-------------------------------|
| **按钮 click 触发**(最常见) | `searchBtns[].click` | moduleList | ✅ |
| **改了 X 自动给 Y 赋值** | `searchConditionChange` | moduleList | ✅(也可用参数) |
| **打开页面就有默认值** | `afterModuleJSON` 改 `defaultValue` | moduleListCode | ❌(改原始 config) |
| **页面 mount 后赋值** | 用 `searchConditionChange` + 标志位(框架**没有** mounted 钩子) | moduleList | ✅ |
| **不走 UI**(用户看不到值,只看到结果) | `paramsBeforeRequest` | mList | ❌(走后端参数) |

**重要**:`this.searchFieldList` 只在 **moduleList 实例**上(`searchBtns.click` / `searchConditionChange`)可访问。

---

## 5. 实战代码

### 场景 1:按钮 click 触发设置"近一年更新时间"(用户原问题,模式 2)

> "我希望能够**更新时间**搜索条件"

```js
searchBtns: [{
    id: 'updateLastYear',
    name: '近一年更新',
    icon: 'time',
    type: 'primary',
    click: function () {
        let updateTimeItem = this.searchFieldList.find(i => i.id === 'updateTime')
        if (!updateTimeItem) {
            this.$message.warning('模型未配置更新时间搜索项')
            return
        }
        // 模式 2:近 1 年(dateType: '1' = 过去 N [单位] 之内)
        updateTimeItem.value = {
            dateType: '1',
            afterTime: 1,
            measurement: 'y'
        }
        this.search()
    }
}]
```

### 场景 2:按钮 click 触发设置具体时间段(模式 1)

```js
click: function () {
    let createTimeItem = this.searchFieldList.find(i => i.id === 'createTime')
    if (!createTimeItem) return
    // 模式 1:时间段
    createTimeItem.value = {
        dateType: '0',
        startTime: '2025-01-01',
        endTime: '2025-12-31'
    }
    this.search()
}
```

### 场景 3:按钮 click 触发设置"超过 30 天前"(模式 3)

```js
click: function () {
    let createTimeItem = this.searchFieldList.find(i => i.id === 'createTime')
    if (!createTimeItem) return
    // 模式 3:超过 N [单位] 之前
    createTimeItem.value = {
        dateType: '2',
        beforeTime: 30,
        measurement: 'd'
    }
    this.search()
}
```

### 场景 4:打开页面就有默认值

**方式 A(标准)** — 后端模型设计器配 `defaultValue`,前端无代码。

**方式 B(前端改)** — `afterModuleJSON` 改 searchCondition 的 defaultValue:

```js
afterModuleJSON: function (module) {
    // 给 status 设默认选中"启用"
    let statusItem = module.searchCondition?.find(i => i.id === 'status')
    if (statusItem) {
        statusItem.defaultValue = '1'
    }
    // 给 createTime 设默认"近 1 年"
    let createTimeItem = module.searchCondition?.find(i => i.id === 'createTime')
    if (createTimeItem) {
        createTimeItem.defaultValue = {
            dateType: '1', afterTime: 1, measurement: 'y'
        }
    }
    return module
}
```

⚠️ **`defaultValue` 字段名因项目而异** — 改完不生效按下面 3 步排查:

1. **Network** 面板 → 找 `listModule.do`(或类似 listModule 接口)
2. 打开请求的 **Response** → 找到 `searchCondition` 数组 → 找一个真实搜索项的字段树
3. 字段名可能是以下之一(按本框架实测常见优先级):
   - `DefaultValValue`(框架内部字段,最常见)
   - `defaultValue`(驼峰)
   - `default_value`(下划线)
   - `value`(与运行时 value 字段同名,**不推荐用这个**,容易混淆)
   - 其他(以你项目实际为准)

**调试技巧**:在 `afterModuleJSON` 第一行加 `console.log('第一个搜索项:', module.searchCondition?.[0])`,看实际返回结构长什么样,字段名一清二楚。

### 场景 5:联动设置(改了 X 自动给 Y 赋值)

```js
searchConditionChange: function (fieldName, searchFieldList) {
    // 选了"部门"后,清空"员工"(原员工可能不属于新部门)
    if (fieldName === 'deptId') {
        let empItem = searchFieldList.find(i => i.id === 'userId')
        if (empItem) empItem.value = null
    }
}
```

### 场景 6:重置 / 清空某个搜索项

```js
// 清空单个
let item = this.searchFieldList.find(i => i.id === 'keyword')
if (item) item.value = null
this.search()

// 清空所有搜索项(框架自带)
this.searchReset()
```

⚠️ `searchReset()` 只会清空搜索项 UI,**不会**重置模块作用域变量(如 `_filterEnabled`)。

### 场景 7:批量预填(打开页面给多个搜索项设值)

用 `afterModuleJSON.push`(备用方案)或 后端模型设计器配置。详见 [module-list-search §4.2](../frontend-module-list/sub/search/SKILL.md)。

### 场景 8:按钮 click 触发设置"距今一年的具体起止日期"(模式 1 实战)

> 业务原话:"点击按钮,把搜索条件中的创建时间调整为距离今天一年的范围进行搜索,要求搜索框 UI 也要同步更新"
>
> 与场景 1(模式 2)对比:模式 1 显示具体起止日期(如 `2025-07-02 至 2026-07-02`),模式 2 显示自然语义(如 `在过去的 1 年之内`)。

```js
searchBtns: [{
    id: 'lastYear',
    name: '近一年出售',  // 按钮文案按业务调整
    icon: 'time',
    type: 'primary',
    click: function () {
        // 1. 定位
        let item = this.searchFieldList.find(i => i.id === 'createTime')
        if (!item) {
            this.$message.warning('未找到「创建时间」搜索项,请确认后端 searchCondition 已配')
            return
        }
        // 2. 算日期(今天 + 一年前的今天),yyyy-MM-dd 字符串
        let now = new Date()
        let start = new Date(now)
        start.setFullYear(start.getFullYear() - 1)
        let pad = n => String(n).padStart(2, '0')
        let fmt = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
        // 3. 赋值(模式 1 = 时间段,注意 dateType 是字符串 '0',不是数字)
        item.value = {
            dateType: '0',
            startTime: fmt(start),
            endTime: fmt(now)
        }
        // 4. 触发搜索(框架不会自动搜)
        this.search()
        this.$message.success(`已设置「创建时间」:${fmt(start)} ~ ${fmt(now)}`)
    }
}]
```

**为什么用模式 1 而不是模式 2?**

按 §3.1 决策树——业务方要求"创建时间调整为距离今天一年的**范围**",UI 期望显示具体起止日期(类似"近一年出售"这种业务语义),所以走模式 1;若只想显示"近 1 年"模糊语义,改用模式 2 的 `{dateType: '1', afterTime: 1, measurement: 'y'}`(见场景 1)。

**易错点检查**(对照 §2 横幅 3 条):
- ✅ `dateType: '0'` 是字符串,与模式 1 radio 匹配
- ✅ 直接 `this.searchFieldList.find()` 走引用,无深拷贝
- ✅ `this.search()` 触发请求

**依赖**:后端 `searchCondition` 必须已配 `createTime`(selectType=5)。如果不配,`item` 为 undefined,会走到 `this.$message.warning` 分支,需找后端在模型设计器里勾选。

---

## 6. 关键事实

### 6.1 `this` 指向总表(决定你能用什么 API)

| 自定义 key | `this` 指向 | `searchFieldList` 可用? | 备注 |
|---|---|---|---|
| `searchBtns[].click` | moduleList | ✅ | **按钮触发最常用入口** |
| `searchConditionChange(fieldName, searchFieldList)` | moduleList | ✅(也可用参数) | 联动专用 |
| `afterModuleJSON` | moduleListCode | ❌ | 只能改原始 config(走 defaultValue) |
| `paramsBeforeRequest` | mList | ❌ | 走后端参数,不走 UI |
| `beforeRowBtnRender` | mList | ❌ | 行按钮过滤 |
| `buttons / afterListJSON / afterListRender / selectionChange / dblClick` 等 | 见 [frontend-module-list](../frontend-module-list/SKILL.md) 总览 | — | — |

> **一句话原则**:想改 UI 搜索项就只能在 `searchBtns.click` / `searchConditionChange` 里写;只想走后端过滤走 `paramsBeforeRequest`(详见下方 §6.5 决策树)。

### 6.2 `searchFieldList` 的特性

| 项 | 说明 |
|---|---|
| 是什么 | **Vue 响应式数组**(moduleList 实例的 data 属性) |
| 引用关系 | 搜索栏 UI 直接读这个数组,改 `item` 即触发 UI 重渲染 |
| 改 `item.value` 后 | UI 自动同步(响应式);**但不会自动 `this.search()`** |
| 改完是否自动搜 | **否**,必须手动 `this.search()` |
| 能深拷贝吗 | **不能**:`JSON.parse(JSON.stringify(searchFieldList))` 会丢响应式,后续改不生效;`Object.freeze()` 会阻止后续改值 |
| 能用 `[...searchFieldList]` 吗 | **不推荐**:浅拷贝是新数组,改新数组不影响原 UI,得 `searchFieldList[i].value = ...` |
| `searchConditionChange` 参数 vs `this.searchFieldList` | **同一引用**,二选一即可 |

### 6.3 `searchConditionChange` 签名(最易写错)

```js
searchConditionChange: function (fieldName, searchFieldList) {
    // fieldName       : String   当前变更的字段 id(如 'createTime' / 'status' / 'deptId')
    // searchFieldList : Array    整个搜索项数组,与 this.searchFieldList 同引用
    // this            : moduleList 实例(可选,主要用于 this.search() / this.$message)
    //
    // ❌ 错误写法 1:把 this 当参数
    //   function (this, fieldName, searchFieldList) { ... }
    // ❌ 错误写法 2:用 array index 找
    //   searchFieldList[0].value = ...   // index 不固定,可能改错字段
    // ❌ 错误写法 3:在联动里忘了 this.search()
    //   只改 item.value,列表没刷新(用户感受不到)
    //
    // ✅ 推荐:用参数 searchFieldList + find;this 只用于工具方法
}
```

### 6.4 各搜索项类型值格式速查

| 项 | 说明 |
|---|---|
| Date `dateType` 是字符串 | `'0'` / `'1'` / `'2'`(**字符串**,不是数字;且要与 UI 当前 radio 匹配) |
| Date `dateType` 与 UI radio 对应 | `'0'`=时间段 / `'1'`=过去 N / `'2'`=超过 N。设 value 前看 UI 当前 radioIndex,二者严格匹配 |
| Date `measurement` 单位值 | `'d'`(天)/ `'w'`(周)/ `'month'`(**月,不是 `'m'`**)/ `'y'`(年) |
| Date 时间格式 | `yyyy-MM-dd` 字符串(**不是 Date 对象**;由 Date.vue 第 18 行 `value-format` 决定) |
| 数字区间 value | `{ startNum, endNum }` 对象(**支持单边**;两边都为 null 才算空) |
| 下拉多选 value | `id` 拼接字符串,默认 `;` 分隔(见 `MultipleSelect.vue` `divisionMark`);数组需 `value.join(';')` |
| 下拉单选 value | 选项 `id` 字符串(不是 `text`);Network 看 `selectorData` 数组取 id |
| 复选框 value | `Boolean`(`true` / `false`,不是字符串) |
| 框架有没有 mounted 钩子 | **没有**;"打开页面就设值"用 `afterModuleJSON.defaultValue`(场景 4)或 `searchConditionChange` + 标志位 |
| `searchReset()` 重置模块变量吗 | **不会**(`_filterEnabled` 等模块作用域变量需手动重置) |
| 设错格式组件会报错吗 | **不会**,UI 不显示或后端过滤失效,bug 难发现(走 §7 排查) |

### 6.5 选 `searchFieldList` 还是 `paramsBeforeRequest`?(决策树)

很多新人会问:**这个需求该改 UI 搜索项,还是走后端参数?** 下面是反向选择树。

```
我需要给搜索项 X 赋值,问自己 3 个问题:
│
├─ Q1:后端 searchCondition 里配了 X 吗?
│   ├─ 是 → 走 A (searchFieldList)
│   └─ 否 → 走 B (paramsBeforeRequest)
│       ⚠️ 但强烈建议先找后端把 X 配上,再走 A(更通用,无需前端兜底)
│
├─ Q2:用户期望在搜索框 UI 看到这个值吗?
│   ├─ 是 → 走 A (searchFieldList)
│   └─ 否(纯后台过滤) → 走 B (paramsBeforeRequest)
│
└─ Q3:后端期望的参数格式跟 searchFieldList 默认一致吗?
    ├─ 是(默认 yyyy-MM-dd) → 走 A
    └─ 否(后端要 yyyy-MM-dd HH:mm:ss / 时间戳 / 数组) → 走 B
        ⚠️ 但仍可走 A,见下方 "对齐参数格式" 技巧
```

**对比表**:

| 维度 | A:走 `searchFieldList` | B:走 `paramsBeforeRequest` |
|---|---|---|
| 适用入口 | `searchBtns.click` / `searchConditionChange` | 任意 customSetting key(因为 this 是 mList) |
| 用户能在搜索框看到值吗 | ✅(实时显示) | ❌(只在 Network 请求里) |
| 参与"重置"按钮吗 | ✅(`searchReset()` 一并清空) | ❌(用户点重置后,过滤仍生效) |
| 参与"回填"链路吗 | ✅(从 URL query / Vuex 恢复) | ❌(用户刷新即丢) |
| 后端参数格式可控性 | 默认 `yyyy-MM-dd`,要改格式得另想办法 | 完全可控,自己拼 |
| 依赖后端 searchCondition | 必须配 | 无要求 |
| 代码量 | 3 行核心 + 1 行 `this.search()` | 10+ 行日期计算 + 对象合并 |

**对齐参数格式**(A 方案但要不同格式):

有时即便走 A,后端仍要 `yyyy-MM-dd HH:mm:ss`。可在 click 里改 value 后,**追加一个 paramsBeforeRequest 兜底**,把 value 同步转成后端要的格式:

```js
// 在 searchBtns.click 里设置 value
item.value = { dateType: '0', startTime: '2025-01-01', endTime: '2025-12-31' }
this.search()

// 同时在 paramsBeforeRequest 里把 dateType='0' 的展开成后端要的 HH:mm:ss 格式
paramsBeforeRequest: function (params) {
    let ct = this.searchFieldList?.find(i => i.id === 'createTime')
    if (ct?.value?.dateType === '0') {
        params.createTimeStart = ct.value.startTime + ' 00:00:00'
        params.createTimeEnd = ct.value.endTime + ' 23:59:59'
    }
    return params
}
```

**反面案例(本 skill 改进点来源)**:

某列表曾用 B 方案(模块级 `_lastYearFilterEnabled` 标志 + `paramsBeforeRequest`),实现"近一年出售"按钮——结果**用户点了按钮,搜索框 UI 什么也没变,只看到数据变了**。改成 A 方案后,UI 和数据同步刷新,且无需额外的"标志位同步"机制。

---

## 7. 常见问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 改了 Date 的 value 但 UI 没切换模式 | value 的 `dateType` 与当前 radioIndex 不匹配 | value 必须带 `dateType: '0'`/`'1'`/`'2'`,与期望模式对应 |
| 设了"近一年"但 UI 显示"全部" | 用了模式 1 的 `{startTime, endTime}` 但想要"近一年" | 改成模式 2:`{ dateType: '1', afterTime: 1, measurement: 'y' }` |
| 改了值但 UI 没变化 | 直接改了 searchFieldList 的副本,不是引用 | 必须用 `this.searchFieldList.find(...)` 或 searchConditionChange 参数,**别深拷贝** |
| 改了值但列表没刷新 | 忘了 `this.search()` | 改完手动 `this.search()` |
| `afterModuleJSON` 里 `this.searchFieldList` undefined | this 是 moduleListCode,没有这属性 | 在 afterModuleJSON 里改的是原始 searchCondition 的 `defaultValue` |
| 设了时间范围但列表没过滤 | 后端没配时间搜索项 / value 不是对象 | Network 看请求 URL 确认参数;查后端 `selectType` 是不是 5 |
| 设了下拉默认值但 UI 没显示 | `value` 不是选项 `id` | Network 看 selectorData / data 数组,用里面的 `id` 而不是 `text` |
| 下拉多选设值后只显示一个 | `value` 用了数组,实际是字符串拼接 | 用 `value.join(';')` 转成字符串(默认 `;` 分隔) |
| 数字区间只设了一边报错 | value 是 `{ startNum: null, endNum: 100 }` | **支持单边**,但 `startNum` 和 `endNum` 都是 null 才算空 |
| `measurement: 'm'` 不生效 | 错把 'm' 当月 | 是 `'month'`(从 Date.vue 第 103 行 `dateTypeList`) |
| `paramsBeforeRequest` 想改 UI 值,改不了 | 这 key 不走 UI | 走 `searchFieldList`(在 searchBtns.click / searchConditionChange 里) |
| `defaultValue` 不生效 | 字段名错了 | Network 看 `listModule.do` 返回的 searchCondition 数组,**确认字段名**(常见 `defaultValue` / `value` / `defVal`) |

---

## 8. 下一步去哪

- **搜索条件变化监听 / 联动**(改了 X 自动响应)→ [module-list-search §2](../frontend-module-list/sub/search/SKILL.md#2-searchconditionchange-⭐⭐⭐⭐搜索条件联动)
- **按角色显隐搜索项 / 改 selectType / 动态加搜索项** → [module-list-search §4](../frontend-module-list/sub/search/SKILL.md#4-单个搜索项按角色显隐aftermodulejson-改-searchcondition-⭐⭐⭐)
- **搜索栏按钮** → [module-list-buttons §5](../frontend-module-list/sub/buttons/SKILL.md#5-searchbtns搜索栏按钮)
- **整个 customSetting 总览** → [frontend-module-list](../frontend-module-list/SKILL.md)

---

## 9. 源码参考(高级,排查用)

| 组件 | 路径 | 关键方法 |
|------|------|---------|
| MSearch 主组件 | `src/components/frame/Common/MSearch/index.vue` | `compSearch` / `searchReset` |
| **Date**(3 模式) | `src/components/frame/Common/MSearch/components/Date.vue` | `updateValue`(第 268 行) / `clear`(第 245 行) |
| Year | `src/components/frame/Common/MSearch/components/Year.vue` | 直接传 `bd-date` |
| YearMonth | `src/components/frame/Common/MSearch/components/YearMonth.vue` | 直接传 `bd-date` |
| NumRange | `src/components/frame/Common/MSearch/components/NumRange.vue` | `numRange` 格式 `{ startNum, endNum }` |
| MultipleSelect | `src/components/frame/Common/MSearch/components/MultipleSelect.vue` | `divisionMark` 默认 `;` |
| SingleSelect | `src/components/frame/Common/MSearch/components/SingleSelect.vue` | 单选 `id` |
| Text | `src/components/frame/Common/MSearch/components/Text.vue` | 模糊匹配 |
| Checkbox | `src/components/frame/Common/MSearch/components/Checkbox.vue` | 布尔 |
| searchType 字典 | `src/views/common/modelDesigner/fieldDic.js:95-138` | `otherDic.searchType` |