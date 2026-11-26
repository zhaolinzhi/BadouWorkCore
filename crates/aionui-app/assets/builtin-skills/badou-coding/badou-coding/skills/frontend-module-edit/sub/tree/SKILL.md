---
name: frontend-module-edit-tree
description: 八斗 Module 树型列表/表单 customSetting — 树节点接口 + 节点参数注入 + 树型表单提交参数。当用户说"树型列表"、"树节点点击"、"树型表单"、"左侧是树右侧是表单"、"树节点数据源"时触发。覆盖 treeAjaxConfig / defaultParams / addFormData 3 个 key。
---

# Module 表单 — 树型列表/表单

> 树型列表/表单是八斗 Module 的**特殊页面布局**(左侧树 + 右侧表单/列表),有 3 个专属 customSetting key。**先看 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/list.js`(树型列表的 list)和 `edit.js`(树型列表下的表单)里。

**进入前必读**:mdCode + list/edit + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-list §0](../../../frontend-module-list/SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 3 个 key

| 位置 | key | 类型 | 用途 | 频次 |
|------|------|------|------|------|
| 树型列表 | `treeAjaxConfig` | `Function` | 树节点数据接口 | ⭐⭐⭐ |
| 树型列表 | `defaultParams` | `Function` | 列表请求参数(注入树节点) | ⭐⭐⭐ |
| 树型表单 | `addFormData` | `Function` | 表单提交参数(注入树节点) | ⭐⭐⭐ |

> **重要**:树型列表/表单**拥有普通列表/表单的所有 customSetting key**,本 skill 只讲**树型专属的 3 个**。

---

## 2. `treeAjaxConfig`(树节点数据接口)

**位置**:`list.js`(树型列表的 customSetting)

**签名**:`treeAjaxConfig(nodeParentId, data, node) → { url, params }`

**this 指向**:**moduleList 实例**

**用途**:告诉框架"点开某个树节点时,加载它子节点的接口是啥"。

**必须 return**:`{ url, params }` 对象

```js
export default {
    treeAjaxConfig: function (nodeParentId, data, node) {
        // 第一次展开(根节点)
        if (!nodeParentId) {
            return {
                url: `${this.BASEURL}/org/department/departmenttree/tree.do`,
                params: {}
            }
        }
        // 子节点展开
        return {
            url: `${this.BASEURL}/org/department/departmenttree/ptree.do`,
            params: { pid: nodeParentId }
        }
    }
}
```

> ⚠️ **必须 return** `{ url, params }`,否则树不展开。

---

## 3. `defaultParams`(列表请求参数 — 注入当前树节点)

**位置**:`list.js`(树型列表的 customSetting)

**签名**:`defaultParams(params, data, node, nodeComponent) → 新参数对象`

**this 指向**:**moduleList 实例**

**用途**:把当前点击的树节点数据**注入到列表请求参数**,这样列表就能根据"当前选中的树节点"过滤。

```js
export default {
    /**
     * @param {Object} params 已有参数对象
     * @param {Object} data 当前树节点数据
     * @param {Object} node 树节点对象
     * @param {Object} nodeComponent 节点实例
     */
    defaultParams: function (params, data, node, nodeComponent) {
        return {
            // 保留已有参数
            ...(params || {}),
            // 注入当前节点 id
            departmentId: data.id,
            // 节点其它字段也可
            // departmentName: data.name
        }
    }
}
```

> 实战:左侧是"部门树",右侧是"员工列表"。点哪个部门,列表就显示该部门的员工——`departmentId` 就是这个**过滤桥梁**。

---

## 4. `addFormData`(树型表单提交参数 — 注入当前树节点)

**位置**:`edit.js`(树型列表下的表单 customSetting)

**签名**:`addFormData(currentNodeData) → 新参数对象`

**this 指向**:**moduleEdit 实例**

**用途**:新增表单时,把当前树节点数据作为**表单的初始数据**一起提交。

```js
export default {
    /**
     * @param {Object} currentNodeData 当前所在树节点
     */
    addFormData: function (currentNodeData) {
        return {
            // 例子: textId, textName 会作为表单提交参数
            textId: currentNodeData.id,
            textName: currentNodeData.name,
            // 父节点 id
            parentId: currentNodeData.parentId
        }
    }
}
```

> 实战:左侧"部门树",点"研发部"节点 → 右侧"新增员工表单"自动带上 `deptId = 研发部.id` → 员工就归属研发部。

---

## 5. 关键事实

| 项 | 说明 |
|------|------|
| `treeAjaxConfig` 不 return | 树节点不展开(没有子节点数据) |
| `defaultParams` 不 return | 列表请求不会按树节点过滤 |
| `addFormData` 不 return | 表单不会自动带树节点数据 |
| 树型列表/表单 = 普通列表/表单 + 3 个 key | 普通 customSetting 都还能用 |
| `data.id` 来自哪里 | 后端树接口返回的字段(可能是 `id`/`value`/`key`) |
| `currentNodeData` 来自哪里 | `defaultParams` 里的 `data` 参数,同源 |

---

## 6. 完整实战:左侧部门树 + 右侧员工列表 + 新增员工表单

### 6.1 部门树列表(左侧) — `dept_mdCode/list.js`

```js
export default {
    // 1. 树节点接口
    treeAjaxConfig: function (nodeParentId) {
        if (!nodeParentId) {
            return {
                url: `${this.BASEURL}/org/department/tree.do`,
                params: {}
            }
        }
        return {
            url: `${this.BASEURL}/org/department/children.do`,
            params: { pid: nodeParentId }
        }
    },
    // 2. 列表请求时注入当前部门 id
    defaultParams: function (params, data) {
        return {
            ...(params || {}),
            departmentId: data?.id  // 当前选中的部门
        }
    }
}
```

### 6.2 员工列表(右侧) — `employee_mdCode/list.js`

```js
export default {
    // 普通列表 customSetting,无需改(由父页面注入 departmentId)
    renderField: { /* ... */ }
}
```

### 6.3 新增员工表单 — `employee_mdCode/edit.js`

```js
export default {
    // 1. 树型表单专属:自动带当前部门数据
    addFormData: function (currentNodeData) {
        return {
            departmentId: currentNodeData?.id,
            departmentName: currentNodeData?.name
        }
    },
    
    // 2. 普通表单 customSetting 仍可写
    afterEditJSON (formData) {
        return formData
    },
    beforeRender: function () {
        // 还能改字段属性
    }
}
```

---

## 7. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| 树不展开 | `treeAjaxConfig` 没 return | 必须 return `{ url, params }` |
| 列表与树节点不联动 | `defaultParams` 没 return | 必须 return 新参数对象(没变化也 return) |
| 新增员工没归属部门 | `addFormData` 没 return | 必须 return 含部门 id 的对象 |
| 树节点点开没数据 | `url` 错或 `params` 没传 `nodeParentId` | 仔细看后端树接口文档 |
| 改了 `defaultParams` 后列表空了 | 把 `params` 整个覆盖了 | 用 `...(params || {})` 保留旧参数,只追加 |
| 树节点 `data.id` 是 undefined | 字段名不是 `id` | 看后端树接口的返回结构,可能叫 `value`/`key` |

---

## 8. 下一步去哪

- **普通列表 customSetting** → [frontend-module-list](../../../frontend-module-list/SKILL.md)
- **普通表单 customSetting** → [frontend-module-edit](../../SKILL.md)
- **流程表单** → [module-edit-flow](../flow/SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
