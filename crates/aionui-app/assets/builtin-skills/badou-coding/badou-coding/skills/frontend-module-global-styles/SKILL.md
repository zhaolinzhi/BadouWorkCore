---
name: frontend-module-global-styles
description: 项目**全局可复用样式类**速查。customSetting 插槽 JSX / renderField render / 业务视图 CSS 想加间距/颜色/字体/布局/光标等效果时触发。覆盖文字对齐/字体/颜色/背景/间距/布局/文本溢出/光标/必填项红点 9 大类。
---

# 全局可复用样式类

> 项目已定义在 `src/styles/` 下的**全局样式类**,**任何 Vue 组件 / customSetting JSX / 业务 CSS 都可以直接 class="xxx" 使用**,不用自己写一份新的。
>
> **适用场景**:
> - customSetting 的 `listTopSlot` / `btnNextLineSlot` / `btnFixedRightSlot` / `searchFixedRightSlot` 等插槽 JSX
> - `renderField.*.render` / `renderFieldHeader.*.render` 返回的 JSX
> - 业务视图的 `<style lang='scss' scoped>`

> ⚠️ 这是**项目约定类**,不是 Element UI 自带。**框架不会自动帮你加**——必须手动写到 `class="..."` 或 `:class="..."` 上。

---

## 0. 速查目录

| 类别 | 走哪一节 |
|------|---------|
| 文字对齐(textL/textR/textC) | [§1](#1-文字对齐) |
| 字体大小与粗细(font12-18/bold) | [§2](#2-字体大小与粗细) |
| 文字颜色(primaryC/warningC/color3/...) | [§3](#3-文字颜色) |
| 背景 / 边框 / 阴影(primaryTag/warningBg/box-shadow) | [§4](#4-背景--边框--阴影) |
| 间距(padding/margin/marginB/marL-10/...) | [§5](#5-间距) |
| 布局(d-b/d-ib/d-f/p-r/p-a/...) | [§6](#6-布局) |
| 文本溢出(text-o-1/text-o-2/text-o-3) | [§7](#7-文本溢出) |
| 光标 / 交互(pointer/noCursor/noEvents) | [§8](#8-光标--交互) |
| 必填项小红点(true-required) | [§9](#9-必填项小红点) |

---

## 1. 文字对齐

来源:[`src/styles/commonAttr.scss:8-10`](../../../src/styles/commonAttr.scss)

| 类 | 效果 |
|---|------|
| `textL` | `text-align: left` |
| `textR` | `text-align: right` |
| `textC` | `text-align: center` |

```jsx
<div class="textL">左对齐</div>
<div class="textR">右对齐</div>
<div class="textC">居中</div>
```

---

## 2. 字体大小与粗细

来源:[`src/styles/commonAttr.scss:12-17`](../../../src/styles/commonAttr.scss)

| 类 | 效果 |
|---|------|
| `font12` | `font-size: 12px !important`(覆盖子元素) |
| `font14` | `font-size: 14px !important` |
| `font16` | `font-size: 16px !important` |
| `font18` | `font-size: 18px !important` |
| `bold` | `font-weight: bold` |

```jsx
<span class="font12 color9">次要说明文字</span>
<span class="bold primaryC">加粗主题色</span>
```

---

## 3. 文字颜色

### 3.1 主题字色

来源:[`src/styles/frame.scss:209-218`](../../../src/styles/frame.scss) `defaultColor` mixin

**6 套主题色**:primary / success / warning / danger / operate / grey。每个主题提供 3 个类:`xxxC`(字色)/ `xxxBg`(背景)/ `xxxTag`(标签样式)。

| 类 | 效果 |
|---|------|
| `primaryC` | 主色字 |
| `successC` | 成功色字(绿) |
| `warningC` | 警告色字(黄) |
| `dangerC` | 危险色字(红) |
| `operateC` | 操作色字(蓝) |
| `greyC` | 灰色字 |

### 3.2 普通灰度字色

来源:[`src/styles/commonAttr.scss:71-73`](../../../src/styles/commonAttr.scss)

| 类 | 效果 |
|---|------|
| `color3` | `#333` 深灰 |
| `color6` | `#666` 中灰 |
| `color9` | `#999` 浅灰 |
| `whiteC` | `#fff` 白色 |
| `text-danger` | `color: $danger !important` (frame.scss:466) |

```jsx
<span class="warningC bold">警示文字</span>
<span class="successC">成功文字</span>
<span class="color9 font12">次要说明</span>
```

---

## 4. 背景 / 边框 / 阴影

### 4.1 主题背景 / 标签

来源:同 §3.1(同一个 `@each` 循环生成)

| 类 | 效果 |
|---|------|
| `primaryBg` / `successBg` / `warningBg` / `dangerBg` / `operateBg` / `greyBg` | 主色背景,白字 |
| `primaryTag` / `successTag` / `warningTag` / `dangerTag` / `operateTag` / `greyTag` | 浅色背景 + 主色字(标签样式) |

**`xxxTag` 是最常用的"提示条/标签"**——浅色背景 + 主题色字,内置 padding/border-radius。

```jsx
{/* 警告提示条:浅黄背景 + 黄字 + padding */}
<div class="warningTag padding">
    <bd-icon name="warning" class="warningC" />
    <span>这是一条警告提示</span>
</div>
```

### 4.2 普通背景

来源:[`src/styles/frame.scss:124-125`](../../../src/styles/frame.scss) / [`commonAttr.scss:74-77`](../../../src/styles/commonAttr.scss)

| 类 | 效果 |
|---|------|
| `bg-white` | 白色背景 |
| `bg-grey` | 灰色背景 |
| `defaultBg` | `--content-bg`(项目内容区背景) |
| `border` | `1px solid $lineColor` |
| `noBorder` | `border: none !important` |
| `box-shadow` | `0 0 6px 0 rgba(16,16,16,0.1)` |

---

## 5. 间距

### 5.1 通用间距(推荐)

来源:[`src/styles/frame.scss:331-336`](../../../src/styles/frame.scss)

| 类 | 效果 |
|---|------|
| `padding` | `padding: $space`(项目默认间距) |
| `margin` | `margin: $space` |
| `noPadding` | `padding: 0` |
| `noMargin` | `margin: 0` |
| `marginB` | `margin-bottom: $space` |

### 5.2 细粒度间距(常用)

来源:[`src/styles/commonAttr.scss:19-69`](../../../src/styles/commonAttr.scss)

| 类 | 效果 |
|---|------|
| `marT-5` / `marT-10` / `marT-20` | 上外边距 5/10/20px |
| `marR-5` / `marR-10` / `marR-20` | 右外边距 |
| `marB-5` / `marB-10` / `marB-20` | 下外边距 |
| `marL-5` / `marL-10` / `marL-15(!important)` / `marL-20` | 左外边距 |
| `padT-10` / `padT-20` | 上内边距 |
| `padR-10` / `padB-10` / `padL-10` | 各方向内边距 |
| `pad-10` / `pad-20` | 全方向内边距 |
| `pad-0` | `padding: 0 !important` |
| `marH-2` | `margin: 0 2px` |
| `mar-10` / `mar-20` | 全方向外边距 10/20px |

> 💡 实际写插槽 JSX 时:**类名组合使用**最常见,例如:
> ```jsx
> <div class="operateC warningTag margin textL">
>     {/* operateC 主题蓝字 + warningTag 浅黄标签 + margin 外间距 + textL 左对齐 */}
> </div>
> ```

---

## 6. 布局

来源:[`src/styles/commonAttr.scss:79-105`](../../../src/styles/commonAttr.scss)

### 6.1 display

| 类 | 效果 |
|---|------|
| `d-b` | `display: block !important` |
| `d-ib` | `display: inline-block` |
| `d-f` | `display: flex` |
| `none` | `display: none !important` |
| `flex-1` | `flex: 1` |
| `o-hidden` | `overflow: hidden` |
| `o-auto` | `overflow: auto` |

### 6.2 position

| 类 | 效果 |
|---|------|
| `p-r` | `position: relative` |
| `p-a` | `position: absolute` |
| `p-f` | `position: fixed` |

### 6.3 vertical-align

| 类 | 效果 |
|---|------|
| `v-t` | `vertical-align: top` |
| `v-m` | `vertical-align: middle` |

### 6.4 宽高

| 类 | 效果 |
|---|------|
| `w-per-100` | `width: 100%` |
| `h-per-100` | `height: 100%` |
| `per-100` | `width: 100% !important; height: 100% !important` |
| `w-per-50` / `w-per-80` / `w-per-90` | 百分比宽度 |
| `w-100` / `w-200` | 固定宽度 100/200px |
| `h-auto` | `height: auto !important` |

---

## 7. 文本溢出

来源:[`src/styles/commonAttr.scss:114-131`](../../../src/styles/commonAttr.scss) `@include t-o-line` mixin

| 类 | 效果 |
|---|------|
| `text-o-1` | 1 行溢出省略(`-webkit-line-clamp: 1`) |
| `text-o-2` | 2 行溢出省略 |
| `text-o-3` | 3 行溢出省略 |

> ⚠️ 不兼容 Safari。

---

## 8. 光标 / 交互

来源:[`src/styles/frame.scss:166-168`](../../../src/styles/frame.scss)

| 类 | 效果 |
|---|------|
| `pointer` | `cursor: pointer !important` |
| `noCursor` | `cursor: default !important` |
| `is-disabled` | `cursor: not-allowed !important` |
| `noEvents` | `pointer-events: none !important` |
| `pointer-events-none` | 同 `noEvents` |

---

## 9. 必填项小红点

来源:[`src/styles/commonAttr.scss:132-159`](../../../src/styles/commonAttr.scss)

| 类 | 效果 |
|---|------|
| `true-required` | 标签前自动加红色 `*`(用 `position: relative` + `&:before`) |
| `false-required` | 占位 8px,不显示红点(用于动态切换状态) |

```jsx
<span :class="[`${isRequired}-required`]">姓名:</span>小明
```

---

## 10. 组合使用最佳实践

### 插槽 JSX 标准模板

```jsx
listTopSlot () {
    return Promise.resolve((h, context) => (
        <div class="operateC warningTag margin textL">
            <bd-icon name="warning" class="warningC" cursor="pointer" size="small" />
            <span style="margin-left: 6px;">提示文字</span>
        </div>
    ))
}
```

**类名搭配思路**:
- `xxxTag` = 一眼看到的提示条样式
- `xxxC` = 给单独一行/一个字加主题色
- `margin` / `padding` = 间距(项目默认)
- `textL` / `textR` / `textC` = 文字对齐
- `d-ib` / `d-f` = 排版

### 渲染按钮组(行内)

```jsx
<div class="d-ib">
    <el-button class="marR-5" size="small">按钮1</el-button>
    <el-button class="marR-5" size="small" type="primary">按钮2</el-button>
</div>
```

### 提示条模板

```jsx
{/* info 提示条 */}
<div class="infoTag padding marB-10">
    <bd-icon name="info" class="infoC" />
    <span class="margin-l">说明文字</span>
</div>

{/* 警告提示条 */}
<div class="warningTag padding marB-10">
    <bd-icon name="warning" class="warningC" />
    <span class="margin-l">警示文字</span>
</div>
```

---

## 11. 找不到合适的类怎么办?

| 场景 | 解决方案 |
|------|---------|
| 想要更精细的样式 | 用 `style="..."` 内联,例如 `style="margin-left: 6px;"` |
| 想要组件级样式 | 写到业务的 `<style lang='scss' scoped>` 里 |
| 想要跟 element 组件样式一致 | 参考 [`src/styles/uiFrame.scss`](../../../src/styles/uiFrame.scss) 找对应 element 组件的覆盖样式 |
| 这个类没用过/不确定存在 | **不要猜**,用 `style="..."` 内联代替,或者问项目同事确认 |

> ⚠️ **绝不可凭印象猜类名**——类名错了 = 没样式,bug 难发现。**没见过的类直接 `style` 内联**。

---

## 12. 常见组合速查

| 想要的效果 | 类名组合 |
|-----------|---------|
| 黄色提示条,左对齐,带默认外边距 | `warningTag margin textL` |
| 红色警告文字加粗 | `dangerC bold` |
| 浅灰说明文字,12px | `color9 font12` |
| 主题蓝文字 + 下边距 | `primaryC marginB` |
| 阴影盒子 | `box-shadow padding` |
| 必填标签 | `true-required` |
| 链接(可点击) | `primaryC pointer` |
| 不可点击文字 | `noCursor color9` |
| 1 行省略文字 | `text-o-1`(不兼容 Safari) |
| 100% 高度 | `per-100` |
| 横排按钮组 | `d-ib` + 内部元素用 `marR-5` |
| 居中盒子 | `textC d-b` |

---

## 13. 与其他 skill 的关系

- **插槽 JSX**(4 个插槽)→ 在 [frontend-module-list/sub/table-look §8](frontend-module-list/sub/table-look/SKILL.md#8-4-个插槽返回-jsxthis-是-modulelist) 中引用了本 skill
- **renderField render** → JSX 里需要样式时也参考本 skill
- **业务视图** → 写 `<style lang='scss' scoped>` 时优先复用本 skill 的类,避免重复定义
</content>
</invoke>