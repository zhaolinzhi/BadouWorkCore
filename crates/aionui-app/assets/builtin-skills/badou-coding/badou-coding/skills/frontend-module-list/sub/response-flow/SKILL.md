---
name: frontend-module-list-response-flow
description: 八斗 Module 列表 customSetting — **响应处理层**(数据返回后处理 / DOM 渲染后)。当用户说"数据返回后处理"、"列表渲染后钩子"、"每行追加字段"、"客户端二次过滤"、"DOM 渲染完后做事" 时触发。覆盖 afterListJSON / afterListRender 2 个 key。
---

# Module 列表 — 响应处理层

> 列表请求"返回后的所有事"——改返回数据、监听 DOM 渲染。本 skill 是 [data-flow index](../data-flow/SKILL.md) 的子章节。

> 📌 涉及的文件落点:**动手前先确认 JS 路径**(必读) → 详见 [frontend-module-list §0](../../SKILL.md#0-动手前先确认-js-路径必读)

---

## 1. 本 skill 覆盖的 2 个 key

| key | 用途 | 频次 | 触发时机 |
|------|------|------|------|
| `afterListJSON` | 数据返回后处理 | ⭐⭐⭐⭐ | 请求**后**,框架塞表格**前** |
| `afterListRender` | 列表 DOM 渲染后 | ⭐⭐ | 渲染**后**(`$nextTick`) |

---

## 2. `afterListJSON` ⭐⭐⭐⭐(数据返回后处理)

**来源**:`ModuleList/index.vue` 第 814-817 行

**签名**:`afterListJSON(data)` → **必须 return** 处理后的数组

**this 指向**:**mList 实例**

### 2.1 给每行追加展示用字段

```js
afterListJSON: function (data) {
    return data.map(row => ({
        ...row,
        _statusText: row.status === 1 ? '启用' : '禁用',
        _avatarUrl: row.avatar || '/default.png'
    }))
}
```

### 2.2 客户端二次过滤

```js
afterListJSON: function (data) {
    return data.filter(row => row.isVisible !== false)
}
```

### 2.3 排序

```js
afterListJSON: function (data) {
    return [...data].sort((a, b) => a.createTime < b.createTime ? 1 : -1)
}
```

> ⚠️ **不 return = 列表空白**。多数"列表没数据"的 bug 都在这里忘了 return。

### 2.4 行级 loading 状态(本项目实战 2026-06-24)

```js
afterListJSON: function (data) {
    return data.map(row => ({
        ...row,
        loading: false  // 默认值,行按钮异步操作期间可改为 true
    }))
}
```

> 💡 `row.loading` 是约定俗成的字段名,在 `renderField` 里配合显示加载状态。

---

## 3. `afterListRender`(DOM 渲染后)⭐⭐

**来源**:`ModuleList/index.vue` 第 836-838 行(`init().finally` + `$nextTick`)

**签名**:`afterListRender()` → 无返回值,无参数

**this 指向**:**mList 实例**

### 3.1 默认选中第一行(本项目实战 2026-06-24)

```js
afterListRender: function () {
    if (this.temp_data && this.temp_data.length > 0 && this.$refs.list) {
        if (!this.multiple) {
            // 单选模式先清空,避免切换筛选条件后保留旧选中
            this.$refs.list.clearSelection()
        }
        this.$refs.list.toggleRowSelection(this.temp_data[0])
    }
}
```

### 3.2 绑定额外的 DOM 事件 / 注入第三方组件

```js
afterListRender: function () {
    // 表格 DOM 已经渲染完毕
    const $table = this.$refs.mList?.$el
    if ($table) {
        // ...额外的 DOM 操作
    }
}
```

> 💡 `afterListRender` 在 `$nextTick` 内,数据已就位——DOM 操作放这里安全。

---

## 4. 关键事实

| 函数 | 不 return 后果 |
|------|---------------|
| `afterListJSON` | 列表无数据 |
| `afterListRender` | OK,无返回值 |

**this 指向**:两个 key 都在 mList(底层表格),**不是** moduleList,也不是 moduleListCode。

---

## 5. 常见问题

| 问题 | 现象 | 解决 |
|---|------|------|
| 列表空白 | `afterListJSON` 忘了 return | 必须 `return` 处理后的数组 |
| `afterListRender` 不执行 | 直接调用的不是钩子函数,而是任意命名的 method | 必须字段名是 `afterListRender`,且 customSetting 顶层直接定义 |
| 想拿当前行数据做渲染后处理 | `afterListRender` 的 this 是 mList,`this.temp_data` 是当前页数据 | 用 `this.temp_data[index]` 取 |
| `afterListRender` 里 `this.$refs` undefined | 钩子在 mList 早期执行,ref 还没绑定 | 用 `this.$nextTick(() => { ... })` 包一层 |
| 改完数据没生效 | `afterListJSON` 改了 row 但模板没用新字段 | 检查渲染函数是否读 `row._xxx`,而不是 `row.xxx` |

---

## 6. 下一步去哪

- **请求配置层**(URL / 方法 / 参数) → [request-flow](../request-flow/SKILL.md)
- **模型配置变更**(改 fieldList / searchCondition 等) → [module-config-mutation](../module-config-mutation/SKILL.md)
- **回到入口** → [data-flow index](../data-flow/SKILL.md)
- **回到列表 customSetting 总览** → [frontend-module-list](../../SKILL.md)
- **this 指向 = 具体文件速查** → [frontend-module-this-reference](../../../frontend-module-this-reference/SKILL.md)

---

## 7. 修订记录

- **2026-06-24**:从原 data-flow/SKILL.md 拆出,合并 §5 afterListJSON + §6 afterListRender
