---
name: frontend-module-list-module-config-mutation
description: 八斗 Module 列表 customSetting — **模型配置变更层**(改 fieldList / searchCondition / selectorData / moduleButtons / dic / childTab 等)。当用户说"改模块配置"、"动态加列"、"按角色显隐列"、"按角色显隐搜索项"、"动态加搜索项"、"改搜索项默认值"、"改搜索项可选项"、"按角色隐藏顶部按钮"、"改字典"、"改模块名" 时触发。覆盖 afterModuleJSON 1 个 key(但能改的东西很多)。
---

# Module 列表 — 模型配置变更层

> 列表"模型配置加载完后的所有修改"——改列、改搜索项、改按钮、改字典、改模块名。本 skill 是 [data-flow index](../data-flow/SKILL.md) 的子章节。

> 📌 涉及的文件落点:**动手前先确认 JS 路径**(必读) → 详见 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 1 个 key + 它能改的所有东西

| key | 用途 | 频次 | 触发时机 |
|------|------|------|------|
| `afterModuleJSON` | 模型配置加载后,改任何字段 | ⭐⭐⭐⭐ | 模型加载**后**(`loadListCfg` 接口返回后) |

> ⚠️ 这一个 key 可以改十多种东西——这是本 skill 篇幅最大的原因:**它的作用域覆盖整个 model 配置对象**。

---

## 2. `afterModuleJSON` ⭐⭐⭐⭐(模型配置加载后)

**来源**:`ModuleListCode.vue` 第 117-119 行(**注意:在入口层,不在 ModuleList/index.vue**)

**签名**:`afterModuleJSON(module)` → **必须 return** module 对象

**this 指向**:**moduleListCode 实例**(可用 `this.BASEURL` / `this.mdCode` / `this.$store`)

### 2.1 module 对象从哪儿来

`afterModuleJSON(module)` 拿到的 `module`,就是 `src/js/ModuleUtils.js:78-132` 的 `listModuleCfg(mdCode)` 返回的对象。流程如下:

```
loadListCfg(mdCode)               ← 后端接口,返回 _module(所有字段是字符串)
    ↓
module = {
    ..._module,                  ← 展开 _module 所有原始字段(字符串)
    id: _module.moduleId,        ← 归一化字段 ↓
    name: _module.moduleName,
    mdCode: _module.module,
    fieldList: Str_To_Obj(_module.moduleDisplay),       ← 数组
    allFieldList: Str_To_Obj(_module.moduleAllFields),  ← 数组
    searchCondition: Str_To_Obj(_module.searchCondition), ← 数组
    selectorData: Str_To_Obj(_module.selectorData),     ← 数组
    customJs: _module.listJs,
    customSetting: jsObj.default                       ← require 加载后的 customSetting
}
    ↓
afterModuleJSON(module)          ← 在这里改 module 的字段
    ↓ (必须 return)
this.module = result             ← ModuleListCode 拿这个往下传
```

> 💡 **关键事实**:同名字段**数组会覆盖字符串**——`..._module` 先把字符串版 `searchCondition` 塞进 module,然后下一行 `searchCondition: Str_To_Obj(...)` 又用**数组版**覆盖了它。所以 `module.searchCondition` 是**数组**(可 `filter`,`push` 仅作为备用方案,详见 [search 子 skill 关键事实小节](../search/SKILL.md)),而 `module.moduleDisplay` 还是**字符串**(没被覆盖,不用管)。

### 2.2 完整 module 数据示例(以商品列表为例)

> 业务方拿 `loadListCfg` 接口返回的 JSON 对照下面看——**原 JSON 字段就是字符串,转数组后才是 afterModuleJSON 能改的对象**。

```json
// loadListCfg 接口返回的原始数据(关键字段):
{
    "moduleId": "4baf6177...",
    "moduleName": "商品",
    "module": "test_goods",                                    // ← mdCode
    "moduleDisplay": "[{\"display\":\"商品名称\",\"name\":\"name\"},...]",  // ← 字符串,转数组后是 fieldList
    "moduleAllFields": "[{\"display\":\"商品主键\",\"name\":\"id\",\"isHide\":true},...]",
    "searchCondition": "[{\"name\":\"商品名称\",\"id\":\"name\"},...]",   // ← 字符串,转数组后是 searchCondition
    "selectorData": "[{\"name\":\"商品名称\",\"id\":\"name\",\"selectType\":1},...]",
    "moduleButtons": [{"code":"export","name":"导出",...}, ...],
    "dic": null,
    "formOption": null,
    "childTab": [],
    "listJs": "/business/text/wjx_goods_list.js"
}
```

转成 `listModuleCfg` 输出后,`afterModuleJSON(module)` 拿到的对象大致为:

```js
module = {
    // ── 后端原始字段(字符串,afterModuleJSON 通常不动)──
    moduleDisplay: '[{"display":"商品名称","name":"name"},...]',
    moduleAllFields: '[{"display":"商品主键","name":"id","isHide":true},...]',
    searchCondition: '[{"name":"商品名称","id":"name"},...]',  // ← 字符串(被覆盖前)
    selectorData: '[{"name":"商品名称","id":"name","selectType":1},...]',
    moduleButtons: [...],
    dic: null,
    formOption: null,
    childTab: [],
    listJs: '/business/text/wjx_goods_list.js',
    // ...其他后端字段(moduleId / moduleName / module 等)

    // ── 归一化后的字段(数组,afterModuleJSON 主要改这些)──
    id: '4baf6177...',                         // = moduleId
    name: '商品',                              // = moduleName
    mdCode: 'test_goods',                      // = module
    fieldList: [{display:'商品名称',name:'name'}, ...],      // 表格显示列
    allFieldList: [{display:'商品主键','name':'id','isHide':true}, ...], // 全字段
    searchCondition: [{name:'商品名称',id:'name'}, ...],     // ✅ 数组,afterModuleJSON 改这个
    selectorData: [{name:'商品名称',id:'name','selectType':1}, ...], // ✅ 数组
    customJs: '/business/text/wjx_goods_list.js',
    customSetting: { ... }                     // 当前 customSetting 对象(require 加载后)
}
```

### 2.3 可改字段速查表 ⭐⭐⭐⭐

> 业务方最常问:"afterModuleJSON 能做什么?"——对照下面这张表,**直接看 module 哪个字段、能改什么、对应实现什么需求**。

| module 字段 | 类型 | 来自 loadListCfg 哪个字段 | 能改什么(常用属性) | 典型需求 |
|---|---|---|---|---|
| **`fieldList`** | Array | `moduleDisplay` (Str_To_Obj) | 表格列:`display / name / width / fixed / priority / sort / type / isHidden / isSort / noTooltip` | 动态加列、按角色显隐列、改列宽、改列头文案 |
| `allFieldList` | Array | `moduleAllFields` (Str_To_Obj) | 全字段(含 `isHide: true` 的隐藏字段):`display / name / priority / isHide` | fieldList 是**显示**列;allFieldList 是**全**字段(含隐藏)。需要按 isHide 过滤时用这个 |
| **`searchCondition`** | Array | `searchCondition` (Str_To_Obj) | **搜索项**:`id / name / selectType / isExtended / defaultValue / sortIndex / url / data / autoPagination` | **按角色显隐/动态加减搜索项、改搜索类型、改默认值、改默认值顺序** |
| **`selectorData`** | Array | `selectorData` (Str_To_Obj) | 搜索项的详细数据(下拉 options) | 按角色改搜索项可选项、配合 searchCondition 同步操作 |
| `moduleButtons` | Array | `moduleButtons` | 顶部按钮:`code / name / icon / priority / type / functionName / izCustom` | 按角色隐藏顶部按钮、改按钮名/图标 |
| `dic` | Array | `dic` (Str_To_Obj) | 数据字典(下拉项翻译) | 动态补充字典、改字典值 |
| `childTab` | Array | `childTab` | 关联 tab(Edit 页) | 动态加 tab |
| `customSetting` | Object | (运行时由 require 加载) | customSetting 自身(改后再传给 ModuleList) | 几乎不用改——改这里一般直接改 `export default {}` 对象 |
| `name` / `mdCode` / `id` | String | `moduleName` / `module` / `moduleId` | 模块基本信息 | 一般不改;多模型复用同一 customSetting 时可动态改 `mdCode` |
| `moduleDisplay` / `moduleAllFields` / `searchCondition` / `selectorData` / `dic` *(字符串版)* | String | (原始字段) | — | **不要改字符串版**!改了解析后的数组即可 |

### 2.4 典型需求 → 改哪个字段 一句话速查

| 业务需求 | 改哪个字段 | 难度 |
|---|---|---|
| 列表动态加一列(比如"操作"列) | `fieldList.push(...)` | ⭐ |
| 按角色隐藏某列 | `fieldList.filter(...)` + 同步 `renderField` 不渲染 | ⭐⭐ |
| **按角色显示/隐藏某个搜索项** | **`searchCondition.filter` + `selectorData.filter`** | ⭐⭐ |
| 动态加一个搜索项(后端没配,**备用方案**) | `searchCondition.push(...)` + 同步处理 `selectorData` | ⭐⭐ |
| 改某个搜索项的默认值 | `searchCondition.find().defaultValue = ...` | ⭐ |
| 按角色改某个搜索项的可选项(下拉) | `selectorData.find().data = [...]` | ⭐⭐ |
| 按角色隐藏/修改顶部按钮 | `moduleButtons.filter/map` 或在 `buttons` 函数里处理 | ⭐ |
| 动态加数据字典项 | `dic.push(...)` 或改现有字典项 | ⭐ |
| 改模块名 | `name` / `moduleName` | ⭐ |
| 多模型复用同一 customSetting | 根据 `mdCode` 分支判断 | ⭐⭐ |

> 👉 上面没写到的需求,基本就不在 afterModuleJSON 范围内了——属于渲染/请求/事件层,看其他 skill。

### 2.5 必须 `return module` 才会生效

不 return → `ModuleListCode.vue:121` 那行 `this.module = afterModuleJSON.call(this, _module)` 拿到的是 `undefined`,后续 `ModuleList/index.vue` 拿不到 `module`,渲染会直接挂掉。

```js
afterModuleJSON: function (module) {
    // ...改动
    return module  // ← 必加,不 return = 白写
}
```

---

## 3. 动态加列(fieldList.push)

```js
afterModuleJSON: function (module) {
    const { fieldList } = module
    if (!fieldList.find(f => f.name === 'operate')) {
        fieldList.push({
            display: '操作',
            name: 'operate',
            width: '150',
            noTooltip: true,
            fixed: 'right'
        })
    }
    return module
}
```

---

## 4. 改搜索项默认值

```js
afterModuleJSON: function (module) {
    const { searchCondition } = module
    // 给"状态"搜索项加默认值
    const statusItem = searchCondition.find(s => s.name === 'status')
    if (statusItem) {
        statusItem.defaultValue = 1
    }
    return module
}
```

---

## 5. 按角色显隐/动态加减搜索项(高频)

> 完整搜索项配置细节(`selectType` 字典、流程图等)见 [search 子 skill §4](../search/SKILL.md#4-单个搜索项按角色显隐aftermodulejson-改-searchcondition)。

> ⚠️ **默认约定**:一般情况**不**动态 push 搜索项(后端没配就过滤不生效,排查困难)。代码只做 `filter`,依赖后端已在模型设计器把对应字段配为搜索条件。
>
> **如果改完不生效(列还在/搜索项还在)**:需要用户提供 `listModule.do` 接口返回值(`listModuleCfg` 内部就是调它),确认后端是否已把该字段配为搜索条件 / 加到 moduleDisplay。**等用户提供接口返回值后再决定下一步**。

```js
import store from '@/store'

export default {
    afterModuleJSON: function (module) {
        let roleCode = store.state.user.userInfo.roleCode
        // 非 SUPER 角色:从 searchCondition + selectorData 中过滤掉 description
        //   依赖:后端已在 searchCondition 中配置 description
        if (roleCode !== 'SUPER') {
            if (Array.isArray(module.searchCondition)) {
                module.searchCondition = module.searchCondition.filter(i => i.id !== 'description')
            }
            if (Array.isArray(module.selectorData)) {
                module.selectorData = module.selectorData.filter(i => i.id !== 'description')
            }
        }
        return module
    }
}
```

> ⚠️ `searchCondition` / `selectorData` 要**两边同步过滤**——`GetSearchFieldList` 按 id 合并这两个数组,只过滤一边会留下脏数据(详见 [search 子 skill §4.2](../search/SKILL.md#42-典型场景))。

---

## 6. 实战(摘自 `public/moduleJs/business/text/wjx_form_list.js:52-62`)

```js
afterModuleJSON: function (module) {
    let { fieldList } = module
    fieldList.push({ 
        display: '操作', 
        name: 'operate', 
        width: '150', 
        noTooltip: true,
        fixed: 'right'
    })
    return module
}
```

---

## 7. 关键事实

| 项 | 说明 |
|------|------|
| 触发位置 | `ModuleListCode.vue`(入口层),不在 `ModuleList/index.vue` |
| this 指向 | `moduleListCode` 实例(可用 `this.BASEURL` 等) |
| 不 return 后果 | 后续 `ModuleList/index.vue` 拿不到 `module`,**渲染直接挂掉** |
| 同名覆盖 | `..._module` 后再用 `Str_To_Obj(...)` 数组版覆盖 → `searchCondition` 等是数组 |
| 字符串版不要改 | `moduleDisplay` / `moduleAllFields` / `searchCondition` 等字符串版是原始数据,改它无效 |

---

## 8. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| 动态加的列没出来 | `afterModuleJSON` 没 return | 必须 `return module` |
| `this.BASEURL` undefined | 误以为 this 是 mList | `afterModuleJSON` 内 this 是 moduleListCode,可用 `this.BASEURL`;其余请求/响应 key 的 this 是 mList |
| 按角色隐藏搜索项不生效 | 只过滤了 `searchCondition` 没过滤 `selectorData` | 两边同步过滤,详见 §5 |
| 改 `moduleDisplay` 字符串版没生效 | 改的是字符串版,不是数组版 | 改 `module.fieldList`(数组版) |
| 想给 column 加 prop 透传给 el-table | 用 `fieldList.push` 加 `prop` 字段 | 不在 `afterModuleJSON` 范围,见 `renderField`(本 skill 不讲) |

---

## 9. 下一步去哪

- **请求配置层**(URL / 方法 / 参数) → [request-flow](../request-flow/SKILL.md)
- **响应处理层**(数据返回后处理 / DOM 渲染后) → [response-flow](../response-flow/SKILL.md)
- **回到入口** → [data-flow index](../data-flow/SKILL.md)
- **回到列表 customSetting 总览** → [frontend-module-list](../../SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)

---

## 10. 修订记录

- **2026-06-24**:从原 data-flow/SKILL.md 拆出,把原 §7 afterModuleJSON 全量搬迁(动态加列/搜索项显隐/字段速查表/典型需求表)
