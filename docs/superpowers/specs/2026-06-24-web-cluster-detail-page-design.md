# Web Cluster Detail Page Design

> Status: approved for planning
> Scope: `apps/web`
> Date: 2026-06-24

## Goal

在首页与归档页已经建立稳定只读模式之后，为 `apps/web` 增加第一个详情型页面：`/clusters/[id]`。

这轮目标不是扩展完整站点导航，也不是一次打通文章阅读闭环，而是验证以下三件事：

- Astro 前端可以从“列表页”继续延伸到“详情页”
- `GET /api/v1/clusters/{cluster_id}` 可以被静态详情页消费
- 详情页仍能保持 seam 模式、极简视觉语言与零运行时 JS 的约束

## Problem

当前项目已经具备：

- 首页 `GET /api/v1/digests/latest`
- 归档页 `GET /api/v1/archive/dates`
- cluster 详情接口 `GET /api/v1/clusters/{cluster_id}`

但前端仍缺少第一个真实详情页。如果现在直接跳到 article 详情页或单日 digest 页面，会带来几个问题：

- 首页 digest entry 的 `cluster_id` 仍然只是静态字段，没有落成真实页面目标
- 前端详情页模式尚未建立，后续每个资源页都会重新决定结构与状态边界
- 列表页与详情页之间的最小信息架构链路还没有被验证

因此，这一轮最合适的下一步不是继续做第二个列表页，也不是直接做最末端文章页，而是先完成最小 cluster detail 页。

## Research Decision

本轮采用“最小 cluster 详情页”的方案，而不是在这一轮预留更重的前瞻结构。

### Candidates Considered

- 最小 cluster 详情页，只消费当前 `ClusterDetailResource`
- cluster 详情页 + 轻量返回上下文
- cluster 详情页 + 未来相关文章/来源区占位

### Decision

选择：

- 新增 `/clusters/[id]`
- 只消费当前已有 contract 字段
- 只渲染详情头部与元信息区
- 用受控状态映射处理成功、缺失与错误
- 不在本轮预留相关文章列表、原文外链或复杂导航

### Why This Wins

- 严格贴合当前 contract，不会为了 UI 需要虚构数据结构
- 能最小成本验证“列表到详情”的第二种页面模式
- 为后续 article 页面留下清晰边界，而不是在本轮提前重叠职责
- 页面实现和测试可以高度复用首页与归档页的模式

## Scope

### In Scope

- 新增动态路由 `/clusters/[id]`
- 新增 cluster 内容 seam
- 默认请求真实 API `GET /api/v1/clusters/{cluster_id}`
- 提供受控的 `success` / `not-found` / `error` 状态
- 首页 digest entry 在本轮接入真实 cluster 详情链接
- 为 cluster 详情页增加最小静态样式
- 增加 seam 单测与页面构建测试
- 为 cluster 详情页增加独立状态覆盖开关

### Out of Scope

- `/articles/[id]`
- `/digests/[date]`
- 相关文章列表
- 原文来源列表
- cluster 内文章明细展开
- 完整 breadcrumb、站点导航系统或前进后退逻辑
- 客户端交互、搜索、筛选、分页

## Architecture

### High-Level Shape

cluster 详情页继续复用当前已验证的分层方式：

- 页面层：`src/pages/clusters/[id].astro`
- 内容层：`src/lib/content/getClusterDetail.ts`
- 配置层：`src/lib/config/site.ts`
- 展示层：`src/components/cluster/*` 与已有状态组件

依赖方向保持单向：

- 页面层依赖 cluster seam
- seam 决定当前读真实 API 还是读覆盖态
- 页面不直接发 fetch，不直接拼 API URL，也不直接引用 mock 常量

### Design Principle

- 先建立第一个详情页模板，再扩展更多详情资源
- 严格以 contract 为中心，不以未来需求反推当前 UI
- 页面应足够完整可读，但不过度承诺未来信息密度

## Module Design

### Proposed Structure

```text
apps/web/
  src/
    pages/
      clusters/
        [id].astro
    components/
      cluster/
        ClusterDetailHeader.astro
        ClusterMetaList.astro
    lib/
      content/
        getClusterDetail.ts
        mockCluster.ts
      config/
        site.ts
    tests/
      content/
        getClusterDetail.test.ts
      cluster-page.test.ts
      cluster-page-states.test.ts
```

### Module Responsibilities

#### `src/pages/clusters/[id].astro`

- 负责装配 cluster detail 页面
- 从 `Astro.params.id` 读取 cluster id
- 只调用单一 seam `loadClusterDetail()`
- 只分支处理 `success` / `not-found` / `error`

#### `src/lib/content/getClusterDetail.ts`

- 对页面暴露单一读取接口
- 默认请求 `/clusters/{id}`
- 将 API 结果映射为受控页面状态
- 支持测试注入 `fetchImpl`
- 支持通过独立 env 开关做本地覆盖

#### `src/components/cluster/*`

- `ClusterDetailHeader.astro`：标题、摘要与类别
- `ClusterMetaList.astro`：来源数与 digest dates 元信息

这些组件只消费稳定 props，不关心数据源来自真实 API 还是覆盖态。

## Data Flow

### Contract

cluster 详情页当前只消费：

```ts
interface ClusterDetailResource {
  id: string;
  category: string;
  headline: string;
  summary: string;
  source_count: number;
  digest_dates: string[];
}
```

### Page State

`loadClusterDetail(clusterId)` 返回三态：

- `success`: `{ kind: "success"; cluster: ClusterDetailResource }`
- `not-found`: `{ kind: "not-found" }`
- `error`: `{ kind: "error"; message: string }`

### Override Rule

cluster 页使用独立覆盖开关：

- `PUBLIC_CLUSTER_STATE=success|not-found|error`

这样可以避免与首页、归档页共用状态开关，保持测试边界清晰。

### Default Behavior

无覆盖时：

- 请求 `GET /api/v1/clusters/{cluster_id}`
- `200` => `success`
- `404` => `not-found`
- 非成功响应或网络异常 => `error`

## Page Design

### Information Architecture

`/clusters/[id]` 页面只承担“阅读一个聚合事件详情概览”的任务。

页面由两段组成：

1. 详情头部：headline、summary、category
2. 元信息区：source count、digest dates

### Content Rules

- 不展示相关文章列表，因为当前 contract 不提供
- 不伪造 article 链接、source 名称或来源域名
- `digest_dates` 只显示为日期列表，不要求在本轮连到 `/digests/[date]`
- 若首页要提供入口，应直接把 digest entry 链到对应 cluster detail，而不是发明中间跳板页

## Routing Decision

### Candidate Shapes

- `/clusters/[id]`
- `/cluster/[id]`
- `/topics/[id]`

### Decision

选择 `/clusters/[id]`。

原因：

- 与现有 API 资源命名完全一致
- 前后端语义对齐，不额外引入 topic/story 等新词
- 后续 article 页面也可以顺势采用 `/articles/[id]`

## Visual Direction

cluster 详情页继续复用首页与归档页的“极简升级版”方向：

- 单列布局
- 大留白
- 细分隔线
- 低饱和 metadata
- 用少量层级强调 headline 与摘要

详情页不需要做成杂志式长文页面，而应更像“静态事件卡片的展开版”。

## Error Handling

### `not-found`

当 cluster id 在后端不存在时：

- 页面展示明确的 not-found 面板
- 不把 `404` 混成通用 error
- 文案应告诉用户该 cluster 当前不存在或已不可用

### `error`

网络失败、非 404 的异常状态或 contract 不匹配时：

- 页面展示已有 error 面板风格
- 不泄露底层实现细节
- 继续使用简洁、统一的错误文案

## Testing And Verification

本轮至少覆盖以下验证：

- seam 单测：
  - 覆盖态 `success` / `not-found` / `error`
  - 真实 fetch 成功
  - `404` 映射为 `not-found`
  - 网络失败映射为 `error`
- 页面构建测试：
  - success 构建能看到 headline、summary、source count
  - not-found 构建能看到缺失态文案
  - error 构建能看到错误态文案
- 首页链接测试或静态构建校验：
  - 首页最新 digest entry 会指向 `/clusters/cluster-ai-chip-001`

构建测试必须继续使用独立输出目录，避免并行测试互相覆盖 `dist/`。

## Acceptance Criteria

完成本轮后，以下条件必须同时成立：

- `apps/web` 存在动态路由 `/clusters/[id]`
- 页面通过单一 seam 消费 cluster detail
- 默认读取真实 API `/api/v1/clusters/{cluster_id}`
- 详情页存在 `success` / `not-found` / `error` 三态
- 页面只展示当前 contract 能保证的字段
- 首页存在指向 cluster detail 的真实链接
- seam 测试与页面构建测试通过
- 未引入 article 页面、单日 digest 页面或伪造的相关文章区

## Risks And Non-Goals

### Risks

- 若现在为详情页预留过多未来版位，会让当前 contract 显得不够用并诱发假数据
- 若把 `404` 直接映射成通用 `error`，后续用户体验会变得模糊
- 若首页链接和详情路由不同步，信息架构会断裂

### Non-Goals

- 本轮不是文章详情页交付
- 本轮不是单日 digest 页交付
- 本轮不是全站导航系统交付
- 本轮不是更丰富 cluster 数据模型交付

## Recommended Next Step

本 spec 获批后，下一步应写 implementation plan，建议拆成三个子阶段：

1. 建立 cluster seam 与单测
2. 落动态路由、成功态详情页与首页链接
3. 落 not-found/error 构建验证与 README 更新
