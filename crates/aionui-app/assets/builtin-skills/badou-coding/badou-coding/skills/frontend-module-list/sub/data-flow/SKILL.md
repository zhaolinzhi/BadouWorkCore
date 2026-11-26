---
name: frontend-module-list-data-flow
description: 八斗 Module 列表 customSetting — **请求与数据流索引**。本身是"数据流"4 个 sub-skill 的总览/索引,不直接触发。请按用户需求选对子 skill:请求配置 (request-flow) / 响应处理 (response-flow) / 模型配置变更 (module-config-mutation)。
---

# Module 列表 — 请求与数据流(索引)

> 这是**入口索引**,不直接讲 key,讲**生命周期 + 4 个子 skill 怎么选**。
>
> 📌 涉及的文件落点:**动手前先确认 JS 路径**(必读) → 详见 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 0. 4 个子 skill(2026-06-24 拆分自原 data-flow)

| 子 skill | name | 一句话 | 文件 |
|---------|------|--------|------|
| **请求配置层** | `module-list-request-flow` | URL / 方法 / 参数 / 完全接管 | [sub/request-flow/SKILL.md](request-flow/SKILL.md) |
| **响应处理层** | `module-list-response-flow` | 数据返回后处理 / DOM 渲染后 | [sub/response-flow/SKILL.md](response-flow/SKILL.md) |
| **模型配置变更层** | `module-list-module-config-mutation` | 改 fieldList / searchCondition / 按钮 / 字典 | [sub/module-config-mutation/SKILL.md](module-config-mutation/SKILL.md) |

> ⚠️ 本 skill 是**索引**——具体 key 怎么用,跳到对应 sub-skill 看。

---

## 1. 完整生命周期(ModuleList → MList)

```
mdCode watch 触发
    ↓
[模块配置加载层: module-config-mutation]
afterModuleJSON(module)  ← 模型配置加载后(改 fieldList/searchCondition)
    ↓
用户点搜索/分页/排序
    ↓
请求构造
    ↓
[请求配置层: request-flow]
dataUrl() → URL              ← 可改 URL
    ↓
paramsBeforeRequest(params)   ← 可改请求参数(加签/补参)
    ↓
diySearch(config)?            ← 如果存在,完全接管,跳过下面
    ↓
请求发到后端
    ↓
[响应处理层: response-flow]
afterListJSON(data) → data    ← 可改返回数据(必须 return)
    ↓
表格赋值渲染
    ↓
afterListRender()             ← DOM 渲染完成(无需参数)
```

---

## 2. 触发本 skill 的需求(分流表)

| 用户原话 | 跳到哪个 sub-skill |
|---------|-------------------|
| 改请求方法 / 加签 / 改请求 URL / 请求前改参数 / 换 GET 请求 / 自定义请求完全接管 | → [request-flow](request-flow/SKILL.md) |
| 数据返回后处理 / 列表渲染后钩子 / 每行追加字段 / 客户端二次过滤 / DOM 渲染完后做事 | → [response-flow](response-flow/SKILL.md) |
| 改模块配置 / 动态加列 / 按角色显隐列 / 按角色显隐搜索项 / 动态加搜索项 / 改搜索项默认值 / 改搜索项可选项 / 按角色隐藏顶部按钮 / 改字典 / 改模块名 | → [module-config-mutation](module-config-mutation/SKILL.md) |

---

## 3. 关键 this 指向(本索引独有提示)

> 💡 **6 个 key 全量速查见 [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md) §4.1**(每行一个 key)。
> 本节只列**跨 sub-skill 通用**的关键提示(避免业务方在每个 sub-skill 里重复查)。

> ⚠️ **跨 sub-skill 时 this 指向会变**:`afterModuleJSON` 在最外层 `ModuleListCode.vue`(`moduleListCode` 实例)拿到完整 module;其余 5 个 key 都在底层 `MList/index.vue`(`mList` 实例)拿到数据。
>
> **为什么 this 这么碎?** 因为跨 3 层组件:`moduleListCode`(入口) → `moduleList`(中转) → `mList`(底层表格)。各 key 按"什么时候拿什么"分散在不同层调用。

---

## 4. 关键事实(全部 6 个 key 通用)

| 函数 | 不 return 后果 |
|------|---------------|
| `dataUrl` | 自定义 URL 不生效(回退默认) |
| `paramsBeforeRequest` | 啥也不生效 |
| `afterListJSON` | 列表无数据 |
| `afterListRender` | OK,无返回值 |
| `afterModuleJSON` | 模型配置丢失(后续渲染异常,**直接挂掉**) |
| `diySearch` | return `true` 表示已处理,否则走默认 |

---

## 5. 常见问题(全部 6 个 key 通用)

| 问题 | 现象 | 解决 |
|---|------|------|
| 改完 paramsBeforeRequest 没生效 | 忘了 return | 必须 return 新对象 |
| 列表空白 | afterListJSON 忘了 return | 必须 return 处理后的数组 |
| 动态加的列没出来 | afterModuleJSON 没 return | 必须 `return module`(在 module-config-mutation §2.5) |
| Network 看不到新参数 | paramsBeforeRequest 里 `return` 写成函数表达式 | 用 `return { ...params, ... }` |
| 改 `dataUrl` 不生效 | 写成字符串形式 `dataUrl: '/xxx.do'` | **必须是函数**(详见 request-flow §2) |
| `this.BASEURL` undefined | 误以为 this 是 mList | `afterModuleJSON` 内 this 是 moduleListCode,可用 `this.BASEURL`;其余 this 是 mList |

---

## 6. 下一步去哪

- **请求配置层**(URL / 方法 / 参数 / 完全接管) → [request-flow](request-flow/SKILL.md)
- **响应处理层**(数据返回后处理 / DOM 渲染后) → [response-flow](response-flow/SKILL.md)
- **模型配置变更层**(改 fieldList / searchCondition / 按钮 / 字典) → [module-config-mutation](module-config-mutation/SKILL.md)
- **回到列表 customSetting 总览** → [frontend-module-list](../../SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)

---

## 7. 修订记录

- **2026-06-24**:从 700 行的单体 data-flow 拆出 3 个 sub-skill(request-flow / response-flow / module-config-mutation),本 skill 降级为索引,只保留生命周期 / 关键事实 / 常见问题 / 跳转到子 skill
