# News Digest V2 Master Development Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-ready News Digest V2 that is frontend/backend separated, API-first, and structured for future multi-client expansion without reintroducing V1 coupling.

**Architecture:** News Digest V2 is organized as a layered program rather than a single linear feature. L1 delivers the first launchable Web + API product, L2 adds operational tooling, L3 makes the platform client-ready beyond Web, and L4 hardens the system for long-term governance, quality, and cost control.

**Tech Stack:** `FastAPI`, `SQLAlchemy`, `Alembic`, `PostgreSQL`, `Astro`, `TypeScript`, `packages/shared-types`, `packages/ui`, project docs in `docs/`, curated project skills in `.claude/skills` and `.agents/skills`

## Global Constraints

- Short-term implementation scope is limited to `L1 Web + API 首发`; `L2-L4` remain planned but should not start until L1 exit criteria are met.
- All runtime coupling must be API-first; the frontend must not read backend export files directly.
- Shared contracts must live in `packages/shared-types`; reusable UI primitives and design tokens must live in `packages/ui`.
- Documentation is a first-class deliverable; architecture and execution docs in `docs/` must be updated together with implementation.
- Every task must be independently reviewable, testable, and safe for either parallel agent execution or sequential execution.
- Preferred task workflow remains aligned with `docs/context/WORKFLOW.md`: develop, verify, commit, then mark task complete.

---

## How To Use This Plan

### Layer Definitions

- `L1`: Web + API 首发，当前唯一允许启动的实现层。
- `L2`: 运营后台与人工干预能力，在 L1 稳定后启动。
- `L3`: 多客户端扩展能力，在 L2 核心闭环完成后启动。
- `L4`: 长期治理、质量、性能、安全、成本与节奏机制。

### Complexity Ratings

- `S`: 小任务，边界清晰，单一输出。
- `M`: 中任务，涉及 2-3 个相关文件或一个完整子模块。
- `L`: 大任务，跨模块协作但仍可独立验收。
- `XL`: 组合任务，涉及架构边界、跨团队约束或较重集成。

### Execution Modes

- **Parallel Mode:** 同层、无直接依赖的任务可交给不同 Agent 并行推进。
- **Linear Mode:** 若单人持续推进，按本文件中的依赖顺序逐项执行即可。

### Recommended Skill Map

- 架构与边界设计：`domain-modeling`, `codebase-design`, `design-an-interface`
- 前端视觉与页面落地：`frontend-design`, `ui-ux-pro-max`, `agent-browser`, `webapp-testing`
- 测试与质量：`tdd`, `qa`, `review`
- 调试与问题定位：`diagnosing-bugs`
- Git 安全：`git-guardrails-claude-code`

### L1 Exit Criteria

- `services/api` 提供稳定的日报、归档、详情、健康检查 API。
- `apps/web` 通过 API 渲染新 UI，完成首页、归档、详情、RSS 与 SEO 基础面。
- `packages/shared-types` 与 API schema 保持一致，前后端契约不漂移。
- 基本自动化测试、CI、预发与生产部署链路可运行。
- 首发版监控、日志、告警、性能与可访问性基线建立完成。

---

## Dependency Spine

```text
L1.A 计划与架构
  -> L1.B 基础骨架
  -> L1.C 数据与内容链路
  -> L1.D API 交付层
  -> L1.E Web 体验层
  -> L1.F 质量与交付层
  -> L1 发布验收

L2 运营后台
  -> L3 多客户端
  -> L4 长期治理
```

---

## L1: Web + API 首发

### Lane A: 产品与架构基线

#### Task L1-A01: 固化 V2 架构总纲

- **Complexity:** `S`
- **Core Goal:** 在 `docs/architecture/` 中建立 V2 总体架构说明，统一产品目标、模块边界和层级关系。
- **Depends On:** 无
- **Recommended Skills:** `codebase-design`
- **Acceptance:**
  - `docs/architecture/overview.md` 存在并说明 Web、API、shared-types、ui、pipeline 的边界。
  - 文档明确“前端不得直接读导出 JSON”。
  - `claude.md` 与该文档不存在冲突描述。

#### Task L1-A02: 定义领域模型与统一术语

- **Complexity:** `M`
- **Core Goal:** 为 `Source`, `Article`, `Cluster`, `Digest`, `Translation` 建立统一领域词汇和关系图。
- **Depends On:** `L1-A01`
- **Recommended Skills:** `domain-modeling`
- **Acceptance:**
  - `docs/architecture/domain-model.md` 描述核心实体、状态和关系。
  - 同一概念在后续 API、数据库、前端文案中只使用一套命名。
  - 至少列出“数据来源 -> 文章 -> 聚类 -> 日报 -> 翻译 -> 发布”的完整链路。

#### Task L1-A03: 定义 API 资源模型

- **Complexity:** `M`
- **Core Goal:** 设计首发版 API 资源、字段、分页、错误模型和兼容策略。
- **Depends On:** `L1-A02`
- **Recommended Skills:** `design-an-interface`
- **Acceptance:**
  - `docs/architecture/api-boundary.md` 明确首发 API 路由、响应结构和错误格式。
  - 覆盖 `latest digest`、按日期归档、cluster/article detail、health。
  - 指出哪些字段来自 shared types，哪些字段为内部字段不对外暴露。

#### Task L1-A04: 定义共享契约演进规则

- **Complexity:** `S`
- **Core Goal:** 明确 `packages/shared-types` 的来源、版本策略和消费方式。
- **Depends On:** `L1-A03`
- **Recommended Skills:** `codebase-design`
- **Acceptance:**
  - `docs/architecture/contract-strategy.md` 说明 schema 来源与同步策略。
  - 约定契约变更必须先更新 schema，再更新前后端实现。
  - 明确兼容性规则与 breaking change 处理方式。

#### Task L1-A05: 定义非功能目标

- **Complexity:** `S`
- **Core Goal:** 固化 L1 的性能、可访问性、SEO、稳定性与内容更新目标。
- **Depends On:** `L1-A01`
- **Recommended Skills:** `review`
- **Acceptance:**
  - `docs/architecture/non-functional-targets.md` 存在。
  - 明确移动端性能、Lighthouse、健康检查、更新频率、错误恢复的最低基线。
  - 这些目标能被后续测试与部署任务引用。

### Lane B: 基础骨架与共享层

#### Task L1-B01: 初始化仓库级开发约定

- **Complexity:** `S`
- **Core Goal:** 建立 monorepo 级目录约定、脚本入口和统一开发命令。
- **Depends On:** `L1-A01`
- **Recommended Skills:** `codebase-design`
- **Acceptance:**
  - 根目录开发说明更新。
  - 明确 `apps/`, `services/`, `packages/`, `docs/` 的职责。
  - 团队可通过统一入口找到启动、测试、构建命令。

#### Task L1-B02: 建立环境变量与配置规范

- **Complexity:** `S`
- **Core Goal:** 统一 API、Web、数据库、翻译、调度、部署配置的命名与来源。
- **Depends On:** `L1-A01`
- **Recommended Skills:** `review`
- **Acceptance:**
  - 新增配置文档与 `.env.example` 级别模板。
  - 开发、测试、预发、生产四类环境的差异明确。
  - 没有把密钥写入仓库。

#### Task L1-B03: 初始化 `packages/shared-types`

- **Complexity:** `M`
- **Core Goal:** 建立共享 schema、类型导出和消费约定。
- **Depends On:** `L1-A04`
- **Recommended Skills:** `design-an-interface`
- **Acceptance:**
  - `packages/shared-types` 拥有清晰入口文件。
  - Digest、Archive、Health 等对外响应模型有明确类型定义。
  - Web 与 API 都能引用同一份契约定义。

#### Task L1-B04: 初始化 `packages/ui`

- **Complexity:** `M`
- **Core Goal:** 建立设计 token、排版、颜色、间距、按钮与基础信息组件规范。
- **Depends On:** `L1-A05`
- **Recommended Skills:** `frontend-design`, `ui-ux-pro-max`
- **Acceptance:**
  - `packages/ui` 至少提供 token 文档与基础导出入口。
  - 字体、颜色、spacing、responsive 断点有统一定义。
  - 能支撑首页、归档、详情页共用的 UI 语言。

#### Task L1-B05: 初始化 `services/api` 骨架

- **Complexity:** `M`
- **Core Goal:** 建立 API 服务目录结构、入口、依赖管理和健康检查最小运行链路。
- **Depends On:** `L1-B02`
- **Recommended Skills:** `codebase-design`, `tdd`
- **Acceptance:**
  - API 服务可本地启动。
  - 至少存在 `/api/v1/health` 占位返回。
  - 目录结构能容纳 routers, services, repositories, schemas, jobs。

#### Task L1-B06: 初始化 `apps/web` 骨架

- **Complexity:** `M`
- **Core Goal:** 建立前端项目结构、路由骨架、样式入口和 API 接入位。
- **Depends On:** `L1-B04`
- **Recommended Skills:** `frontend-design`
- **Acceptance:**
  - Web 应用可本地启动。
  - 至少存在首页路由和基础布局。
  - 前端通过配置指向 API，而非本地导出文件。

### Lane C: 数据与内容链路

#### Task L1-C01: 建立 V2 数据库 schema 与 migration

- **Complexity:** `M`
- **Core Goal:** 把 V1 已验证的数据结构转化为 V2 可维护的 schema 与 migration。
- **Depends On:** `L1-A02`, `L1-B05`
- **Recommended Skills:** `domain-modeling`, `tdd`
- **Acceptance:**
  - 数据表覆盖 sources, articles, translations, clusters, cluster_members, daily_digests。
  - migration 可在空库执行成功。
  - schema 与 `docs/architecture/domain-model.md` 对齐。

#### Task L1-C02: 建立源配置与加载器

- **Complexity:** `S`
- **Core Goal:** 以配置文件或表驱动方式管理新闻源，而不是散落在脚本中。
- **Depends On:** `L1-C01`
- **Recommended Skills:** `codebase-design`
- **Acceptance:**
  - Source 配置能被 API/调度消费。
  - 支持启用、停用、语言、类型、抓取策略字段。
  - 至少有一组首发默认源可加载。

#### Task L1-C03: 定义抓取适配器接口

- **Complexity:** `S`
- **Core Goal:** 为 RSS 抓取与正文爬取定义统一输入输出接口。
- **Depends On:** `L1-C02`
- **Recommended Skills:** `design-an-interface`
- **Acceptance:**
  - 接口清楚区分 source fetch、content extract、normalize 三个阶段。
  - 后续 RSS 与 crawler 都能复用统一文章模型。
  - 失败、超时、重试字段有统一表达。

#### Task L1-C04: 实现 RSS 抓取器

- **Complexity:** `M`
- **Core Goal:** 实现首发新闻源的 RSS 抓取、标准化和基础容错。
- **Depends On:** `L1-C03`
- **Recommended Skills:** `tdd`, `review`
- **Acceptance:**
  - 至少一组配置源能成功抓到文章。
  - 支持超时、重试、User-Agent 基本配置。
  - 抓取结果可写入 articles 表。

#### Task L1-C05: 实现正文提取器

- **Complexity:** `M`
- **Core Goal:** 对需要正文抽取的来源实现正文抓取与清洗。
- **Depends On:** `L1-C03`
- **Recommended Skills:** `tdd`
- **Acceptance:**
  - 能从目标站点提取正文或摘要补全信息。
  - 失败不会中断整轮抓取。
  - 抽取结果进入统一文章规范化流程。

#### Task L1-C06: 实现文章规范化与去重

- **Complexity:** `M`
- **Core Goal:** 统一 URL、清洗文本、处理重复文章，降低后续聚类噪声。
- **Depends On:** `L1-C04`, `L1-C05`
- **Recommended Skills:** `tdd`, `review`
- **Acceptance:**
  - URL 规范化规则可复用。
  - 标题/URL 去重策略能阻止明显重复入库。
  - 单元测试覆盖常见重复与空值场景。

#### Task L1-C07: 实现事件聚类服务

- **Complexity:** `L`
- **Core Goal:** 将多家媒体对同一事件的报道聚成 cluster。
- **Depends On:** `L1-C06`
- **Recommended Skills:** `domain-modeling`, `tdd`
- **Acceptance:**
  - 同一事件的多篇文章可映射到同一个 cluster。
  - 代表文章选取规则明确。
  - 失败聚类不会破坏已入库文章。

#### Task L1-C08: 实现日报排序与生成服务

- **Complexity:** `M`
- **Core Goal:** 基于 cluster 热度和时效性生成当日 digest。
- **Depends On:** `L1-C07`
- **Recommended Skills:** `tdd`
- **Acceptance:**
  - 能生成指定日期的 top digest。
  - 排序公式与可调参数有文档记录。
  - 重跑同一天任务具备幂等行为。

#### Task L1-C09: 实现批量翻译服务

- **Complexity:** `M`
- **Core Goal:** 对 digest 条目执行标题/摘要批量翻译，并保留 fallback 与质量护栏。
- **Depends On:** `L1-C08`
- **Recommended Skills:** `tdd`, `review`
- **Acceptance:**
  - 翻译结果落库并记录 provider。
  - 空摘要、空译文、供应商失败场景有可预测行为。
  - 已译内容不会重复计费。

#### Task L1-C10: 实现调度编排任务

- **Complexity:** `L`
- **Core Goal:** 把抓取、规范化、聚类、digest、翻译串成稳定可观测的任务链路。
- **Depends On:** `L1-C04` 至 `L1-C09`
- **Recommended Skills:** `codebase-design`, `review`
- **Acceptance:**
  - 能按计划触发整轮处理。
  - 单个来源失败不阻断整体轮次。
  - 任务状态、错误和耗时可记录。

### Lane D: API 交付层

#### Task L1-D01: 实现日报读取服务

- **Complexity:** `M`
- **Core Goal:** 向外提供 `latest digest` 和按日期 digest 的查询服务。
- **Depends On:** `L1-C08`, `L1-B03`
- **Recommended Skills:** `design-an-interface`, `tdd`
- **Acceptance:**
  - 存在稳定的 service/repository/query 层。
  - 返回数据符合 shared types。
  - 无数据日期返回明确空结果或 404 约定。

#### Task L1-D02: 实现归档与详情读取服务

- **Complexity:** `M`
- **Core Goal:** 提供归档列表、cluster/article detail 等读取能力。
- **Depends On:** `L1-D01`
- **Recommended Skills:** `tdd`
- **Acceptance:**
  - API 能查询可用日期列表。
  - cluster 或 article 详情返回字段完整。
  - 详情页所需元数据可直接消费。

#### Task L1-D03: 实现健康检查与基础指标

- **Complexity:** `S`
- **Core Goal:** 提供进程存活、数据库连通、最近任务状态等健康信号。
- **Depends On:** `L1-B05`, `L1-C10`
- **Recommended Skills:** `review`
- **Acceptance:**
  - `/api/v1/health` 区分 liveness 与 readiness 所需信息。
  - 至少能反映数据库连通和最近 digest 生成状态。
  - 可被部署与监控系统直接调用。

#### Task L1-D04: 暴露首发路由层

- **Complexity:** `M`
- **Core Goal:** 将 digest、archive、detail、health 以稳定路由形式公开。
- **Depends On:** `L1-D01`, `L1-D02`, `L1-D03`
- **Recommended Skills:** `design-an-interface`
- **Acceptance:**
  - 路由有统一前缀与版本号。
  - 错误响应格式一致。
  - OpenAPI 文档可自动生成。

#### Task L1-D05: 建立契约导出与客户端类型消费

- **Complexity:** `M`
- **Core Goal:** 让 API schema 可以同步到前端消费，防止契约漂移。
- **Depends On:** `L1-D04`, `L1-B03`
- **Recommended Skills:** `design-an-interface`, `review`
- **Acceptance:**
  - 契约生成/导出流程存在。
  - Web 项目可直接消费生成结果或共享类型。
  - 契约变更会触发检查或测试失败。

### Lane E: Web 体验层

#### Task L1-E01: 实现应用壳与全局布局

- **Complexity:** `S`
- **Core Goal:** 建立站点头部、页脚、全局布局、导航和基础元信息入口。
- **Depends On:** `L1-B04`, `L1-B06`
- **Recommended Skills:** `frontend-design`
- **Acceptance:**
  - 首页、归档、详情页共享统一壳层。
  - 导航覆盖 about/archive/rss 等首发入口。
  - 页面有统一的 SEO 基础入口。

#### Task L1-E02: 落地设计系统基础组件

- **Complexity:** `M`
- **Core Goal:** 实现标题层级、按钮、标签、来源标记、卡片、状态组件等基础 UI。
- **Depends On:** `L1-B04`
- **Recommended Skills:** `frontend-design`, `ui-ux-pro-max`
- **Acceptance:**
  - 基础组件与 token 配套。
  - 组件足以支撑首页和归档页面。
  - 无需每个页面重复定义样式。

#### Task L1-E03: 实现首页 Digest 页面

- **Complexity:** `M`
- **Core Goal:** 用新 UI 呈现 latest digest，并支持核心阅读动作。
- **Depends On:** `L1-D01`, `L1-E01`, `L1-E02`
- **Recommended Skills:** `frontend-design`, `webapp-testing`
- **Acceptance:**
  - 首页从 API 获取 latest digest。
  - 展示标题、摘要、来源、发布日期、原文入口。
  - 空数据与错误状态可读。

#### Task L1-E04: 实现归档列表与日期页

- **Complexity:** `M`
- **Core Goal:** 提供历史 digest 浏览入口，支持按日期查看。
- **Depends On:** `L1-D02`, `L1-E01`, `L1-E02`
- **Recommended Skills:** `frontend-design`
- **Acceptance:**
  - 归档列表可展示可用日期。
  - 日期页可直接渲染指定日期 digest。
  - 不存在数据时反馈友好。

#### Task L1-E05: 实现详情页

- **Complexity:** `M`
- **Core Goal:** 提供 cluster 或代表文章详情页，承载更完整内容与元数据。
- **Depends On:** `L1-D02`, `L1-E02`
- **Recommended Skills:** `frontend-design`
- **Acceptance:**
  - 详情页可展示代表文章、来源聚合与原文跳转。
  - 页面具备可分享的标题与 meta。
  - 前端状态管理不复杂化。

#### Task L1-E06: 实现搜索与状态体验

- **Complexity:** `M`
- **Core Goal:** 补齐搜索、空状态、错误状态、加载状态、无结果状态。
- **Depends On:** `L1-E03`, `L1-E04`
- **Recommended Skills:** `frontend-design`, `webapp-testing`
- **Acceptance:**
  - 首发搜索可定位 digest 内容、来源或标题。
  - 空、错、无结果三类状态视觉和文案区分清楚。
  - 移动端可用，键盘/快捷键行为可预测。

#### Task L1-E07: 实现 SEO 基础面

- **Complexity:** `S`
- **Core Goal:** 建立 meta、Open Graph、Twitter Card、robots、sitemap、JSON-LD 基础。
- **Depends On:** `L1-E01`, `L1-E03`, `L1-E04`, `L1-E05`
- **Recommended Skills:** `review`
- **Acceptance:**
  - 首页、归档、详情页有正确的 meta 信息。
  - `robots.txt` 与 `sitemap.xml` 可访问。
  - 至少有一类结构化数据输出。

#### Task L1-E08: 实现 RSS 输出与订阅页

- **Complexity:** `S`
- **Core Goal:** 恢复标准 RSS feed，并独立提供订阅说明页。
- **Depends On:** `L1-D01`, `L1-E01`
- **Recommended Skills:** `review`
- **Acceptance:**
  - `/feed.xml` 返回合法 XML feed。
  - `/rss` 提供订阅说明入口。
  - 空数据时也返回合法空 feed。

#### Task L1-E09: 完成性能与可访问性打磨

- **Complexity:** `M`
- **Core Goal:** 让首发版达到既定性能、可访问性与移动端体验目标。
- **Depends On:** `L1-E03` 至 `L1-E08`
- **Recommended Skills:** `webapp-testing`, `agent-browser`, `review`
- **Acceptance:**
  - 关键页面的 Lighthouse 达到既定基线。
  - 触控目标、键盘焦点、色彩对比满足基本可访问性要求。
  - 没有明显阻塞首发的性能回归。

### Lane F: 质量与交付层

#### Task L1-F01: 建立 API 单元与集成测试基线

- **Complexity:** `M`
- **Core Goal:** 为 schema、service、repository、router 建立最小自动化测试框架。
- **Depends On:** `L1-B05`, `L1-C01`, `L1-D04`
- **Recommended Skills:** `tdd`, `qa`
- **Acceptance:**
  - 测试工程可独立运行。
  - 至少覆盖 health、digest 读取、空数据、错误路径。
  - 新增 API 功能可以沿用同一测试模板。

#### Task L1-F02: 建立契约测试

- **Complexity:** `S`
- **Core Goal:** 验证 API 响应与 `packages/shared-types` 的一致性。
- **Depends On:** `L1-B03`, `L1-D05`
- **Recommended Skills:** `tdd`
- **Acceptance:**
  - 契约漂移会在测试中暴露。
  - 关键响应模型存在 schema 校验。
  - 前后端双方都能引用测试结果。

#### Task L1-F03: 建立 Web 组件与页面测试基线

- **Complexity:** `M`
- **Core Goal:** 为布局、首页、归档、详情、状态组件建立页面级测试能力。
- **Depends On:** `L1-E03` 至 `L1-E08`
- **Recommended Skills:** `tdd`, `webapp-testing`
- **Acceptance:**
  - 关键页面至少有 smoke test。
  - 空数据与错误状态有覆盖。
  - 构建失败或关键渲染缺失会被发现。

#### Task L1-F04: 建立 E2E 首发主链路测试

- **Complexity:** `M`
- **Core Goal:** 用真实运行中的 API + Web 验证首发主链路。
- **Depends On:** `L1-D04`, `L1-E09`
- **Recommended Skills:** `qa`, `webapp-testing`, `agent-browser`
- **Acceptance:**
  - 至少覆盖“查看首页 -> 进入归档 -> 打开详情 -> 访问 RSS”。
  - 关键路径失败可在 CI 中重现。
  - 首发验收不再只靠人工点点看。

#### Task L1-F05: 建立 CI 流水线

- **Complexity:** `M`
- **Core Goal:** 让 lint、typecheck、test、build 在 CI 中统一执行。
- **Depends On:** `L1-F01`, `L1-F02`, `L1-F03`
- **Recommended Skills:** `review`
- **Acceptance:**
  - Push 或 PR 时自动运行检查。
  - 失败能明确指向 API、Web 或 shared-types。
  - 不允许未通过测试的改动合入主线。

#### Task L1-F06: 建立预发/预览环境

- **Complexity:** `M`
- **Core Goal:** 让 API 与 Web 在预发环境可联调和验收。
- **Depends On:** `L1-F05`, `L1-D04`, `L1-E09`
- **Recommended Skills:** `review`
- **Acceptance:**
  - 存在可访问的预览 URL 或预发实例。
  - 前后端联调不依赖本地单机环境。
  - 预发配置与生产配置差异可追踪。

#### Task L1-F07: 建立生产部署、日志与告警

- **Complexity:** `L`
- **Core Goal:** 完成首发版上线链路及最小生产观测能力。
- **Depends On:** `L1-F06`, `L1-D03`, `L1-C10`
- **Recommended Skills:** `review`, `qa`
- **Acceptance:**
  - API 与 Web 可部署到生产环境。
  - 健康检查、错误日志、核心告警可工作。
  - 每日更新失败能被感知，而不是静默失效。

---

## L2: 运营后台与人工干预

### Lane G: 运营能力

#### Task L2-G01: 定义后台权限模型

- **Complexity:** `S`
- **Core Goal:** 明确后台用户、角色和可操作范围。
- **Depends On:** `L1` 全部完成
- **Recommended Skills:** `domain-modeling`
- **Acceptance:**
  - 角色边界清晰。
  - 后台与公开 API 的权限边界明确。
  - 不把权限模型耦合进首发公共读接口。

#### Task L2-G02: 实现源管理 API 与界面

- **Complexity:** `M`
- **Core Goal:** 让运营可以新增、禁用、排序和检查抓取源。
- **Depends On:** `L2-G01`, `L1-C02`
- **Recommended Skills:** `design-an-interface`, `frontend-design`
- **Acceptance:**
  - 源的增删改查有后台入口。
  - 配置变更可影响调度行为。
  - 关键字段校验完整。

#### Task L2-G03: 实现人工精选与重排

- **Complexity:** `M`
- **Core Goal:** 支持运营对 digest 结果进行人工重排、剔除与置顶。
- **Depends On:** `L2-G01`, `L1-C08`
- **Recommended Skills:** `design-an-interface`, `frontend-design`
- **Acceptance:**
  - 不修改原始抓取数据，仅对发布结果施加人工决策。
  - 手工操作可回溯。
  - 发布结果能反映人工调整。

#### Task L2-G04: 实现翻译审校与覆盖

- **Complexity:** `M`
- **Core Goal:** 允许人工审校自动翻译结果并覆盖发布文本。
- **Depends On:** `L2-G01`, `L1-C09`
- **Recommended Skills:** `design-an-interface`
- **Acceptance:**
  - 可查看原文、机翻、人工修订版。
  - 人工修订有状态标识与审校记录。
  - 发布优先读取人工修订版。

#### Task L2-G05: 实现作业控制台与运行手册

- **Complexity:** `M`
- **Core Goal:** 让运营可查看任务状态、失败原因并执行有限重跑。
- **Depends On:** `L1-C10`, `L1-D03`
- **Recommended Skills:** `qa`, `frontend-design`
- **Acceptance:**
  - 能看到最近任务执行记录。
  - 能区分抓取失败、翻译失败、发布失败。
  - 有明确 runbook 文档指导处置。

---

## L3: 多客户端扩展

### Lane H: Client-Ready Platform

#### Task L3-H01: 定义 API 版本治理

- **Complexity:** `S`
- **Core Goal:** 为 Web 之外客户端建立稳定版本与兼容策略。
- **Depends On:** `L2` 完成
- **Recommended Skills:** `design-an-interface`
- **Acceptance:**
  - 文档说明版本生命周期。
  - breaking change 有治理规则。
  - 客户端不会因小改动被频繁破坏。

#### Task L3-H02: 建立 SDK/客户端访问层

- **Complexity:** `M`
- **Core Goal:** 为未来 App 或其他客户端提供统一访问 SDK 或轻量客户端包。
- **Depends On:** `L3-H01`, `L1-D05`
- **Recommended Skills:** `design-an-interface`
- **Acceptance:**
  - SDK 可消费公开 API。
  - 错误、重试、缓存策略具备基本抽象。
  - Web 不依赖该 SDK 也不被其反向耦合。

#### Task L3-H03: 设计跨客户端内容能力

- **Complexity:** `M`
- **Core Goal:** 把阅读进度、收藏、语言偏好等潜在跨端能力抽象出来。
- **Depends On:** `L3-H01`
- **Recommended Skills:** `domain-modeling`
- **Acceptance:**
  - 明确哪些能力需要账户体系，哪些可以匿名。
  - 不把未确认需求硬塞进 L1/L2。
  - 为后续客户端预留扩展点。

#### Task L3-H04: 设计通知与订阅接口

- **Complexity:** `S`
- **Core Goal:** 为邮件、Push、Webhook 等订阅能力定义统一入口。
- **Depends On:** `L3-H01`
- **Recommended Skills:** `design-an-interface`
- **Acceptance:**
  - 订阅对象、触发策略、退订策略有明确模型。
  - 不与 Web 单一页面逻辑绑定。
  - 可供后续单独实施。

---

## L4: 长期治理

### Lane I: Quality, Security, Cost, Governance

#### Task L4-I01: 建立安全与隐私基线

- **Complexity:** `M`
- **Core Goal:** 识别密钥管理、后台访问、日志脱敏和第三方供应商风险。
- **Depends On:** `L2`, `L3`
- **Recommended Skills:** `review`
- **Acceptance:**
  - 存在安全与隐私检查清单。
  - 敏感配置、日志、后台入口有明确保护措施。
  - 首发后新增能力不会绕过基线。

#### Task L4-I02: 建立成本与配额治理

- **Complexity:** `S`
- **Core Goal:** 跟踪翻译、抓取、部署和监控成本，避免规模增长后失控。
- **Depends On:** `L1-C09`, `L1-F07`
- **Recommended Skills:** `review`
- **Acceptance:**
  - 有成本归因视图或文档。
  - 翻译与抓取存在配额/限速策略。
  - 供应商切换或降级规则清楚。

#### Task L4-I03: 建立内容质量与编辑审计机制

- **Complexity:** `M`
- **Core Goal:** 持续检查聚类质量、翻译质量和人工编辑质量。
- **Depends On:** `L2-G03`, `L2-G04`
- **Recommended Skills:** `qa`, `review`
- **Acceptance:**
  - 定期抽检规则明确。
  - 质量问题可回溯到数据源、算法或人工步骤。
  - 有最小可执行的改进闭环。

#### Task L4-I04: 建立性能回归治理

- **Complexity:** `S`
- **Core Goal:** 把性能目标从一次性优化变成持续门禁。
- **Depends On:** `L1-E09`, `L1-F05`
- **Recommended Skills:** `webapp-testing`, `review`
- **Acceptance:**
  - 存在性能预算与回归检查。
  - 关键页面性能恶化会被自动发现。
  - 回归结果可用于决定是否阻止发布。

#### Task L4-I05: 建立路线图与 backlog 治理机制

- **Complexity:** `S`
- **Core Goal:** 让长期演进持续回到同一规划框架，而不是再次失控散落。
- **Depends On:** `L1`, `L2`, `L3`
- **Recommended Skills:** `writing-plans`, `review`
- **Acceptance:**
  - 总计划与实际完成状态定期同步。
  - 新需求进入 backlog 前必须指明所属层级和依赖。
  - 长期计划可持续服务多 Agent 或单人线性开发。

---

## Suggested Parallel Batches

### Batch P1: 文档与边界

- `L1-A01`, `L1-A02`, `L1-A03`, `L1-A04`, `L1-A05`

### Batch P2: 基础骨架

- `L1-B01`, `L1-B02`, `L1-B03`, `L1-B04`, `L1-B05`, `L1-B06`

### Batch P3: 后端主链路

- `L1-C01`, `L1-C02`, `L1-C03`, `L1-C04`, `L1-C05`, `L1-C06`

### Batch P4: 聚类与发布

- `L1-C07`, `L1-C08`, `L1-C09`, `L1-C10`, `L1-D01`, `L1-D02`, `L1-D03`, `L1-D04`, `L1-D05`

### Batch P5: Web 首发

- `L1-E01`, `L1-E02`, `L1-E03`, `L1-E04`, `L1-E05`, `L1-E06`, `L1-E07`, `L1-E08`, `L1-E09`

### Batch P6: 质量与发布

- `L1-F01`, `L1-F02`, `L1-F03`, `L1-F04`, `L1-F05`, `L1-F06`, `L1-F07`

---

## Recommended First Linear Sequence

1. `L1-A01` -> `L1-A05`
2. `L1-B01` -> `L1-B06`
3. `L1-C01` -> `L1-C06`
4. `L1-C07` -> `L1-C10`
5. `L1-D01` -> `L1-D05`
6. `L1-E01` -> `L1-E09`
7. `L1-F01` -> `L1-F07`

---

## Immediate Next Tasks

- **Now:** Start with `L1-A01`, `L1-A02`, `L1-A03`
- **Then:** Start `L1-B03`, `L1-B04`, `L1-B05`, `L1-B06`
- **Lock Condition:** Do not open `L2` tasks before `L1-F07` is accepted

---

## Self-Review

- **Coverage Check:** The plan covers short-term launch (`L1`), post-launch operations (`L2`), multi-client expansion (`L3`), and long-term governance (`L4`).
- **Placeholder Scan:** No task uses `TBD`, `TODO`, or unspecified acceptance wording.
- **Consistency Check:** All tasks align with `claude.md`, `docs/context/WORKFLOW.md`, and the requirement that short-term work only starts from `L1`.
