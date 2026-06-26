# Design Tokens 使用指南

本文档说明 `@news-digest/ui` 中设计 token 的分类、用法和设计意图。

## 设计方向

本包采用 **极简升级版（Direction C）** 风格，融合报纸风格的衬线标题与系统字体栈正文。核心原则：

1. **零运行时依赖** — 不加载任何 Web Font，全部使用系统字体栈
2. **移动优先** — 基础样式面向移动端，通过断点向上扩展
3. **可读性优先** — 所有文本颜色组合满足 WCAG 2.1 AA（对比度 >= 4.5:1）
4. **充裕留白** — 基于 4px 网格的宽松间距系统

---

## 颜色 (Colors)

### 导入

```ts
import { colors, neutral, accent } from '@news-digest/ui';
```

### 结构

| 类别 | 说明 | 示例 |
|------|------|------|
| `neutral` | 灰阶色板（黑→白） | `neutral[700]` = `#404040` |
| `accent` | 低饱和度蓝色强调色 | `accent[500]` = `#2E6EA6` |
| `colors` | 语义化颜色别名 | `colors.textPrimary`, `colors.link` |

### 使用规则

- **组件中只使用语义别名**（`colors.textPrimary`），不直接引用灰阶值
- 需要自定义组合时，使用 `neutral` 或 `accent` 的具体色阶
- 所有正文文本颜色 >= 7:1 对比度（`neutral[700]` 在白色背景上为 14.7:1）

---

## 间距 (Spacing)

### 导入

```ts
import { spacing, spacingScale, layout } from '@news-digest/ui';
```

### 间距比例

基于 4px 网格，提供 10 级间距：

| Token | px | 典型用途 |
|-------|-----|---------|
| `spacing[0]` | 0 | 无间距 |
| `spacing[1]` | 4px | 图标内边距、微间距 |
| `spacing[2]` | 8px | 行内元素间距 |
| `spacing[3]` | 12px | 紧凑内边距 |
| `spacing[4]` | 16px | 默认内边距、垂直节奏 |
| `spacing[6]` | 24px | 区块内边距、卡片间距 |
| `spacing[8]` | 32px | 大卡片内边距 |
| `spacing[12]` | 48px | 区块分隔 |
| `spacing[16]` | 64px | 页面级区块间距 |
| `spacing[24]` | 96px | 首屏 / 主要区块间距 |

### 布局常量

```ts
layout.contentMaxWidth  // '680px' — 文章正文最大宽度
layout.pageMaxWidth     // '1200px' — 页面最大宽度
layout.touchTargetMin   // '44px'  — 最小触控目标
layout.radiusCard       // '4px'   — 卡片圆角
layout.radiusButton     // '2px'   — 按钮圆角
```

---

## 排版 (Typography)

### 导入

```ts
import { fontFamily, fontSize, typography } from '@news-digest/ui';
```

### 字体族

| 名称 | 用途 | 首选字体 |
|------|------|---------|
| `fontFamily.serif` | 标题、强调 | Georgia |
| `fontFamily.sans` | 正文、UI 元素 | 系统无衬线 |
| `fontFamily.mono` | 日期、元数据、代码 | SF Mono / Consolas |

### 排版预设

预设将 `fontFamily` + `fontSize` + `lineHeight` + `fontWeight` + `letterSpacing` 组合成即用样式：

| 预设 | 用途 | 字族 | 字号 |
|------|------|------|------|
| `hero` | 首屏大标题 | serif | 40px |
| `pageTitle` | 页面标题 | serif | 32px |
| `cardTitle` | 卡片 / 文章标题 | serif | 24px |
| `sectionHeading` | 区块标题 | serif | 20px |
| `body` | 正文 | sans | 16px |
| `lead` | 文章导语 | sans | 18px |
| `caption` | 副文本、说明 | sans | 14px |
| `meta` | 日期、来源、标签 | sans | 13px |
| `tag` | 分类标签（大写） | sans | 12px |

### 使用示例

```ts
import { typography, colors, spacing } from '@news-digest/ui';

// 在 CSS-in-JS 或组件样式中：
const cardTitleStyle = {
  ...typography.cardTitle,
  color: colors.textPrimary,
  marginBottom: spacing[2],
};
```

---

## 响应式断点 (Breakpoints)

### 导入

```ts
import { breakpoints, breakpointValues } from '@news-digest/ui';
```

| 断点 | 值 | 目标设备 |
|------|-----|---------|
| `sm` | 640px | 平板竖屏 |
| `md` | 1024px | 平板横屏 / 小桌面 |
| `lg` | 1280px | 大桌面 |

### 响应式排版调整建议

基础样式面向移动端（< 640px）。建议在媒体查询中按断点递增：

- `>= sm`：`cardTitle` 可提升至 `fontSize['3xl']`（24px）
- `>= md`：`body` 可使用 `lineHeight.relaxed`（1.8），增大行距提升可读性
- `>= lg`：`pageTitle` 可使用 `fontSize['5xl']`（40px），页面采用双栏布局

---

## 场景速查

### 首页

- 大标题：`typography.hero` / `typography.pageTitle`
- 文章卡片标题：`typography.cardTitle`
- 文章摘要：`typography.body`
- 元数据（日期、来源）：`typography.meta`
- 分类标签：`typography.tag` + `accent[100]` 背景

### 归档页

- 页面标题：`typography.pageTitle`
- 日期分组标题：`typography.sectionHeading`
- 文章条目标题：`typography.cardTitle`
- 文章条目摘要：`typography.caption`

### 详情页

- 文章标题：`typography.pageTitle`
- 导语段落：`typography.lead`
- 正文：`typography.body`
- 来源链接：`colors.link` / `colors.linkHover`

---

## 可访问性检查清单

- [ ] 正文文本对比度 >= 4.5:1（`colors.textSecondary` 在白色背景上为 14.7:1）
- [ ] 触控目标 >= 44px（使用 `layout.touchTargetMin`）
- [ ] 链接可辨识（使用 `colors.link` 而非仅靠颜色）
- [ ] 焦点状态可见（使用 `colors.borderFocus` 作为 focus ring 颜色）
