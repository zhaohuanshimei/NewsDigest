# Parallel Tasks Board

> 本文件是并行任务派单与验收的单一事实来源。subagent 只读本文件中自己任务 ID 对应的 section，不写本文件。派单与状态更新由协调者完成。

## 状态约定

- `pending` — 已派单，等待 subagent 执行
- `in_progress` — subagent 已开始
- `review` — subagent 已交付 commit，等待验收
- `done` — 已验收通过，压缩到"已完成"区

## 当前并行批次（2026-06-25）

### Task E07-SEO

- **Status:** pending
- **Owner:** subagent
- **Commit:** (待交付)

#### 任务
实现 L1-E07 SEO 基础面。目标：为首页、归档页、cluster 详情页建立 meta、Open Graph、Twitter Card、robots.txt、sitemap.xml、JSON-LD 基础。

#### 上下文文件（先读）
- apps/web/src/layouts/BaseLayout.astro — 当前布局，props 是 { title, description }
- apps/web/src/pages/index.astro — 首页
- apps/web/src/pages/archive.astro — 归档页
- apps/web/src/pages/clusters/[id].astro — cluster 详情页
- apps/web/src/lib/config/site.ts — SITE_TITLE, SITE_DESCRIPTION
- apps/web/astro.config.mjs — Astro 配置
- apps/web/package.json — 当前依赖

#### 可以修改的文件（ONLY these）
- apps/web/src/layouts/BaseLayout.astro — 加 meta/OG/Twitter Card
- apps/web/src/pages/index.astro — 加页面级 meta 和 JSON-LD
- apps/web/src/pages/archive.astro — 加页面级 meta
- apps/web/src/pages/clusters/[id].astro — 加页面级 meta
- apps/web/astro.config.mjs — 加 sitemap 集成（@astrojs/sitemap）
- apps/web/package.json — 加 @astrojs/sitemap 依赖
- apps/web/public/robots.txt — 新建

#### 禁碰文件（DO NOT touch）
- apps/web/src/styles/global.css
- apps/web/src/lib/config/site.ts
- apps/web/src/lib/content/* （所有 seam 文件）
- apps/web/src/env.d.ts
- apps/web/src/components/digest/*
- apps/web/src/components/cluster/*
- apps/web/src/components/states/*
- packages/shared-types/*
- services/api/*
- 任何 docs/ 下的文件

#### 验收标准
1. 首页、归档页、cluster 详情页有正确的 `<title>`、meta description、Open Graph 标签、Twitter Card 标签
2. `/robots.txt` 可访问且内容合理
3. `/sitemap.xml` 可访问（通过 @astrojs/sitemap 集成自动生成）
4. 至少首页有 JSON-LD 结构化数据输出
5. 构建不报错，现有测试不回归

#### 完成后必须运行
`npm --prefix apps/web run check`，确认全绿后再 commit。

#### commit 格式
```
git add <你改的文件>
git commit -m "feat: add seo meta sitemap and robots"
```

---

### Task E08-RSS

- **Status:** pending
- **Owner:** subagent
- **Commit:** (待交付)

#### 任务
实现 L1-E08 RSS 输出与订阅页。目标：恢复标准 RSS feed，并独立提供订阅说明页。

#### 上下文文件（先读）
- apps/web/src/pages/index.astro — 首页，了解现有页面结构
- apps/web/src/layouts/BaseLayout.astro — 布局组件
- apps/web/src/lib/config/site.ts — SITE_TITLE, SITE_DESCRIPTION, readApiBaseUrl
- apps/web/src/lib/content/getLatestDigest.ts — 首页 seam，了解如何获取 digest
- apps/web/src/lib/content/mockDigest.ts — mock 数据结构
- apps/web/astro.config.mjs — Astro 配置
- apps/web/package.json — 当前依赖
- packages/shared-types/src/resources/digest.ts — DigestResource 契约

#### 可以创建的文件（ONLY these, all new）
- apps/web/src/pages/feed.xml.ts — RSS feed 端点
- apps/web/src/pages/rss.astro — 订阅说明页

#### 禁碰文件（DO NOT touch）
- apps/web/astro.config.mjs
- apps/web/src/styles/global.css
- apps/web/src/lib/config/site.ts
- apps/web/src/lib/content/* （所有 seam 文件）
- apps/web/src/env.d.ts
- apps/web/src/pages/index.astro
- apps/web/src/pages/archive.astro
- apps/web/src/pages/clusters/*
- apps/web/src/components/*
- apps/web/src/layouts/*
- packages/shared-types/*
- services/api/*
- 任何 docs/ 下的文件

#### 实现要求
1. `/feed.xml` 返回合法 XML RSS 2.0 feed，content-type: `application/xml`
2. feed 内容从 `loadHomepageDigest()` 获取（复用现有 seam），success 时输出条目，empty/error 时返回合法空 feed
3. `/rss` 提供订阅说明页，使用 BaseLayout，告知用户 feed 地址
4. 不要 fabricate 原文链接，`DigestEntryResource` 只保证 `headline`/`summary`/`source_count`

#### 完成后必须运行
`npm --prefix apps/web run check`，确认全绿后再 commit。

#### commit 格式
```
git add apps/web/src/pages/feed.xml.ts apps/web/src/pages/rss.astro
git commit -m "feat: add rss feed and subscription page"
```

---

### Task B02-CONFIG

- **Status:** pending
- **Owner:** subagent
- **Commit:** (待交付)

#### 任务
实现 L1-B02 环境变量与配置规范。目标：统一 API、Web、数据库、翻译、调度、部署配置的命名与来源。

#### 上下文文件（先读）
- docs/architecture/overview.md — 架构总览
- docs/architecture/non-functional-targets.md — 非功能目标
- apps/web/src/lib/config/site.ts — 前端现有配置（DEFAULT_API_BASE_URL, readApiBaseUrl, 各种 mock override）
- apps/web/src/env.d.ts — 前端环境变量类型
- services/api/app/core/config.py — 后端现有配置（API_PREFIX）
- services/api/app/core/metadata.py — 后端元信息

#### 可以创建/修改的文件（ONLY these）
- .env.example — 新建，全项目统一环境变量模板
- docs/architecture/configuration.md — 新建，配置规范文档

#### 禁碰文件（DO NOT touch）
- 所有 apps/ 下的代码文件
- 所有 services/ 下的代码文件
- 所有 packages/ 下的代码文件
- apps/web/src/env.d.ts
- apps/web/src/lib/config/site.ts
- services/api/app/core/config.py
- 任何其他 docs/ 下的文件（只新建 configuration.md，不改其他）

#### 实现要求
1. `.env.example` 覆盖：API 服务端口、数据库连接、翻译 API key 占位、前端 API base URL、各环境差异说明
2. 开发、测试、预发、生产四类环境的差异明确（用注释分组）
3. 不把真实密钥写入文件，只用占位符
4. `docs/architecture/configuration.md` 说明：变量命名规范、来源优先级、各环境差异、密钥管理原则
5. 文档里引用的变量名必须和现有代码里实际使用的一致（`PUBLIC_DIGEST_STATE`, `PUBLIC_ARCHIVE_STATE`, `PUBLIC_CLUSTER_STATE`, `NEWS_DIGEST_API_BASE_URL`, `API_PREFIX`）

#### 完成后
这个任务不涉及代码，无需跑测试。确认文档和 `.env.example` 写好后直接 commit。

#### commit 格式
```
git add .env.example docs/architecture/configuration.md
git commit -m "docs: add environment configuration spec and env example"
```

---

## 已完成

（暂无）
