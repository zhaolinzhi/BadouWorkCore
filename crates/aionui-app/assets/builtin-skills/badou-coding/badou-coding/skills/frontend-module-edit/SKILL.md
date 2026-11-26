---
name: frontend-module-edit
description: 八斗 Module 平台**表单页**(新增/编辑/查看) customSetting **总览/索引**。**何时调用**:用户要做表单页定制,且需求横跨多个 key(例如"字段联动 + 动态显隐 + 提交前改值")、想看完整 key 列表、或不确定用哪个 key;包含 fields / form-react / validation / submit-flow / layout / tab-nav / flow / tree 八个方向。**何时不调用**:① 用户已明确要改某个具体 key(如 valueChange / validateRule / saveUrl)→ 跳 sub/ 下对应子 skill;② 用户在问列表页 → 走 frontend-module-list;③ 首次接触 Module 平台 → 走 frontend-module-quickstart;④ 通用 Vue/Element UI 问题 → 与 Module 无关。
---

# Module 表单 — customSetting 总览(Edit / Add / View)

> 表单页(新增、编辑、查看)魔改的**总入口**。List 的 customSetting 走 [frontend-module-list](../frontend-module-list/SKILL.md),本 skill 专门处理**表单/详情**页。
> **8 个子 skill** 覆盖 30+ 个 key,本总览负责"用户语义 → 对应 key"映射和"this 指向 / 生命周期"速查。

---

## 0. 动手前先确认 JS 路径(必读)

写在 `public/moduleJs/{mdCode}/edit.js` 的 `export default` 对象里(由后端模型设计器指向)。

**进入前必问 4 件事**(用 AskUserQuestion):

1. **mdCode** 是哪个(比如 `user_info`、`wjx_form`)
2. 是 **edit** 还是 **add** 还是 **view**(决定走 `isView`、`detailId` 等)
3. **JS 完整路径**(是不是 `public/moduleJs/{mdCode}/edit.js`,还是业务方有其它目录)
4. 后端是否已配 `customJs` 指向这个文件(没配的话写也白写)

参考真实案例:`public/moduleJs/business/text/wjx_form_edit.js`。

---

## 1. 表单 customSetting key 全景(按"用户语义"分组)

| 用户想做的事 | 对应 key | 跳到子 skill |
|--------------|---------|------------|
| 字段 A 改了,字段 B/CD 的值/选项/显隐要跟着变 | `valueChange` / `fieldChange` | [sub/fields](sub/fields/SKILL.md) |
| 给某个字段注入组件专属属性(如 `initDialogParams`) | `fieldCustom` | [sub/fields](sub/fields/SKILL.md) |
| 字段渲染前预处理(改 options / 加 url / 转格式) | `beforeFieldChange` | [sub/fields](sub/fields/SKILL.md) |
| 字段后追加 DOM(旁边加按钮/说明/小图标) | `appendDom` | [sub/form-react](sub/form-react/SKILL.md) |
| 整个表单内容完全自己排版(不用默认栅格) | `contentRender` | [sub/form-react](sub/form-react/SKILL.md) |
| 自定义字段校验规则(后端规则不够用时) | `validateRule` | [sub/validation](sub/validation/SKILL.md) |
| 字段动态显隐/只读/必填 | `valueChange` + `setFieldVisible` / `setFieldReadonly` / `setFieldRequired` | [sub/validation](sub/validation/SKILL.md) |
| 地址本 / 弹窗选列表 特殊赋值 | `beforeRender` + `extraValueObj` / `valueText` | [sub/validation](sub/validation/SKILL.md) |
| 改请求详情数据的 URL / 参数(标准响应 = 直接 fieldObj 平铺,无需 customSetting) | `dataUrl` / `paramsBeforeRequest` | [sub/submit-flow/detail-data](sub/submit-flow/detail-data.md) |
| fieldObj 内"值"属性名不是 `value` 时,告诉框架从哪个属性取值(用 `,` 分隔) | `valuePath` | [sub/submit-flow/detail-data §3](sub/submit-flow/detail-data.md#3-valuepathfieldobj内部属性路径) |
| 拿到详情数据后做二次转换(转码/格式化/字段重命名) | `afterEditJSON` | [sub/submit-flow/detail-data §5](sub/submit-flow/detail-data.md#5-aftereditjson详情数据处理) |
| 改请求的模型配置(module JSON) | `afterModuleJSON` / `viewType` / `beforeModuleInitRender` | [sub/submit-flow/module-config](sub/submit-flow/module-config.md) |
| 改保存地址 / 关闭"保存后新增" / 自定义按钮 / 按钮拦截 | `saveUrl` / `openBtnSaveAndAdd` / `buttons` | [sub/submit-flow/save-and-buttons](sub/submit-flow/save-and-buttons.md) |
| 按钮重写时插业务 / 加保存事件节点 | `Save.call(this, btnObj, {...})` | [sub/submit-flow/save-and-buttons §3.6](sub/submit-flow/save-and-buttons.md#36-按钮事件插入点savecallthis-btnobj-) |
| 拿表单对象 / 关闭校验 | `getFormRef()` / `validateForm({openValidate: false})` | [sub/submit-flow/save-and-buttons §3.7](sub/submit-flow/save-and-buttons.md#37-拿表单对象的官方-apigetformref-) |
| 暂存/草稿按钮(跳过校验直接保存) | `buttons` + `validateForm({openValidate: false})` + `Save_Module_Form` | [sub/submit-flow/save-and-buttons §3.10](sub/submit-flow/save-and-buttons.md#310-暂存草稿按钮跳过校验直接保存-) |
| 刷新表单(除模型配置外的全部数据) | `this.$emit('refreshForm')` | [sub/submit-flow/save-and-buttons §3.9](sub/submit-flow/save-and-buttons.md#39-刷新表单thisemitrefreshform-) |
| 表格视图(默认 2 列) | `viewType` | [sub/submit-flow/module-config](sub/submit-flow/module-config.md) |
| 改栅格列数 / 表单 mounted 时统一改字段 | `columnNum` / `beforeRender` | [sub/layout](sub/layout/SKILL.md) |
| 表单标题右侧加自定义内容(上一条/下一条/外部跳转) | `titleRightSlot` | [sub/layout](sub/layout/SKILL.md) |
| tab 切换前拦截(有未保存就提示) | `beforeTabLeave` / `isChangeInfo` | [sub/tab-nav](sub/tab-nav/SKILL.md) |
| tab 切换监听 / 点击监听 | `tabChange` / `tabClick` | [sub/tab-nav](sub/tab-nav/SKILL.md) |
| 关联子表(嵌套表单 / 关联模块编辑) | `childTab` / `scopeSave` / `isChangeInfo` | [sub/tab-nav](sub/tab-nav/SKILL.md) |
| 流程表单(审批流) | `flowButtons` / `Save` / `Submit` (from flow-edit) | [sub/flow](sub/flow/SKILL.md) |
| 树型列表/表单(左侧树+右侧表单) | `treeAjaxConfig` / `defaultParams` / `addFormData` | [sub/tree](sub/tree/SKILL.md) |

---

## 2. 8 个子 skill 跳转(高频)

| 你想干什么 | 跳到 |
|-----------|------|
| **字段值变更/联动/属性注入** | [sub/fields](sub/fields/SKILL.md) |
| **字段后追加 DOM / 整个表单重排版** | [sub/form-react](sub/form-react/SKILL.md) |
| **校验规则 / 动态显隐 / 动态只读 / 地址本赋值** | [sub/validation](sub/validation/SKILL.md) |
| **数据请求/响应(改 URL/参数/数据处理)** | [sub/submit-flow/detail-data](sub/submit-flow/detail-data.md) |
| **模型配置定制(动态加按钮/字段/改视图)** | [sub/submit-flow/module-config](sub/submit-flow/module-config.md) |
| **保存/按钮(改保存接口/自定义按钮/暂存/拦截)** | [sub/submit-flow/save-and-buttons](sub/submit-flow/save-and-buttons.md) |
| **布局(列数 / 渲染前) / 标题栏右侧** | [sub/layout](sub/layout/SKILL.md) |
| **Tab 切换 / 关联子表(嵌套)** | [sub/tab-nav](sub/tab-nav/SKILL.md) |
| **流程表单(审批流)** | [sub/flow](sub/flow/SKILL.md) |
| **树型列表/表单** | [sub/tree](sub/tree/SKILL.md) |

---

## 2.5 `this` 上下文速查表(必读 ⚠️)

> ⚠️ **customSetting 各种 key 的 `this` 指向不同**,且**`this.formData` 在某些 key 里不存在**。
> 这是项目里**最容易踩的坑**(本次踩了 3 个版本才定位到)。

| key | this 指向 | formData 在哪 | fieldList 在哪 |
|---|---|---|---|
| `afterModuleJSON` / `dataUrl` / `valuePath` / `paramsBeforeRequest` / `afterEditJSON` | **moduleEditCode** | `this.formData` ✅ | `this.module.fieldList` |
| `beforeFieldChange` / `beforeRender` / `valueChange` / `validateRule` / `fieldCustom` | **moduleForm** | **`this.$attrs.formData`** ⚠️ | `this.fieldList` ✅ |
| `renderField.formatter/click/render` | **MForm** | `this.$attrs.formData` 或 `this.dataForm`(computed) | `this.dataList` ✅ |
| `beforeModuleInitRender` / `buttons` / `saveUrl` | **moduleEdit** | `this.formData` ✅ | `this.fieldList` ✅ |
| `contentRender` / `appendDom.appendRender` | **DiyFormRender**(MForm 子组件) | ❌ 都不可用,从 `D('xxx')` 取 | ❌ 不可用 |
| `viewType` / `openBtnSaveAndAdd` | 无 this(纯配置) | — | — |

> ⚠️ **`contentRender` 的 this 指向不是 moduleForm,是 DiyFormRender**(MForm 调用 `this.render.call(this, ...)` 时的 this)——
> 所以 `this.formData` / `this.fieldList` / `this.$attrs.formData` 全部是 undefined。需要字段值用参数 `D('fieldName').value`;
> 需要 isView 用 `this.$parent?.isView`(MForm 实例上的 prop)。详见 [form-react §3.2](sub/form-react/SKILL.md#32-this-指向纠错内容渲染的真实上下文)。

**另外,moduleForm / moduleEdit 上还有 `this.elseAttrs`**:

| 属性 | 来源 | 内容 |
|---|---|---|
| `this.elseAttrs` | moduleForm / moduleEdit 的 prop | **关联子表场景**专用:主表 id / 主表字段列表 / 主表作用域 / 实体关联名称 / 关联字段值 / 子模块模型名称 / 模型编码 等(详见 [ChildModuleEdit.vue:206-216](src/components/frame/Module/ModuleEdit/items/ChildModuleEdit.vue#L206-L216)) |
| | | **没有关联子表时是 undefined** |

**核心规律**:

| this 类型 | this.formData 存在? | 说明 |
|---|---|---|
| **moduleEditCode / moduleEdit** | ✅ 存在 | formData 是 moduleEditCode 的 data / moduleEdit 的 props |
| **moduleForm / MForm** | ❌ 不存在 | formData **没声明为 prop**,落到 `this.$attrs.formData` |

> 💡 **判断方法**:打开 `src/components/frame/Module/ModuleForm/index.vue` 和 `src/components/frame/Common/MForm/index.vue`,
> 看 props 里有没有 `formData` —— **没有就要从 `$attrs` 取**。

**实战中常见的 4 种取 formData 写法**:

```js
// ❌ 错误写法(moduleForm / MForm 里用 this.formData = undefined)
beforeRender (fieldList) {
    const checkboxValue = this.formData?.checkboxf?.value  // undefined
}

// ✅ 正确写法 1:从 $attrs 取(moduleForm / MForm)
beforeRender (fieldList) {
    const checkboxValue = this.$attrs?.formData?.checkboxf?.value
}

// ✅ 正确写法 2:从 formScope 取(valueChange 场景,formScope 也带 formData)
valueChange: {
    checkboxf (formScope, fieldName, value) {
        const checkboxValue = formScope.formData?.checkboxf?.value
    }
}

// ✅ 正确写法 3:从 fieldList 取(更稳,formData 改了 fieldList 里字段的 value 也跟着变)
const radioField = this.fieldList.find(f => f.name === 'radiof')
const checkboxField = this.fieldList.find(f => f.name === 'checkboxf')
const checkboxValue = checkboxField?.value?.value ?? checkboxField?.value
```

---

## 3. 三个 viewType 都要写 customSetting 吗?

| viewType | 是不是 customSetting 都生效 | 备注 |
|----------|--------------------------|------|
| **add**(新增,`detailId` 为空或 `'add'`) | ✅ | 走完整个 mount 流程,只是 `dataUrl` 不发请求 |
| **edit**(编辑,有 `detailId`) | ✅ | 走完整流程,会发 `dataUrl` 拉详情 |
| **view**(查看,`isView: true`) | ✅ 但**注意** | `renderField` 此时才生效(查看模式专用) |

**注意**:`view` 模式下,**所有按钮的 `click` 都被框架拦截**(不会真保存),所以 `beforeSave` / `saveUrl` 等"保存向"key 在 view 下没意义。

---

## 4. 与 List customSetting 的关系

| 维度 | List | Edit |
|------|------|------|
| 文件名 | `public/moduleJs/{mdCode}/list.js` | `public/moduleJs/{mdCode}/edit.js` |
| 主入口组件 | `ModuleList` | `ModuleEditCode` → `ModuleEdit` → `ModuleForm` |
| 组件层级 | 2 层(ModuleList → MList) | 3 层(ModuleEditCode → ModuleEdit → ModuleForm) |
| 上下文 | 行数据 + 列表实例 | `formData` + 表单实例 + 字段元数据 |
| this 指向 | moduleList / mList 二选一 | moduleEditCode / moduleEdit / moduleForm / mForm 四选一 |
| 字段值事件 | 无(用 `selectionChange` 替代) | **`valueChange` 必学**,这是表单核心交互 |

> ⚠️ **this 指向差异巨大**——同一个 key 在不同层级调用,this 是不同的 Vue 实例,`this.formData` / `this.$store` / `this.$refs` 行为可能不一样。每个 key 的"this 指向"在子 skill 里都会标清楚。

---

## 5. 完整表单生命周期(模块视角)

```
用户进表单页(URL: /module/edit/:mdCode/:id?)
  │
  ├─ ModuleEditCode mounted
  │    ├─ watch mdCode 触发
  │    │    ├─ 请求 module 配置(editModuleCfg)
  │    │    └─ afterModuleJSON(module)            ← 改 model,影响 fieldList/btnList/childTab
  │    │
  │    ├─ 如果有 detailId,请求详情数据
  │    │    ├─ dataUrl()                          ← 改 URL
  │    │    ├─ paramsBeforeRequest(params)        ← 改请求参数
  │    │    ├─ 后端返回
  │    │    ├─ valuePath 解析路径                 ← 改"哪个字段算详情"
  │    │    └─ afterEditJSON(formData)            ← 拿到数据后再处理
  │    │
  │    └─ 渲染表单(ModuleEdit → ModuleForm)
  │         ├─ beforeRender(fieldList)            ← 改字段(已构造完)
  │         ├─ beforeFieldChange(fieldObj)        ← 改单个字段(格式化前)
  │         ├─ 字段渲染
  │         │    ├─ appendDom(字段后追加)         ← 自定义 DOM
  │         │    └─ fieldCustom(name)             ← 注入组件属性
  │         │
  │         └─ 用户交互
  │              ├─ 字段值变化
  │              │    └─ valueChange[fieldName](scope, name, value, ...)   ← 联动核心
  │              │
  │              └─ 按钮点击(保存/取消/自定义)
  │                   ├─ beforeValidate            ← Event_Expand 注入
  │                   ├─ validateRule(fieldList)   ← 校验
  │                   ├─ before                   ← Event_Expand 注入
  │                   ├─ saveUrl(mdCode)          ← 可改保存 URL
  │                   └─ after                    ← Event_Expand 注入
  │
  └─ 表单 tab 切换(如果有 childTab)
       ├─ beforeTabLeave(activeName, oldName)     ← 拦截
       ├─ tabClick(...)                          ← 点击
       └─ tabChange(...)                         ← 切换成功
```

---

## 6. 低频 key 一行用法(无需子 skill)

| key | 一行说明 |
|------|---------|
| `defaultParamsObj` | 传入默认请求参数对象,会合并到详情请求参数里 |
| `addFormData` | 外部直接传入的表单数据(不走接口),用于隐藏字段追加 |
| `formData` | 直接传给 `module-edit` 的 props,手动指定回显数据 |
| `isView` | `Boolean`,查看模式(影响按钮和 `renderField`) |
| `detailId` | `String`,编辑时为 ID,新增时为空/`'add'` |
| `renderField` | **仅查看模式**生效的字段渲染,格式同 List 版,但**参数是 4 个不是 8 个**:`render(h, context, value, item)` / `formatter(value, item)` / `click(value, item)` |
| `viewType` | `String`,表格视图(后端常配) |
| `beforeApproveRender` | 流程页弹窗 tab 渲染前(详见 [sub/flow](sub/flow/SKILL.md)) |

---

## 7. 入口组件 vs 业务配置的协作

> **核心要点**:`public/moduleJs/{mdCode}/edit.js` 里的 `customSetting` 是**注入物**,不是替代物。

- **业务方写 customSetting** → 框架在合适时机调你的函数/读取你的对象
- **业务方不写** → 框架走默认行为(从后端 module 配置生成)
- **优先级**:customSetting 的存在会**覆盖/增强**默认行为,不会"完全取代"框架

**写 customSetting 时的 3 条铁律**:

1. **绝大多数函数都要 `return`**:忘了 return 是 80% bug 的根源
2. **不要在 customSetting 里直接改 state**:返回修改后的对象即可,框架会接管
3. **this 指向要清楚**:每个 key 在文件里都标注了"this 指向 moduleForm / moduleEdit / moduleEditCode",写之前看仔细

---

## 8. 常见问题(总览)

| 问题 | 现象 | 解决 |
|---|------|------|
| customSetting 写了不生效 | 后端没配 `customJs` 指向这个文件 | 找后端同学在模型设计器里配 |
| `valueChange` 写了没触发 | 字段名拼错 | 严格匹配后端 `fieldList` 里的 name |
| `valueChange` 里改了其它字段,UI 不更新 | 改了 `formData` 但没赋值 | 走 `this.$set` 或组件提供的赋值方法 |
| `saveUrl` 改了还是走默认 | 函数忘了 return URL | 必须 return string |
| `childTab` 配了关联但显示空 | 关联字段没配 `relationEntityField` | 后端 module JSON 要配 |
| `beforeRender` 改字段没生效 | 改了 `fieldList` 没 return | 必须 return 修改后的数组 |
| `view` 模式下按钮被点 | 用了 isView 模式但没禁用按钮 | view 模式框架会自动只读,业务不要在按钮里强行走保存 |

---

## 9. 完整可复制最小骨架

```js
// public/moduleJs/{mdCode}/edit.js
export default {
    // ===== 数据请求/响应 =====
    dataUrl () {
        return `${this.BASEURL}/jdbc/common/${this.mdCode}/getEdit.do`
    },
    paramsBeforeRequest (params) {
        return { ...params, _t: Date.now() }
    },
    afterEditJSON (formData) {
        // 拿到详情后做转换
        return formData
    },
    afterModuleJSON (module) {
        // 改模型配置(按钮、字段、tab)
        return module
    },
    
    // ===== 字段联动 =====
    valueChange: {
        // 字段 A 改了 → 字段 B 跟着变
        status (formScope, fieldName, value) {
            // formScope.setField('relatedField', value === 1 ? 'yes' : 'no')
        }
    },
    
    // ===== 校验 =====
    validateRule (fieldList) {
        return {
            // userName: [{ required: true, message: '必填' }]
        }
    },
    
    // ===== 布局 =====
    columnNum: 2,
    beforeRender (fieldList) {
        // 改字段
        return fieldList
    },
    
    // ===== 按钮 =====
    saveUrl (mdCode) {
        return `${this.BASEURL}/jdbc/common/${mdCode}/saveCustom.do`
    },
    openBtnSaveAndAdd: true,
    buttons: [
        // { id: 'myBtn', name: '我的按钮', click () { ... } }
    ]
}
```

---

## 10. 下一步去哪

- **看 List 的 customSetting** → [frontend-module-list](../frontend-module-list/SKILL.md)
- **总入口/5 分钟上手** → [frontend-module-quickstart](../frontend-module-quickstart/SKILL.md)
- **this 指向 = 具体文件 速查** → [frontend-module-this-reference](../frontend-module-this-reference/SKILL.md)(顶层,`Skill` 工具可加载)
