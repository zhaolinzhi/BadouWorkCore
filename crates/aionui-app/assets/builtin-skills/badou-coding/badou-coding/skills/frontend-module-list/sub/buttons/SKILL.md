---
name: frontend-module-list-buttons
description: 八斗 Module 列表 customSetting — 按钮完整指南。当用户说"加按钮"、"顶部按钮"、"行按钮"、"行按钮获取当前行"、"搜索栏按钮"、"按钮排序"、"按钮按数据显隐"、"右键菜单"、"按钮加载态"时触发。覆盖 buttons/searchBtns/colBtnType/beforeRowBtnRender + 11 个 button 子属性(priority/position/rightMenu/showArgs/disableArgs/isHide/style/loading/functionName/isEdit/isView)+ getBaseBtnFun 事件插入 + getSelection 获取当前行。
---

# Module 列表 — 按钮

> 列表页**所有按钮类**customSetting 一站式指南。**先看 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。
> **搜索栏交互(搜索条件变化/显隐)见 [module-list-search](../search/SKILL.md)**。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/list.js` 的 `export default` 对象里。

**进入前必读**:mdCode + list/edit + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 5 个顶层 key + 11 个 button 子属性

**顶层 key**:

| key | 用途 | 频次 |
|------|------|------|
| `buttons` | 顶部 + 行按钮(可传数组或函数) | ⭐⭐⭐⭐⭐ |
| `searchBtns` | 搜索栏按钮(搜索/重置那一排) | ⭐⭐⭐ |
| `colBtnType` | 行按钮样式 | ⭐ |
| `beforeRowBtnRender` | 行按钮渲染前筛选 | ⭐ |
| `getBaseBtnFun` | 在默认按钮事件前后插入逻辑 | ⭐⭐⭐⭐ |

**`buttons[].xxx` 子属性(11 个)**:

| 子属性 | 类型 | 用途 | 频次 |
|------|------|------|------|
| `id` | `String` | 唯一标识,系统默认是 `add`/`edit`/`view`/`delete`/`import`/`export` | ⭐⭐⭐⭐⭐ |
| `name` | `String` | 按钮文字 | ⭐⭐⭐⭐⭐ |
| `icon` | `String` | 图标 | ⭐⭐⭐⭐ |
| `type` | `String` | 颜色:`primary`/`warning`/`danger`/`success`/`info` | ⭐⭐⭐⭐ |
| `click` | `Function` | 按钮点击事件(可用箭头但 this 会丢) | ⭐⭐⭐⭐⭐ |
| `isHide` | `Boolean\|Function` | 隐藏(支持函数动态判断) | ⭐⭐⭐⭐ |
| `loading` | `Boolean` | 点击后 loading 状态(框架自动维护) | ⭐⭐ |
| `priority` | `Number` | 排序(数字越小越靠前) | ⭐⭐⭐ |
| `position` | `Array<'top'\|'right'>` | 位置:顶部 / 行操作列 / 都有 | ⭐⭐ |
| `rightMenu` | `Boolean\|String` | 是否出现在列表右键菜单(可指定组名) | ⭐⭐ |
| `showArgs` | `Object` | 按当前行数据动态显隐 | ⭐⭐ |
| `disableArgs` | `Object` | 按当前行数据动态禁用 | ⭐⭐ |
| `style` | `Object` | 按钮自定义样式(`backgroundColor` 等) | ⭐ |
| `functionName` | `String` | 把 click 抽到 `createListFun` 里引用 | ⭐ |
| `getSelection` 用法 | — | 行按钮 click 内用 `this.getSelection()` 拿当前行(顶部按钮拿不到) | ⭐⭐⭐⭐⭐ |

---

## 2. `buttons` ⭐⭐⭐⭐⭐(顶部/行按钮)

**来源**:`ModuleList/index.vue` 第 1156-1215 行 `getBtnList`

**两种形式**:**Array**(与默认按钮合并)或 **Function**(返回最终按钮数组,完全替换默认)。

### 2.1 数组形式 — 合并默认按钮

```js
buttons: [
    {
        id: 'export',  // 唯一标识
        name: '导出 Excel',
        icon: 'el-icon-download',
        type: 'primary',  // primary/warning/danger/success/info
        click: function (btnObj) {
            // this 指向 moduleList 实例
            this.$message.success('点了导出')
        }
    }
]
```

### 2.2 函数形式 — 接收默认按钮,返回新数组

```js
buttons: function (defaultBtns) {
    // this 指向 moduleList 实例
    // defaultBtns = [{ id: 'add', click: Add }, { id: 'edit', ... }, ...]
    return defaultBtns.filter(btn => btn.id !== 'delete')  // 干掉删除
}
```

> ⚠️ 函数形式**完全替换**,返回啥就显示啥。直接传数组则是**合并**。

### 2.3 隐藏默认按钮(2 种)

```js
// 1. 写死隐藏
buttons: [
    { id: 'delete', isHide: true }
]

// 2. 函数动态判断(返回 truthy = 隐藏)
buttons: [
    { id: 'view', isHide: function () { return /* 某条件 */ } }
]
```

**`isHide` 函数形式的关键约束**(由 [ShowStatus](../../../service/module.js#L265-L282) 调用):

| 项 | 实际行为 |
|---|---|
| **参数** | **不传任何参数**(`obj[sign]()`),原 skill 写的 `function (row) {...}` 里 `row` 永远是 `undefined` |
| **`this` 指向** | 指向**按钮对象 `btnObj`**,**不是 moduleList 实例**——拿不到 `this.$store` / `this.getSelection()` |
| **返回值** | 返回 truthy → 隐藏;返回 falsy → 显示 |
| **来源** | [src/service/module.js:273-276](../../../service/module.js#L273-L276) |

**典型场景:按角色(读 Vuex)显隐——用 `buttons` 函数形式,别用 `isHide` 函数**

`isHide` 函数内 `this` 是按钮对象,拿不到 `this.$store`,只能 `import store from '@/store'`。**更简洁的做法**是直接用 `buttons` 函数形式(§2.2),`this` 指向 moduleList,能直接 `this.$store`:

```js
// ✅ 推荐:角色控制(读 Vuex this.$store)
buttons: function (defaultBtns) {
    // this 指向 moduleList
    const isSuper = this.$store.state.user.userInfo.roleCode === 'SUPER'
    return isSuper
        ? defaultBtns
        : defaultBtns.filter(btn => btn.id !== 'edit' && btn.id !== 'delete')
}
```

> ⚠️ 如果一定要用 `isHide` 函数按角色控制(例如只想精准隐藏某一个按钮),需要 `import store`:
> ```js
> import store from '@/store'
> export default {
>     buttons: [
>         {
>             id: 'edit',
>             isHide: function () {  // this 指向按钮对象,不是 moduleList
>                 return store.state.user.userInfo.roleCode !== 'SUPER'
>             }
>         }
>     ]
> }
> ```

### 2.4 重写默认按钮 click(覆盖默认行为) ⭐⭐⭐⭐

**典型场景**:不想用默认行为(例如 view 默认跳当前模型的查看页),要跳到**另一个模型**的页,或调**自定义接口**(如改 delete 的后端地址)。

**核心做法**:用**相同的 id** 在 `buttons` 数组里写一个新按钮,框架会用你的 `click` **覆盖**默认 click,但**继承**默认的 `position`、`priority`、`icon`、`name` 等属性。

```js
export default {
    buttons: [
        // 重写默认查看:跳到另一个模型的查看页
        {
            id: 'view',
            click: function (btnObj) {
                // this 指向 moduleList 实例
                let selection = this.getSelection()
                if (selection.length !== 1) {
                    this.$message.warning('请选择一行!')
                    return
                }
                this.pushPage({
                    // 关键:用目标模型的 mdCode 替换默认的 this.mdCode
                    path: `/module/view/tableView/目标mdCode/${selection[0].id}`,
                    title: btnObj.name
                })
            }
        }
    ]
}
```

**与 `getBaseBtnFun` 的区别**(详见 §4):

| 方式 | 适用场景 |
|------|---------|
| `id` 同名 + 重写 `click` | 行为完全不同(跳别的模型 / 调别的接口) |
| `getBaseBtnFun` | 在默认事件前后**插入**逻辑,保留默认行为 |

**默认按钮的路径 / 接口速查**(覆盖时把 `this.mdCode` 换成目标):

| id | 默认行为 | 默认路径 / 接口 |
|---|---|---|
| `add` | 跳新增页 | `/module/stander/tableEdit/${this.mdCode}/add` |
| `edit` | 跳编辑页 | `/module/stander/tableEdit/${this.mdCode}/${row.id}` |
| `view` | 跳查看页 | `/module/view/tableView/${this.mdCode}/${row.id}` |
| `delete` | 调默认删除接口 | `Common_Delete({ mdCode, ids })` |

**典型场景:重写 delete 为自定义接口**

```js
{
    id: 'delete',
    click: function (btnObj) {
        let selection = this.getSelection()
        if (selection.length === 0) {
            this.$message.warning('至少选择一行!')
            return
        }
        this.$confirm('确定删除吗?').then(() => {
            this.$axios.post('/api/your-custom-delete', {
                ids: selection.map(i => i.id).join(',')
            }).then(() => {
                this.listPageRef().init()  // 刷新列表
                this.$message.success('删除成功')
            })
        })
    }
}
```

> ⚠️ 覆盖时**不写 position / priority** 即可继承默认;如果写了,会用你写的值(覆盖默认)。

### 2.5 行按钮获取当前行数据(高频) ⭐⭐⭐⭐

`position: ['right']` 的行按钮 click 内,**不能用 `btnObj` 拿行数据**(btnObj 没有 row 字段)。

正确做法是用 `this.getSelection()`:

```js
buttons: [
    {
        id: 'onShelf',
        name: '上架',
        icon: 'send',
        type: 'primary',
        position: ['right'],
        click: function () {
            // this 指向 moduleList 实例
            // 行按钮点击时,框架会把当前行数据存到 tempSelection
            // getSelection() 优先返回 tempSelection(当前行),其次返回勾选数据
            let selection = this.getSelection()
            console.log('当前所在行数据:', selection)
        }
    }
]
```

**机制**(看 `ModuleList/index.vue:646-649`):
```js
getSelection () {
    return this.listPageRef().tempSelection || this.listRef().selection
}
```

- `tempSelection`:行按钮点击时由 MList 注入(单一当前行)
- `listRef().selection`:表格勾选行数组

> 📌 **参考实现**:[src/components/frame/Module/BtnBaseFun/list.js:29](../../../components/frame/Module/BtnBaseFun/list.js#L29) — `let selection = this.getSelection()`

> ⚠️ 顶部按钮(position 不含 right)click 内,`this.getSelection()` 只能拿到**已勾选**的行,拿不到"当前点击行"(顶部按钮没有"当前行"概念)。

### 2.6 批量操作(配合 `selectionChange`)

```js
import { Message } from 'element-ui'

export default {
    buttons: [
        {
            id: 'batchEnable',
            name: '批量启用',
            icon: 'el-icon-check',
            type: 'success',
            click: function () {
                // this 指向 moduleList
                const rows = this.selectedRows || []
                if (!rows.length) {
                    Message.warning('请先勾选数据')
                    return
                }
                this.$confirm(`确认启用 ${rows.length} 条?`, '提示').then(() => {
                    // 调业务接口...
                })
            }
        }
    ],
    selectionChange (selection) {
        // 把已选行存到 moduleList,供按钮 click 访问
        this.selectedRows = selection
    }
}
```

---

## 3. button 子属性(11 个) — 必读 ⭐⭐⭐⭐⭐

> 这一节是**业务方最容易漏的 11 个 button 配置**,很多"按钮为什么不显示/位置不对"都出在这里。

### 3.1 `id`(必须,系统用它识别)

默认 id:`add` / `edit` / `view` / `delete` / `import` / `export`。
- 用相同 `id` → **覆盖**默认行为
- 用不同 `id` → **新增**一个按钮
- `isHide: true` → 隐藏

### 3.2 `loading`(点击 loading 状态)

```js
buttons: [
    {
        id: 'save',
        name: '保存',
        loading: false,   // 初始 false,点击后框架自动置 true,接口完成置 false
        click: async function (btnObj) {
            // 框架自动:btnObj.loading = true
            await this.postFile(...)
            // 框架自动:btnObj.loading = false
        }
    }
]
```

> 业务方**不用手动维护** `btnObj.loading`,框架会根据 click 返回的 Promise 状态自动切。

### 3.3 `priority`(按钮排序)— ⭐⭐⭐

不写 priority 默认为 999999,排在所有默认按钮之后。

```js
export default {
    buttons: [
        {
            id: 'operateEvt',
            name: '操作',
            priority: 35,  // 数字越小越靠前
            click: function () {}
        },
        {
            id: 'add',  // id 一致就覆盖,没写 priority 用默认值 5
            name: '重写的新增按钮',
            click: function () {}
        },
        {
            id: 'edit',
            priority: 1,  // 重写 priority 后排第一
            click: function () {}
        }
    ]
}
```

**默认按钮 priority**:
| id | priority |
|---|---|
| add | 5 |
| edit | 10 |
| view | 15 |
| import | 25 |
| export | 30 |
| delete | 40 |

### 3.4 `position`(按钮位置:顶部 / 行操作列)

```js
buttons: [
    { id: 'topBtn', name: '顶部按钮', position: ['top'] },
    { id: 'rowBtn', name: '行操作', position: ['right'] },  // 出现在每行的操作列
    { id: 'both', name: '两边都有', position: ['top', 'right'] }  // 同时在顶部和行操作列
]
```

### 3.5 `rightMenu`(右键菜单)— ⭐⭐

```js
buttons: [
    { id: 'r1', name: '鼠标右键1', type: 'success', rightMenu: true },
    { id: 'r2', name: '分组右键', type: 'success', rightMenu: 'customGroup' }
    // 传 String 时作为组名,右键菜单会按组名分组
]
```

> 列表行**右键**时弹出,核心面向**当前右击的该行数据**,与勾选项无关。

### 3.6 `showArgs`(按行数据动态显隐)— ⭐⭐

```js
buttons: [
    {
        id: 'delete',
        // 同个字段内是"或"关系,不同字段间是"与"关系
        // 数组内统一是字符串,'null'/'undefined' 用 '' 标识
        showArgs: {
            status: ['', '0'],   // status 是空或 0
            fieldA: ['finished']  // 且 fieldA = 'finished'
        }
    }
]
```

**逻辑**:
- status 满足 ['', '0'] 之一 **或** fieldA 满足 ['finished']
- 但**不同字段间是 AND**

### 3.7 `disableArgs`(按行数据动态禁用)— ⭐⭐

```js
buttons: [
    {
        id: 'edit',
        disableArgs: {
            status: ['', '0'],
            fieldA: ['finished']
        }
    }
]
```

**与 `showArgs` 区别**:`showArgs` 不满足时按钮**隐藏**,`disableArgs` 不满足时按钮**禁用但显示**。

**对不同位置的影响**:
- 列表右侧操作列:满足 showArgs 的按钮**显示**,不满足 disableArgs 的按钮也显示但**禁用**
- 列表顶部菜单:满足 disableArgs 的按钮**禁用**,满足 showArgs 不满足的按钮**隐藏**
- 建议:需要按行控制的按钮放在**操作列**

**来源**:`utils/index.js:309 Set_BtnList_Args`

### 3.8 `style`(自定义按钮样式)

```js
buttons: [
    {
        id: 'add',
        style: {
            backgroundColor: 'red',
            color: 'yellow',
            borderColor: 'red'
        }
    }
]
```

### 3.9 `functionName`(把 click 抽到 createListFun)

```js
buttons: [
    {
        id: 'add',
        functionName: 'customAdd'  // 这里只写名字
    }
],
createListFun: {
    customAdd (btnObj) {
        // this 指向 moduleList
        this.$message.warning('自定义新增')
    }
}
```

### 3.10 `isEdit` / `isView`(Edit 侧专属,List 侧用不到)

List 侧用不到,详见 [module-edit-submit-flow §3](../../../frontend-module-edit/sub/submit-flow/save-and-buttons.md#3-buttons自定义按钮-高频-⭐⭐⭐⭐⭐)。

---

## 4. 事件插入点 `getBaseBtnFun`(重写默认按钮的"夹缝"做法) ⭐⭐⭐⭐

**典型场景**:你不想重写整个默认按钮,只想在"保存前"或"删除后"加一段逻辑。

**用法**:

```js
buttons: [
    {
        id: 'edit',
        click: function (btnObj) {
            // 获取原本默认的 edit 事件
            let _fun = this.getBaseBtnFun('edit')
            _fun.call(this, btnObj, {
                // 1. 同步场景(不需要等待)
                before: (selection) => {
                    alert('即将进入编辑页')
                },
                // 2. 异步场景(必须 resolve 才能往下走)
                before: (resolve, selection) => {
                    this.$confirm('确认编辑?').then(() => {
                        resolve()
                    }).catch(() => {
                        // 不调 resolve 就会卡住
                    })
                },
                // 3. 条件终止(不符合就不走)
                before: (resolve, selection) => {
                    if (selection[0]?.name === 'aa') {
                        resolve()
                    } else {
                        // 不调 resolve 就不往下走
                        this.$message.warning('名字不是 aa,取消编辑')
                    }
                }
            })
        }
    }
]
```

**支持的事件插入点**(按按钮维度):
| 按钮 | 插入点 |
|------|------|
| `add` | `before` / `after`(跳转前后) |
| `edit` | `before` / `after`(跳转前后) |
| `view` | `before` / `after` |
| `import` | `before` / `after` |
| `export` | `before` / `after` |
| `delete` | `beforeConfirm` / `before` / `after` |

> **来源**:`ModuleList/index.vue:614 getBaseBtnFun`,`utils/index.js:9 Get_Btn_ClickFun`

### 4.1 实战:删除按钮前加 alert/confirm 提醒 ⭐⭐⭐⭐

**典型场景**:默认删除事件(二次确认 + 调 `Common_Delete` + 刷新列表)**不变**,只在**之前**插一个 alert / confirm 提示用户。

```js
buttons: function (defaultBtns) {
    return defaultBtns.map(btn => {
        if (btn.id === 'delete') {
            return {
                ...btn,
                click: function (btnObj) {
                    // 1. 拿到框架的默认删除函数
                    let _fun = this.getBaseBtnFun('delete')
                    // 2. 调用它,加 before 钩子
                    _fun.call(this, btnObj, {
                        before: () => {
                            // 同步 alert(关掉 alert 后继续走默认事件)
                            alert('提醒下用户,即将准备修改了')
                        }
                    })
                }
            }
        }
        return btn
    })
}
```

**执行流程**:
1. 用户点删除 → 框架调 `click(btnObj)`
2. 业务 `click` 拿 `getBaseBtnFun('delete')` 得到默认删除函数 `_fun`
3. `_fun.call(this, btnObj, { before })` 触发
4. **`before` 钩子先跑**:`alert(...)` → 用户点确定
5. 接着跑**默认事件**:弹二次确认 → 调 `Common_Delete` → 刷新列表

> ⚠️ **不要在 `before` 里用 `$confirm` / 同步 return false 来"取消"默认事件** — `before` 同步形式**没有中断能力**,想中断必须用 §4.2 场景 2 的异步 `before`(接 `resolve`)。

### 4.2 典型场景合集(直接复制)

#### 场景 1:删除前 confirm 二次确认(同步,仅提示)

```js
click: function (btnObj) {
    this.getBaseBtnFun('delete').call(this, btnObj, {
        before: (selection) => {
            // 同步钩子不能中断,只能用作"提醒",无法取消默认事件
            this.$message.warning(`即将删除 ${selection.length} 条数据`)
        }
    })
}
```

#### 场景 2:删除前调后端校验(异步,推荐)⭐⭐⭐⭐

**关键**:`before` 接 `(resolve, selection) => {...}`,**调 `resolve()` 才继续**,不调就卡住,默认事件不会触发。

```js
click: function (btnObj) {
    this.getBaseBtnFun('delete').call(this, btnObj, {
        before: (resolve, selection) => {
            // 调后端判断这条数据能否删除(比如有引用)
            this.$axios.post('/api/check-can-delete', { id: selection[0].id }).then(res => {
                if (res.data.canDelete) {
                    resolve()  // ✅ 通过,继续走默认删除
                } else {
                    this.$message.warning(res.data.reason || '该数据不可删除')
                    // 不调 resolve → 默认事件不会触发
                }
            }).catch(() => {
                this.$message.error('校验失败')
                // 也不调 resolve
            })
        }
    })
}
```

#### 场景 3:删除成功后联动操作(`after` 钩子)

```js
click: function (btnObj) {
    this.getBaseBtnFun('delete').call(this, btnObj, {
        after: (res) => {
            // 默认删除完成后,res 是接口返回的数据
            this.$message.success('删除成功,已通知关联模块')
            // 调其他模块的刷新 / 触发全局事件
            this.$EventBus.$emit('data-changed')
        }
    })
}
```

#### 场景 4:编辑前异步校验 + 自定义提示(异步 `before`)

```js
click: function (btnObj) {
    this.getBaseBtnFun('edit').call(this, btnObj, {
        before: (resolve, selection) => {
            if (selection[0].status === 'locked') {
                this.$message.warning('该数据已锁定,不可编辑')
                // 不调 resolve,默认事件不触发
                return
            }
            this.$axios.post('/api/check-edit-permission', { id: selection[0].id }).then(res => {
                if (res.data.hasPermission) {
                    resolve()
                } else {
                    this.$message.warning('您没有编辑权限')
                }
            })
        }
    })
}
```

### 4.3 delete 的 3 个钩子区别 ⭐⭐⭐

delete 比其他按钮多一个 `beforeConfirm` 钩子,触发顺序是:

```
用户点删除
  ↓
before 钩子(业务方最早插手)
  ↓
二次确认弹窗(框架自带)
  ↓
beforeConfirm 钩子(二次确认之后、接口调用之前)
  ↓
调 Common_Delete 接口
  ↓
after 钩子(接口完成后)
```

| 钩子 | 时机 | 典型用途 | 同步 / 异步 |
|------|------|---------|------------|
| `before` | 二次确认**之前** | alert 提醒 / 业务前置校验 / 弹自定义确认 | 都支持 |
| `beforeConfirm` | 二次确认**之后** | 调后端判断能否删 / 加 loading / 埋点上报 | 都支持 |
| `after` | 接口完成**之后** | 联动刷新 / 通知其他模块 / 自定义成功提示 | 同步(框架会等 Promise) |

> 📌 其他按钮(add/edit/view/import/export)**没有** `beforeConfirm`,只有 `before` / `after`。
> 📌 `beforeConfirm` / `before` / `after` 三个钩子可以**同时存在**,框架会按顺序串行执行。

---

## 5. `searchBtns`(搜索栏按钮)

**结构**:同 `buttons`,但只影响搜索栏(搜索/重置那一排)。

> 📌 **按钮 click 里经常需要给搜索项赋值**(如"近一年"按钮设置时间范围)。值格式细节(Date 3 种模式、NumRange、数字区间等)看顶层独立 skill [frontend-module-list-search-set-value](../../../frontend-module-list-search-set-value/SKILL.md)。

```js
searchBtns: [
    // 隐藏搜索按钮
    { id: 'search', isHide: true },
    // 改重置按钮的事件
    {
        id: 'reset',
        name: '重置',
        icon: 'reset',
        type: 'warning',
        click: () => { alert('不允许重置') }
    },
    // 加一个新按钮
    {
        id: 'text',
        name: '测试',
        icon: 'save',
        type: 'primary',
        click: function (btnObj) {
            this.$message.info('点了测试')
        }
    }
]
```

---

## 6. `colBtnType`(行按钮样式)

```js
colBtnType: 'text'  // text(蓝色文字) / button(完整按钮) / icon(仅图标)
```

**`text`**:只显示文字,通常蓝色 — 最常见
**`button`**:完整按钮 — 强调时用
**`icon`**:只显示图标,鼠标悬浮显示文字 — 节省操作列宽度

---

## 7. `beforeRowBtnRender`(行按钮渲染前过滤)

**来源**:[src/components/frame/Common/MList/components/OperateBtnList.vue:80](../../../components/frame/Common/MList/components/OperateBtnList.vue#L80)

**签名**:`beforeRowBtnRender(btnList, row, rowIndex, btnListOrigin) → btnList`

**this 指向**:**mList 实例**(由 `this.beforeRender.call(this.listScope, ...)` 注入,`listScope` 即 mList)

**调用源码**:
```js
res = Set_BtnList_Args(res, [this.dataInfo])                    // 先按 showArgs/disableArgs 处理
res = res.filter(i => Show_Status(i)).map(b => ({ ...b, loading: false }))
if (typeof this.beforeRender === 'function') {
    res = this.beforeRender.call(this.listScope, res, this.dataInfo, ...(this.fnAttrs || []))
}
return res
//      ↑ 返回值会赋回 res,所以必须 return 一个新的 btnList
```

⚠️ **3 个最易出错的地方**:

| 问题 | 现象 | 正确 |
|---|---|---|
| 1. 入参写 `(btnObj, row)` | `btnObj` 实际是**整个按钮列表** | 第一个参数是 `btnList`(数组) |
| 2. 用 `find` 后改 `btn.disabled` | ❌ 没用,深拷贝隔离了 | 直接 `btnList[i].disabled = true` 改数组元素 |
| 3. `return true/false` | **`res` 被覆盖成布尔值,所有行按钮消失** | 必须 `return btnList`(或 `return btnList.filter(...)`) |

### 7.1 正确用法:按行禁用 / 隐藏

```js
beforeRowBtnRender: function (btnList, row, rowIndex) {
    // 状态 status 值为 1 时,禁用编辑按钮
    let editBtn = btnList.find(b => b.id === 'edit') || {}
    editBtn.disabled = Boolean(String(row.status) === '1')

    // 也可直接 filter 掉某些按钮(彻底隐藏)
    // return btnList.filter(b => !(b.id === 'delete' && row.status === '1'))

    return btnList
}
```

### 7.2 行内多按钮按状态灰显

```js
// 场景:状态=1(上架)时,"上架"按钮置灰;"状态=2(待审)时,"下架"按钮置灰
beforeRowBtnRender: function (btnList, row) {
    let status = String(row.status)
    let onShelfBtn = btnList.find(b => b.id === 'onShelf')
    if (onShelfBtn && status === '1') {
        onShelfBtn.disabled = true
    }
    let onUnShelfBtn = btnList.find(b => b.id === 'onUnShelf')
    if (onUnShelfBtn && status === '2') {
        onUnShelfBtn.disabled = true
    }
    return btnList
}
```

> 与 `showArgs` / `disableArgs` 区别:
> - `showArgs` / `disableArgs`:配置式,只能写"等于"判断,跨字段 AND
> - `beforeRowBtnRender`:JS 写法,可任意判断(取反、范围、多字段联合、改 disabled / 直接 filter)

---

## 8. 关键事实

- `buttons[].click` 内 `this` 是 **moduleList 实例**(可访问 `this.selectedRows`、`this.$refs.moduleListCode` 等)
- `beforeRowBtnRender` 内 `this` 是 **mList 实例**(由 `listScope` 注入,详见 §7)
- **`isHide` 函数内 `this` 是按钮对象(btnObj),不是 moduleList**——拿不到 `this.$store` / `this.getSelection()`;要读 Vuex 用 `buttons` 函数形式更稳(详见 §2.3)
- **行按钮获取当前行**:用 `this.getSelection()`(不是 `btnObj.row`);顶部按钮只能拿到已勾选项
- 想在 renderField(列渲染)里调函数 → 在 `createFun` 注册(那个 `this` 是 mList)
- 默认按钮的 `id`: `add` / `edit` / `view` / `delete` / `import` / `export`
- 用相同 `id` 覆盖默认行为;`isHide: true` 隐藏;**同名覆盖时,只写 click 即可,其他属性(position/priority/icon/name)继承默认**(详见 §2.4)
- `isHide` **支持函数形式**,但函数**不传参**且 `this` 指向**按钮对象**(不是 moduleList);要读 Vuex 用 `buttons` 函数形式更稳(详见 §2.3)
- **没重写 priority 时**,按默认 priority 排(越小越前)
- **`getBaseBtnFun`** 是"重写默认按钮"的标准做法,比自己重写整个 click 简单

---

## 9. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| 按钮 click 报"undefined is not a function" | 用了箭头函数,this 指向错 | `buttons[].click` 用 `function`,`this` 才指向 moduleList |
| 批量按钮点了不响应 | 没存 `selectedRows` | 在 `selectionChange` 里 `this.selectedRows = selection` |
| 默认按钮没干掉 | 用了不同的 `id` | 必须用相同 `id`(`delete` / `add` 等)才能覆盖 |
| 按钮 click 里访问 `this.someField` undefined | 误用 createFun 的注入函数 | createFun 注入到 mList,按钮 click 内是 moduleList |
| 行按钮 click 拿不到当前行 | 误以为 `btnObj.row` 有值 | 用 `this.getSelection()`,框架会从 tempSelection 取 |
| 按钮位置不对 | 没用 `position` | 不写 position 默认顶部,要放操作列加 `position: ['right']` |
| 按钮没排序 | 没写 `priority` | 不写默认 999999,排最后 |
| 改了优先级不生效 | 默认按钮的 priority 是固定的 | 覆盖时**重新写 priority**才会改变顺序 |
| `showArgs` 不满足时按钮还显示 | 业务上想让按钮"在所有情况都显示" | `showArgs` 隐含 AND,任何条件不满足就隐藏 |
| 重写 click 时把默认逻辑丢了 | 整个 click 重写 | 用 `getBaseBtnFun` 在默认事件前后插入,不要整个重写 |
| `getBaseBtnFun('delete')` 拿不到默认函数 | 误用别的 id 调(比如 `getBaseBtnFun('del')`) | 必须用与按钮**同 id**(`delete`/`edit`/`view` 等),**别拼写错** |
| `before` 钩子写了但默认事件没触发 | 异步 `before` 没调 `resolve()` | 异步钩子 `(resolve) => {...}` 必须调 `resolve()` 才继续走默认事件(详见 §4.2 场景 2) |
| 同步 `before` 钩子里想"取消"默认事件 | 用 `return false` / `$confirm` 拒接 | 同步 `before` **没有中断能力**,想中断必须改用异步 `before` 接 `resolve`(详见 §4.1 注) |
| 三个钩子同时写但只生效一个 | 误以为只能写一个 | `before` / `beforeConfirm` / `after` 可以**同时存在**,框架按顺序串行执行(详见 §4.3) |
| 覆盖默认按钮后位置/图标不对 | 写了 `position` / `icon` 反而覆盖了默认 | 覆盖时**不写**这两个属性,只写 `click`,框架会继承默认的 position/priority/icon/name(详见 §2.4) |
| `isHide` 函数里 `row` 永远是 undefined | 误以为 `isHide: function (row) { ... }` 能拿行数据 | `ShowStatus` 调用 isHide 时**不传参**(详见 §2.3);要按行数据显隐,用 `buttons` 函数形式配合 `getSelection()` |
| `isHide` 函数里 `this.$store` undefined | 误以为 this 指向 moduleList | 函数内 `this` 指向**按钮对象**;读 Vuex 要 `import store from '@/store'`,或改用 `buttons` 函数形式 |
| `beforeRowBtnRender` 里 `dataInfo.row` undefined | 误以为第二个参数是 `{ row, $index }` 包裹 | 第二个参数**直接是行对象本身**(OperateBtnList.vue:80 `:dataInfo="scope.row"`);签名是 `(btnList, row, rowIndex)`,详见 §7 |
| `beforeRowBtnRender` return `true/false` → **行所有按钮消失** | 误以为是 Boolean 返回值 | `res = this.beforeRender.call(...)`,**返回值会赋回 res**,必须 `return btnList`(或 `btnList.filter(...)`);return 布尔值会把 res 覆盖成 `true`,所有按钮清空,详见 §7 |

---

## 10. 下一步去哪

- **搜索栏交互**(搜索条件变化/显隐) → `module-list-search`
- **列渲染** → `module-list-render-field`
- **请求/数据流** → `module-list-data-flow`
- **选择 + 双击** → `module-list-selection-row`
- **表格外观** → `module-list-table-look`
- **导入导出** → `module-list-import-export`
- **回到总览** → `frontend-module-list`
- **表单按钮(Edit 的 saveUrl / buttons)** → [module-edit-submit-flow](../../../frontend-module-edit/sub/submit-flow/SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
