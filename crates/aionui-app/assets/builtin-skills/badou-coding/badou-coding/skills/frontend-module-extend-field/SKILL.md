---
name: frontend-module-extend-field
description: Module 平台**扩展新字段类型**。**何时调用**:现有的 20+ 内置字段类型(text/select/date/richtext/...)不够用,需要新增一种自定义字段类型(例如"地图坐标选择器"、"评分星级+评语"、"业务专属组合控件")。涉及在 items/index.js 注册组件、遵守 MForm 的 props/事件契约、后端模型设计器加新 type。**何时不调用**:用户只是用现有字段类型做配置(走 frontend-module-quickstart / customSetting 相关);字段是后端新增的标准类型 → 不需要前端扩展;用户想给现有字段加 render 效果 → 用 customSetting.renderField 而不是新组件。
---

# Module 平台 — 扩展新字段类型

> 当内置的 20+ 字段类型不够用,需要新增一种**自定义组件**作为字段类型时,按本 skill 走。

---

## 0. 先判断:真的需要扩展吗?

**绝大多数"想加新字段"的需求,用现有类型 + customSetting 就能解决,不要走扩展:**

| 需求 | 正确做法 | 错的做法 |
|---|---|---|
| 给状态列加颜色徽章 | `customSetting.renderField` | 扩展新"状态徽章"组件 |
| 字段后追加一个帮助链接 | `customSetting.appendDom` | 扩展新"字段+帮助"组件 |
| 改字段默认值/校验 | 后端模型设计器 + `validateRule` | 扩展"自带默认值"组件 |
| 字段 A 变化时联动 B | `customSetting.valueChange` | 扩展"联动组件" |

**什么时候真的需要扩展:**
- 现有类型**没有**对应的 UI 控件(比如"地图坐标选择器"、"人员选择器+头像预览"、"签名板")
- 这种字段**不是单点修饰**,而是整个交互都需要重新设计

---

## 1. 已有 20+ 字段类型清单(确认没有再扩)

定义在 [src/components/frame/Common/MForm/components/items/index.js](../../../../src/components/frame/Common/MForm/components/items/index.js):

| type | 组件 | 路径 |
|---|---|---|
| `text` | Text | `items/Text` |
| `textarea` | Textarea | `items/Textarea` |
| `number` | Number | `items/Number` |
| `select` | Select | `items/Select` |
| `radio` | Radio | `items/Radio` |
| `checkbox` | Checkbox | `items/Checkbox` |
| `switch` | Switch | `items/Switch` |
| `date` | Date | `items/Date/index` |
| `richtext` | RichText | `items/RichText/index.vue` |
| `code` | Code(JSON) | `items/Code` |
| `codemirror` | CodeMirror(SQL/Java/Python) | `items/CodeMirror` |
| `cascader` | Cascader | `items/Cascader` |
| `autocomplete` | AutoComplete | `items/AutoComplete` |
| `attach` | Attach | `items/File/Attach/index` |
| `image` | ImagePicker | `items/File/ImagePicker/index` |
| `addresspicker` | AddressPicker | `items/AddressPicker/index` |
| `addressbook` | AddressBook | `items/AddressBook` |
| `dialoglist` | DialogList | `items/DialogList` |
| `colorpicker` | ColorPicker | `items/ColorPicker` |
| `iconpicker` | IconPicker | `items/IconPicker` |
| `pathpicker` | PathPicker | `items/PathPicker` |
| `roadmap` | Roadmap | `items/Roadmap` |
| `rate` | Rate | `items/Rate` |

> 旧版兼容别名(`FormText` / `FormSelect` 等)见 index.js 第 26-50 行,**新写组件不要用别名**。

---

## 2. 扩展步骤(4 步)

### 第 1 步:创建组件文件

在 `src/components/frame/Common/MForm/components/items/` 下新建目录,例如 `MyField/index.vue`:

```
items/
└── MyField/                  ← 新建
    └── index.vue             ← 新建
```

**组件最小骨架**(遵守 MForm 的 props/事件契约):

```vue
<template>
    <div class="m-form-my-field">
        <!-- 你的 UI -->
        <el-input v-model="currentValue" @input="handleChange" />
    </div>
</template>

<script>
export default {
    name: 'MyField',
    props: {
        // MForm 通用契约(几乎所有字段组件都需要)
        value: {                    // v-model 绑定
            type: [String, Number, Object, Array],
            default: ''
        },
        fieldItem: {                // 当前字段的完整配置(含 isRequired / disabled 等)
            type: Object,
            default: () => ({})
        },
        // 你的业务 props(可选)
        options: {
            type: Array,
            default: () => []
        }
    },
    data () {
        return {
            currentValue: this.value
        }
    },
    watch: {
        value (val) {
            this.currentValue = val
        }
    },
    methods: {
        handleChange (val) {
            this.$emit('input', val)        // 必须:回传值给 MForm
            this.$emit('change', val)       // 可选:触发联动
        }
    }
}
</script>
```

**契约要点:**
- 必须接收 `value` prop(用 `v-model` 绑定)
- 必须 emit `input` 事件回传新值
- 可选 emit `change` 事件供 `customSetting.valueChange` 监听
- 可选接收 `fieldItem` 读后端配置的 `isRequired` / `disabled` / 自定义属性

### 第 2 步:在 items/index.js 注册

编辑 [src/components/frame/Common/MForm/components/items/index.js](../../../../src/components/frame/Common/MForm/components/items/index.js):

```js
// 1. 顶部 import
import MyField from './MyField'

// 2. export {} 里加一行(放在"新字段"区域,别混入"待废弃"区域)
export {
    // ... 已有字段
    // 自定义扩展
    MyField,           // ← 新加
}
```

### 第 3 步:后端模型设计器配新 type

去后端"模型设计器" → 字段管理 → 新建字段:
- `fieldType` = `MyField`(和你注册时的组件名一致)
- 后端 type → 前端组件的映射是按**组件名**(`name` 字段)匹配的,不是按 import 名

> ⚠️ 如果你想让后端用小写短名(如 `myfield` 或 `map`),需要在 index.js 里加 `MyField as myfield` 这种别名导出。

### 第 4 步:联调

1. 启 dev server → 访问对应 `mdCode` 页面
2. 浏览器 console 确认没报错
3. 在表单里点这个字段,看是否正常交互
4. 保存 → 看后端是否收到正确数据格式

---

## 3. 一个完整例子:扩展"人员选择器+头像"

### 场景
后端给的 `assignee` 字段要存 `{ userId, userName, avatar }`,现有 `addressbook` 类型只存 `userId`,不满足需求。

### 组件实现

```vue
<!-- items/UserPicker/index.vue -->
<template>
    <div class="user-picker" @click="openDialog">
        <el-avatar v-if="user.avatar" :src="user.avatar" :size="32" />
        <span v-else class="placeholder">点击选择人员</span>
        <span v-if="user.userName" class="name">{{ user.userName }}</span>
        <el-button v-if="user.userId" type="text" @click.stop="clear">清空</el-button>
    </div>
</template>

<script>
export default {
    name: 'UserPicker',
    props: {
        value: {
            type: Object,
            default: () => ({ userId: '', userName: '', avatar: '' })
        },
        fieldItem: {
            type: Object,
            default: () => ({})
        }
    },
    data () {
        return {
            user: { ...this.value }
        }
    },
    watch: {
        value: {
            deep: true,
            handler (val) { this.user = { ...val } }
        }
    },
    methods: {
        openDialog () {
            if (this.fieldItem.disabled) return
            // 弹个选择人员的 dialog(略)
            // 选完拿到 { userId, userName, avatar } 后:
            this.user = pickedUser
            this.$emit('input', pickedUser)
            this.$emit('change', pickedUser)
        },
        clear () {
            this.user = { userId: '', userName: '', avatar: '' }
            this.$emit('input', this.user)
            this.$emit('change', this.user)
        }
    }
}
</script>
```

### 注册

```js
// items/index.js
import UserPicker from './UserPicker'

export {
    // ... 已有
    UserPicker,           // ← 新加
}
```

### 后端配字段
- `fieldType` = `UserPicker`(组件 `name`)
- 后端要求 JSON 字段 `valueType` = `object`

---

## 4. 常见问题

| 问题 | 现象 | 解决 |
|---|---|---|
| 改了组件没生效 | 页面仍用旧版 | 清缓存(见 page-debug §6)+ 检查 import 路径 |
| `value` prop 拿不到 | 字段值始终是空 | 检查父组件是否 `v-model` 绑定,或 `value.sync` |
| `fieldItem.disabled` 不生效 | 只读模式下仍能编辑 | 在组件 `watch` 里监听 `fieldItem.disabled` 同步到内部 state |
| 改了类型名不生效 | 后端配了 `UserPicker` 但渲染不出来 | 检查组件 `name` 字段是否一致;或加 `as` 别名 |
| IE 兼容问题 | 用了 `?.` / `??` 报语法错 | 框架兼容 IE,避免 ES2020+ 语法 |
| 双向绑定不更新 | 父级拿不到新值 | 必须 emit `input` 事件,这是 MForm 的契约 |

---

## 5. 进阶:跨字段类型复用

如果新组件**复用了**已有组件的逻辑(比如"评分+评语"复用了 `Rate` + `Text`):

```js
// items/index.js 里可以这样组织
import ScoreWithComment from './ScoreWithComment'  // 内部 import Rate + Text

export {
    ScoreWithComment,   // 暴露给后端配 type
    // Rate, Text 仍正常导出(给后端单独配)
}
```

不要因为有了"评分+评语"就把 `Rate` 删了——后端别处可能还在单独用 `Rate`。

---

## 6. 验证 checklist

扩展完一个新字段类型,过一遍:

- [ ] 组件在 `items/{Name}/index.vue` 创建完毕
- [ ] `items/index.js` 已 import + export
- [ ] 组件 `name` 字段 = 后端 `fieldType` 字符串
- [ ] 组件接收 `value` prop、emit `input` 事件
- [ ] 只读/必填状态能通过 `fieldItem.disabled` / `fieldItem.isRequired` 体现
- [ ] dev server 启起来,浏览器 console 无 error
- [ ] 表单里能正常输入/选择/保存
- [ ] 后端收到的数据格式符合预期
- [ ] 关闭浏览器开发者工具(框架禁用)再开一遍,看是否还有副作用

---

## 7. 下一步去哪

- **写新功能** → [frontend-module-quickstart](../frontend-module-quickstart/SKILL.md)
- **列表/表单定制** → [frontend-module-list](../frontend-module-list/SKILL.md) / [frontend-module-edit](../frontend-module-edit/SKILL.md)
- **页面出问题** → [frontend-module-page-debug](../frontend-module-page-debug/SKILL.md)
