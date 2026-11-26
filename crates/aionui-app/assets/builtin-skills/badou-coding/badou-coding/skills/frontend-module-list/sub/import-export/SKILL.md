---
name: frontend-module-list-import-export
description: 八斗 Module 列表 customSetting — 导入导出完整指南。当用户说"加导出按钮"、"加导入按钮"、"自定义导出 URL"、"导出禁用某些字段"、"导入额外参数"时触发。覆盖 exportUrl/exportTitle/exportProps/exportDefined + importUrl/importTemplateUrl/importTitle/importKey/importProps 共 9 个 key。
---

# Module 列表 — 导入导出

> 导入导出的 9 个 key(导出 4 件套 + 导入 5 件套)。**先看 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/list.js` 的 `export default` 对象里。

**进入前必读**:mdCode + list/edit + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 9 个 key

| key | 类型 | 用途 |
|------|------|------|
| `exportUrl` | `String\|Function` | 导出地址 |
| `exportTitle` | `String\|Function` | 导出标题 |
| `exportProps` | `Object\|Function` | 导出配置 |
| `exportDefined` | `String` | 导出禁用字段(逗号分隔) |
| `importUrl` | `String\|Function` | 导入地址 |
| `importTemplateUrl` | `String\|Function` | 导入模版下载地址 |
| `importTitle` | `String\|Function` | 导入标题 |
| `importKey` | `Object\|Function` | 导入额外参数 |
| `importProps` | `Object\|Function` | 导入配置 |

**来源**:`service/module.js` 第 677-813 行 `Get_Import_And_Export_Prop` 方法(被 `ExportData`/`ImportData` 调用)。

---

## 2. 导出 4 件套

### 2.1 `exportUrl`(导出地址)

**来源**:`Get_Import_And_Export_Prop` 第 736-744 行(`src/service/module.js:677`,由 `ExportData` 调用 `Get_Import_And_Export_Prop.call(this, 2, setting)`)

**this 指向**(函数形式):**`moduleList` 实例** —— 具体文件为 [src/components/frame/Module/ModuleList/index.vue](../../../../../src/components/frame/Module/ModuleList/index.vue)(组件 `name: 'module-list'`,可在 DevTools 用 `this.$options.name === 'module-list'` 验证)

```js
// 字符串
exportUrl: '/jdbc/common/xxx/export.do',

// 函数(常用,可以动态拼 mdCode)
exportUrl: function () {
    // this = moduleList 实例(ModuleList/index.vue)
    return `${this.BASEURL}/jdbc/common/basecommonlist/export.do?mdCode=${this.mdCode}`
}
```

**实战**(摘自 `public/moduleJs/business/text/wjx_form_list.js:2-5`):

```js
exportUrl: function () {
    return `${this.BASEURL}/jdbc/common/basecommonlist/export.do?mdCode=${this.mdCode}`
}
```

### 2.2 `exportTitle`(导出弹窗标题)

**this 指向**(函数形式):**moduleList 实例**

```js
exportTitle: function () {
    // this 指向 moduleList
    return `导出${this.name}数据`
}
```

### 2.3 `exportProps`(导出配置)

**this 指向**(函数形式):**moduleList 实例**

```js
exportProps: function (mdCode) {
    // this 指向 moduleList,mdCode 是当前模型编码
    return {
        // 传给导出弹窗的配置
        maxCount: 10000,         // 单次最多导出行数
        showSelect: true,        // 是否允许选列
        // ...其它 ExportDialog 组件的 props
    }
}
```

### 2.4 `exportDefined`(导出禁用字段)

**this 指向**:**无**(`String`,纯配置)

```js
// 逗号分隔,这些字段不出现在"可导出列"里(一般是 id、临时字段)
exportDefined: 'id,createTime,updateTime,_statusText'
```

---

## 3. 导入 5 件套

### 3.1 `importUrl`(导入地址)

**this 指向**(函数形式):**moduleList 实例**(由 `ImportData` 调用 `diy_importUrl.call(this)`)

```js
importUrl: '/jdbc/common/import.do',
// 或函数
importUrl: function () {
    // this 指向 moduleList 实例
    return `${this.BASEURL}/jdbc/common/import.do`
}
```

### 3.2 `importTemplateUrl`(模版下载地址)

**this 指向**(函数形式):**moduleList 实例**

```js
importTemplateUrl: '/template/user_info.xlsx',
// 或从后端动态获取
importTemplateUrl: function () {
    // this 指向 moduleList 实例
    return `/api/template/${this.mdCode}.xlsx`
}
```

### 3.3 `importTitle`(导入弹窗标题)

**this 指向**(函数形式):**moduleList 实例**

```js
importTitle: '导入用户信息',
// 或
importTitle: function () {
    // this 指向 moduleList 实例
    return `导入${this.name}`
}
```

### 3.4 `importKey`(导入额外参数)

**this 指向**(函数形式):**moduleList 实例**

```js
importKey: {
    extraFlag: 1,
    orgId: '固定值'
},
// 或函数
importKey: function () {
    // this 指向 moduleList 实例
    return {
        orgId: this.$store?.state?.user?.userInfo?.orgId
    }
}
```

### 3.5 `importProps`(导入配置)

**this 指向**(函数形式):**moduleList 实例**

```js
importProps: function (mdCode) {
    // this 指向 moduleList,mdCode 是当前模型编码
    return {
        maxSize: 10,  // MB
        // ...其它 ImportDialog 组件的 props
    }
}
```

---

## 4. 完整实战:导出 + 导入

```js
// public/moduleJs/order/list.js
export default {
    // 导出
    exportUrl: function () {
        return `${this.BASEURL}/jdbc/common/order/export.do`
    },
    exportTitle: function () {
        return `导出${this.name}数据`
    },
    exportProps: function () {
        return {
            maxCount: 50000,
            showSelect: true
        }
    },
    exportDefined: 'id,createTime,updateTime',
    
    // 导入
    importUrl: '/jdbc/common/order/import.do',
    importTemplateUrl: '/template/order.xlsx',
    importTitle: '导入订单',
    importKey: function () {
        return {
            orgId: this.$store?.state?.user?.userInfo?.orgId
        }
    },
    importProps: function () {
        return {
            maxSize: 20
        }
    }
}
```

---

## 5. 关键事实

> 💡 所有 9 个 key(函数式)的 this 指向都已经在每个 key 块顶部标了具体文件;**全量速查见 [frontend-module-this-reference](../../../../frontend-module-this-reference/SKILL.md) §4.1**(9 个 key 一行一个)。

### 5.1 其他要点(新 skill 里没有的)

| 项 | 说明 |
|------|------|
| 默认导出/导入按钮 | `id: 'export'` / `id: 'import'`,**在 `buttons` 里覆盖** |
| 已废弃的 `exportDialogTitle` | 等同 `exportTitle`,**别用** |
| **统一规律** | 所有函数形式 key 由 `ExportData` / `ImportData` 统一调用,`this` 一律是 moduleList 实例。要拿 `mdCode` / `BASEURL` / `$store`,函数内直接 `this.xxx` 即可(不要 `import store from '@/store'`,除非在 `createFun` / `createListFun` 这种 this 不是 moduleList 的场景) |

---

## 6. 与 `buttons` 的关系

导入导出**默认就有按钮**(在 `BtnBaseFun/list.js` 里),但通过 `customSetting` 可:
- **改默认行为**:`buttons: [{ id: 'export', click: ... }]`
- **隐藏默认按钮**:`buttons: [{ id: 'export', isHide: true }]`
- **完全自己写**:`buttons: [{ id: 'export', name: '我的导出', click: ... }]`

详见 [buttons §2](../buttons/SKILL.md#2-buttons-顶部行按钮)。

---

## 7. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| 导出按钮点了没反应 | 后端没配 exportUrl | `exportUrl` 必须配(默认是空) |
| 导出列里没看到想要的字段 | 用了 `exportDefined` 误伤了 | 检查 `exportDefined` 是不是把那个字段加进去了 |
| 导入模版下载不下来 | `importTemplateUrl` 路径错 | 浏览器直接访问这个 URL 看 404 还是 200 |
| 导入时缺参数 | `importKey` 没传业务参数 | 用函数形式,从 store 取值 |
| 写了 `exportDialogTitle` | 已废弃,可能不生效 | 改用 `exportTitle` |

---

## 8. 下一步去哪

- **列渲染** → `module-list-render-field`
- **按钮** → `module-list-buttons`
- **搜索栏交互** → `module-list-search`
- **请求/数据流** → `module-list-data-flow`
- **表格外观** → `module-list-table-look`
- **回到总览** → `frontend-module-list`
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
