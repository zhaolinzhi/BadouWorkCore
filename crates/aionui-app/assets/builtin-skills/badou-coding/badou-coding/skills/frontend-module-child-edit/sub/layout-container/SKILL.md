---
name: frontend-module-child-edit-layout-container
description: 八斗 Module 表单 customSetting — 关联子表的 4 类排版容器(mainDefault / mainTab / defaultB / linkTab / defaultC) + 5 个核心 CSS 类(marB / defaultBg / h-auto / h-per-100 / fullHeight)详解。当用户问"子表怎么排版"、"子表底部间距"、"子表铺满高度"、"defaultBg 是什么"、"hasMuchPart 怎么算"时触发。
---

# 关联子表 — 排版容器与 CSS 布局详解

> 来源:[ModuleEdit/index.vue:478-578](../../../../../src/components/frame/Module/ModuleEdit/index.vue#L478-L578) 的 `linkData` 计算属性 + [ModuleEdit/index.vue:1015-1067](../../../../../src/components/frame/Module/ModuleEdit/index.vue#L1015-L1067) 的 `<style scoped>` + [commonAttr.scss](../../../../../src/styles/commonAttr.scss)。
>
> **父 skill**:[frontend-module-child-edit](../SKILL.md)

---

## 1. 一图看懂 linkData 4 类排版容器

```
页面从上往下:
┌────────────────────────────────────────┐
│ mainDefault = [主表, 关1, 关2, ...]    │  ← ①主表+按顺序展示的关联(无平级 Tab 时)
├────────────────────────────────────────┤
│ mainTab = [[主表, 关1], [关2], ...]    │  ← ②平级 Tab 结构(主表作为 Tab[0])
├────────────────────────────────────────┤
│ defaultB = [关1, 关2, ...]             │  ← ③平级 Tab 之后、按顺序展示的块
├────────────────────────────────────────┤
│ linkTab = [[关1, 关2], [关3], ...]     │  ← ④主表下方的子 Tab 组
├────────────────────────────────────────┤
│ defaultC = [关1, 关2, ...]             │  ← ⑤子 Tab 之后、按顺序展示的块
└────────────────────────────────────────┘
```

---

## 2. 5 类容器数据结构与触发条件

| 容器 key | 数据结构 | 触发条件 | 用途 |
|---|---|---|---|
| `mainDefault` | `[主表, 关联1, 关联2]` | `showStyle=3` 且前面无任何平级 Tab | 主表 + 顺序展示的关联 |
| `mainTab` | `[[主表, 关1], [关2], [关3, 关4, 关5]]` | `showStyle=1`(平级 Tab) | 主表作为首个 Tab + 其他平级 Tab |
| `defaultB` | `[关1, 关2, 关3]` | `showStyle=3` 但前面已有平级 Tab | 顺序展示的中间块 |
| `linkTab` | `[[关1, 关2], [关3], [关4, 关5, 关6]]` | `showStyle=2`(子 Tab) | 主表下方的子 Tab 组 |
| `defaultC` | `[关1, 关2, 关3, 关4]` | `showStyle=3` 且最末尾 | 顺序展示的尾部块 |

> 注:`mainTab` 和 `linkTab` 都是**二维结构**(每个 tab 项下有多个子模块)。

---

## 3. 6 种典型排版组合

| 场景 | mainDefault | mainTab | defaultB | linkTab | defaultC |
|---|---|---|---|---|---|
| 主表 + 全部独立 | `[主表, 关1, 关2]` | — | — | — | — |
| 主表 + 平级 Tab + 独立 | `[主表]` | `[[主表, 关1], [关2], [关3, 关4, 关5]]` | `[关6, 关7]` | — | — |
| 主表 + 平级 Tab + 子 Tab + 独立 | `[主表]` | `[[主表, 关1], [关2]]` | `[关3]` | `[[关4, 关5], [关6], [关7, 关8]]` | `[关9, 关10]` |
| 全部平级 Tab | — | `[[主表], [关1], [关2], [关3]]` | — | — | — |
| 全部独立(无主表 tab) | `[主表]` | — | `[关1, 关2, 关3]` | — | `[关4, 关5]` |
| 全部子 Tab | `[主表]` | — | — | `[[关1, 关2], [关3], [关4, 关5, 关6]]` | — |

> ⚠️ 注意:**mainDefault 始终包含主表(在 `[0]` 位置)**,主表**也会**作为 `mainTab[0]` 的内容(当存在平级 Tab 时)。

---

## 4. 容器渲染的 CSS 类映射

> 来源:[ModuleEdit/index.vue:40-200](../../../../../src/components/frame/Module/ModuleEdit/index.vue#L40-L200) 的 template。

### 4.1 mainDefault

```vue
<!-- 主表(首个,mainDefault[0]) -->
<module-form class="marB s-part" :class="{'h-auto': !!detailId}"></module-form>
<!-- 子模块(mainDefault[1+]) -->
<child-module-edit
    class="defaultBg h-auto"
    :class="{
        'marB': index !== linkData.mainDefault.slice(1).length - 1 || ...
    }"
    :fullHeight="!hasMuchPart && i.children.length === 1">
</child-module-edit>
```

### 4.2 mainTab 整体

```vue
<bd-tabs
    :data="linkData.mainTab"
    class="defaultBg s-part"
    :class="{
        'marB': linkData.defaultB.length + linkData.linkTab.length + linkData.defaultC.length > 0
    }"
    :autoHeight="hasMuchPart">
    <!-- 主表 Tab 内容 -->
    <template v-slot:mainTab_0>
        <module-form :noTitle="true" class="h-auto marginB"></module-form>
        <child-module-edit class="h-auto marB" :fullHeight="false"></child-module-edit>
    </template>
    <!-- 其他 Tab 内容 -->
    <template v-for="(i, i_index) in linkData.mainTab.slice(1)" v-slot:[i[tabKey.id]]>
        <child-module-edit
            :class="{
                'h-auto marginB': i.children.length > 1
            }"
            :fullHeight="!hasMuchPart && i.children.length === 1">
        </child-module-edit>
    </template>
</bd-tabs>
```

### 4.3 defaultB

```vue
<child-module-edit
    class="defaultBg"
    :class="{
        'marB': index !== linkData.defaultB.length - 1 || ...
    }"
    :fullHeight="!hasMuchPart">
</child-module-edit>
```

### 4.4 linkTab 整体

```vue
<bd-tabs
    :data="linkData.linkTab"
    class="defaultBg s-part"
    :class="{
        'marB': linkData.defaultC.length > 0
    }"
    :autoHeight="hasMuchPart">
    <!-- linkTab 内每个 tab 下的子模块 -->
    <child-module-edit
        :class="{
            'h-auto marginB': i.children.length > 1
        }"
        :fullHeight="!hasMuchPart">
    </child-module-edit>
</bd-tabs>
```

### 4.5 defaultC

```vue
<child-module-edit
    class="defaultBg"
    :class="{
        'marB': index !== linkData.defaultC.length - 1
    }"
    :fullHeight="!hasMuchPart">
</child-module-edit>
```

---

## 5. 5 个核心 CSS 类速查

| 类名 | 作用 | 来源 |
|---|---|---|
| `marB` | 底部 margin = `$space` | [commonAttr.scss:33](../../../../../src/styles/commonAttr.scss#L33) |
| `defaultBg` | `background: var(--content-bg)` | [frame.scss:338](../../../../../src/styles/frame.scss#L338) |
| `h-auto` | `height: auto !important` | [commonAttr.scss:100](../../../../../src/styles/commonAttr.scss#L100) |
| `h-per-100` | `height: 100%` | [commonAttr.scss:98](../../../../../src/styles/commonAttr.scss#L98) |
| `fullHeight`(prop) | 传给 ChildModuleEdit,内部加 `h-per-100` | [ChildModuleEdit.vue:5-7](../../../../../src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L5-L7) |

### 5.1 类与容器的对应

| 容器 | 容器本身 | 子模块 |
|---|---|---|
| `mainDefault[0]`(主表) | `marB s-part`(+ `h-auto` 当 detailId) | — |
| `mainDefault[1+]`(子模块) | `defaultBg h-auto` | — |
| `mainTab`(整体) | `defaultBg s-part`(+ `marB` 后续还有块) | `h-auto marB`(主表 tab 内)/ `h-auto marginB`(其他 tab 内) |
| `defaultB`(子模块) | `defaultBg`(+ `marB` 后续还有块) | — |
| `linkTab`(整体) | `defaultBg s-part`(+ `marB` 后续还有 defaultC) | `h-auto marginB`(tab 内多模块) |
| `defaultC`(子模块) | `defaultBg`(+ `marB` 后续还有块) | — |

### 5.2 `fullHeight` prop 的计算规则

```js
// ModuleEdit/index.vue:66 / 125 / 178 等多处
:fullHeight="!hasMuchPart && i.children.length === 1"
```

**口诀**:**页面只有平级 Tab(`hasMuchPart=false`)且 tab 下只有 1 个模块 → 铺满;否则自适应**。

---

## 6. `hasMuchPart` 计算逻辑

```js
// ModuleEdit/index.vue:425-432
hasMuchPart () {
    if (!this.detailId) return        // 新增页不算
    if (!this._showLinkData) return   // 没关联子表不算
    // 关键判断:所有关联的 showStyle 都 = 平级 Tab 1 → 视为"只有一个大模块"
    return !this._showLinkData.every(i => !i.showStyle || i.showStyle === 1)
}
```

| 场景 | hasMuchPart | 行为 |
|---|---|---|
| 新增页(无 detailId) | `undefined` | 整页只渲染主表,无子模块 |
| 无任何关联子表 | `undefined` | 走默认表单 |
| 所有关联都是平级 Tab(都=1 或空) | `false` | 子模块**铺满整屏** |
| 至少一个 showStyle=2 或 =3 | `true` | 整页**滚动**,子模块高度 `auto` |

### 6.1 `hasMuchPart` 怎么影响 CSS

| 类 | `hasMuchPart=false` | `hasMuchPart=true` |
|---|---|---|
| `bd-module-edit` | — | `o-auto`(整页滚动) |
| `bd-module-edit__main` | — | `has-much-part`(整页滚动) |
| `bd-tabs` 的 `autoHeight` | `false` | `true`(Tab 自适应高度) |
| `s-part`(最后一个) | `marB` | 无 `marB`(由滚动接管) |

详见 [ModuleEdit/index.vue:1016-1042](../../../../../src/components/frame/Module/ModuleEdit/index.vue#L1016-L1042)。

---

## 7. 子模块标题自动隐藏规则

```js
// ModuleEdit/index.vue:641-652
isHideTitle (tabItem) {
    let { tabName, children } = tabItem
    // 当 tab 下只有 1 个模块,且模块名称 === tab 名称 → 不显示模块的标题(避免重复)
    if (children && children.length === 1 && children[0].title === tabName) {
        return true
    }
    return false
}
```

> 这就是为什么:**子表的 title 与所在 tabName 一致时,标题会被自动隐藏**——避免"TAB 订单明细"下面又出现一个"订单明细"标题。

---

## 8. 实战:不同组合下的子模块高度速查

| 场景 | 子模块 CSS 类 | 视觉效果 |
|---|---|---|
| 平级 Tab + 单个 tab 下单模块 | `defaultBg h-auto`(+ `fullHeight` 决定 `h-per-100`) | 整屏或随内容 |
| 平级 Tab + 单个 tab 下多模块 | `h-auto marB`(首个) / `h-auto marginB`(中间) / `h-auto`(末尾) | 模块堆叠 |
| 顺序展示(mainDefault) | `defaultBg h-auto` | 独立块,无 Tab |
| 子 Tab(linkTab)内多模块 | `h-auto marginB`(首个加,中间加) | 主表下方 Tab 内堆叠 |

> 💡 业务方**几乎不需要手动改这些 CSS**——它们由 `ModuleEdit/index.vue` 自动绑定。

---

## 9. 下一步去哪

- **父子表通信** → [sub/parent-child-communication/SKILL.md](parent-child-communication/SKILL.md)
- **showStyle 展示风格** → [sub/show-style/SKILL.md](show-style/SKILL.md)
- **showType 渲染方式** → [sub/show-type/SKILL.md](show-type/SKILL.md)
- **childTab 字段配置 + 实战** → [sub/child-tab-config/SKILL.md](child-tab-config/SKILL.md)
- **总览** → [frontend-module-child-edit](../SKILL.md)