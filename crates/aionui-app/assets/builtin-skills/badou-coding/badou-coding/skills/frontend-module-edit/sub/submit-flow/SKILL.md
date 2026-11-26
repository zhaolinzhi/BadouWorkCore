---
name: frontend-module-edit-submit-flow
description: 八斗 Module 表单 customSetting — 数据请求/响应/保存/按钮索引页。当用户说"改详情接口 URL"、"改保存接口"、"保存后新增"、"数据回来再处理"、"请求参数加签"、"自定义按钮"、"按钮拦截"、"暂存按钮"时,从本索引页进入对应子文件。共拆分 3 个子文件:detail-data(数据请求/响应) / module-config(模型配置定制) / save-and-buttons(保存/按钮)。覆盖 11 个 key。
---

# Module 表单 — 数据请求/响应/保存/按钮(索引)

> 表单"数据流"和"按钮"全部相关 key。**先看 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)** 确认 JS 路径。
>
> **本 skill 已拆分为 3 个子文件**,根据你的需求跳到对应文件。

---

## 0. 文件落点(进入本 skill 前必做)

写在 `public/moduleJs/{mdCode}/edit.js` 的 `export default` 对象里。

**进入前必读**:mdCode + edit/add/view + 完整路径 + 是否已配 customJs → 4 项询问模板见 [frontend-module-edit §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 11 个 key

| key | 类型 | 用途 | 频次 | 子文件 |
|------|------|------|------|--------|
| `dataUrl` | `Function` | 详情请求 URL | ⭐⭐⭐ | [detail-data §2](detail-data.md) |
| `valuePath` | `String` | 详情数据所在路径 | ⭐⭐ | [detail-data §3](detail-data.md) |
| `paramsBeforeRequest` | `Function` | 详情请求参数 | ⭐⭐⭐ | [detail-data §4](detail-data.md) |
| `afterEditJSON` | `Function` | 详情数据拿到后处理 | ⭐⭐⭐ | [detail-data §5](detail-data.md) |
| `afterModuleJSON` | `Function` | 模型配置加载后处理 | ⭐⭐⭐⭐ | [module-config §1](module-config.md) |
| `viewType` | `String` | 表格视图(默认 2 列) | ⭐ | [module-config §2](module-config.md) |
| `beforeModuleInitRender` | `Function` | 渲染前最后定制 | ⭐⭐ | [module-config §3](module-config.md) |
| `saveUrl` | `Function` | 保存接口 URL | ⭐⭐⭐ | [save-and-buttons §1](save-and-buttons.md) |
| `openBtnSaveAndAdd` | `Boolean` | 开启"保存后新增" | ⭐⭐ | [save-and-buttons §2](save-and-buttons.md) |
| `buttons` | `Array\|Function` | 自定义按钮(含 7 个子属性) | ⭐⭐⭐⭐⭐ | [save-and-buttons §3](save-and-buttons.md) |
| `beforeApproveRender` | `Function` | 流程按钮 tab 渲染前 | ⭐ | [save-and-buttons §4](save-and-buttons.md) |

---

## 2. 各子文件跳转

| 你想干什么 | 跳到 |
|-----------|------|
| **改详情请求 URL / 改详情返回结构路径 / 详情请求加签 / 详情数据回来再处理** | [detail-data.md](detail-data.md) |
| **动态加按钮(从模块配置加) / 动态加字段 / 隐藏默认按钮 / 改按钮文案 / 改表格视图** | [module-config.md](module-config.md) |
| **改保存接口 / 开保存后新增 / 自定义按钮 / 按钮重写 / 按钮拦截 / 暂存草稿按钮 / 流程按钮 tab** | [save-and-buttons.md](save-and-buttons.md) |

---

## 3. 关键事实

| 项 | 说明 |
|------|------|
| `dataUrl` / `saveUrl` 的 this | **不同** — dataUrl 在 moduleEditCode,saveUrl 在 moduleEdit |
| `valuePath` 不写 | 默认从 `data` 字段取 |
| `afterEditJSON` 不 return | 表单回填空 |
| `afterModuleJSON` 不 return | 后续渲染异常 |
| `buttons` 函数形式接收 `defaultBtnList` | 第一个参数,需要 return 数组 |
| `openBtnSaveAndAdd: true` | 仅在新增(add)时显示,编辑模式不显示 |
| `loading: false` 必须显式声明 | 自定义按钮的 btnObj 在 click 里赋值的 loading 不触发响应式,必须在按钮对象上声明 |

---

## 4. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| `dataUrl` 改了没生效 | 忘了 return | 必须 return string |
| `valuePath` 写错路径 | 表单空 | 浏览器看后端返回结构,严格按 `.` 分隔 |
| `afterEditJSON` 改完字段没回填 | 忘了 return | 必须 return formData |
| `afterModuleJSON` 改的字段没显示 | 忘了 return module | 必须 return |
| `saveUrl` 改了还是走默认 | 忘了 return | 必须 return string |
| `openBtnSaveAndAdd: true` 没按钮 | 误以为编辑也显示 | 只在 add 模式显示 |
| `buttons` 函数没 return | 所有按钮消失 | 必须 return 数组 |
| 自定义按钮点完没刷新 | 框架默认会刷新,但函数形式 return 时要保留 defaultBtnList | 不 return defaultBtnList 会丢默认 |
| `Event_Expand` 报了 import 错 | 路径不对 | 从 `@/components/frame/Module/BtnBaseFun/edit` 导入 |
| 自定义按钮 loading 不起效 | 按钮对象上没声明 `loading: false` | 必须在按钮定义里和 loading 同级写 `loading: false` |

---

## 5. 下一步去哪

- **字段值变更/联动** → [module-edit-fields](../fields/SKILL.md)
- **字段后追加 DOM** → [module-edit-form-react](../form-react/SKILL.md)
- **校验规则 / 动态显隐** → [module-edit-validation](../validation/SKILL.md)
- **布局(列数 / 渲染前)** → [module-edit-layout](../layout/SKILL.md)
- **Tab 切换 / 子表** → [module-edit-tab-nav](../tab-nav/SKILL.md)
- **回到总览** → [frontend-module-edit](../../SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)
