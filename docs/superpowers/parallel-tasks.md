# Parallel Tasks Board

> 本文件是任务派单与验收的单一事实来源。subagent 只读本文件中自己 Task ID 对应的 section，不写本文件。派单与状态更新由协调者完成。

## 状态约定

- `pending` — 已派单，等待 agent 执行
- `in_progress` — agent 已开始
- `review` — agent 已交付 commit，等待验收
- `done` — 已验收通过，压缩到"已完成"区

---

## 当前任务批次（2026-06-26）：L1-C 数据管线（P4）

> **执行方式：四路并行。** 四个 task 同时派单给四个独立 agent。每个 agent 只读自己的 task section，只创建/修改自己 allowed 列表中的文件。各 task 之间通过已存在的 ORM 模型和接口契约解耦，开发阶段用 mock 数据独立测试，无需等待其他 task。

> **⚠️ 关键原则：禁止 cross-task 文件冲突。** 每个 task 的 allowed 文件列表互不重叠。如果某 agent 发现需要改不在自己 allowed 列表里的文件，必须停止并报告协调者，不可擅改。

---

### Task P4-A: L1-C05 正文提取器

- **Status:** pending
- **Owner:** (待分配)
- **Commit:** （待交付）

#### 任务
实现 `ContentFetcher(BaseFetcher)`，对文章 URL 获取 HTML 并用 readability 提取正文。

#### 上下文文件（先读）
- services/api/app/core/fetcher_interface.py — BaseFetcher, FetchRequest, FetchResult, ExtractedItem 定义
- services/api/app/services/fetchers/rss_fetcher.py — RssFetcher 实现参考
- services/api/tests/test_fetcher_interface.py — FetchResult 契约参考
- docs/architecture/domain-model.md — Article 定义

#### 可以创建的文件（仅此 2 个）
- services/api/app/services/fetchers/content_fetcher.py
- services/api/tests/test_content_fetcher.py

#### 禁碰文件
- 除上面 2 个文件外的一切文件，包括 apps/web/, packages/, services/api/ 下其他所有文件

#### 实现要求
1. 实现 `ContentFetcher(BaseFetcher)`，`kind` 返回 `"content"`
2. `fetch(request)`：用 urllib 或 httpx 请求 URL，返回 FetchResult
3. extract(result)：从 FetchResult.raw_content 的 HTML 中用 readability-lxml 提取正文
   - 输出 `ExtractedItem(title=..., body=..., url=...)` （仅一条）
   - 如 readability 提取失败，返回空列表（不抛异常）
4. normalize(items)：直接将 ExtractedItem 转为 NormalizedArticle（无需特殊处理）
5. 所有失败路径返回 FetchResult(success=False, error_message=..., error_code=...) 或空 list
6. 单元测试覆盖：成功提取、HTTP 404、网络错误、空 HTML、非 HTML 响应

#### 依赖安装
```bash
pip install readability-lxml
```

#### 验收检查
```bash
cd services/api && python -m pytest tests/test_content_fetcher.py -v
```

#### 完成后 commit
```bash
git add services/api/app/services/fetchers/content_fetcher.py services/api/tests/test_content_fetcher.py
git commit -m "feat: implement content fetcher with readability extraction"
```

---

### Task P4-B: L1-C06 文章规范化与去重

- **Status:** pending
- **Owner:** (待分配)
- **Commit:** （待交付）

#### 任务
实现 `ArticleNormalizer`，统一 URL 格式、清洗文本、基于 URL 和 dedupe_key 防止重复入库。

#### 上下文文件（先读）
- services/api/app/core/fetcher_interface.py — NormalizedArticle, make_dedupe_key 定义
- services/api/app/repositories/article_repository.py — get_by_url, get_by_dedupe_key, create
- services/api/app/models/article.py — Article ORM 模型
- docs/architecture/domain-model.md — Article 定义

#### 可以创建/修改的文件
- services/api/app/services/article_normalizer.py — 新建
- services/api/tests/test_article_normalizer.py — 新建
- services/api/app/repositories/article_repository.py — **仅可增加查询方法**，不改已有方法签名

#### 禁碰文件
- apps/web/, packages/, services/api/app/models/, services/api/app/services/fetchers/, services/api/app/routers/, services/api/app/schemas/, services/api/app/services/digests.py, services/api/app/services/article_service.py, services/api/app/repositories/source_repository.py, services/api/app/database.py, services/api/app/core/config.py, docs/

#### 实现要求
1. 实现 `ArticleNormalizer` 类（普通 service 类，非 BaseFetcher）
2. 接收 `Session` + `ArticleRepository` 作为依赖
3. URL 规范化：
   - 去除尾部斜杠
   - 去除 `utm_*` / `fbclid` / `gclid` 等追踪参数
   - 统一 protocol 为 https
4. 文本清洗：
   - 去除多余空白（strip, 合并多空格）
   - HTML entity 解码（`&amp;` → `&` 等）
   - title > 500 字符截断，summary > 2000 字符截断
5. 去重检查：
   - 先用 `get_by_url` 查（URL 规范化后）
   - 再用 `get_by_dedupe_key` 查（make_dedupe_key 生成）
   - 任一匹配则标记为 duplicate，不创建
6. 提供 `normalize_article(article: NormalizedArticle) -> Article | None`
   - 返回创建的 Article ORM 对象，或 None（重复时）
7. 单元测试覆盖：URL 规范化、HTML entity、空白折叠、截断、URL 重复、dedupe_key 重复、全部合法

#### 验收检查
```bash
cd services/api && python -m pytest tests/test_article_normalizer.py -v
```

#### 完成后 commit
```bash
git add services/api/app/services/article_normalizer.py services/api/tests/test_article_normalizer.py
git commit -m "feat: implement article normalizer with URL cleaning and dedup"
```

> note: 如果需修改 article_repository.py，单独 stage：`git add services/api/app/repositories/article_repository.py`

---

### Task P4-C: L1-C07 事件聚类服务

- **Status:** pending
- **Owner:** (待分配)
- **Commit:** （待交付）

#### 任务
实现 `ClusterService`，将多家媒体对同一事件的报道聚成 cluster，支持代表文章选取和分值计算。

#### 上下文文件（先读）
- services/api/app/models/article.py — Article 模型
- services/api/app/models/cluster.py — Cluster 模型
- services/api/app/models/cluster_member.py — ClusterMember 模型
- services/api/app/repositories/article_repository.py — list_recent, get_by_id
- docs/architecture/domain-model.md — Cluster 实体定义

#### 可以创建的文件（仅此 3 个）
- services/api/app/services/cluster_service.py
- services/api/app/repositories/cluster_repository.py
- services/api/tests/test_cluster_service.py

#### 禁碰文件
- 同 P4-A（除上面 3 个文件外一切文件）

#### 实现要求
1. 实现 `ClusterService`，接收 Session 作为依赖
2. `cluster_articles(since: datetime) -> int`：对 since 之后的文章聚类
3. 聚类算法：**TF-IDF + cosine similarity**
   - 用 sklearn TfidfVectorizer（停用词 = english）
   - 输入 = title + " " + (summary or "")
   - 相似度阈值 0.6（可配置默认参数）
4. 代表文章选取：cluster 内 source 最丰富的文章
5. Cluster 分值：
   - `score = article_count * 0.4 + distinct_source_count * 0.6`
   - 单一来源 cluster 自动扣分
6. 聚类为全量扫描 + 分组，不做增量（简单即可）
7. 同一篇文章不应出现在多个 cluster 中
8. 已存在于 cluster 的文章自动跳过

#### 依赖安装
```bash
pip install scikit-learn scipy
```

#### 验收检查
```bash
cd services/api && python -m pytest tests/test_cluster_service.py -v
```

#### 完成后 commit
```bash
git add services/api/app/services/cluster_service.py services/api/app/repositories/cluster_repository.py services/api/tests/test_cluster_service.py
git commit -m "feat: implement event clustering with TF-IDF similarity"
```

---

### Task P4-D: L1-C08 日报排序与生成服务

- **Status:** pending
- **Owner:** (待分配)
- **Commit:** （待交付）

#### 任务
实现 `DigestGenerator`，基于 cluster 热度和时效性生成指定日期的日报。支持幂等重跑。

#### 上下文文件（先读）
- services/api/app/models/digest.py — Digest 模型
- services/api/app/models/digest_entry.py — DigestEntry 模型
- services/api/app/models/cluster.py — Cluster 模型
- services/api/app/models/cluster_member.py — ClusterMember, 关联 article
- services/api/app/models/article.py — Article, 取 headline/summary
- packages/shared-types/src/resources/digest.py — DigestResource 契约（对齐输出结构）
- docs/architecture/domain-model.md — Digest / DigestEntry 定义

#### 可以创建的文件（仅此 3 个）
- services/api/app/services/digest_generator.py
- services/api/app/repositories/digest_repository.py
- services/api/tests/test_digest_generator.py

#### 禁碰文件
- 同 P4-A。特别注意不要改 services/api/app/services/digests.py（现有静态 stub）

#### 实现要求
1. 实现 `DigestGenerator`，接收 Session 作为依赖
2. `generate(target_date: date) -> Digest`：
   - 查询 target_date 当天或最近的 clusters
   - 按 `score = cluster.score * 0.6 + cluster.size * 0.3 + num_sources * 0.1` 降序
   - 取 top 15（默认）
3. 每个 DigestEntry：
   - headline / summary 来自 cluster 的 representative article
   - category 可为 None
   - source_count = cluster 内不同 source 数量
4. 幂等：先删 target_date 已存在的 Digest + entries，再重建
5. 空数据日：创建 `Digest(status="draft")`，entries=[]，不会 404
6. 单元测试覆盖：正常生成、幂等覆盖、空数据日、边界日期

#### 验收检查
```bash
cd services/api && python -m pytest tests/test_digest_generator.py -v
```

#### 完成后 commit
```bash
git add services/api/app/services/digest_generator.py services/api/app/repositories/digest_repository.py services/api/tests/test_digest_generator.py
git commit -m "feat: implement daily digest generation service"
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

**合计：95 后端 pytest + 29 前端 vitest = 124 tests 全部通过 ✅**

## 后续批次规划

| 批次 | 任务 | 说明 |
|------|------|------|
| **本批（P4）** | C05, C06, C07, C08 | 四路并行：正文提取 / 规范化去重 / 聚类 / 日报生成 |
| 下一批（P5） | C09, C10, D01→D05 | 翻译服务、调度编排、API 现实数据 |
| 再下一批（P6） | E01/E02/E06/E09 + B04 | Web 剩余功能 + packages/ui |
| 最后一批（P7） | F01→F07 | CI/CD、测试基线、部署、监控 |
