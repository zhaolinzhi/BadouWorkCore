---
name: frontend-module-tree-table
description: 八斗 Module 平台**普通列表(非树模型)展示树形数据** 完整指南。**何时调用**:用户想在普通列表(单列表,非左树+右表)里展示层级/父子关系数据(如目录树、菜单树、评论楼中楼、组织架构扁平展示等),需要知道 el-table 树形属性如何通过 `elseTableAttrs` 透传机制配到 customSetting、接口数据应该返回什么格式(嵌套 children vs 扁平 parentId)、全量加载与懒加载(lazy+load)两种模式的差异、是否需要配 row-key。**何时不调用**:① 用户想用"左树+右表/右表单"布局 → 走 `frontend-module-tree-list`/`frontend-module-tree-edit`;② 用户只是普通列表(扁平)定制 → 走 `frontend-module-list`;③ 用户首次接触 Module 平台 → 走 `frontend-module-quickstart`;④ 通用 Vue/Element UI 问题。
---

# Module 列表 — 树形表格(tree-table)customSetting

> 本 skill 讲的是**普通列表本身是树形**(行可展开嵌套子行)的实现方式。
> **不是**"左树+右表/右表单"的"树模型"——那个见 [frontend-module-tree-list](frontend-module-tree-list/SKILL.md) 和 [frontend-module-tree-edit](frontend-module-tree-edit/SKILL.md)。

---

## ⚠️ 0. 核心结论先说(必读)

框架**没有**专门的 `customSetting.isTreeTable` 之类的 key,但有个**透传机制**可以让 el-table 自带的树形属性生效:

```text
customSetting.xxx(如 tree-prop)
  ↓ ModuleList.updateCustomSetting() 里没解构
  ↓ ...elseTableAttrs 收集
  ↓ tableAttrs computed 末尾展开
  ↓ <bd-table-list> v-bind="tableAttrs"
  ↓ MList v-bind="$attrs"
  ↓ <el-table :tree-prop="..." />  ✅ 生效
```

来源:[src/components/frame/Module/ModuleList/index.vue:1015-1017](../../../src/components/frame/Module/ModuleList/index.vue#L1015-L1017) + [tableAttrs:426](../../../src/components/frame/Module/ModuleList/index.vue#L426) + [MList v-bind="$attrs":36](../../../src/components/frame/Common/MList/index.vue#L36)。

**所以**:业务方在 `customSetting` 里直接写 el-table 的树形属性,框架会自动透传。**不需要**后端配合、不需要新组件、不需要新 key。

---

## ⚠️ 1. 动手前必问 4 件事

| 询问项 | 为什么要问 |
|--------|-----------|
| **mdCode** | 决定 `public/moduleJs/{mdCode}/list.js` 路径 |
| **数据格式**(嵌套 vs 扁平) | 决定是用 `tree-prop` 还是先 `afterListJSON` 转树 |
| **数据量级**(全量 vs 懒加载) | 决定用 `default-expand-all` 还是 `lazy + load` |
| **是否已配 `customJs`** | 没配的话写也白写 |

---

## 2. el-table 树形属性速查(核心 5 个)

> 这些都是 **Element UI el-table 原生属性**,框架通过 `elseTableAttrs` 透传,无需新代码。

| 属性 | 类型 | 默认 | 作用 | 频次 |
|------|------|------|------|------|
| **`tree-prop`** | `String` | `'children'` | 指定行数据里**子节点数组**的字段名(默认就是 `children`) | ⭐⭐⭐⭐⭐ |
| **`row-key`** | `String` | 无默认 | 行数据的唯一 key 字段名。**树形表格必须配**,否则渲染异常 | ⭐⭐⭐⭐⭐ |
| `default-expand-all` | `Boolean` | `false` | 是否默认展开所有行(适合全量数据 + 不太深) | ⭐⭐⭐ |
| `expand-row-keys` | `Array` | — | 手动控制哪些行展开(可控) | ⭐⭐ |
| `lazy` + `load` | `Boolean` + `Function(row, treeNode, resolve)` | `false` | **懒加载**模式:展开行时才请求子节点(适合数据量大、层级深) | ⭐⭐⭐⭐ |

> ⚠️ 框架默认 `row-key` 是 `undefined`(见 [MList/index.vue:386-388](../../../src/components/frame/Common/MList/index.vue#L386-L388)),所以**树形表格必须自己传**。

---

## 3. 数据格式要求(2 种模式)

### 3.1 模式 A:嵌套 children(最简单,推荐)

**接口返回数据格式**:
```json
[
    {
        "id": 1,
        "name": "总公司",
        "children": [
            { "id": 2, "name": "研发部", "children": [...] },
            { "id": 3, "name": "市场部", "children": [] }
        ]
    }
]
```

**customSetting 配置**(一行搞定):
```js
// public/moduleJs/{mdCode}/list.js
export default {
    treeProp: 'children',  // 默认就是 children,可省略
    rowKey: 'id'           // 必传
}
```

> 默认 `tree-prop` 就是 `children`,所以**后端如果按嵌套返回,基本不用配置**。

### 3.2 模式 B:扁平 parentId(后端老接口常见)

**接口返回数据格式**:
```json
[
    { "id": 1, "parentId": 0, "name": "总公司" },
    { "id": 2, "parentId": 1, "name": "研发部" },
    { "id": 3, "parentId": 1, "name": "市场部" },
    { "id": 4, "parentId": 2, "name": "前端组" }
]
```

**方案 1:用 `afterListJSON` 转成嵌套**(推荐,简单):
```js
// public/moduleJs/{mdCode}/list.js
export default {
    rowKey: 'id',
    afterListJSON (list) {
        // list: 扁平数组
        // 转成嵌套结构(自己实现)
        return buildTree(list, 0, 'parentId', 'id', 'children')
    }
}

function buildTree (list, parentId, pidKey, idKey, childrenKey) {
    return list
        .filter(item => item[pidKey] === parentId)
        .map(item => ({
            ...item,
            [childrenKey]: buildTree(list, item[idKey], pidKey, idKey, childrenKey)
        }))
}
```

**方案 2:用 `lazy` 模式懒加载**(性能更好,但需后端配合):
```js
// public/moduleJs/{mdCode}/list.js
export default {
    rowKey: 'id',
    lazy: true,
    load: function (row, treeNode, resolve) {
        // this 是 moduleList 实例
        // row: 当前展开行(已加载的父行)
        // treeNode: el-table 内部节点对象 { level, ... }
        // resolve: 回调,把异步加载的子行数组传给它
        this.post(`${this.BASEURL}/xxx/listChildren.do`, { parentId: row.id })
            .then(res => resolve(res.bean || []))
            .catch(() => resolve([]))
    }
}
```

---

## 4. 两种加载模式详解

### 4.1 全量加载(默认,适合 < 1000 行)

```js
// public/moduleJs/{mdCode}/list.js
export default {
    rowKey: 'id',
    // tree-prop: 'children'  // 默认值,可省略
    defaultExpandAll: true,  // 默认展开所有(可选)
    // 或 expandRowKeys: [1, 2],  // 手动控制展开哪些行
}
```

**特点**:
- 接口一次性返回所有嵌套数据
- `default-expand-all: true` 时首屏所有行展开
- 数据量大时**首屏慢**(要渲染所有节点)
- 适合:层级浅(< 3 层)、数据少(< 1000 行)、需要全局浏览

### 4.2 懒加载(适合 > 1000 行 / 层级深)

```js
// public/moduleJs/{mdCode}/list.js
export default {
    rowKey: 'id',
    lazy: true,
    load: function (row, treeNode, resolve) {
        // this 是 moduleList 实例(关键!不是 mList)
        // 后端只返回当前行的直接子节点(不再嵌套)
        this.post(`${this.BASEURL}/xxx/listChildren.do`, { parentId: row.id })
            .then(res => resolve(res.bean || []))
            .catch(() => resolve([]))
    }
}
```

**接口要求**:
```json
// /xxx/listChildren.do?parentId=1
{
    "hasOk": true,
    "bean": [
        { "id": 2, "name": "研发部" },  // 不含 children 字段
        { "id": 3, "name": "市场部" }
    ]
}
```

**特点**:
- 接口只返回当前行的**直接子节点**(不含 grandchildren)
- 用户点开行才发请求,首屏快
- `resolve` 是异步回调,接 array
- 适合:数据量大、层级深(> 3 层)、结构需要边用边加载

**易错点**:
- ⚠️ `load` 函数里的 `this` 是 **moduleList 实例**(不是 mList),详见 §6
- 子节点数据**不要**含 `children` 字段(否则 el-table 会以为有子节点,继续显示展开箭头,点了又请求)
- 如果某些行没有子节点(叶子),后端要返回 `hasChildren: false` 或返回空数组(用 `resolve([])` 让 el-table 不显示展开箭头)

---

## 5. 完整实战:3 个典型场景

### 5.1 场景 1:菜单管理树(全量加载)

```js
// public/moduleJs/frame/system/menu_list.js
export default {
    rowKey: 'id',
    // tree-prop: 'children',  // 默认值,可省略
    defaultExpandAll: false,  // 默认折叠,用户按需展开
    
    // 常规列表配置不变
    renderField: {
        name: {
            formatter (val, row) {
                return <span><i class={row.icon}></i> {val}</span>
            }
        }
    }
}
```

**后端返回**:
```json
[
    {
        "id": 1, "name": "系统管理",
        "children": [
            { "id": 11, "name": "用户管理", "children": [] },
            { "id": 12, "name": "角色管理", "children": [...] }
        ]
    }
]
```

### 5.2 场景 2:评论楼中楼(懒加载 + 排序)

```js
// public/moduleJs/business/comment_list.js
export default {
    rowKey: 'id',
    lazy: true,
    load: function (row, treeNode, resolve) {
        // this 是 moduleList 实例
        let url = `${this.BASEURL}/comment/children.do`
        let params = { parentId: row.id }
        this.post(url, params).then(res => {
            // 按时间倒序
            let list = (res.bean || []).sort((a, b) => b.createTime - a.createTime)
            resolve(list)
        }).catch(() => resolve([]))
    },
    
    // 渲染回复按钮(操作列)
    renderField: {
        // ...
    },
    buttons: [
        {
            id: 'reply',
            name: '回复',
            click: function (btnObj) {
                let row = this.getSelection()?.[0]
                if (!row) return this.$message.warning('请选择一行')
                this.pushPage({
                    path: `/module/stander/edit/comment/add`,
                    query: { addFormData: encodeURIComponent(JSON.stringify({ parentId: row.id })) }
                })
            }
        }
    ]
}
```

### 5.3 场景 3:扁平数据自动转树(用 afterListJSON)

```js
// public/moduleJs/frame/org/dept_list.js
export default {
    rowKey: 'id',
    afterListJSON (list) {
        // list: 扁平数据 [{id, parentId, name}, ...]
        return buildTree(list, 0)
    }
}

// 辅助函数(可以放在公共 utils 或同文件内)
function buildTree (list, parentId) {
    return list
        .filter(item => item.parentId === parentId)
        .map(item => ({
            ...item,
            children: buildTree(list, item.id)
        }))
}
```

---

## 6. `this` 指向速查(树形表格 customSetting)

| 上下文 | `this` 指向 | 备注 |
|--------|-------------|------|
| `lazy` + `load` 函数 | **moduleList 实例** | 与 `buttons.click` 一致;可用 `this.post` / `this.BASEURL` / `this.mdCode` |
| `afterListJSON`(转树场景) | **mList 实例** | 与其他 `afterListJSON` 一致;`this.temp_data` 是处理后的数据 |
| `renderField.*`(节点列渲染) | **mList 实例** | 同普通列表 |
| `buttons[].click`(操作列按钮) | **moduleList 实例** | 同普通列表 |
| `default-expand-all` / `expand-row-keys` / `row-key` / `tree-prop` | 无 this(纯配置) | 直接写字面量 |

> 详见 [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)。

---

## 7. 与"树模型"的对比(避免混淆)

| 维度 | **树形表格**(本 skill) | **树模型**(左树+右表/右表单) |
|------|----------------------|--------------------------|
| 布局 | **单列表**(行可展开) | **左树 + 右侧列表/表单** |
| 入口路由 | `/module/stander/list/...` | `/module/tree/list/...` 或 `/module/tree/edit/...` |
| 入口组件 | `ModuleList` / `ModuleListCode` | `ModuleListTree` / `ModuleEditTree` |
| customSetting 文件 | `public/moduleJs/{mdCode}/list.js` | 同上(同一个 JS 文件) |
| 数据来源 | 单一接口返回整棵树(或懒加载) | 树节点走 `Tree_Node_List_URL`,列表走 `Tree_List_URL`(或各自自定义) |
| 父节点选中交互 | **无**(只是行展开) | **有**(点击左侧树节点联动右侧列表) |
| 配置 key | 直接写 el-table 原生属性(`tree-prop`/`lazy`/`load` 等) | 走 [frontend-module-tree-list §2 树专属 3 个 key](frontend-module-tree-list/SKILL.md#2-树专属-3-个key树模型区别于普通列表的全部差异) |
| 适用场景 | 列表本身是层级数据(菜单/评论/楼中楼/扁平组织) | 左侧分类 + 右侧数据(部门下员工、分类下商品) |

**判断口诀**:
- **树形表格**:用户说"列表行展开"、"评论楼中楼"、"嵌套数据" → 用本 skill
- **树模型**:用户说"左树右表"、"分类联动"、"点部门看员工" → 用 `frontend-module-tree-list`

---

## 8. 关键事实

### 8.1 透传机制:不是新 key,是"漏"过去

```js
// ModuleList.updateCustomSetting()
let {
    buttons, renderField, afterListJSON, ...  // 解构已知 key
    ...elseTableAttrs  // 其余所有 key 都"漏"到这里
} = customSetting || {}
this.elseTableAttrs = elseTableAttrs

// ModuleList.tableAttrs computed
return {
    // 已知属性...
    ...this.elseTableAttrs  // 末尾展开
}
```

> ⚠️ **风险**:`...elseTableAttrs` 是"宽容透传",会**接收任何 key**,包括拼错的 key(`treeprop` 而非 `tree-prop`)、与框架内部 prop 同名的 key(如 `data` / `params` / `url` 等)。拼错时不会报错,只是不生效。
> **建议**:配完去浏览器 console 看 el-table DOM 上是否真的带上了这些属性。

### 8.2 rowKey 不配会渲染异常

```js
// ❌ 漏了 rowKey
export default {
    treeProp: 'children'
}
// 现象:折叠展开状态错乱、行选中错乱、树节点更新丢状态

// ✅ 必须配
export default {
    treeProp: 'children',
    rowKey: 'id'  // 或业务实际唯一字段名
}
```

### 8.3 懒加载子节点数据不要含 children

```js
// ❌ 后端返回
[
    { "id": 2, "name": "研发部", "children": [] }  // 空数组也算!
]

// ✅ 后端应该返回
[
    { "id": 2, "name": "研发部" }  // 完全不带 children 字段
]
```

> 如果 `load` 返回的数据含 `children: []`(空数组),el-table 仍会显示展开箭头,用户点开又请求一次(浪费)。
> 业务方可以在 `load` 里 `delete item.children`(不太优雅)或后端干脆不返回该字段。

### 8.4 tree-prop 默认就是 'children'

只有当后端字段名不是 `children` 时才需要写:
```js
// 后端字段叫 "subItems"
export default {
    treeProp: 'subItems',
    rowKey: 'id'
}
```

### 8.5 行内操作列可能与树形展开冲突

el-table 树形表格默认**点击整行**(非操作列区域)会展开/折叠子节点。
如果操作列的按钮只想"展开行而不展开子节点",需要 `event.stopPropagation()`:

```js
renderField: {
    expandBtn: {
        render (h, context) {
            return (
                <el-button
                    onClick={(e) => {
                        e.stopPropagation()  // 阻止行展开
                        // 自定义展开
                    }}>
                    自定义展开
                </el-button>
            )
        }
    }
}
```

### 8.6 树形表格 + 分页

树形表格 + `isUsePagination: true` 时,**分页只对根节点生效**(el-table 行为),子节点都算"展开的内容",不占分页。
如果业务方想"分页 + 树形",要么:
- 关掉分页(`isUsePagination: false`),全量加载
- 改用"懒加载 + 全部根节点一次性返回"模式
- 或者接受"分页只对根节点生效"的行为(用户看到的子节点可能跨页)

---

## 9. 常见问题

| 问题 | 现象 | 解决 |
|------|------|------|
| 配了 `tree-prop` 没生效 | console 看 el-table 上没这属性 | 检查拼写(连字符 vs 驼峰);框架透传不校验拼写 |
| 行展开状态错乱 | 没配 `row-key` | 必须配 `row-key`,值是行数据的唯一字段名(通常是 `id`) |
| 懒加载每次都重新请求 | `load` 返回的数据含 `children: []` | 后端/前端去掉 `children` 字段 |
| `lazy: true` 后默认所有行展开 | — | 懒加载模式下 `default-expand-all` 行为可能异常;手动用 `expand-row-keys` 控制 |
| 树形表格 + 行按钮点击,行也展开/收起了 | 没阻止事件冒泡 | 在按钮的 `nativeOn-click` 加 `e.stopPropagation()` |
| 业务方在 `customSetting` 里写了 `data: [...]` | 不走请求,直接用这数据 | 框架会识别 `data` 字段(见 [ModuleList:456-458](../../../src/components/frame/Module/ModuleList/index.vue#L456-L458)),可用于静态数据演示 |
| 树形表格的导出 | — | 导出的是"扁平"还是"嵌套"?默认是扁平(所有可见行);有需要用 `exportProps` 自定义 |
| 树形表格 + 搜索栏 | 只搜得到根节点匹配的 | 搜索是按 root 节点过滤的,展开后的子节点不一定匹配;需要业务方自定义 `paramsBeforeRequest` + 后端配合 |
| 配了 `tree-prop` 但 el-table 上没展开箭头 | 数据没 `children` 字段/字段名错 | 检查 Network 返回数据是否真的有 children(且是非空数组) |
| 想给树节点加复选框 | — | 用 el-table 的 `selection` 列 + `selectable` 函数(根据 `row.hasChildren` 决定) |

---

## 10. 验证 checklist

写完一个树形表格 customSetting,过一遍:

- [ ] **菜单 URL** 用的是 `/module/stander/list/...`(不是 `/module/tree/list/...`,那个是树模型)
- [ ] 后端 `customJs` 指向 `public/moduleJs/{mdCode}/list.js`
- [ ] Network 接口返回数据是**嵌套**结构(全量模式)或**扁平 + parentId**(需 `afterListJSON` 转树)
- [ ] `row-key` 已配(值是行数据的唯一字段名)
- [ ] 浏览器 console 看 `<el-table>` DOM 上确实有 `tree-prop` 属性(说明透传生效)
- [ ] 行展开/折叠按钮能正常点击
- [ ] 选中状态不丢(不会一展开就取消选中)
- [ ] 操作列按钮点了**不会**顺手展开行(若不需要)
- [ ] 懒加载模式:`load` 函数里 `this.post` 能正确发请求,`resolve()` 接数组
- [ ] `load` 返回的数据**不含 children 字段**(避免重复请求)
- [ ] 搜索栏、按钮、分页、导出等**与普通列表写法一致**
- [ ] console 无 error / 无 warning(el-table 树形常见 warning 是没配 row-key)

---

## 11. 完整可复制最小骨架

### 11.1 全量加载(最简)

```js
// public/moduleJs/{mdCode}/list.js
export default {
    // 树形表格核心配置
    rowKey: 'id',
    // tree-prop: 'children',  // 默认值,可省略
    
    // 可选:默认展开所有
    // defaultExpandAll: true,
    
    // 其他普通列表 customSetting 写法不变
    renderField: { /* ... */ },
    buttons: [ /* ... */ ],
    afterListJSON (list) { return list }
}
```

### 11.2 懒加载(标准)

```js
// public/moduleJs/{mdCode}/list.js
export default {
    rowKey: 'id',
    lazy: true,
    load: function (row, treeNode, resolve) {
        // this 是 moduleList 实例
        this.post(`${this.BASEURL}/xxx/listChildren.do`, { parentId: row.id })
            .then(res => resolve(res.bean || []))
            .catch(() => resolve([]))
    }
}
```

### 11.3 扁平 parentId 转树

```js
// public/moduleJs/{mdCode}/list.js
export default {
    rowKey: 'id',
    afterListJSON (list) {
        // list: [{ id, parentId, name }, ...]
        // 转成 [{ id, parentId, name, children: [...] }, ...]
        const buildTree = (items, parentId) =>
            items
                .filter(item => item.parentId === parentId)
                .map(item => ({
                    ...item,
                    children: buildTree(items, item.id)
                }))
        return buildTree(list, 0)
    }
}
```

---

## 12. 下一步去哪

- **左树+右表/右表单**(`frontend-module-tree-list` / `frontend-module-tree-edit`)—— 不同的场景
- **普通列表 customSetting 总览** → [frontend-module-list](frontend-module-list/SKILL.md)(40+ key)
- **首次接触 Module 平台** → [frontend-module-quickstart](../frontend-module-quickstart/SKILL.md)
- **el-table 树形原生文档** → Element UI 官方文档搜索 `el-table` 的 `tree-prop`/`lazy`/`load` 属性
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)