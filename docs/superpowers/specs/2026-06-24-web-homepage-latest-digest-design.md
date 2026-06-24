# Web Homepage Latest Digest Design

> Status: approved for planning
> Scope: `apps/web`
> Date: 2026-06-24

## Goal

将 News Digest V2 从“只有 API 与 shared-types 骨架”推进到“存在真实 Web 客户端首页”的下一步，建立一个最小但完整的 `apps/web` 首页阅读闭环。

这轮工作的目标不是完成整个 Web 站点，而是验证以下四件事：

- `apps/web` 可以成为真实可启动的前端应用，而不是占位目录
- 首页可以消费与真实 API 契约一致的 `DigestResource`
- 首页样式能够落到“极简升级版”的第一版，而不是默认脚手架页面
- 页面层与数据来源解耦，后续可以从 mock 平滑切换到真实 API

## Problem

当前仓库已经拥有：

- `services/api` 的最小只读资源面
- `packages/shared-types` 的公开资源契约

但 `apps/web` 仍然只有占位 README。若此时直接进入归档页、详情页、SEO、组件库抽取或真实 API 联调，会在没有最小前端骨架、没有首页信息架构、没有稳定视觉基线的情况下推进，导致以下问题：

- 前端目录与页面边界会在实现中临时决定，缺少稳定结构
- 页面可能直接耦合 mock 数据或 API URL，后续切换成本升高
- UI 可能先退化成脚手架默认风格，再返工到目标视觉方向

因此，这一轮必须先证明：

- `apps/web` 能以 `Astro` 形式真实运行
- 首页能以真实契约 shape 渲染 latest digest
- 数据 seam 与页面 seam 已分开
- 视觉语言与项目“内容优先、极简、无干扰”的方向保持一致

## Research Decision

本轮在 Web 首页数据接入上采用 `Mock Behind Real Contract` 策略，而不是立即接真实 API，也不是让页面直接 import 零散 mock 常量。

### Candidates Considered

- 构建时直接请求真实 `GET /api/v1/digests/latest`
- 服务端请求时拉取真实 API
- 页面直接 import mock 数据
- 通过单一 gateway 读取真实契约 shape 的 mock 数据

### Decision

采用以下组合：

- 使用 `Astro + TypeScript` 建立前端骨架
- 首页通过一个单一 seam `getLatestDigest()` 读取数据
- `getLatestDigest()` 当前返回与真实 API 一致的 `DigestResource`
- mock 数据位于数据层内部，不暴露给页面层

### Why This Wins

- 符合仓库已经确定的 `Astro` 与静态站点方向
- 保持页面层只依赖资源契约，不依赖数据来源细节
- 避免页面直接耦合 mock 文件，后续切真 API 只需替换 gateway 实现
- 在不引入真实联调复杂度的前提下，让首页尽早使用真实契约语言

## Scope

### In Scope

- 初始化 `apps/web` 为可本地启动的 `Astro + TypeScript` 应用
- 建立基础布局、全局样式入口与首页路由
- 首页渲染 latest digest 的阅读视图
- 使用与真实 API 契约一致的 mock `DigestResource`
- 为首页提供成功态、空态、错误态
- 落第一版“极简升级版”视觉基线
- 通过配置或数据层 seam 为后续切换真实 API 预留位置

### Out of Scope

- 真实 API 联调
- 归档页、日期页、cluster 详情页、article 详情页、RSS 页
- 浏览器端 hydration 交互、筛选、搜索、锚点导航
- `packages/ui` 的正式抽取与设计系统沉淀
- 完整 SEO 文案与社交卡片策略
- 前端端到端测试矩阵与复杂可视回归

## Architecture

### High-Level Shape

本轮只建立一个最小 Web 首页闭环：

- 页面层：负责首页结构、阅读体验、视觉呈现
- 数据层：负责提供 `DigestResource`
- 配置层：负责站点常量与未来 API 切换位

依赖方向应保持单向：

- 页面与组件依赖数据 seam
- 数据 seam 决定当前取 mock 还是未来真实 API
- 页面不直接依赖 mock 文件

### Design Principle

- 优先建立 seam，不优先建立复杂组件系统
- 优先建立阅读体验，不优先建立完整站点信息架构
- 优先让 mock 与真实契约对齐，不优先让 mock 更贴近某个临时 UI shape
- 优先零运行时 JS，不引入无必要客户端逻辑

## Module Design

### Proposed Structure

```text
apps/web/
  public/
  src/
    pages/
      index.astro
    layouts/
      BaseLayout.astro
    components/
      digest/
        DigestHeader.astro
        DigestEntryList.astro
        DigestEntryItem.astro
      states/
        EmptyState.astro
        ErrorState.astro
    lib/
      content/
        getLatestDigest.ts
        mockDigest.ts
      config/
        site.ts
    styles/
      global.css
  astro.config.mjs
  package.json
  tsconfig.json
```

### Module Responsibilities

#### `src/pages/index.astro`

- 负责首页的数据读取与页面装配
- 不直接持有 mock 常量
- 只组织成功态、空态、错误态的页面分支

#### `src/layouts/BaseLayout.astro`

- 提供统一页面壳层
- 提供基础 title 和 meta 基线
- 承载全局样式入口

#### `src/components/digest/*`

- `DigestHeader.astro`：渲染 digest 日期与发布时间
- `DigestEntryList.astro`：负责 entry 列表容器
- `DigestEntryItem.astro`：负责单条阅读块

这些组件只消费稳定 props，不关心数据源来自 mock 还是 API。

#### `src/components/states/*`

- `EmptyState.astro`：处理无数据时的可读反馈
- `ErrorState.astro`：处理读取失败时的可读反馈

这两个状态组件让首页结构在切换真实 API 时保持稳定。

#### `src/lib/content/getLatestDigest.ts`

这是本轮最重要的 seam。

它的职责是：

- 对页面暴露单一读取接口
- 当前返回 mock `DigestResource`
- 未来可以切换到 HTTP/API，而不改页面组件

这意味着：

- 页面层不直接 import `mockDigest.ts`
- 真实 API 接入时优先替换 `getLatestDigest()`，而不是直接修改首页模板

#### `src/lib/content/mockDigest.ts`

- 只存放当前首页所需的 mock 数据
- 数据 shape 必须与 `DigestResource` 保持一致
- 这是实现细节，不作为页面层公开接口

## Homepage Design

### Information Architecture

首页只承担“阅读 latest digest”的任务，不承担完整导航入口。

页面建议分为三段：

1. 轻量头部
2. digest 主阅读区
3. 极轻页脚

#### Header

包含：

- 站点名
- 一句极短说明
- 可选的更新提示

要求：

- 信息克制
- 不抢主内容视觉权重
- 不引入复杂导航条

#### Main Content

首页主体只渲染一个 `DigestResource`：

- digest 日期
- 发布时间
- 按 `rank` 顺序的 entry 列表

每个 entry 至少显示：

- `headline`
- `summary`
- `source_count`

说明：

- 当前真实 `DigestEntryResource` 只提供 `headline`、`summary`、`source_count` 等字段，不提供原文 URL 或来源名称
- 因此首页这轮只展示契约中已稳定存在的字段，不额外伪造原文入口
- 原文入口与更细粒度来源信息应在后续 digest 契约扩展后再进入首页需求

这轮不要求：

- 分类 chips
- 折叠交互
- 详情页链接壳层
- 复杂导航和筛选

#### Footer

只保留最轻的收尾信息，不让其与正文竞争注意力。

## Visual Direction

### Chosen Direction

采用 `docs/design/DESIGN_DIRECTIONS.md` 中的“方向 C: 极简升级版”。

### Visual Rules

- 单列布局
- 大量留白
- 强调排版层级而不是装饰元素
- 使用系统字体栈
- 使用细分隔线和克制的强调色
- 保持接近静态阅读物，而不是卡片瀑布流

### Typography

- 页面标题最大且最稳
- digest 日期与发布时间为次级信息
- `headline` 明显强于 `summary`
- metadata 弱化但保持可读

### Color

- 背景采用近白或浅暖中性色
- 正文采用深灰而非纯黑
- 链接或强调元素使用单一、低饱和强调色

### Motion

- 只允许 `hover` / `focus` 的轻微反馈
- 不加入运行时动画或浏览器端动画脚本

## Data Flow

### Current Phase

首页调用：

- `getLatestDigest()`

`getLatestDigest()` 当前返回：

- 成功：`DigestResource`
- 空：`null` 或等价受控结果
- 错误：受控错误结果

页面根据结果渲染：

- 成功态
- 空态
- 错误态

### Future Migration Path

当后续切换到真实 API 时：

- 保持页面与组件接口不变
- 保持 mock 数据 shape 不变
- 只替换 `getLatestDigest()` 的内部实现

这条迁移路径是本轮设计成功与否的关键标准。

## Testing And Verification

本轮只要求最小可验证能力：

- `apps/web` 可本地启动
- 首页路由存在
- 首页构建通过
- 首页能渲染 mock `DigestResource`
- 空态与错误态至少各有一种可验证方式

推荐测试重点：

- 页面级公开行为验证
- 不测试内部模块实现细节

推荐行为示例：

- “首页显示 latest digest 标题”
- “首页显示 digest 日期”
- “无数据时显示可读提示”
- “读取失败时显示简洁错误反馈”

## Acceptance Criteria

完成本轮后，以下条件必须同时成立：

- `apps/web` 不再是占位目录，而是可运行的 Astro 项目
- 首页路由存在并可渲染
- 首页通过单一 seam 消费 latest digest
- mock 数据 shape 与 `DigestResource` 保持一致
- 页面具有成功态、空态、错误态
- 页面视觉不退化为默认脚手架样式，能体现第一版“极简升级版”
- 不引入浏览器端运行时依赖作为渲染前提

## Risks And Non-Goals

### Risks

- 若页面直接 import mock 数据，后续切真 API 时会让模板层返工
- 若样式一开始过度组件化，会把这轮简单首页演化成 UI 系统工程
- 若首页过早加入归档、详情、RSS 入口，会把 scope 扩大到多页面工程

### Non-Goals

- 这轮不是完整 Web 客户端交付
- 这轮不是 API 联调阶段
- 这轮不是设计系统沉淀阶段
- 这轮不是 SEO 完整交付阶段

## Recommended Next Step

在本 spec 获批后，下一步应写 implementation plan，目标是把工作拆为三个实现子阶段：

1. 初始化 `Astro` 骨架与基础布局
2. 落首页 latest digest 阅读页与 mock seam
3. 落极简升级版样式与最小验证
