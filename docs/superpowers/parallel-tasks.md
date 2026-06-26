# Parallel Tasks Board

> 本文件是任务派单与验收的单一事实来源。subagent 只读本文件中自己 Task ID 对应的 section，不写本文件。派单与状态更新由协调者完成。

## 状态约定

- `pending` — 已派单，等待 agent 执行
- `in_progress` — agent 已开始
- `review` — agent 已交付 commit，等待验收
- `done` — 已验收通过，压缩到"已完成"区

---

## 当前任务批次

（无 — P4 已全部验收通过，等待 P5 派单）

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
| **下一批（P5）** | C09, C10, D01→D05 | 翻译服务、调度编排、API 现实数据 |
| 再下一批（P6） | E01/E02/E06/E09 + B04 | Web 剩余功能 + packages/ui |
| 最后一批（P7） | F01→F07 | CI/CD、测试基线、部署、监控 |
