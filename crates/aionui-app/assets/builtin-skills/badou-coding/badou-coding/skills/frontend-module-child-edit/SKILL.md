---
name: frontend-module-child-edit
description: 八斗 Module 表单 customSetting — **关联子表**(嵌套模块)的展示风格、排版风格、容器布局、父子通信定制总览。当用户说"关联子表样式不对"、"子表铺满"、"主表与子表 Tab 切换"、"子表怎么横着排"、"子表用什么布局"、"childTab 配置"、"子表怎么拿主表数据"时触发。跳转到 5 个 sub skill(showStyle / 排版容器 / showType / 字段配置 / 父子通信)了解细节。
---

# Module 表单 — 关联子表(嵌套模块)展示与排版(总览)

> 本 skill 是**总览入口**,讲子表"怎么放"、"放成什么样"的**全局视角**。
> 具体细节跳到 5 个 sub skill:
>
> | 你想知道 | 跳到 |
> |---|---|
> | **`showType` 4 类渲染方式(编辑表单 / 列表 / 查看表单 / 自定义页面)+ pageUrl 挂载机制** | [sub/show-type](sub/show-type/SKILL.md) |
> | **父子表通信**(子表拿主表数据 / 通知主表 / 自定义页面双向交互) | [sub/parent-child-communication](sub/parent-child-communication/SKILL.md) |
> | `showStyle` 3 种展示风格的细节、平级 Tab / 子 Tab / 顺序展示的区别 | [sub/show-style](sub/show-style/SKILL.md) |
> | 4 类排版容器(`mainDefault` / `mainTab` / `defaultB` / `linkTab` / `defaultC`)+ CSS 布局(`marB` / `defaultBg` / `h-auto` / `fullHeight`)+ `hasMuchPart` | [sub/layout-container](sub/layout-container/SKILL.md) |
> | childTab 12 项字段速查 + 5 种典型实战 + `afterModuleJSON` 改 childTab | [sub/child-tab-config](sub/child-tab-config/SKILL.md) |

---

## 0. 动手前先确认 JS 路径(必读)

子表相关配置**通常走后端模型设计器**(在 `sys_module_link` 模型里配),**一般不用 customSetting JS 写**——customSetting 里**几乎从不**直接动 childTab。

**进入前用 AskUserQuestion 确认 4 件事**:

1. **mdCode** 是哪个(主表的)
2. 是 **edit** 还是 **add** 还是 **view**
3. **JS 完整路径**(几乎都不需要碰)
4. 后端是否已配好 `sys_module_link` 的关联子表数据

> 业务方改子表展示风格的**主线在后端**:在"模型关联管理"里改每条 childTab 记录的 `showStyle` / `showType` / `tabName` / `relationEntityField` 等字段。

---

## 1. 一图看懂:子表在主表里"放哪儿"由谁决定

```
后端模型设计器(sys_module_link 表)配置每条关联
    ↓
接口返回到 module.childTab 数组
    ↓
前端 ModuleEdit/index.vue 用 3 个维度决定最终渲染
    ├─ 维度1:展示风格(showStyle) → 主表与子表 是 Tab 平级 / 主表+子表 / 按顺序排  → [sub/show-style](sub/show-style/SKILL.md)
    ├─ 维度2:排版容器(linkData)  → 解析成 5 类容器:mainDefault / mainTab / defaultB / linkTab / defaultC  → [sub/layout-container](sub/layout-container/SKILL.md)
    └─ 维度3:展示类型(showType)  → 子表渲染成什么:编辑表单 / 列表 / 查看表单 / 自定义页面  → [sub/show-type](sub/show-type/SKILL.md)
```

> 整个流程全部在 `ModuleEdit/index.vue` 内,**业务方写 customSetting 几乎不需要碰这些**——但**理解清楚才知道"为什么我的页面长这样"**。

---

## 2. 关键事实速查(必背)

### 2.1 三个维度的默认值与可选值

| 维度 | 字段 | 默认值 | 可选值 |
|---|---|---|---|
| 展示风格 | `showStyle` | `1`(平级 Tab) | `1`=平级 Tab / `2`=子 Tab / `3`=顺序展示 |
| 展示类型 | `showType` | `1`(列表) | `0`=编辑表单 / `1`=列表 / `2`=查看表单 / `4`=自定义页面(⚠️ 没有 3) |
| 是否展示 | `showTab` | `1` | `'0'`=隐藏 / `'1'`=展示 |

### 2.2 三个核心字段的关系

| 字段 | 含义 | 必填 |
|---|---|---|
| `module` | 子模块 mdCode | ✅ |
| `relationEntityField` | 主表里"指向子表"的字段名(框架会自动取其值过滤子表数据) | ✅ |
| `showTab` | 是否展示 | ✅ |
| `tabName` | 所属 Tab 名称(同名 + 同 showStyle 合并) | ❌ |
| `entityField` | 主表里作为关联值的字段名(默认 = relationEntityField) | ❌ |

完整字段速查 → [sub/child-tab-config](sub/child-tab-config/SKILL.md)

### 2.3 5 类排版容器(从上往下)

```
┌────────────────────────────────────────┐
│ mainDefault = [主表, 关1, 关2, ...]    │  ← 主表+顺序展示的关联
├────────────────────────────────────────┤
│ mainTab = [[主表, 关1], [关2], ...]    │  ← 平级 Tab 结构
├────────────────────────────────────────┤
│ defaultB = [关1, 关2, ...]             │  ← 平级 Tab 之后、按顺序展示
├────────────────────────────────────────┤
│ linkTab = [[关1, 关2], [关3], ...]     │  ← 主表下方的子 Tab 组
├────────────────────────────────────────┤
│ defaultC = [关1, 关2, ...]             │  ← 子 Tab 之后、按顺序展示
└────────────────────────────────────────┘
```

完整容器说明 + CSS 类映射 → [sub/layout-container](sub/layout-container/SKILL.md)

### 2.4 5 个核心 CSS 类

| 类名 | 作用 | 典型位置 |
|---|---|---|
| `marB` | 底部 margin = `$space` | 多模块**块与块之间** |
| `defaultBg` | `background: var(--content-bg)` | 所有独立模块、Tab 容器 |
| `h-auto` | `height: auto !important` | 顺序展示的模块 |
| `h-per-100` | `height: 100%` | 平级 Tab 下的模块(铺满) |
| `fullHeight`(prop) | 内部加 `h-per-100` | 当 tab 下只有 1 个模块时 |

### 2.5 hasMuchPart 计算规则

```js
hasMuchPart = !this._showLinkData.every(i => !i.showStyle || i.showStyle === 1)
```

| 场景 | hasMuchPart | 行为 |
|---|---|---|
| 所有关联都是平级 Tab(都=1 或空) | `false` | 子模块**铺满整屏** |
| 至少一个 showStyle=2 或 =3 | `true` | 整页**滚动**,子模块高度 `auto` |

### 2.6 关键设计事实

- **`addFormData` 自动注入**:ChildModuleEdit 自动生成 `{[relationEntityField]: 主表关联字段值}`,实现"新增子表数据自动带上主表 id"
- **`elseAttrs` 注入**:传给子模块,让子模块能取到主表字段列表、主表作用域、关联字段值等
- **`isInLink=true`**:子模块按钮事件过滤,只显示允许在子模块出现的按钮
- **主表始终在 mainDefault[0]**:即使存在平级 Tab,主表也会同时作为 `mainTab[0]` 的内容
- **tabName 合并**:同 tabName + 同 showStyle 的子模块合并到同一 Tab 内
- **子表标题自动隐藏**:tab 下只有 1 个模块且 `title === tabName` 时,自动隐藏模块标题

### 2.7 特殊场景:`showType=4` 自定义页面速查

> 当子表是**自定义 Vue 组件**(而非表单/列表/查看)时,用 `showType=4`。完整文档 → [sub/show-type](sub/show-type/SKILL.md),实战案例 → [sub/child-tab-config](sub/child-tab-config/SKILL.md)。

```js
// 后端 childTab 配置
{
    module: 'business_a_item',
    title: '自定义业务',
    showTab: '1',
    showStyle: 1,                    // 排版风格与其他子表一致
    showType: 4,                     // ← 关键:自定义页面
    pageUrl: 'business/customChildPage',  // ← 关键:指向 src/views/{pageUrl}.vue
    relationEntityField: 'parentId'
}
```

| 必须做的 | 说明 |
|---|---|
| ✅ 后端配 `showType=4` + `pageUrl` | `pageUrl` 路径**省略 `@/views/` 前缀和 `.vue` 后缀** |
| ✅ 在 `src/views/{pageUrl}.vue` 创建组件 | `export default` 必须是 Vue 组件 |
| ✅ 组件接收 props:`mainFieldList` / `mainScope` / `mainMdCode` / `id` / `scope` / `getExtendScope` | 框架**自动注入** |
| ✅ 组件定义 `beforeDestroy` 方法 | 框架会**手动调用**做清理(若无需清理可不写) |

| 不要做的 | 原因 |
|---|---|
| ❌ `pageUrl` 写完整路径如 `@/views/business/customChildPage.vue` | 框架内部用 `require(\`@/views/${pageUrl}\`)` 拼接,前缀后缀都不能加 |
| ❌ 子模块用 `isInLink` 之外的方式访问主表 | 走 `props.mainScope` 或 `this.$attrs.elseAttrs.mainScope`(子模块的 this) |

**完整 Vue 文件示例**(含与主表通信):

```vue
<!-- src/views/business/customChildPage.vue -->
<template>
    <div class="custom-child-page">
        <h3>主表 id: {{ id }}</h3>
        <el-button @click="callMainMethod">调用主表方法</el-button>
    </div>
</template>

<script>
export default {
    props: {
        mainFieldList: Array,    // 主表字段列表
        mainScope: Object,       // 主表 ModuleEdit 实例(可调主表方法)
        mainMdCode: String,
        id: String,              // 主表记录 id
        scope: Object,           // ChildModuleEdit 实例
        getExtendScope: Function
    },
    methods: {
        callMainMethod () {
            this.mainScope?.someMethod?.()
        }
    },
    mounted () {
        // 把当前作用域暴露给父组件(用于后续通信)
        this.getExtendScope?.(this)
    },
    beforeDestroy () {
        // 清理逻辑(EventBus 监听、定时器等)
        // 框架在 ChildModuleEdit.beforeDestroy 中会自动调用
    }
}
</script>
```

---

## 3. this 指向速查

| 场景 | this 指向 | 备注 |
|---|---|---|
| `ModuleEdit/index.vue` mounted 中的所有 customSetting | **moduleEdit 实例** | `this.detailId` / `this.formData` / `this.fieldList` 都有 |
| `afterModuleJSON` / `dataUrl` / `valuePath` / `paramsBeforeRequest` / `afterEditJSON` | **moduleEditCode** | 改 module 配置影响 childTab |
| `buttons` / `saveUrl` / `beforeModuleInitRender` | **moduleEdit** | 与子表无关,改的是主表按钮 |
| **子模块自己的** `valueChange` / `beforeRender` / `buttons` 等 | **子模块的 moduleForm / mForm** | 与子表本身无关(走子模块 customSetting JS) |

> 详细 this 速查 → [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)

---

## 4. 常见问题

| 问题 | 现象 | 原因 / 解决 |
|---|---|---|
| 子表没显示 | 页面只有主表 | 后端 `showTab` 没配成 `'1'`,或子模块模型编码(`module`)写错 |
| 子表请求列表返回空 | 列表没数据 | `relationEntityField` 配错,**主表里没有该字段**会发警告 `关联字段X在主表中找不到` |
| Tab 头出现但内容空 | tab 配置了但没渲染 | 后端 `module` 字段写错(子模块 mdCode 不存在) |
| 子表 Tab 顺序不对 | Tab 顺序与预期不符 | Tab 顺序由**后端 sort 字段**决定,前端无法控制 |
| 想让子模块按钮也出现在主模块 | 主模块按钮区没该按钮 | `isInLink` 过滤了——子模块的按钮**只在子模块内可见**,不会上升到主模块 |
| 改了 `showStyle=3` 但页面还是有 Tab | 配置没生效 | 检查 `childTab` 里是否同时存在 `showStyle=1` 的项——只要有 1 个平级 Tab,整页就有 Tab 头 |
| `showType=4` 没渲染 | 自定义页面没出来 | 检查 `pageUrl` 是否正确(指向 `src/views/{pageUrl}.vue`),且 export default 必须是 Vue 组件 |
| 想在主表和子表之间加自定义内容 | 主表下、子表上有"空隙" | 不能在框架内置结构中插入,**只能**通过 `contentRender` 改主表自身;或在主模块后追加一个 `showStyle=3 + showType=0` 的"伪装子表" |
| 同一 tabName 但 showStyle 不同 | 子表没合并到同一 Tab | `addTabItem` 同时校验 `tabName` 和 `showStyle`,两者必须都相同才会合并 |
| 改了 childTab 配置没生效 | 页面还是旧的样子 | 配置**通常走后端**——后端保存后**刷新页面**才会生效 |

完整 FAQ → [sub/child-tab-config](sub/child-tab-config/SKILL.md)

---

## 5. 验证 checklist

写完 / 改完一个含子表的表单,过一遍:

- [ ] 主表 + 所有配置的子表都在页面正确显示
- [ ] `showStyle` 决定的排版结构符合预期(Tab 平级 / 子 Tab / 顺序展示)
- [ ] `tabName` 相同的子表合并到同一 Tab 内
- [ ] 子表的标题在 `tabName === 子表标题` 时自动隐藏
- [ ] 子表列表的过滤条件(Network 请求参数)含 `relationEntityField` = 主表关联字段值
- [ ] 新增子表数据时,`addFormData` 自动带上主表 id
- [ ] `isInLink=true` 时,子模块只显示允许的按钮(`isInLink` 标记的)
- [ ] `hasMuchPart=false` 时子表铺满,`true` 时整页滚动
- [ ] 修改 `showStyle` / `tabName` 后,刷新页面立即生效
- [ ] console 无 `关联字段X在主表中找不到` 警告

---

## 6. 下一步去哪

### 子表相关 sub skill

- **父子表双向通信**(子表拿主表数据 / 通知主表 / 自定义页面交互)→ [sub/parent-child-communication/SKILL.md](sub/parent-child-communication/SKILL.md)
- **showStyle 展示风格** → [sub/show-style/SKILL.md](sub/show-style/SKILL.md)
- **排版容器 + CSS 布局** → [sub/layout-container/SKILL.md](sub/layout-container/SKILL.md)
- **showType 渲染方式** → [sub/show-type/SKILL.md](sub/show-type/SKILL.md)
- **childTab 字段配置 + 实战** → [sub/child-tab-config/SKILL.md](sub/child-tab-config/SKILL.md)

### 其他相关 skill

- 子模块**自己的** customSetting → [frontend-module-edit](../frontend-module-edit/SKILL.md)
- Tab 切换拦截 / `scopeSave` / `isChangeInfo` → [module-edit-tab-nav](../frontend-module-edit/sub/tab-nav/SKILL.md)
- 子表渲染时的字段联动 → [module-edit-fields](../frontend-module-edit/sub/fields/SKILL.md)
- 树模型编辑页 → [frontend-module-tree-edit](../frontend-module-tree-edit/SKILL.md)
- 首次接触 Module 平台 → [frontend-module-quickstart](../frontend-module-quickstart/SKILL.md)
- 页面出问题 → [frontend-module-page-debug](../frontend-module-page-debug/SKILL.md)
- this 指向速查 → [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)