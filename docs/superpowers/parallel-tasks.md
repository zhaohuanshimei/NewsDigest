# Parallel Tasks Board

> 本文件是任务派单与验收的单一事实来源。subagent 只读本文件中自己 Task ID 对应的 section，不写本文件。派单与状态更新由协调者完成。

## 状态约定

- `pending` — 已派单，等待 agent 执行
- `in_progress` — agent 已开始
- `review` — agent 已交付 commit，等待验收
- `done` — 已验收通过，压缩到"已完成"区

---

## 当前任务批次

**无待执行任务。** P6 批次已全部完成，P7 批次待后续执行。

### Task P6-A: L1-E01 实现应用壳与全局布局

- **Status:** done
- **Owner:** agent-aa385376ca884a8c9
- **Commit:** `b1ebc7c`

#### 任务
建立站点头部、页脚、全局布局、导航和基础元信息入口。

#### 上下文文件（先读）
- apps/web/src/layouts/ — 现有布局文件
- apps/web/src/components/ — 现有组件
- docs/design/ — UI 设计文档
- docs/architecture/domain-model.md — 领域模型

#### 可以创建/修改的文件
- apps/web/src/layouts/BaseLayout.astro — **修改**（统一壳层）
- apps/web/src/components/layout/Header.astro — 新建
- apps/web/src/components/layout/Footer.astro — 新建
- apps/web/src/components/layout/Navigation.astro — 新建
- apps/web/tests/layout.test.ts — 新建

#### 禁碰文件
- 除上面 5 个文件外的一切文件

#### 实现要求
1. 首页、归档、详情页共享统一壳层
2. 导航覆盖 about/archive/rss 等首发入口
3. 页面有统一的 SEO 基础入口
4. 单元测试覆盖布局结构

#### 验收检查
```bash
cd apps/web && npm test
```

#### 完成后 commit
```bash
git add apps/web/src/layouts/BaseLayout.astro apps/web/src/components/layout/ apps/web/tests/layout.test.ts
git commit -m "feat: implement app shell and global layout"
```

---

### Task P6-B: L1-E02 落地设计系统基础组件

- **Status:** done
- **Owner:** agent-abcc74f611be039ee
- **Commit:** `8f44710`

#### 任务
实现标题层级、按钮、标签、来源标记、卡片、状态组件等基础 UI。

#### 上下文文件（先读）
- packages/ui/ — UI 包目录（待创建）
- docs/design/ — UI 设计文档
- apps/web/src/components/ — 现有组件

#### 可以创建/修改的文件
- packages/ui/src/components/Button.astro — 新建
- packages/ui/src/components/Card.astro — 新建
- packages/ui/src/components/Heading.astro — 新建
- packages/ui/src/components/Tag.astro — 新建
- packages/ui/src/components/SourceBadge.astro — 新建
- packages/ui/src/tokens.css — 新建（设计 token）
- packages/ui/package.json — 新建
- apps/web/tests/ui-components.test.ts — 新建

#### 禁碰文件
- 除上面 8 个文件外的一切文件

#### 实现要求
1. 基础组件与 token 配套
2. 组件足以支撑首页和归档页面
3. 无需每个页面重复定义样式
4. 单元测试覆盖组件渲染

#### 验收检查
```bash
cd apps/web && npm test
```

#### 完成后 commit
```bash
git add packages/ui/ apps/web/tests/ui-components.test.ts
git commit -m "feat: implement design system base components"
```

---

### Task P6-C: L1-E06 实现搜索与状态体验

- **Status:** done
- **Owner:** agent-ac072c437f88259b3
- **Commit:** `b1ebc7c` + `1c722a0`

#### 任务
补齐搜索、空状态、错误状态、加载状态、无结果状态。

#### 上下文文件（先读）
- apps/web/src/pages/ — 现有页面
- apps/web/src/components/ — 现有组件
- docs/design/ — UI 设计文档

#### 可以创建/修改的文件
- apps/web/src/components/states/EmptyState.astro — 新建
- apps/web/src/components/states/ErrorState.astro — 新建
- apps/web/src/components/states/LoadingState.astro — 新建
- apps/web/src/components/states/NoResultsState.astro — 新建
- apps/web/src/components/search/SearchBar.astro — 新建
- apps/web/tests/states.test.ts — 新建

#### 禁碰文件
- 除上面 6 个文件外的一切文件

#### 实现要求
1. 首发搜索可定位 digest 内容、来源或标题
2. 空、错、无结果三类状态视觉和文案区分清楚
3. 移动端可用，键盘/快捷键行为可预测
4. 单元测试覆盖状态组件

#### 验收检查
```bash
cd apps/web && npm test
```

#### 完成后 commit
```bash
git add apps/web/src/components/states/ apps/web/src/components/search/ apps/web/tests/states.test.ts
git commit -m "feat: implement search and state experience"
```

---

### Task P6-D: L1-E09 完成性能与可访问性打磨

- **Status:** done
- **Owner:** agent-ac072c437f88259b3
- **Commit:** `7e2ab65`

#### 任务
让首发版达到既定性能、可访问性与移动端体验目标。

#### 上下文文件（先读）
- apps/web/src/pages/ — 所有页面
- apps/web/src/components/ — 所有组件
- docs/architecture/non-functional-targets.md — 非功能目标

#### 可以创建/修改的文件
- apps/web/src/styles/accessibility.css — 新建
- apps/web/src/styles/performance.css — 新建
- apps/web/tests/accessibility.test.ts — 新建
- apps/web/tests/performance.test.ts — 新建

#### 禁碰文件
- 除上面 4 个文件外的一切文件

#### 实现要求
1. 关键页面的 Lighthouse 达到既定基线
2. 触控目标、键盘焦点、色彩对比满足基本可访问性要求
3. 没有明显阻塞首发的性能回归
4. 单元测试覆盖可访问性和性能检查

#### 验收检查
```bash
cd apps/web && npm test
```

#### 完成后 commit
```bash
git add apps/web/src/styles/ apps/web/tests/accessibility.test.ts apps/web/tests/performance.test.ts
git commit -m "feat: complete performance and accessibility polish"
```

---

### Task P6-E: L1-B04 初始化 packages/ui

- **Status:** done
- **Owner:** agent-abca68ce6594a462c
- **Commit:** `b1dbfa1`

#### 任务
建立设计 token、排版、颜色、间距、按钮与基础信息组件规范。

#### 上下文文件（先读）
- packages/ui/ — UI 包目录（待创建）
- docs/design/ — UI 设计文档
- docs/architecture/non-functional-targets.md — 非功能目标

#### 可以创建/修改的文件
- packages/ui/README.md — 新建
- packages/ui/package.json — 新建
- packages/ui/src/index.ts — 新建
- packages/ui/src/tokens/colors.ts — 新建
- packages/ui/src/tokens/spacing.ts — 新建
- packages/ui/src/tokens/typography.ts — 新建
- packages/ui/src/docs/design-tokens.md — 新建

#### 禁碰文件
- 除上面 7 个文件外的一切文件

#### 实现要求
1. packages/ui 至少提供 token 文档与基础导出入口
2. 字体、颜色、spacing、responsive 断点有统一定义
3. 能支撑首页、归档、详情页共用的 UI 语言
4. 文档说明 token 使用方式

#### 验收检查
```bash
cd packages/ui && cat README.md
```

#### 完成后 commit
```bash
git add packages/ui/
git commit -m "feat: initialize packages/ui with design tokens"
```

---

### Task P5-A: L1-C09 批量翻译服务

- **Status:** done
- **Owner:** agent-a124e15266c46b3dc
- **Commit:** `d43bf0b`

#### 任务
实现 `TranslationService`，对 digest 条目执行标题/摘要批量翻译，保留 fallback 与质量护栏。

#### 上下文文件（先读）
- services/api/app/models/translation.py — Translation ORM 模型
- services/api/app/models/digest_entry.py — DigestEntry 模型
- services/api/app/models/article.py — Article 模型
- services/api/app/repositories/ — repository 风格参考
- services/api/app/services/cluster_service.py — service 风格参考
- docs/architecture/domain-model.md — Translation 实体定义

#### 可以创建的文件（仅此 3 个）
- services/api/app/services/translation_service.py
- services/api/app/repositories/translation_repository.py
- services/api/tests/test_translation_service.py

#### 禁碰文件
- 除上面 3 个文件外的一切文件

#### 实现要求
1. 实现 `TranslationService`，接收 Session 作为依赖
2. `translate_digest_entries(digest_id: int, target_language: str = "zh") -> int`
   - 查询该 digest 的所有 entries
   - 对每个 entry 的 headline + summary 调用翻译 provider
   - 落库到 Translation 表，记录 provider 名称
3. 翻译 provider 抽象为接口 `TranslationProvider`（protocol/ABC）：
   - `translate(text: str, target_lang: str) -> str | None`
   - 提供一个 `MockTranslationProvider` 用于测试
   - 提供一个 `NullTranslationProvider`（失败时返回原文，不抛异常）
4. 质量护栏：
   - 空摘要跳过，不翻译
   - 空译文不落库（避免覆盖原文）
   - provider 失败返回 None，该条目用原文兜底
   - 已翻译内容不重复翻译（查 Translation 表，status="completed" 跳过）
5. 单元测试覆盖：正常翻译、空摘要、provider 失败、已翻译跳过、批量处理

#### 验收检查
```bash
cd services/api && python -m pytest tests/test_translation_service.py -v
```

#### 完成后 commit
```bash
git add services/api/app/services/translation_service.py services/api/app/repositories/translation_repository.py services/api/tests/test_translation_service.py
git commit -m "feat: implement batch translation service with provider abstraction"
```

---

### Task P5-B: L1-D01 日报读取服务

- **Status:** done
- **Owner:** agent-adf1638c20a80bafe
- **Commit:** `d43bf0b`

#### 任务
实现 `DigestQueryService`，向外提供 latest digest 和按日期 digest 的查询能力，返回数据符合 shared-types。

#### 上下文文件（先读）
- services/api/app/models/digest.py — Digest 模型
- services/api/app/models/digest_entry.py — DigestEntry 模型
- services/api/app/models/cluster.py — Cluster 模型
- packages/shared-types/src/resources/digest.py — DigestResource 契约（对齐输出结构）
- packages/shared-types/src/resources/archive.ts — ArchiveDateListResource 契约
- services/api/app/services/digest_generator.py — 生成服务参考
- docs/architecture/domain-model.md — Digest 定义

#### 可以创建的文件（仅此 3 个）
- services/api/app/services/digest_query_service.py
- services/api/app/repositories/digest_query_repository.py
- services/api/tests/test_digest_query_service.py

#### 禁碰文件
- 除上面 3 个文件外的一切文件。不碰 services/api/app/services/digests.py（现有静态 stub）和 services/api/app/repositories/digest_repository.py（C08 产物）

#### 实现要求
1. 实现 `DigestQueryService`，接收 Session 作为依赖
2. `get_latest() -> DigestResource | None`
   - 查询最近一个 status="published" 或最新日期的 digest
   - 返回符合 shared-types DigestResource 结构的 dict/对象
3. `get_by_date(date: date) -> DigestResource | None`
   - 查询指定日期 digest，无则返回 None（404 约定）
4. `get_available_dates(limit: int = 30) -> list[date]`
   - 返回有 digest 的日期列表（降序）
5. 输出结构严格对齐 `packages/shared-types/src/resources/digest.ts`
6. 空 digest（entries=[]）正常返回，不抛异常
7. 单元测试覆盖：有数据、空数据、指定日期无数据、latest 选取、日期列表

#### 验收检查
```bash
cd services/api && python -m pytest tests/test_digest_query_service.py -v
```

#### 完成后 commit
```bash
git add services/api/app/services/digest_query_service.py services/api/app/repositories/digest_query_repository.py services/api/tests/test_digest_query_service.py
git commit -m "feat: implement digest query service aligned with shared types"
```

---

### Task P5-C: L1-C10 调度编排任务

- **Status:** done
- **Owner:** agent-a9428756bafdb537d
- **Commit:** `d43bf0b`

#### 任务
实现 `PipelineOrchestrator`，把抓取、规范化、聚类、digest、翻译串成稳定可观测的任务链路。

#### 上下文文件（先读）
- services/api/app/services/article_service.py — 抓取+持久化
- services/api/app/services/article_normalizer.py — 规范化
- services/api/app/services/cluster_service.py — 聚类
- services/api/app/services/digest_generator.py — digest 生成
- services/api/app/services/translation_service.py — 翻译（P5-A 产物，先读接口约定）
- services/api/app/repositories/source_repository.py — 源列表
- docs/architecture/domain-model.md — pipeline 定义

#### 可以创建的文件（仅此 3 个）
- services/api/app/services/pipeline_orchestrator.py
- services/api/tests/test_pipeline_orchestrator.py
- services/api/app/core/pipeline_state.py — 任务状态记录数据类

#### 禁碰文件
- 除上面 3 个文件外的一切文件。对其他 service 只读不改。

#### 实现要求
1. 实现 `PipelineOrchestrator`，接收 Session + 各 service 作为依赖（依赖注入，便于测试 mock）
2. `run_full_pipeline(target_date: date) -> PipelineResult`
   - Step 1: fetch_all_active_sources（抓取）
   - Step 2: normalize pending articles（规范化）
   - Step 3: cluster_articles(since=yesterday)（聚类）
   - Step 4: generate(target_date)（digest 生成）
   - Step 5: translate_digest_entries（翻译，可选）
3. **容错：单个来源失败不阻断整体轮次**
   - 每个 step 内部 try/except，记录失败但不抛
   - 返回 PipelineResult 含每步状态/错误/耗时
4. `PipelineResult` 数据类：
   - `started_at`, `finished_at`, `duration_seconds`
   - `steps: list[StepResult]`（name, status, error, duration, count）
   - `success: bool`（全部 step 成功才 True）
5. 幂等：重复调用同一天不产生重复数据（依赖底层 service 幂等性）
6. 单元测试覆盖：全流程成功、某步失败继续执行、空数据日、幂等重跑

#### 验收检查
```bash
cd services/api && python -m pytest tests/test_pipeline_orchestrator.py -v
```

#### 完成后 commit
```bash
git add services/api/app/services/pipeline_orchestrator.py services/api/app/core/pipeline_state.py services/api/tests/test_pipeline_orchestrator.py
git commit -m "feat: implement pipeline orchestrator with fault-tolerant steps"
```

---

### Task P5-D: L1-D02 归档与详情读取服务

- **Status:** done
- **Owner:** agent-ae6db212ad86c414e
- **Commit:** `d43bf0b`

#### 任务
实现 `ArchiveQueryService`，提供归档日期列表、cluster 详情、article 详情查询能力。

#### 上下文文件（先读）
- services/api/app/models/cluster.py — Cluster 模型
- services/api/app/models/cluster_member.py — ClusterMember 模型
- services/api/app/models/article.py — Article 模型
- services/api/app/models/digest.py — Digest 模型（取日期列表）
- packages/shared-types/src/resources/archive.ts — ArchiveDateListResource 契约
- packages/shared-types/src/resources/cluster.ts — ClusterDetailResource 契约
- packages/shared-types/src/resources/article.ts — ArticleDetailResource 契约
- docs/architecture/domain-model.md — Cluster/Article 定义

#### 可以创建的文件（仅此 3 个）
- services/api/app/services/archive_query_service.py
- services/api/app/repositories/archive_query_repository.py
- services/api/tests/test_archive_query_service.py

#### 禁碰文件
- 除上面 3 个文件外的一切文件

#### 实现要求
1. 实现 `ArchiveQueryService`，接收 Session 作为依赖
2. `get_archive_dates(limit: int = 30) -> ArchiveDateListResource`
   - 返回有 digest 的日期列表（降序）
   - 结构对齐 shared-types archive.ts
3. `get_cluster_detail(cluster_id: int) -> ClusterDetailResource | None`
   - 返回 cluster + members + representative article
   - 无则返回 None
4. `get_article_detail(article_id: int) -> ArticleDetailResource | None`
   - 返回 article 完整字段
   - 无则返回 None
5. 输出结构严格对齐 shared-types 三个 resource 契约
6. 单元测试覆盖：正常返回、不存在返回 None、归档空列表、cluster 含 members

#### 验收检查
```bash
cd services/api && python -m pytest tests/test_archive_query_service.py -v
```

#### 完成后 commit
```bash
git add services/api/app/services/archive_query_service.py services/api/app/repositories/archive_query_repository.py services/api/tests/test_archive_query_service.py
git commit -m "feat: implement archive and detail query services"
```

---

## 已完成

| Task ID | Commit | Note |
|---------|--------|------|
| L1-A01～A05 | `(early commits)` | docs/architecture/ 7 篇文档 |
| L1-B02 | `d4a2709` | .env.example + configuration.md |
| L1-B03 | `da23858` | shared-types 六大资源契约 |
| L1-B05 | `40e45bc` | FastAPI 骨架 + 6 路由 |
| L1-B06 | `(early commits)` | Astro 项目 + pages/layouts |
| L1-E03 | `a77db8e`~`f395ec2` | 首页 Digest 展示 |
| L1-E04 | `6e2000a` | 归档列表页面 |
| L1-E05 | `a77db8e`~`f395ec2` | Cluster 详情页 |
| L1-E07 | `997e414` | SEO meta/OG/sitemap/robots/JSON-LD |
| L1-E08 | `5719627` | RSS feed.xml.ts + rss.astro |
| Fix: site URL | `1d125a1` | astro.config.mjs site + 相对 robots + Astro.site |
| L1-C01 | `8088fc2` | DB models + Alembic + database session |
| L1-C03 | `b04cdc9` + `61be084` | 抓取适配器接口 + 23 tests |
| L1-C02 | `9b5ccaa` | 源配置服务 + 5 默认源 |
| L1-C04 | `45a2d8d` | RSS 抓取器 + article 持久化 |
| Review fixes | `6fa88e9` | 8 review issues (utcnow→UTC, String(10), retry, error_code, _fetch_with_retry, update_last_fetched_at, conftest scope, version pins) + DateTime(timezone=True) migration |
| L1-C05 | `6896d7e` | ContentFetcher + readability-lxml + 18 tests |
| L1-C06 | `7884796` | ArticleNormalizer + URL 清洗 + 去重 + 30 tests |
| L1-C07 | `9ad748d` | ClusterService + TF-IDF + cosine similarity + 12 tests |
| L1-C08 | `a389bad` | DigestGenerator + 幂等生成 + 5 tests |
| P4 integration | `032a794` | requirements.txt 补 readability-lxml/scikit-learn/scipy |
| **P5 第一波** | `d43bf0b` | TranslationService (12) + PipelineOrchestrator (10) + DigestQueryService (8) + ArchiveQueryService (12) = 42 tests |
| **P5 第二波** | `c78b898`~`c607dc1` | HealthService (5) + 路由层切换 (11) + 契约导出 (17) = 33 tests |
| **P6** | `b1ebc7c`~`7e2ab65` | 应用壳 (3) + 设计系统 (14) + 搜索状态 (28) + 性能可访问性 (14) + packages/ui |
| P5/P6 验收修复 | (本提交) | structlog 加入 requirements + pipeline UTC 修复 + DigestEntry import 补全 |

**合计：233 后端 pytest + 167 前端 vitest = 400 tests 全部通过 ✅**

## 后续批次规划

| 批次 | 任务 | 说明 |
|------|------|------|
| ~~P4~~ | ~~C05, C06, C07, C08~~ | ✅ 已完成 — 四路并行交付 |
| ~~P5 第一波~~ | ~~C09, C10, D01, D02~~ | ✅ 已完成 — 四路并行交付 |
| ~~P5 第二波~~ | ~~D03, D04, D05~~ | ✅ 已完成 — 三路并行交付 |
| ~~P6~~ | ~~E01/E02/E06/E09 + B04~~ | ✅ 已完成 — 五路并行交付 |
| **最后一批（P7）** | F01→F07 | CI/CD、测试基线、部署、监控 |

### 剩余任务总计

| 阶段 | 剩余任务数 | 说明 |
|------|-----------|------|
| ~~P5 第一波~~ | ~~4~~ | ~~✅ 已完成~~ |
| ~~P5 第二波~~ | ~~3~~ | ~~✅ 已完成~~ |
| ~~P6~~ | ~~5~~ | ~~✅ 已完成~~ |
| **P7（最后一批）** | **~7** | F01-F07 |
| **合计** | **~7** | 距离 L1 完成约 7 个任务 |
