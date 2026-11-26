---
name: frontend-module-page-debug
description: Module 平台页面**问题排查手册**。**何时调用**:用户报 Module 相关 bug——列表/表单白屏、字段不显示、customSetting 改完不生效、按钮点击无反应、请求报错 404/500/401、缓存导致看不到新效果、表格渲染异常、保存失败。**何时不调用**:用户在写新功能(走 frontend-module-list/edit)或在问"如何实现某个需求" → 那是设计问题,不是 bug;通用 Vue/Element UI 报错 → 走对应框架 skill。
---

# Module 平台 — 页面问题排查

> 业务方最常遇到的"为什么没生效"问题的统一排查手册。先看 §0 通用流程,再按症状跳到对应章节。

---

## 0. 排查通用流程(万能三步)

**任何 Module 页面问题,先按这三步走一遍,80% 能解决:**

1. **看 console** — F12 打开控制台,看红色 error(尤其是 `[ModuleUtils]`、`customSetting` 相关的报错)
2. **看 Network** — 看 `listModule.do` / `editModule.do` / `viewModule.do` 三个接口的请求/响应,确认 mdCode 没拼错、字段有返回
3. **清缓存** — `localStorage` 里搜 `${mdCode}_list` / `${mdCode}_edit` 删掉;或设置 `VUE_APP_OPEN_MODULE_STORAGE=0` 重启

> 如果三步走完还没解决,继续看下面各症状的专项排查。

---

## 1. 白屏 / 列表加载不出数据

### 1.1 现象
- 进入列表页整个白屏
- 或表格有骨架但没数据
- 或 Network 里 `listModule.do?mdCode=xxx` 报 404

### 1.2 排查清单
| 序号 | 检查点 | 怎么验证 |
|---|---|---|
| ① | `mdCode` 是否拼错 | 复制后端给的编码,严格对比大小写 |
| ② | 后端 `Standard_List` 接口是否通 | 直接访问 `/jdbc/common/.../listModule.do?mdCode=xxx` 看返回 |
| ③ | `fieldList` 是否在后端配了"显示列" | 后端模型设计器 → 字段管理 → 显示列勾上 |
| ④ | 父级高度是否为 0 | 看 `<module-list-code>` 是否传了 `fullHeight` 或父级有高度 |
| ⑤ | `permissionBtnList` 是否过滤掉了所有按钮 | 看 console.warn 提示 |

### 1.3 典型报错
- **"Cannot read property 'xxx' of undefined"** → 后端返回的字段结构变了 / customSetting 引用了不存在的字段
- **"xxx is not a function"** → customSetting 里某个 key 写错位置(写到了 data 而不是 methods)

---

## 2. customSetting 改完不生效

### 2.1 现象
- 改了 `public/moduleJs/{mdCode}/list.js` 或 `edit.js`
- 浏览器刷新后**没看到效果**

### 2.2 排查清单(按概率从高到低)
| 序号 | 检查点 | 怎么验证 |
|---|---|---|
| ① | **后端模型设计器是否配了 `列表/编辑页 js` 路径** | 关键!没配的话前端根本不会加载这个文件 |
| ② | **清缓存** | localStorage 搜 `{mdCode}_list` 删掉;或 `VUE_APP_OPEN_MODULE_STORAGE=0` |
| ③ | **保存了吗** | 文件保存了吗?有保存过吗? |
| ④ | **mdCode 对应错了文件** | 比如改的是 `user_info/list.js` 但页面用的是 `user_info_v2` |
| ⑤ | **export default 没写** | 文件没 `export default { ... }`,require 出来是 undefined |
| ⑥ | **语法错误** | 浏览器 console 看 error,文件有 `}` 漏了等情况 |
| ⑦ | **用了 ES2020+ 语法** | 框架兼容 IE,避免可选链 `?.` 等新语法(除非 babel 已配) |

### 2.3 验证 customJs 是否被加载

打开浏览器 console,搜 `[ModuleUtils]`,看有没有打印 customJs 路径。或在 customSetting 文件第一行加 `console.log('customSetting loaded', 'yourMdCode')`,刷新看是否打印。

---

## 3. 字段渲染异常(表格列/表单字段)

### 3.1 现象
- 表格某列显示 `[object Object]` 或空白
- 表单字段不显示 / 位置错乱
- renderField 返回的 JSX 没生效

### 3.2 排查清单
| 序号 | 检查点 | 怎么验证 |
|---|---|---|
| ① | `renderField` 返回值是否有效 | 必须 return 一个 VNode(`h(...)`)或 null,不能 return 普通对象 |
| ② | `renderField` 触发条件 | 必须**该列的 field 字段名匹配**才会被调用 |
| ③ | `valueChange` 里改的字段名是否拼错 | 字段名区分大小写 |
| ④ | `appendDom` 拼 DOM 时是否漏 `class` / `style` | 看 console.warn 提示 |
| ⑤ | 后端字段的 `fieldType` 是否配错 | 比如 `text` 写成了 `Text`(大写在某些版本会失败) |

---

## 4. 请求报错 404 / 500 / 401

### 4.1 404 — 接口找不到
- `mdCode` 拼错 → 跟后端确认编码
- 后端没部署这个 `mdCode` → 找后端同步
- 路径前缀配错 → 看 `.env.{环境}` 里的 `VUE_APP_BASE_API`

### 4.2 500 — 后端报错
- 直接看后端日志
- 多数是后端代码问题 / 模型设计器字段类型不匹配
- 提交 issue 给后端时附上:mdCode + 入参 JSON + 后端 stacktrace

### 4.3 401 — 鉴权失败
- Token 过期 → 重新登录
- CAS 未登录态跳转登录页
- 接口没加白名单 → 找后端在 `Standard_*` 接口加白

---

## 5. 按钮点击无反应

### 5.1 现象
- 点击"新增/编辑/删除"按钮没反应
- 自定义按钮 click 回调没执行

### 5.2 排查清单
| 序号 | 检查点 | 怎么验证 |
|---|---|---|
| ① | `permissionBtnList` 是否过滤掉了该按钮 | 看 console 提示 |
| ② | `buttons: []` 是不是写在了**覆盖位置** | 自定义 buttons 会**完全替换**默认按钮,不是追加 |
| ③ | `click` 回调里 this 指向错 | customSetting 是普通对象,`this` 不会指向 Vue 实例。要拿到 vm 用 `function(btn, scope) { ... }` 形式或在外层捕获 |
| ④ | 按钮被 `<el-button disabled>` 卡住 | 看后端返回的 `btnStatus` 字段 |

### 5.3 自定义按钮的"覆盖 vs 追加"
- `customSetting.buttons` = **完全替换**默认按钮列表
- 想追加:写一个数组把所有默认按钮也列出来
- 想禁用某个:用 `permissionBtnList` 过滤,别从 customSetting 删

---

## 6. 缓存导致看不到新效果

### 6.1 缓存的来源
- `VUE_APP_OPEN_MODULE_STORAGE=1` 时,`listModule.do` / `editModule.do` 的返回会缓存在 `localStorage`
- 缓存 key 格式:`${mdCode}_list` / `${mdCode}_edit` / `${mdCode}_view`

### 6.2 强制清缓存的 3 种方法(任选其一)

**方法 1:浏览器手动删**(最快)
1. F12 → Application → Local Storage
2. 搜 `mdCode`(比如 `user_info`)
3. 删掉 `_list` / `_edit` / `_view` 三项
4. 刷新页面

**方法 2:设置环境变量关缓存**(最稳)
```bash
# .env.development
VUE_APP_OPEN_MODULE_STORAGE=0
```
重启 dev server。

**方法 3:在 console 执行**
```js
// 删所有 model 缓存
Object.keys(localStorage)
    .filter(k => k.includes('user_info'))
    .forEach(k => localStorage.removeItem(k))
location.reload()
```

---

## 7. 保存失败 / 表单提交报错

### 7.1 现象
- 点保存按钮没反应 / 报红字
- 后端返回"字段校验失败"但前端没拦住

### 7.2 排查清单
| 序号 | 检查点 | 怎么验证 |
|---|---|---|
| ① | `validateRule` 是否拦了 | 看 console 是否触发校验提示 |
| ② | 必填字段是否漏 | 后端字段定义的 `isRequired=1` 才会必填 |
| ③ | 唯一性校验没通过 | `valueUnique` 后端查重失败 |
| ④ | `saveUrl` 是否被改坏 | 自定义了 `saveUrl` 但返回了错的接口路径 |
| ⑤ | `beforeSave` 拦截 | 自定义的 beforeSave 返回 false 会取消保存 |

---

## 8. 性能 / 卡顿

### 8.1 常见原因
- 列表数据量 > 1000 行 + 没分页
- `renderField` 里写了复杂逻辑(没缓存计算结果)
- `watch` 了整个 formData 对象
- 后端接口慢 → 看 Network Timing

### 8.2 优化方向
- 后端配分页(每页 50 条)
- renderField 内避免重复计算:`const map = { ... }` 提到外层
- 不要 watch 整个 `formData`,用 `watch(() => formData.fieldA, ...)` 监听单字段

---

## 9. 调试工具箱

### 9.1 浏览器 console 常用命令

```js
// 看当前页的 mdCode
console.log('mdCode:', this.$route.params.mdCode)

// 看 customSetting 是否被加载
const c = require('@/../public/moduleJs/user_info/list.js')
console.log(c.default)

// 强制刷新当前 Module 页面
this.$refs.moduleListCode.reload()

// 拿到底层 form 实例
this.$refs.moduleEditCode.getFormRef()

// 看 formData 当前值
this.$refs.moduleEditCode.getFormRef().model
```

### 9.2 关键文件路径速查

| 用途 | 路径 |
|---|---|
| 自定义 JS(列表) | `public/moduleJs/{mdCode}/list.js` |
| 自定义 JS(表单) | `public/moduleJs/{mdCode}/edit.js` |
| 模型加载器 | [src/js/ModuleUtils.js](../../../../src/js/ModuleUtils.js) |
| 平台服务方法 | [src/service/module.js](../../../../src/service/module.js) |
| 缓存开关 | `VUE_APP_OPEN_MODULE_STORAGE` |
| 默认按钮实现 | [src/components/frame/Module/BtnBaseFun/list.js](../../../../src/components/frame/Module/BtnBaseFun/list.js) |

---

## 10. 求助模板(发给后端/同事用)

遇到搞不定的问题,贴这个模板能极大缩短定位时间:

```
【问题】
- mdCode:user_info
- 页面:列表页 / 表单页
- 操作路径:点 XXX 按钮后发生 YYY
- 期望:ZZZ
- 实际:出现了什么(截图/文字)

【已尝试】
- [ ] 清过缓存
- [ ] 看 console 无 error(或附 error 信息)
- [ ] Network 请求返回了 200(附响应 JSON)

【环境】
- 环境:dev / test / prd
- 浏览器:Chrome 版本
- mdCode 配的 customJs 路径:public/moduleJs/user_info/list.js
```

---

## 11. 下一步去哪

- **写新功能** → [frontend-module-quickstart](../frontend-module-quickstart/SKILL.md) / [frontend-module-list](../frontend-module-list/SKILL.md) / [frontend-module-edit](../frontend-module-edit/SKILL.md)
- **扩展新字段类型** → [frontend-module-extend-field](../frontend-module-extend-field/SKILL.md)
- **this 指向 = 具体文件 速查** → [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)(顶层,`Skill` 工具可加载)
