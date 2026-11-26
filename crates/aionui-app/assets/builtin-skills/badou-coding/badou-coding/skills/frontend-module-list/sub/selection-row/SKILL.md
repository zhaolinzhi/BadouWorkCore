---
name: frontend-module-list-selection-row
description: 八斗 Module 列表 customSetting — 选择 + 双击 + 多选完整指南。当用户说"勾选数据"、"双击行"、"禁用多选"、"选择项变化"时触发。覆盖 selectionChange / dblClick / multiple 3 个 key。
---

# Module 列表 — 选择 + 双击 + 多选

> 列表"行级交互"的 3 个 key。**先看 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/list.js` 的 `export default` 对象里。

**进入前必读**:mdCode + list/edit + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 3 个 key

| key | 类型 | 用途 | 频次 |
|------|------|------|------|
| `selectionChange` | `Function` | 选择项变化 | ⭐⭐⭐ |
| `dblClick` | `Function` | 行双击 | ⭐⭐⭐ |
| `multiple` | `Boolean` | 是否支持多选 | ⭐⭐ |

---

## 2. `selectionChange`(选择项变化)

**来源**:`MList/index.vue` 第 860-863 行

**签名**:`selectionChange(selection)`

**this 指向**:**mList 实例**

```js
selectionChange: function (selection) {
    // selection: 已选中的行数组
    this.selectedRows = selection
    this.$nextTick(() => {
        // 选中后启用/禁用某些按钮
    })
}
```

### 实战:配合批量按钮

```js
// 见 module-list-buttons §2.4 完整示例
import { Message } from 'element-ui'

export default {
    selectionChange (selection) {
        this.selectedRows = selection
    },
    buttons: [
        {
            id: 'batchDelete',
            name: '批量删除',
            type: 'danger',
            click: function () {
                const rows = this.selectedRows || []
                if (!rows.length) {
                    Message.warning('请先勾选数据')
                    return
                }
                this.$confirm(`确认删除 ${rows.length} 条?`).then(() => {
                    // 调接口,然后 this.search() 刷新
                })
            }
        }
    ]
}
```

> 💡 `this.selectedRows` 的存取:
> - `selectionChange` 存(在 mList,this 是 mList)
> - `buttons[].click` 读(在 moduleList,this 是 moduleList,**不同实例**)
>
> 推荐做法:在 `selectionChange` 里 `this.selectedRows = selection`,Vue 响应式会自动同步到 moduleList 里的同名字段(因为它们都引用同一个 Vuex store 或同一对象)。**但要小心 this 不一样**——见下方"常见问题"。

---

## 3. `dblClick`(行双击)

**来源**:`ModuleList/index.vue` 第 1120-1126 行

**签名**:`dblClick(btnList)`

**this 指向**:**moduleList 实例**

```js
dblClick: function (btnList) {
    // btnList: 当前所有按钮(含默认 + 自定义)
    // 例: 双击行触发"查看"
    const viewBtn = btnList.find(b => b.id === 'view')
    viewBtn && viewBtn.click.call(this, viewBtn)
}
```

**实战**(摘自 `public/moduleJs/frame/notice/notice_user_list.js:110-113`):

```js
dblClick (btnList) {
    let btnItem = btnList.find(i => i.id === 'view')
    btnItem && btnItem.click.call(this, btnItem)
}
```

### 实战:双击行打开编辑

```js
dblClick: function (btnList) {
    const editBtn = btnList.find(b => b.id === 'edit')
    editBtn && editBtn.click.call(this, editBtn)
}
```

### 实战:双击行打开新 tab(查看)

```js
dblClick: function () {
    // 当前选中行
    const currentRow = this.currentRow  // moduleList 暴露的当前行
    if (!currentRow) return
    this.pushPage({
        path: `/module/view/view/user_info/${currentRow.id}`,
        title: currentRow.userName
    })
}
```

---

## 4. `multiple`(多选开关)

```js
multiple: false,  // 表格只能单选(默认 true)
```

> 注:设置 `false` 后,表头的复选框会变成单选框。

---

## 5. 关键事实

| key | this 指向 |
|------|---------|
| `selectionChange` | mList |
| `dblClick` | moduleList |
| `multiple` | 无 this,纯配置 |

**`selectionChange` 和 `buttons[].click` 的 this 不一样**:
- `selectionChange` 存 `this.selectedRows = selection` → mList 实例
- `buttons[].click` 读 `this.selectedRows` → moduleList 实例

**两个实例各自的 `selectedRows` 不是同一份**!如果你只在一个里面 set,在另一个里读会是 undefined。

**推荐方案**:用 `createListFun` 注入到 moduleList 的函数,统一管理 `selectedRows`,或在 `selectionChange` 里**主动**调用 moduleList 的方法。

---

## 6. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| 批量按钮点开发现 `selectedRows.length === 0` | `selectionChange` 和 `buttons[].click` 的 this 不一样 | 用 `createListFun` 注入,或主动存到 Vuex |
| 双击行没反应 | btnList 里没有对应 id | 检查默认按钮 id(`view`/`edit`),或自己在 `buttons` 加一个 |
| 双击行直接编辑了,但只想查看 | 用了 `edit` 而不是 `view` | 在 `btnList.find(b => b.id === 'view')` 改成 view |
| `multiple: false` 但仍能多选 | 没生效 | 确认 `customSetting.multiple` 字段名写对(不是 `isMultiple`) |
| 操作列按钮点了顺便勾选整行 | 没阻止冒泡 | 走 `module-list-render-field` 看阻止冒泡模板 |

---

## 7. 下一步去哪

- **列渲染** → `module-list-render-field`
- **按钮** → `module-list-buttons`
- **搜索栏交互** → `module-list-search`
- **请求/数据流** → `module-list-data-flow`
- **表格外观** → `module-list-table-look`
- **回到总览** → `frontend-module-list`
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
