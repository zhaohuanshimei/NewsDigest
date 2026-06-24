# Web Archive Page Design

> Status: approved for planning
> Scope: `apps/web`
> Date: 2026-06-24

## Goal

在首页真实 API 接通之后，为 `apps/web` 增加第一个独立的第二页面：`/archive`。

这轮目标不是扩展完整站点导航，而是建立一个最小但真实的归档阅读入口，证明以下三件事：

- 前端可以在首页之外继续沿用同一套 seam 模式扩展页面
- `GET /api/v1/archive/dates` 可以被 Astro 页面以只读方式消费
- 归档页能在不破坏现有极简视觉系统的前提下，建立第二个稳定页面模板

## Problem

当前项目已经具备：

- `GET /api/v1/digests/latest`
- `GET /api/v1/archive/dates`
- 首页 latest digest 的真实 API 接入闭环

但前端仍然只有首页。若现在直接跳到 cluster 详情、article 详情或单日 digest 页面，会在缺少“第二个只读列表页”验证的情况下继续扩展，导致：

- 页面模式从首页直接跳到详情页，缺少中间层信息架构验证
- seam 与状态处理模式无法在第二个页面上得到复用验证
- 导航边界会在后续实现时临时决定，而不是现在先沉淀一个稳定入口

因此，这一轮应先完成最小归档页，而不是扩大到多页面闭环。

## Research Decision

本轮采用“独立 `/archive` 页面 + 最小日期列表”的方案，而不是把归档塞回首页，也不是在这一轮顺带做单日 digest 页面。

### Candidates Considered

- 独立 `/archive` 页面，只显示日期列表
- `/archive` 与 `/digests/[date]` 一起做
- 先把归档区块挂到首页底部

### Decision

选择：

- 新增独立路由 `/archive`
- 只消费 `ArchiveDateListResource`
- 只渲染日期列表及其三态视图
- 不在本轮实现单日 digest 页面

### Why This Wins

- 范围最小，能快速验证第二个真实页面
- 与首页的 seam / state / Astro 构建测试模式保持一致
- 避免首页职责变重
- 为后续 `/digests/[date]` 留出清晰的下一步，而不是在本轮一次做完

## Scope

### In Scope

- 新增 `/archive` 页面
- 新增 archive 内容 seam
- 默认请求真实 API `GET /api/v1/archive/dates`
- 提供 `success` / `empty` / `error` 三种状态
- 为归档页增加最小列表样式
- 增加 seam 测试与页面构建测试
- 为归档页增加独立状态覆盖开关 `PUBLIC_ARCHIVE_STATE`

### Out of Scope

- `/digests/[date]`
- cluster / article 详情页
- 归档分页
- 归档按月或按年分组
- 完整导航栏或站点地图
- 搜索、筛选、客户端交互

## Architecture

### High-Level Shape

归档页继续复用首页已经验证过的分层方式：

- 页面层：`src/pages/archive.astro`
- 内容层：`src/lib/content/getArchiveDates.ts`
- 配置层：`src/lib/config/site.ts`
- 展示层：`src/components/archive/*` 与已有状态组件

依赖方向保持单向：

- 页面层依赖 archive seam
- seam 决定当前读真实 API 还是读覆盖态
- 页面不直接持有 API URL，也不直接写 mock 常量

### Design Principle

- 第二页继续沿用第一页面的结构纪律
- 优先验证模式复用，不优先扩大页面数量
- 优先稳定边界，不优先做完整用户路径

## Module Design

### Proposed Structure

```text
apps/web/
  src/
    pages/
      archive.astro
    components/
      archive/
        ArchiveHeader.astro
        ArchiveDateList.astro
        ArchiveDateItem.astro
    lib/
      content/
        getArchiveDates.ts
      config/
        site.ts
    tests/
      content/
        getArchiveDates.test.ts
      archive-page.test.ts
      archive-page-states.test.ts
```

### Module Responsibilities

#### `src/pages/archive.astro`

- 负责装配 archive 页面
- 调用单一 seam `loadArchiveDates()`
- 只分支处理 `success` / `empty` / `error`

#### `src/lib/content/getArchiveDates.ts`

- 对页面暴露单一读取接口
- 默认请求 `/archive/dates`
- 将 API 结果映射为受控页面状态
- 支持测试注入 `fetchImpl`
- 支持通过 `PUBLIC_ARCHIVE_STATE` 做本地覆盖

#### `src/components/archive/*`

- `ArchiveHeader.astro`：归档页标题与说明
- `ArchiveDateList.astro`：日期列表容器
- `ArchiveDateItem.astro`：单条日期项

这些组件只消费稳定 props，不关心数据源来自真实 API 还是覆盖态。

## Data Flow

### Contract

归档页当前只消费：

```ts
interface ArchiveDateListResource {
  dates: string[];
}
```

### Page State

`loadArchiveDates()` 返回三态：

- `success`: `{ kind: "success"; dates: string[] }`
- `empty`: `{ kind: "empty" }`
- `error`: `{ kind: "error"; message: string }`

### Override Rule

归档页使用独立覆盖开关：

- `PUBLIC_ARCHIVE_STATE=success|empty|error`

这样可以避免与首页的 `PUBLIC_DIGEST_STATE` 混用，保持页面边界清晰。

### Default Behavior

无覆盖时：

- 请求 `GET /api/v1/archive/dates`
- `200` 且 `dates.length > 0` => `success`
- `200` 且 `dates.length === 0` => `empty`
- 非成功响应或网络异常 => `error`

## Page Design

### Information Architecture

`/archive` 页面只承担“浏览已发布日期列表”的任务。

页面由两段组成：

1. 轻量页头
2. 日期列表或状态面板

### Content Rules

- 每条日期只显示标准日期字符串
- 本轮不要求把日期做成真实单日页链接
- 若后续要接 `/digests/[date]`，应在下一轮扩展，不在本轮伪造跳转

## Visual Direction

归档页继续复用首页的“极简升级版”方向：

- 单列布局
- 大留白
- 细分隔线
- 系统字体栈
- 低饱和正文与 metadata

新样式只补归档列表所需的最小类名，不再引入第二套视觉系统。

## Testing And Verification

本轮至少覆盖以下验证：

- seam 单测：
  - 覆盖态 `success` / `empty` / `error`
  - 真实 fetch 成功
  - 空列表映射为 `empty`
  - fetch 失败映射为 `error`
- 页面构建测试：
  - success 构建能看到日期列表
  - empty 构建能看到空态文案
  - error 构建能看到错误态文案

构建测试必须继续使用独立输出目录，避免并行测试互相覆盖 `dist/`。

## Acceptance Criteria

完成本轮后，以下条件必须同时成立：

- `apps/web` 存在独立 `/archive` 页面
- 归档页通过单一 seam 消费 archive dates
- 默认读取真实 API `/api/v1/archive/dates`
- 归档页存在 `success` / `empty` / `error` 三态
- 归档页保持与首页一致的极简视觉语言
- seam 测试与页面构建测试通过
- 未引入 `/digests/[date]` 或其他超出范围的页面

## Risks And Non-Goals

### Risks

- 若现在就把日期做成真实链接，会把本轮 scope 拉大到第二个资源页面
- 若归档页复用首页覆盖开关，会让测试边界变模糊
- 若样式为归档页单独起一套语言，会破坏当前视觉一致性

### Non-Goals

- 本轮不是 digest 日期详情页交付
- 本轮不是站点导航系统交付
- 本轮不是搜索/筛选交付

## Recommended Next Step

本 spec 获批后，下一步应写 implementation plan，建议拆成三个子阶段：

1. 建立 archive seam 与测试
2. 落 `/archive` 页面与组件
3. 落 success/empty/error 构建验证与 README 更新
