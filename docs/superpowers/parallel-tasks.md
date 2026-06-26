# Parallel Tasks Board

> 本文件是任务派单与验收的单一事实来源。subagent 只读本文件中自己 Task ID 对应的 section，不写本文件。派单与状态更新由协调者完成。

## 状态约定

- `pending` — 已派单，等待 agent 执行
- `in_progress` — agent 已开始
- `review` — agent 已交付 commit，等待验收
- `done` — 已验收通过，压缩到"已完成"区

---

## 当前任务批次（2026-06-26）：L1-C 数据管线（P4）

> **执行方式：线性顺序。** 同一个 agent 按 Task 1 → Task 2 → Task 3 顺序执行，每个 task 独立 commit。完成前一个 task 后才能开始下一个。

---

### Task 1: L1-C05 正文提取器 + L1-C06 文章规范化与去重

- **Status:** pending
- **Owner:** agent
- **Commit:** （待交付）

#### 任务
对需要正文抽取的来源实现正文抓取与清洗（C05）；统一 URL、清洗文本、处理重复文章（C06）。

#### 上下文文件（先读）
- services/api/app/core/fetcher_interface.py — BaseFetcher, FetchRequest, FetchResult, ExtractedItem, NormalizedArticle, make_dedupe_key
- services/api/app/models/article.py — Article ORM 模型
- services/api/app/repositories/article_repository.py — 文章仓库（get_by_url, get_by_dedupe_key, create 等方法）
- services/api/app/services/fetchers/rss_fetcher.py — RssFetcher 实现参考
- services/api/tests/test_rss_fetcher.py — 测试风格参考
- docs/architecture/domain-model.md — Article 实体定义

#### 可以创建/修改的文件
- services/api/app/services/fetchers/content_fetcher.py — 新建，正文提取器（C05）
- services/api/app/services/article_normalizer.py — 新建，规范化服务（C06）
- services/api/app/repositories/article_repository.py — **可修改**，增加规范化相关的查询方法
- services/api/tests/test_content_fetcher.py — 新建（C05 测试）
- services/api/tests/test_article_normalizer.py — 新建（C06 测试）

#### 禁碰文件
- apps/web/ 下任何文件
- packages/shared-types/ 下任何文件
- services/api/app/models/ 下已有文件（读但不改）
- services/api/app/routers/ 下任何文件
- services/api/app/schemas/ 下任何文件
- services/api/app/services/digests.py
- services/api/app/services/article_service.py
- services/api/app/repositories/source_repository.py
- services/api/app/database.py
- services/api/app/core/config.py
- docs/ 下任何文件

#### C05 实现要求
1. 实现 `ContentFetcher(BaseFetcher)`，对支持正文抓取的文章 URL 获取 HTML 内容
2. 使用 readability-lxml 或类似库从 HTML 中提取正文（纯文本即可）
3. 提取结果填入 ExtractedItem 的 body 字段
4. 失败不抛异常，返回 FetchResult(success=False, error_message=...)
5. 需要在外网可访问的环境才能完整验证，单元测试覆盖接口行为和错误路径

#### C06 实现要求
1. 实现 `ArticleNormalizer` 类（非 BaseFetcher，独立的 service 类）
2. URL 规范化规则：
   - 去除尾部斜杠
   - 去除 `utm_*` / `fbclid` / `gclid` 等追踪参数
   - 统一 protocol 为 https
3. 文本清洗规则：
   - 去除多余空白
   - 去除 HTML entity 转义
   - 截断过长字段（如 title > 500 字符截断）
4. 去重策略：用 `get_by_url` + `get_by_dedupe_key` 分别检查，避免重复入库
5. 单元测试覆盖常见重复与空值场景

#### 验收检查
```bash
cd services/api && python -m pytest tests/ -v
```

#### 完成后 commit
```bash
git add services/api/app/services/fetchers/content_fetcher.py services/api/app/services/article_normalizer.py services/api/tests/test_content_fetcher.py services/api/tests/test_article_normalizer.py
git commit -m "feat: add content fetcher and article normalizer"
```

---

### Task 2: L1-C07 事件聚类服务

- **Status:** pending
- **Owner:** agent
- **Commit:** （待交付）
- **Depends on:** Task 1 完成后开始

#### 任务
将多家媒体对同一事件的报道聚成 cluster，支持代表文章选取、cluster 大小统计和分值计算。

#### 上下文文件（先读）
- services/api/app/models/article.py — Article 模型
- services/api/app/models/cluster.py — Cluster 模型
- services/api/app/models/cluster_member.py — ClusterMember 模型
- services/api/app/repositories/article_repository.py — 文章查询
- services/api/tests/test_cluster_service.py — 新建
- docs/architecture/domain-model.md — Cluster 实体定义

#### 可以创建/修改的文件
- services/api/app/services/cluster_service.py — 新建
- services/api/app/repositories/cluster_repository.py — 新建
- services/api/tests/test_cluster_service.py — 新建

#### 禁碰文件
同 Task 1。

#### 实现要求
1. 实现 `ClusterService`，接收 Session 作为依赖
2. 提供 `cluster_articles(since: datetime) -> int` 方法：对指定时间范围内的文章执行聚类
3. 聚类算法：**基于文本相似度的简单实现**（如 TF-IDF + cosine similarity 或简单的关键词 overlap）
   - 标题 + 摘要的文本相似度超过阈值（可配置，默认 0.6）则归为同一 cluster
   - 同一 cluster 内的文章按 source 多样性评分，选择代表文章（representative_article_id）
4. 提供 `get_or_create_cluster(article_id, similar_article_ids) -> Cluster`
5. Cluster 分值（score）计算：
   - 基础 = 文章数量
   - 加分 = 不同来源数量
   - 减分 = 仅有单一来源
6. 幂等：同一篇文章不应被重复 clustering 产生新 cluster
7. 已存在于 cluster 的文章跳过

#### 验收检查
```bash
cd services/api && python -m pytest tests/test_cluster_service.py -v
```

#### 完成后 commit
```bash
git add services/api/app/services/cluster_service.py services/api/app/repositories/cluster_repository.py services/api/tests/test_cluster_service.py
git commit -m "feat: implement event clustering service"
```

---

### Task 3: L1-C08 日报排序与生成服务

- **Status:** pending
- **Owner:** agent
- **Commit:** （待交付）
- **Depends on:** Task 2 完成后开始

#### 任务
基于 cluster 热度和时效性生成指定日期的日报 digest。支持幂等重跑。

#### 上下文文件（先读）
- services/api/app/models/digest.py — Digest 模型
- services/api/app/models/digest_entry.py — DigestEntry 模型
- services/api/app/models/cluster.py — Cluster 模型
- services/api/app/services/cluster_service.py — 聚类服务（上一步）
- docs/architecture/domain-model.md — Digest / DigestEntry 定义
- packages/shared-types/src/resources/digest.py — DigestResource 契约（对齐输出字段）

#### 可以创建/修改的文件
- services/api/app/services/digest_generator.py — 新建，日报生成服务
- services/api/app/repositories/digest_repository.py — 新建
- services/api/tests/test_digest_generator.py — 新建
- services/api/app/services/article_service.py — **可修改**，增加需要的查询

#### 禁碰文件
同前。注意不要改 services/api/app/services/digests.py（现有的静态 stub 服务）。

#### 实现要求
1. 实现 `DigestGenerator`，接收 Session 作为依赖
2. `generate(target_date: date) -> Digest`：为指定日期生成日报
   - 查询该日期范围内（或最接近的）clusters
   - 按 cluster.score 降序排列
   - 取 top N（默认 15）作为 DailyDigest 条目
   - 创建或覆盖 Digest + DigestEntry 记录
3. 幂等：同一天重复调用不会产生重复条目（先删除已有 Digests 再重建，或用 upsert）
4. 排序公式：
   ```
   score = cluster.score * 0.6 + cluster.size * 0.3 + num_sources * 0.1
   ```
5. 空数据日仍然创建 Digest（status="draft", entries=[]），不会 404
6. 每个 entry 的 headline/summary 来自 cluster 的 representative_article

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

**合计：89 后端 pytest + 29 前端 vitest = 118 tests 全部通过 ✅**

## 后续批次规划

| 批次 | 任务 | 说明 |
|------|------|------|
| **本批（P4）** | C05→C08 | 正文提取、规范化、聚类、日报生成 |
| 下一批（P5） | C09, C10, D01→D05 | 翻译服务、调度编排、API 现实数据 |
| 再下一批（P6） | E01/E02/E06/E09 + B04 | Web 剩余功能 + packages/ui |
| 最后一批（P7） | F01→F07 | CI/CD、测试基线、部署、监控 |
