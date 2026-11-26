---
name: frontend-module-list-render-field
description: 八斗 Module 列表 customSetting — 列渲染(renderField)完整指南。当用户说"加状态徽章"、"列点击"、"JSX 渲染单元格"、"单元格点击事件"、"renderField" 时触发。覆盖 formatter/click/render 三种写法、JSX 5 条铁律、this 指向、可复制代码片段、createFun vs createListFun 区别。
---

# Module 列表 — 列渲染(renderField)

> `renderField` 是业务方**最常用**的 customSetting key,负责把表格里的字段从原始值渲染成彩色徽章/按钮组/可点击文本等。
> 完整内容、参数、实战示例在本 skill。**先看 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

---

## 0. 文件落点(进入本 skill 前必做)

`renderField` 写在 `public/moduleJs/{mdCode}/list.js` 的 `export default` 对象里(由后端模型设计器指向)。

**进入前必读**:
- mdCode + list/edit + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)
- 拿到路径后先 **Read** 现有文件,别直接覆盖

---

## 1. 三种写法概览

`renderField` 结构:`{ [字段名]: { formatter?, click?, render? } }`,**render 优先级最高**。

| 写法 | 适用场景 | 复杂度 |
|------|---------|--------|
| `formatter` | 纯文本/HTML 字符串(状态徽章/格式化日期) | ⭐ |
| `click` | 单元格点击跳转/弹窗 | ⭐⭐ |
| `render` | JSX 复杂组件(按钮组/带事件) | ⭐⭐⭐ |

### 1.1 ⚠️ 字段类型判断 → 是否用 `xxxDesc`(必读)

> **写 `renderField` 的第一步**:先看字段**是不是数据字典**——是 → 用 `xxxDesc`,不是 → 用原字段名。**别无脑加 `Desc`,会整列不渲染**。

#### 1.1.1 判断流程(写之前先看)

```
该字段是数据字典吗?
│
├─ 是(常用字典:status / isRead / isRecord / logLevel / state / type 等)
│   → renderField.xxx 写成 xxxDesc(去掉/加上 Desc)
│   → cellValue = 框架翻译后的中文
│   → 用 row.xxx 拿原值做逻辑判断
│
└─ 不是(普通字段:userName / phone / createTime / price 等)
    → renderField.xxx 保持原字段名(❌ 不要加 Desc,加了整列不渲染)
    → cellValue = 字段原值
```

#### 1.1.2 字典字段的标准写法

> **铁律**:字段类型是**数据字典**时,`renderField` 的 key 必须是 `xxxDesc`(`status` → `statusDesc`、`isRead` → `isReadDesc`),框架会**自动**用字典把 `row.xxxDesc` 翻译成中文(并在表格里默认展示)。直接配 `status` 时,`cellValue` 拿到的是中文翻译文本,不是原始数字。**普通字段不加 Desc**,否则整列不渲染。
>
> **来源**:`src/service/base-service.js:195-220` `getDescObj` —— 框架通过 `row[fieldName + 'Desc']` 拿翻译文本,`row[fieldName]` 拿原值做样式/逻辑判断。
>
> **实战**:`public/moduleJs/frame/notice/notice_user_list.js:117-120` 的 `isReadDesc`、`public/moduleJs/.../sys_interface_info_list.js:8-24` 的 `isRecordDesc` / `logLevelDesc`。

```js
// ✅ 字典字段:用 *Desc 配,row.xxx 拿原值,cellValue 拿中文
renderField: {
    statusDesc: {
        render (h, context, row, column, cellValue) {
            let status = Number(row.status)  // 原值,做逻辑
            let map = { 0: 'success', 1: 'info', 2: 'warning' }
            return (
                <el-tag type={map[status] || ''}>{cellValue}</el-tag>  // cellValue 是中文
            )
        }
    }
}
```

---

## 2. `formatter` — 纯文本格式化

**签名**:`formatter(row, column, cellValue, index, fieldObj)` → `String`

**this 指向**:**mList 实例**

### 2.1 基础用法(普通字段)

```js
renderField: {
    // 假设 userType 不是字典(就是数字),配原字段名 + cellValue 直接用
    userType: {
        formatter: function (row, column, cellValue, index, fieldObj) {
            const map = { 0: '禁用', 1: '启用' }
            return `<span class="status-tag ${cellValue === 1 ? 'success' : 'danger'}">${map[cellValue]}</span>`
        }
    }
}
```

### 2.2 字典字段的标准写法(用 `xxxDesc`)

```js
renderField: {
    // 字典字段必须配 xxxDesc,row.status 拿原值,cellValue 拿中文
    statusDesc: {
        formatter: function (row, column, cellValue, index, fieldObj) {
            const typeMap = { 0: 'success', 1: 'info', 2: 'warning' }
            return `<span class="status-tag ${typeMap[row.status] || ''}">${cellValue}</span>`
        }
    }
}
```

**实战**(摘自 `public/moduleJs/frame/notice/notice_user_list.js:117-120`):

```js
renderField: {
    isReadDesc: {
        formatter (row, column, cellValue, index, fieldObj) {
            let text = String(row.isRead) !== '1' ? '否' : '是'
            return `<span class="${String(row.isRead) !== '1' ? 'warningTag' : 'successTag' }">${text}</span>`
        }
    }
}
```

---

## 3. `click` — 单元格点击事件

**签名**:`click(row, column, cellValue, index, fieldObj)`

**this 指向**:**mList 实例**

```js
renderField: {
    userName: {
        formatter: row => row.userName,
        click: function (row, column, cellValue, index, fieldObj) {
            this.pushPage({
                path: `/module/view/view/user_info/${row.id}`,
                title: row.userName
            })
        }
    }
}
```

> **注意**:`this` 是 mList,不是 moduleListCode,所以 `this.$refs.moduleListCode` 是 undefined。
> 想访问 ref,要么通过 `createFun` 注入,要么在 `pushPage` 后用 `this.$nextTick` 等。

---

## 4. `render` — JSX 渲染(最灵活)

**签名**:`render(h, context, row, column, cellValue, index, fieldObj, scope)` → VNode

**this 指向**:**mList 实例**

### 4.1 JSX 5 条铁律(违反就报错)

1. **return html 必须用小括号 `()` 包裹 JSX 表达式,否则页面报错**(详见下方 [§4.1.1](#411-return-html-必须用小括号包裹-高频易错点))
2. 标签不能写成字符串(如不能 `'<span>'`,要写 `<span>`)
3. 必须有且仅有一个**根级标签**
4. 变量用单花括号 `{value}`(不是 vue 模板的 `{{}}`)
5. 事件格式 `on-事件类型={fn}`,阻止冒泡用 `nativeOn-click`

#### 4.1.1 return html 必须用小括号包裹 ⭐⭐⭐⭐(高频易错点)

**铁律**:`render` 函数如果 return 的是 JSX(HTML)结构,**必须**用小括号 `()` 包裹整个 JSX 表达式。

```js
// ❌ 错误:return 后直接换行写 JSX,会被 ASI(自动分号插入)当成 return undefined,页面报错
render: function (h, context, row, column, cellValue) {
    return
        <el-tag type="success">{cellValue}</el-tag>
}

// ✅ 正确:用小括号 () 包裹 JSX
render: function (h, context, row, column, cellValue) {
    return (
        <el-tag type="success">{cellValue}</el-tag>
    )
}
```

**为什么**:
- JS 在 `return` 后遇到换行会**自动插入分号**,导致 `return` 变成 `return undefined`,而 JSX 变成了**永远到不了的死代码**
- 用 `()` 把 JSX 表达式作为一个整体,告诉 JS 解析器"这一坨是一行"

**经验法则**:
- return 的是**字符串 / 数字 / null** → 不需要 `()`
- return 的是**JSX(HTML)** → **必须用 `()` 包裹**,无论 JSX 多简单(`return (<span>x</span>)` 不能省括号)
- 多个分支都需要 return JSX → 每个分支的 JSX 都要 `()` 包裹

**反例**(摘自实际报错代码):
```js
// ❌ 报错:每个分支都没用 () 包裹
render: function (h, context, row, column, cellValue) {
    if (!cellValue) {
        return <span>--</span>     // ❌ 不会报错(单标签,有时侥幸通过),但不规范
    }
    return
        <el-tag>{cellValue}</el-tag>  // ❌ 报错:return 空 + JSX 死代码
}
```

**正例**:
```js
// ✅ 正确:每个 JSX return 都用 () 包裹
render: function (h, context, row, column, cellValue) {
    if (!cellValue) {
        return (<span>--</span>)
    }
    return (
        <el-tag>{cellValue}</el-tag>
    )
}
```

### 4.2 简单按钮

**实战**(摘自 `public/moduleJs/frame/notice/notice_user_list.js:167-179`):

```js
renderField: {
    attach: {
        render: function (h, context, row, column, cellValue, index, fieldObj) {
            if (!cellValue) {
                return (<span>--</span>)
            }
            const _this = this
            const downLoadFn = () => {
                Download({ url: `${_this.BASEURL}/attach/action/attachsupport/downloadAttach?attachId=${cellValue}` })
            }
            return (
                <bd-button icon="" name="下载附件" type="success" on-click={downLoadFn}></bd-button>
            )
        }
    }
}
```

### 4.3 操作列(完整模板,**最常用**)

**实战**(摘自 `public/moduleJs/business/text/wjx_form_list.js:95-127`):

```js
renderField: {
    operate: {
        render: function (h, context, row, column, cellValue, index, fieldObj, scope) {
            return (
                <span>
                    {/* 编辑按钮 + 阻止冒泡(避免触发行选中) */}
                    <bd-button icon={{name: 'edit'}} type="primary" nativeOn-click={(e) => {
                        this.editFun()
                        e.stopPropagation()
                    }}></bd-button>
                    <bd-button icon="delete" type="danger" nativeOn-click={(e) => {
                        this.delFun()
                        e.stopPropagation()
                    }}></bd-button>
                </span>
            )
        }
    }
}
```

### 4.4 操作列配套:`createFun` 注入函数(2 个 createFun 区别) ⭐⭐

**createFun** vs **createListFun**:
- `createFun`:函数注入到 **mList**(底层表格),`this` 指向 mList — 供 `renderField.*.render` 内 `this.editFun()` 调用
- `createListFun`:函数注入到 **moduleList**(上层),`this` 指向 moduleList — 供 `buttons[].click` 内调用

```js
// list.js 同级 export default 对象
renderField: { /* ... */ },
createFun: {
    // this 指向 mList,供 renderField.*.render 内 this.editFun() 调用
    editFun () {
        this.pushPage({
            path: `/module/stander/edit/edit/user_info/${this.someField?.id || ''}`,
            title: '编辑'
        })
    },
    delFun () {
        this.$confirm('确认删除?').then(() => {
            this.search()  // 调底层刷新
        })
    }
},
createListFun: {
    // this 指向 moduleList,供 buttons[].click 内调用
    handleExport () {
        this.exportData()  // moduleList 的导出方法
    }
}
```

---

## 5. 完整可复制示例

### 5.1 状态徽章 + 操作列(最常见组合)

```js
// public/moduleJs/user_info/list.js
import { Message } from 'element-ui'

export default {
    renderField: {
        // 状态列 → 彩色徽章(数据字典字段,必须配 statusDesc)
        //   row.status 拿原值做颜色判断,cellValue 拿框架翻译后的中文
        statusDesc: {
            formatter: function (row, column, cellValue) {
                const typeMap = { 0: 'info', 1: 'success' }
                return `<span class="status-tag ${typeMap[row.status] || 'info'}">${cellValue}</span>`
            }
        },
        // 操作列
        operate: {
            render: function (h, context, row) {
                return (
                    <span>
                        <el-button type="text" on-click={() => this.editFun(row)}>编辑</el-button>
                        <el-button type="text" on-click={() => this.delFun(row)}>删除</el-button>
                    </span>
                )
            }
        }
    },
    createFun: {
        editFun (row) {
            this.pushPage({
                path: `/module/stander/edit/edit/user_info/${row.id}`,
                title: `编辑 ${row.userName}`
            })
        },
        delFun (row) {
            this.$confirm(`确认删除 ${row.userName}?`, '提示').then(() => {
                this.search()
            })
        }
    }
}
```

### 5.2 单元格点击 + 文本链接(轻量)

```js
export default {
    renderField: {
        userName: {
            formatter: (row) => `<span class="primary-text-3 pointer">${row.userName}</span>`,
            click: function (row) {
                this.pushPage({
                    path: `/module/view/view/user_info/${row.id}`,
                    title: row.userName
                })
            }
        }
    }
}
```

### 5.3 单元格内嵌搜索/过滤

```js
export default {
    renderField: {
        description: {
            formatter: function (row, column, cellValue) {
                if (!cellValue) return '--'
                // 关键词高亮
                return cellValue.replace(/foo/gi, '<mark>foo</mark>')
            }
        }
    }
}
```

---

## 6. 关键事实

- `render` **优先级最高** → `render > click > formatter`(只生效一个)
- **this 是 mList 实例**,不是 moduleListCode(也非 moduleList)
- 操作列按钮**必须** `e.stopPropagation()`(表格行有"点击选中"行为)
- 操作列引用的函数要在 **`createFun`** 里注册(mList 作用域),别直接用箭头函数
- 按钮 click 里要用的函数,要在 **`createListFun`** 里注册(moduleList 作用域)
- 想跳页面优先用 `this.pushPage(...)`,它会自动加 tab 历史;不推荐 `this.$router.push`

---

## 7. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| 写了 `render` 没生效 | `renderField.字段名` 字段名拼错 | 字段名必须**严格匹配**后端 `fieldList` |
| 整列没出来 | 后端 `fieldList` 没声明 | 去找后端模型设计器加 |
| 列出来但内容是 `[object Object]` | `render` return 错了 | 必须 return VNode/JSX,不能 return 普通对象 |
| 报错 "tagName is not defined" | JSX 用了字符串标签 | 必须写 `<span>`,不能 `'<span>'` |
| `return <el-tag>...</el-tag>` 页面报错/无渲染 | JSX 没用 `()` 包裹 | return html **必须**用小括号 `()` 包裹 JSX,否则 ASI 会让 return 变成 `return undefined`(详见 §4.1.1) |
| 操作列按钮点了顺便勾选整行 | 没阻止冒泡 | 加 `e.stopPropagation()` |
| `this.$refs.moduleListCode` undefined | 误以为 this 是 moduleListCode | `this` 是 mList,要么走 `createFun` 注入,要么用 `this.pushPage` |
| JSX 里 `on-click={this.editFun}` 不带 row | editFun 拿不到行数据 | 改成箭头函数 `on-click={() => this.editFun(row)}` |
| `editFun` 报 undefined | 误把函数写在 `createListFun` 里 | renderField 内 this 是 mList,函数要写在 `createFun` |
| 按钮 click 调函数报 undefined | 误把函数写在 `createFun` 里 | buttons 内 this 是 moduleList,函数要写在 `createListFun` |

---

## 8. 完整 key 速查(本 skill 覆盖)

| key | 用途 | 状态 |
|------|------|------|
| `renderField` | 列渲染(formatter/click/render) | ✅ |
| `renderColumn` | **【旧,不推荐】** 等同 `renderField` | ⚠️ 别用 |
| `createFun` | 注入 mList 作用域函数(供 renderField 用) | ✅ |
| `createListFun` | 注入 moduleList 作用域函数(供 buttons 用) | ✅ |
| `renderFieldHeader` | 自定义表头(移到 [table-look](../table-look/SKILL.md#5-renderfieldheader自定义表头单元格)) | ✅ |

---

## 9. 下一步去哪

- **按钮** → `module-list-buttons`
- **搜索栏交互** → `module-list-search`
- **请求/数据流** → `module-list-data-flow`
- **表格外观**(表头/插槽/分页/合并) → `module-list-table-look`
- **导入导出** → `module-list-import-export`
- **回到总览** → `frontend-module-list`
- **表单列渲染(Edit 的 renderField / valueChange / 字段联动)** → [module-edit-fields](../../../frontend-module-edit/sub/fields/SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
