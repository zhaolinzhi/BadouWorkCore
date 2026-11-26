---
name: frontend-module-list-table-look
description: 八斗 Module 列表 customSetting — 表格外观完整指南。当用户说"冻结列"、"合计行"、"行列合并"、"改表头"、"自定义表头渲染"、"列表顶部插槽"、"按钮区插槽"、"搜索区插槽"、"分页控制"时触发。覆盖 freezeColumnIndex / freezeColumnLastIndex / showSummary / spanMerge / renderFieldHeader / columnFormat / isUsePagination / isShowPagination / paginationInfo / 4 个插槽(listTopSlot/btnFixedRightSlot/btnNextLineSlot/searchFixedRightSlot) 14 个 key。
---

# Module 列表 — 表格外观

> 表格"长什么样 + 周边插槽"的 14 个 key。**先看 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/list.js` 的 `export default` 对象里。

**进入前必读**:mdCode + list/edit + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 14 个 key

| 类别 | key | 用途 | 频次 |
|------|------|------|------|
| 冻结列 | `freezeColumnIndex` | 前置冻结列 | ⭐ |
| 冻结列 | `freezeColumnLastIndex` | 后置冻结列 | ⭐ |
| 合计行 | `showSummary` | 表尾合计 | ⭐⭐ |
| 行列合并 | `spanMerge` | 合并相同值的行 | ⭐ |
| 表头 | `renderFieldHeader` | 自定义表头单元格 | ⭐⭐ |
| 表头 | `columnFormat` | 改表头字段数组 | ⭐ |
| 分页 | `isUsePagination` | 是否启用分页 | ⭐ |
| 分页 | `isShowPagination` | 是否显示分页 UI | ⭐ |
| 分页 | `paginationInfo` | 自定义分页参数 | ⭐ |
| 插槽 | `listTopSlot` | 搜索框下方/列表顶部 | ⭐ |
| 插槽 | `btnFixedRightSlot` | 按钮区右侧固定位 | ⭐ |
| 插槽 | `btnNextLineSlot` | 按钮区下一行 | ⭐ |
| 插槽 | `searchFixedRightSlot` | 搜索区右侧固定位 | ⭐ |

---

## 2. 冻结列

### 2.1 基础用法

```js
// 前置冻结到第 2 列(序号列默认冻结,不计入索引)
freezeColumnIndex: 1,        // 序号列 + 数据列 [0] = 共 2 列固定

// 后置冻结从倒数第 3 列开始
freezeColumnLastIndex: 3,    // 数据列 [len-3] ~ [len-1] 固定(常见用法:操作列固定)
```

**典型场景**:左侧"序号 + 第一列"冻结 + 右侧"操作列"冻结 → 横向滚动时关键列始终可见。

```js
export default {
    freezeColumnIndex: 1,
    freezeColumnLastIndex: 3
}
```

> ⚠️ **`freezeColumnIndex` 默认让"序号列"也冻结**,且**不计入索引**(序号列固定 + 数据列 [0] 固定 = 2 列)。

### 2.2 序号列默认冻结的细节

来源:[`MList/index.vue:55-66`](../../../../src/components/frame/Common/MList/index.vue#L55) `:fixed="_indexColumnFixed"`。

| 现象 | 原因 | 怎么关 |
|------|------|--------|
| 设了 `freezeColumnIndex: 1` 后,序号列也被固定 | `_indexColumnFixed` computed 判断 `freezeColumnIndex > 0` 时自动给序号列 `fixed='left'` | MList 框架**没有暴露关闭开关**。要去掉序号列冻结,**只能**:① 改 `hasIndex: false`(不显示序号列);② 把序号列移到右侧:`indexAttrs.fixed = 'right'` |

### 2.3 与 `columnFormat` 的交互 ⚠️ 必读

[`MList/index.vue:465-491`](../../../../src/components/frame/Common/MList/index.vue#L465-L491) `_fieldList` getter 的执行顺序:

```js
1. freezeColumnIndex      → fieldList[i].fixed = 'left'     // 先设 fixed
2. freezeColumnLastIndex  → fieldList[len-i-1].fixed = 'right'
3. columnFormat(fieldList)                                  // 再调 columnFormat
```

**注意**:`columnFormat` 里如果**新建对象**而不 `...f`,会把 `fixed` 属性丢了,冻结列失效。

```js
// ❌ 错误:columnFormat 里新建对象,丢了 fixed
columnFormat: function (fieldList) {
    return fieldList.map(f => ({
        name: f.name,           // 漏了 ...f,fixed / sort / formatter 全没了
        display: f.display,
        width: f.width
    }))
}

// ✅ 正确:...f 透传,fixed 才不会被覆盖
columnFormat: function (fieldList) {
    return fieldList.map(f => ({
        ...f,                   // 关键:透传 fixed / width / sort / formatter 等所有原属性
        display: f.display + ' (新)'
    }))
}
```

详见 [§6 原位合并示例](#61-原位合并手动拼装)里 `...f` 的用法。

### 2.4 与合并表头 / `spanMerge` 的兼容性

| 配合使用 | 表现 | 建议 |
|---------|------|------|
| `freezeColumnIndex` + `columnFormat`(合并表头) | 合并表头跨冻结边界时列宽算不准、列错位 | 合并表头**不跨冻结边界**(整组都在最左或最右);合并表头前先确认冻结边界位置 |
| `freezeColumnIndex` + `spanMerge`(行合并) | rowspan/colspan 在冻结列上可能失效或错位 | 跨冻结边界的合并行先确认业务可接受;否则去掉行合并 |

**临时排查**:如果冻结列效果异常,先去掉 `columnFormat` / `spanMerge` 验证是否冲突;再分别加回定位。

---

## 3. `showSummary`(合计行)

**三种用法**:

### 3.1 布尔:全字段合计

```js
showSummary: true
```

### 3.2 字符串:指定字段合计(逗号分隔)

```js
showSummary: 'price,quantity'  // 只对价格和数量列求和
```

### 3.3 函数:完全自定义

**this 指向**:**mList 实例**(可用 `this.temp_data` 拿到当前页数据)

> 📌 具体文件见 §9.3 速查表。

```js
/**
 * @param {Array} columns 列字段数组
 * @param {Array} data 列表数据
 * @param {Object} baseProp { index, selection } 索引列和选择列的属性
 * @returns {Array} 每列的合计值
 */
showSummary: function (columns, data, baseProp) {
    // this 指向 mList 实例
    let _columns = ['intf', 'numberf']  // 需要合计的字段
    let _sums = []
    columns.forEach((column, index) => {
        if (column.property === baseProp.selection) {
            _sums[index] = ''  // 选择列留空
            return
        }
        if (column.property === baseProp.index) {
            _sums[index] = '合计'  // 序号列显示"合计"
            return
        }
        if (column.property && _columns.includes(column.property)) {
            const values = data.map(item => Number(item[column.property]))
            if (!values.every(value => isNaN(value))) {
                _sums[index] = values.reduce((prev, curr) => {
                    return !isNaN(Number(curr)) ? prev + curr : prev
                }, 0)
                return
            }
        }
        _sums[index] = ''
    })
    return _sums
}
```

> ⚠️ 函数形式必须 return 长度等于 columns 的数组。

---

## 4. `spanMerge`(行列合并)

**两种用法**:

### 4.1 简单对象:按字段值相同合并行

```js
spanMerge: {
    row: 'textf,numberf'  // 垂直方向按值合并,多个字段用逗号隔开
}
```

### 4.2 复杂函数:任意规则合并

**签名**:`spanMerge({ row, column, rowIndex, columnIndex })` → `{ rowspan, colspan }` / `[rowspan, colspan]`

**this 指向**:**mList 实例**(可用 `this.temp_data` 拿到当前页所有数据)

**推荐用框架工具**(`@/service/table` 的 `Get_Table_Span`):

```js
spanMerge: function ({ row, column, rowIndex, columnIndex }) {
    // this 指向 mList 实例
    // import { Get_Table_Span } from '@/service/table'
    return Get_Table_Span(
        { row, column, rowIndex, columnIndex },
        this.temp_data,  // 当前页所有数据
        {
            row: 'customerName,contractTypeDesc',  // 按值相同合并
            spanMergeKey: 'customerName'  // 加上后,只有 key 值相同时才合并
        }
    )
}
```

**自己写(复杂场景)**:
```js
spanMerge: function ({ row, column, rowIndex, columnIndex }) {
    // 例:每隔两行合并第一列
    if (rowIndex % 2 === 0 && columnIndex === 0) {
        return { rowspan: 2, colspan: 1 }
    }
    if (rowIndex % 2 === 1 && columnIndex === 0) {
        return { rowspan: 0, colspan: 0 }  // 被合并的格子返回 0
    }
    return { rowspan: 1, colspan: 1 }
}
```

> `spanMergeKey` 是 2025-06-07 新增,加上后:只有 `spanMergeKey` 字段值相同时,其它字段才会合并。

---

## 5. `renderFieldHeader`(自定义表头单元格)

**结构**:同 `renderField`,作用于**表头**。

**this 指向**:**mList 实例**(与 `renderField` 一致,可在 formatter/render 内访问 `this.BASEURL` / `this.mdCode` / `this.pushPage`)

```js
renderFieldHeader: {
    intf: {
        // 方式一:formatter(只支持基础 HTML 字符串,不能写组件)
        formatter: function (cellValue, fieldObj, scope) {
            // this 指向 mList 实例
            return `
                <span class="primaryC fontS">+1天上班</span><br/>
                <span class="bold dangerC">${cellValue}</span>
            `
        },
        // 方式二:render(可用任意组件)
        render: function (h, context, cellValue, fieldObj, scope) {
            // this 指向 mList 实例
            return (
                <span>
                    <bd-icon name="add" type="success"></bd-icon>
                    {cellValue}
                </span>
            )
        }
    }
}
```

**实战:加必填标识**

```js
renderFieldHeader: {
    userName: {
        render: function (h, context) {
            return (
                <span>
                    用户名 <span style="color: red">*</span>
                </span>
            )
        }
    }
}
```

> 💡 与 `renderField` 的区别:`renderFieldHeader` 作用在**表头单元格**,JSX 同样要遵守 5 条铁律。

---

## 6. `columnFormat`(改整个表头字段数组)

**签名**:`columnFormat(fieldList)` → **return 新数组**

**this 指向**:**moduleList 实例**(由 `getColumnList` / 表格组件初始化阶段调用,可用 `this.$store` / `this.mdCode` / `this.BASEURL`)

**工具方法**:`Merge_TableColumn` from `@/utils/table` — 用于**合并表头**(⚠️ 见 §6.1,有重要限制)。

```js
import { Merge_TableColumn } from '@/utils/table'

export default {
    columnFormat: function (fieldList) {
        // this 指向 moduleList 实例
        // 1. 直接改 display/width
        return fieldList.map(f => {
            if (f.name === 'price') {
                f.display = '价格(元)'
            }
            return f
        })
    }
}
```

### ⚠️ 动手前先确认字段名(必读)

用户要做"多列合并表头"时,**必须先确认每个子列在原 `fieldList` 里的真实 `name`**,不能靠猜:

1. **如果用户给了字段名**(如"创建人名称/创建时间/更新时间/更新人名称")——不能直接用,要去 listModule.do 接口返回值里找:
   - 让用户提供 `listModule.do` 接口返回的 `moduleDisplay` 数组
   - 或者提示用户打开 Network 看 `listModule.do` 的 Response
   - 找到这 4 个中文 display 对应的真实 `name`(可能是 `creatorName` / `createTime` / `updateTime` / `updatorName`,也可能是 `createBy` / `modifiedTime` 等)
2. **如果用户没给字段名**——先**猜测**(按最常见的命名习惯),然后**用 AskUserQuestion 反问一次确认**:
   - "我打算合并的 4 个字段是 `creatorName / createTime / updateTime / updatorName`,这跟后端 moduleDisplay 里的 name 一致吗?不一致的话告诉我实际 name"
3. **如果用户只给了中文 display**——也是猜 name + 反问确认

> 💡 **为什么不能跳确认这一步**:name 错了 → 子列就拿不到原 fieldList 的属性(width / display / sort / isSort 等)→ 列展示异常或完全没数据。**猜 + 反问**比"写完再修"省事。

### ⚠️ 子列顺序必须按原 `fieldList` 的实际顺序

合并表头时,4 个子列在 `format.children` 里的**书写顺序**决定了表格里看到的子列顺序。

**注意**:`Merge_TableColumn` 是 `format.map(...)`,**只按 format 数组顺序返回**,不会按原 `fieldList` 顺序自动排。

**约定**:`format.children` 里子列的顺序**必须跟原 `fieldList` 里这 4 个字段的实际出现顺序一致**。

| 反例 ❌ | 正例 ✅ |
|---|---|
| 代码里写 `[creatorName, createTime, ...]`,但原 fieldList 顺序是 `createTime, creatorName, ...` | 代码里写 `[createTime, creatorName, ...]`,跟原 fieldList 顺序一致 |

> **怎么拿原 fieldList 顺序**:在 `columnFormat` 第一行加 `console.log(fieldList.map(f => f.name))`,浏览器 console 看一眼(只调试用,提交前删掉)。

---

### 6.1 原位合并(手动拼装)⭐⭐⭐

`Merge_TableColumn` 有一个关键限制:**只按 format 数组顺序返回,不能把合并表头"插到中间"**。

| 需求 | `Merge_TableColumn` 能不能做 |
|---|---|
| 把"操作信息"放在表头最前 | ✅ 能 |
| **把"操作信息"插在中间**(前面有 `name`/`description`,后面有 `statusDesc`)| ❌ **不能**——会把原列表其他列全吞了,只留 format 里描述的列 |

**原位合并(把合并表头插在中间)必须手动拼装**:

```js
columnFormat: function (fieldList) {
    // 1. 列出要合并的字段,顺序跟原 fieldList 实际顺序一致
    //    字段名必须先按 §6 流程确认
    let targetNames = ['createTime', 'creatorName', 'updateTime', 'updatorName']
    let groupLabel = '操作信息'

    // 2. 按原 fieldList 顺序遍历,把 4 个目标列替换为一组合并表头
    let result = []
    let inGroup = false  // 标记是否正在吃 4 个目标列

    fieldList.forEach(f => {
        if (targetNames.indexOf(f.name) > -1) {
            if (!inGroup) {
                // 第一个目标列:新建 group
                result.push({ label: groupLabel, children: [] })
                inGroup = true
            }
            // 推入 group.children:展开原 f 的所有属性,只补 label
            //   label 是合并表头要求的字段(框架内部统一读 label),其他用 display 当 fallback
            //   用 ...f 一次性透传 width / sort / formatter / render 等所有原属性
            //   后续原 fieldList 加新字段时不用回来改这里
            result[result.length - 1].children.push({
                ...f,
                label: f.display
            })
        } else {
            inGroup = false
            result.push(f)  // 普通列原样 push
        }
    })

    return result
}
```

**效果**:

```
原 fieldList: [name, description, createTime, creatorName, updateTime, updatorName, statusDesc]
                        ↓
拼装后:        [name, description, 操作信息(4 子列), statusDesc]
```

> 💡 **关键技巧**:`inGroup` 标记防止把不连续的 4 个列建多个 group(虽然一般用不到,但如果原 fieldList 里这 4 列中间夹了其他列,也能正确断开/合并)。

> ⚠️ **适用场景**:合并表头要"插在中间"时。如果合并表头放在最前/最后,**优先用 `Merge_TableColumn`**,代码更短。

---

## 7. 分页控制(3 个 key)

### 7.1 `isUsePagination` 是否启用分页

```js
isUsePagination: false  // 关闭分页(一次加载所有数据,isShowPagination 也自动隐藏)
```

### 7.2 `isShowPagination` 是否显示分页 UI

```js
isShowPagination: false  // 关闭分页展示(不关分页功能,数据仍是分页的)
```

**区别**:
- `isUsePagination: false` → 关闭分页 + 隐藏 UI,**一次性返回所有数据**
- `isShowPagination: false` → 只隐藏 UI,**分页功能还在**,数据仍是分页的

### 7.3 `paginationInfo` 自定义分页参数

```js
paginationInfo: {
    sizes: [10, 20, 50],   // 每页可选
    size: 10                // 默认每页条数(没配 size 但有 sizes 时,默认取 sizes 第一项)
}
```

---

## 8. 4 个插槽(返回 JSX,this 是 moduleList)

**共同签名**:`slot 函数() → Promise<JSX>`

**两种方式**:
```js
// 方式 1:同步
listTopSlot () {
    return Promise.resolve((h, context) => (
        <div class="operateC">列表顶部</div>
    ))
}

// 方式 2:异步(等接口完成再返回内容)
listTopSlot () {
    return new Promise((resolve) => {
        this.post('/api/xxx').then(res => {
            resolve((h, context) => (
                <div>{res.data.title}</div>
            ))
        })
    })
}
```

### 8.1 `btnFixedRightSlot`(按钮栏最右侧固定区域)

```js
btnFixedRightSlot () {
    return Promise.resolve((h, context) => (
        <div class="operateC w-per-100 textL">
            贴近按钮的右侧(铺满+左对齐)
        </div>
    ))
}
```

**刷新方法**:
```js
this.getBtnFixedRightSlot()  // 重新执行插槽函数
```

### 8.2 `btnNextLineSlot`(按钮栏下面一行)

```js
btnNextLineSlot () {
    return Promise.resolve((h, context) => (
        <div class="operateC padding">按钮区下方一行</div>
    ))
}
```

**刷新方法**:
```js
this.getBtnNextLineSlot()
```

### 8.3 `searchFixedRightSlot`(搜索栏最右侧固定区域)

```js
searchFixedRightSlot () {
    return Promise.resolve((h, context) => (
        <div class="operateC padding">搜索栏最右侧</div>
    ))
}
```

**刷新方法**:
```js
this.getSearchFixedRightSlot()
```

### 8.4 `listTopSlot`(搜索栏下方 / 列表顶部)

```js
listTopSlot () {
    return Promise.resolve((h, context) => (
        <div class="operateC">搜索框下方、表格上方</div>
    ))
}
```

**刷新方法**:
```js
this.getListTopSlot()
```

> 💡 **所有 4 个插槽都遵循**:
> - this 指向 moduleList
> - 返回 `Promise<JSX>`,同步用 `Promise.resolve`,异步用 `new Promise`
> - JSX 写法遵守 [renderField 5 条铁律](../render-field/SKILL.md#41-jsx-5-条铁律违反就报错)
> - 重新执行函数 = "刷新插槽"(`getXxxSlot()` 方法)
> - **插槽 JSX 里想加间距/颜色/字体/布局等样式,直接用全局类即可**——见 [frontend-module-global-styles](../../frontend-module-global-styles/SKILL.md)(`warningTag` / `margin` / `textL` / `primaryC` 等,无需自己写 style)

---

## 9. 关键事实

### 9.1 key 用途差异

| key | 用途差异 |
|------|---------|
| `columnFormat` | 改**整个表头数组**(`fieldList` 上的属性,如 display/width/sortable/嵌套) |
| `renderFieldHeader` | 改**单个表头单元格的渲染**(JSX/VNode) |
| `spanMerge.row` | 简单按字段值合并,`spanMergeKey` 进一步控制 |
| 4 个插槽 | 返回 `Promise<JSX>`,this 是 moduleList,可用 this.post 异步 |

### 9.2 this 指向 = 具体文件(本 skill 备注速查)

> 💡 完整的"简称 → 文件 → 组件 name → DevTools 验证"四维对照见 [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md) §1。
> 本节只列本 skill 独有的**关键备注**(新 skill 里没有的),方便快速翻阅。

| key | 类型 | this 指向 | 备注(本 skill 独有) |
|------|------|----------|----------|
| `showSummary` | Function | mList | 可用 `this.temp_data` 拿当前页数据 |
| `spanMerge` | Function | mList | 可用 `this.temp_data` 拿当前页数据 |
| `renderFieldHeader.*` | Function | mList | 与 `renderField` 一致 |
| `columnFormat` | Function | moduleList | 初始化阶段调用 |
| 4 个插槽 | Function | moduleList | 返回 `Promise<JSX>`,可用 `this.post` 异步 |

> 💡 想知道更上层的"组件层级关系"(3 层组件如何嵌套),见 [frontend-module-list §3](../../SKILL.md) 的全局速查表。

---

## 10. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| `showSummary` 函数形式不显示 | 没 return 数组 | 必须 return 长度等于 columns 的数组 |
| `spanMerge` 错位 | rowspan/colspan 返回值写反 | 主格返回 `{rowspan: 2, colspan: 1}`,被合并返回 `{rowspan: 0, colspan: 0}` |
| 冻结列没生效 | 后端 fieldList 顺序问题 / `columnFormat` 覆盖了 fixed | ① 确认 `freezeColumnIndex` 是 customSetting 直接属性(不是包在某个对象里);② `columnFormat` 用 `...f` 透传(见 §2.3) |
| 冻结列宽算不准 | width 没在 fieldList 设置 | 冻结列必须显式 width,否则 el-table 算不准 |
| 冻结列 + 合并表头错位 | 合并表头跨冻结边界 | 合并表头不跨冻结边界,整组放最左或最右(见 §2.4) |
| 冻结列 + `spanMerge` 错位 | 跨冻结边界的合并行 | 去掉行合并,或确认业务可接受错位 |
| 序号列也被冻结了 | `_indexColumnFixed` 默认行为 | 框架无关闭开关;改 `hasIndex: false` 或 `indexAttrs.fixed = 'right'`(见 §2.2) |
| 表头改了 display 但宽度没变 | `columnFormat` 没动 width | display 和 width 都要在 `columnFormat` 里改 |
| 插槽写了不显示 | 没 return Promise | 必须 `return Promise.resolve(JSX)` 或 `return new Promise(resolve => ...)` |
| 插槽内容跟原来一样 | 函数返回了固定值 | 重新执行函数 = "刷新插槽",调用对应的 `getXxxSlot()` |
| `paginationInfo.size` 不生效 | sizes 没配 | 有 sizes 时 size 不写默认取 sizes 第一项 |
| 合并表头列错位 | 没用 `Merge_TableColumn` | 用 `Merge_TableColumn(fieldList, format)` 工具 |

---

## 11. 下一步去哪

- **列渲染** → `module-list-render-field`
- **按钮** → `module-list-buttons`
- **搜索栏交互** → `module-list-search`
- **请求/数据流** → `module-list-data-flow`
- **导入导出** → `module-list-import-export`
- **选择 + 双击** → `module-list-selection-row`
- **回到总览** → `frontend-module-list`
- **表单布局(Edit 的 columnNum / beforeRender)** → [module-edit-layout](../../../frontend-module-edit/sub/layout/SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
