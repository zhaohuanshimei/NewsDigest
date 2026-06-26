# @news-digest/ui

News Digest V2 设计 token 与基础 UI 组件包。

## 设计方向

采用"极简升级版"（Direction C）风格，核心特征：

- **排版**：系统字体栈，衬线标题 + 无衬线正文，清晰的字号层级
- **色彩**：黑白灰为主，低饱和度辅助色，满足 WCAG 2.1 AA 对比度
- **间距**：4px 基础网格，充裕留白，呼吸感
- **响应式**：移动优先，三档断点（sm / md / lg）

## 包结构

```
src/
├── index.ts              # 统一导出入口
├── tokens/
│   ├── colors.ts         # 颜色 token
│   ├── spacing.ts        # 间距 token + 响应式断点
│   └── typography.ts     # 字体 / 字号 / 行高 token
└── docs/
    └── design-tokens.md  # Token 使用文档
```

## 使用方式

```ts
import { colors, spacing, typography, breakpoints } from '@news-digest/ui';
```

详细使用说明见 [`src/docs/design-tokens.md`](./src/docs/design-tokens.md)。

## 约束

- 零运行时依赖，仅导出常量与类型定义
- 所有颜色满足 WCAG 2.1 AA 级对比度要求
- 移动端优先，触摸目标 >= 44px
