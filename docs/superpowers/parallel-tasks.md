# Parallel Tasks Board

> 本文件是任务派单与验收的单一事实来源。subagent 只读本文件中自己 Task ID 对应的 section，不写本文件。派单与状态更新由协调者完成。

## 状态约定

- `pending` — 已派单，等待 agent 执行
- `in_progress` — agent 已开始
- `review` — agent 已交付 commit，等待验收
- `done` — 已验收通过，压缩到"已完成"区

---

## 当前任务批次（2026-06-26）：L1-C09/C10 + L1-D01/D02（P5 第一波）

> **执行方式：四路并行。** 四个 task 同时派单给四个独立 agent。各 task 通过已存在的 ORM 模型、service 类和 shared-types 契约解耦，开发阶段用 mock 数据独立测试。

> **⚠️ 关键原则：禁止 cross-task 文件冲突。** 每个 task 的 allowed 文件列表互不重叠。如需改不在 allowed 列表里的文件，停止并报告协调者。

---

### Task P5-A: L1-C09 批量翻译服务

- **Status:** pending
- **Owner:** (待分配)
- **Commit:** （待交付）

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

- **Status:** pending
- **Owner:** (待分配)
- **Commit:** （待交付）

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

- **Status:** pending
- **Owner:** (待分配)
- **Commit:** （待交付）

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

- **Status:** pending
- **Owner:** (待分配)
- **Commit:** （待交付）

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
| P4 integration | (本提交) | requirements.txt 补 readability-lxml/scikit-learn/scipy |

**合计：172 后端 pytest + 29 前端 vitest = 201 tests 全部通过 ✅**

## 后续批次规划

| 批次 | 任务 | 说明 |
|------|------|------|
| ~~P4~~ | ~~C05, C06, C07, C08~~ | ✅ 已完成 — 四路并行交付 |
| **本批（P5 第一波）** | C09, C10, D01, D02 | 四路并行：翻译 / 调度编排 / 日报读取 / 归档详情读取 |
| P5 第二波 | D03, D04, D05 | 健康检查 / 路由层暴露 / 契约导出（依赖第一波） |
| 再下一批（P6） | E01/E02/E06/E09 + B04 | Web 剩余功能 + packages/ui |
| 最后一批（P7） | F01→F07 | CI/CD、测试基线、部署、监控 |

### 剩余任务总计

| 阶段 | 剩余任务数 | 说明 |
|------|-----------|------|
| P5 第一波（本批） | 4 | C09, C10, D01, D02 |
| P5 第二波 | 3 | D03, D04, D05 |
| P6 | ~5 | E01, E02, E06, E09, B04 |
| P7 | ~7 | F01-F07 |
| **合计** | **~19** | 距离 L1 完成约 19 个任务 |
