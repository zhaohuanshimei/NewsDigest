# Parallel Tasks Board

> 本文件是任务派单与验收的单一事实来源。subagent 只读本文件中自己 Task ID 对应的 section，不写本文件。派单与状态更新由协调者完成。

## 状态约定

- `pending` — 已派单，等待 agent 执行
- `in_progress` — agent 已开始
- `review` — agent 已交付 commit，等待验收
- `done` — 已验收通过，压缩到"已完成"区

---

## 当前任务批次（2026-06-26）：L1-C 数据管线

> **执行方式：线性顺序。** 同一个 agent 按 Task 1 → Task 2 → Task 3 顺序执行，每个 task 独立 commit。完成前一个 task 后才能开始下一个。

---

### Task 1: L1-C01 数据库 schema 与 migration

- **Status:** pending
- **Owner:** agent
- **Commit:** （待交付）

#### 任务
建立 V2 数据库 schema 与首版 Alembic migration。将 V1 已验证的数据结构转化为 V2 SQLAlchemy 模型。

#### 上下文文件（先读）
- docs/architecture/domain-model.md — 领域模型定义（Source, Article, Cluster, Digest 等实体关系）
- docs/architecture/overview.md — 架构总览
- packages/shared-types/src/resources/ — 共享契约中定义的所有 Resource 类型
- services/api/app/core/config.py — 后端配置（DATABASE_URL 已定义）
- legacy-reference/ — 参考 V1 的表结构设计

#### 可以创建/修改的文件
- services/api/app/models/ — 新建目录，放 SQLAlchemy ORM 模型
- services/api/alembic/ — 新建 Alembic 迁移目录
- services/api/alembic.ini — 新建 Alembic 配置
- services/api/app/database.py — 新建，数据库会话/引擎管理
- services/api/app/core/config.py — 修改，增加 DATABASE_URL 读取
- services/api/requirements.txt — 修改，增加 psycopg2, alembic, sqlalchemy 等依赖
- services/api/requirements-dev.txt — 修改，同上

#### 禁碰文件（DO NOT touch）
- apps/web/ 下任何文件
- apps/web/src/lib/config/site.ts
- apps/web/src/env.d.ts
- packages/shared-types/ 下任何文件
- services/api/app/routers/ 下任何文件
- services/api/app/schemas/ 下任何文件
- services/api/app/services/ 下任何文件
- 任何 docs/ 下除已列出的文件

#### 实现要求
1. 数据表覆盖：sources, articles, translations, clusters, cluster_members, daily_digests
2. 模型文件放到 `services/api/app/models/`，每个实体一个文件（例如 source.py, article.py, cluster.py, digest.py）
3. 数据库 session 工具放在 `services/api/app/database.py`
4. migration 能空库执行成功
5. schema 与 `docs/architecture/domain-model.md` 对齐
6. 外键关系、唯一约束、索引按需定义
7. 每个模型有 `id`、`created_at`、`updated_at` 基础字段

#### 验收检查
```bash
cd services/api
# 创建测试数据库
# 运行 migration
alembic upgrade head
# 确认所有表已创建
# 验证核心字段与 domain model 一致
```

#### 完成后 commit
```bash
git add services/api/alembic/ services/api/alembic.ini services/api/app/models/ services/api/app/database.py
git commit -m "feat(db): add ORM models and initial migration"
```

---

### Task 2: L1-C02 源配置与加载器 + L1-C03 抓取适配器接口

- **Status:** pending
- **Owner:** agent
- **Commit:** （待交付）
- **Depends on:** Task 1 完成后开始

#### 任务
以表驱动方式管理新闻源配置，并为 RSS 抓取与正文爬取定义统一输入输出接口。

#### 上下文文件（先读）
- services/api/app/models/ （上一步创建的表模型）
- docs/architecture/domain-model.md — 源（Source）实体定义
- legacy-reference/ — 参考 V1 的源配置方式和抓取逻辑

#### 可以创建/修改的文件
- services/api/app/repositories/source_repository.py — 新建，源的 CRUD 查询
- services/api/app/services/source_service.py — 新建，源配置管理服务
- services/api/app/core/fetcher_interface.py — 新建，抓取适配器接口定义
- services/api/tests/ — 可新建测试
- services/api/requirements.txt — 可增加依赖（如 feedparser）

#### 禁碰文件（DO NOT touch）
- apps/web/ 下任何文件
- packages/shared-types/ 下任何文件
- services/api/app/routers/ 下任何文件
- services/api/app/schemas/ 下任何文件
- services/api/app/services/digests.py
- 任何 docs/ 下文件

#### 实现要求
1. Source 配置支持：id, name, type(rss/crawler), url, language, enabled, fetch_interval_minutes, last_fetched_at
2. 至少有一组首发默认源（参考 V1 配置）可通过 seed 函数或初始 migration 加载
3. 抓取适配器接口清晰区分三个阶段：source fetch → content extract → normalize
4. 接口定义支持超时、重试、User-Agent 配置
5. 错误、失败状态有统一表达方式
6. 有单元测试覆盖

#### 验收检查
```bash
cd services/api
python -m pytest tests/ -v
# 确认源 CRUD 和适配器接口测试通过
```

#### 完成后 commit
```bash
git add services/api/app/repositories/source_repository.py services/api/app/services/source_service.py services/api/app/core/fetcher_interface.py
git commit -m "feat: add source config service and fetch adapter interface"
```

---

### Task 3: L1-C04 RSS 抓取器

- **Status:** pending
- **Owner:** agent
- **Commit:** （待交付）
- **Depends on:** Task 2 完成后开始

#### 任务
实现首发新闻源的 RSS 抓取、标准化文档写入 articles 表。

#### 上下文文件（先读）
- services/api/app/core/fetcher_interface.py （上一步定义的适配器接口）
- services/api/app/models/source.py, article.py （表定义）
- services/api/app/repositories/source_repository.py （源查询工具）
- docs/architecture/domain-model.md — Article 实体定义
- legacy-reference/ — 参考 V1 的 RSS 抓取实现

#### 可以创建/修改的文件
- services/api/app/services/fetchers/ — 新建目录
- services/api/app/services/fetchers/rss_fetcher.py — 新建，RSS 抓取实现
- services/api/app/services/article_service.py — 新建，文章写入/查询服务
- services/api/app/repositories/article_repository.py — 新建，文章仓库
- services/api/tests/ — 可新建测试
- services/api/requirements.txt — 可增加 feedparser 等依赖

#### 禁碰文件（DO NOT touch）
- apps/web/ 下任何文件
- packages/shared-types/ 下任何文件
- services/api/app/routers/ 下任何文件
- services/api/app/schemas/ 下任何文件
- services/api/app/services/digests.py
- 任何 docs/ 下文件

#### 实现要求
1. 实现 `RssFetcher` 类，遵循 Task 2 定义的抓取适配器接口
2. 至少一组配置源能成功抓到文章并写入 articles 表
3. 支持超时、重试、User-Agent 基本配置
4. 抓取结果包含：标题、URL、摘要、来源 ID、发布时间
5. 失败不抛异常（记录到日志），不中断批量抓取
6. 有单元测试覆盖

#### 验收检查
```bash
cd services/api
python -m pytest tests/ -v
# 确认 RSS 抓取器能正常解析 feed 并写入数据库
```

#### 完成后 commit
```bash
git add services/api/app/services/fetchers/ services/api/app/services/article_service.py services/api/app/repositories/article_repository.py
git commit -m "feat: implement RSS fetcher and article persistence"
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

## 后续批次规划

| 批次 | 任务 | 说明 |
|------|------|------|
| 本批（P3） | C01→C04 | 数据库 schema + 源配置 + RSS 抓取 |
| 下一批（P4） | C05→C10 + D01→D05 | 正文提取、聚类、日报、API 现实数据 |
| 再下一批（P5） | E01/E02/E06/E09 + B04 | Web 剩余功能 + packages/ui |
| 最后一批（P6） | F01→F07 | CI/CD、测试基线、部署、监控 |
