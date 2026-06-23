# 开发计划

> 每个任务 ≤ 1 天，独立可验收。完成一项→测试通过→提交 git→勾选 [x]。
> 工作流细节见 `WORKFLOW.md`。
> 阶段目标与优先级判断见 `NORTH_STAR_PLAN.md`。
> 当前按“从零重新开发”执行：仓库中的历史实现不自动计入以下任务完成度。

## 重开准备

- [x] **R0.1** 重置北极星计划与开发计划的状态口径，明确历史实现不计入本轮完成度
- [x] **R0.2** 建立分批开发与实时进度同步机制
- [x] **R0.3** 清理重建前明确不需要保留的生成物与缓存（如 `node_modules`、`dist`、`.lighthouseci`）
- [x] **R0.4** 确定第一批重建任务：项目骨架、依赖、数据库与抓取基础设施

**验收**：计划状态已与“从零重开”一致，后续每批开发都能在本文件中继续承接。

## 里程碑

- **M1**：单源跑通（T1.2 完成）
- **M2**：多源 + 去重 + 每日清单（Phase 2 完成）
- **M3**：翻译接入（Phase 3 完成）
- **M4**：前端发布（Phase 4 完成）
- **M5**：生产稳定（Phase 5 完成）= MVP 发布，打 tag `v0.1-mvp`

---

## Phase 0：项目初始化

- [ ] **T0.0** 建 git 仓库，写 README / WORKFLOW / DEVELOPMENT_PLAN，完成首次提交
- [x] **T0.1** 初始化 Python 项目（`uv` 或 `poetry`），配置 `ruff` + `pytest`
- [x] **T0.2** 建 `docker-compose.yml`：PostgreSQL + 应用容器
- [x] **T0.3** 设计数据库 schema，写初始 migration（Alembic）

**验收**：`docker compose up` 起得来，空库有表，`pytest` 可运行。

### 数据表（草案）

- `sources`：源配置（id, name, url, type[rss/crawl], lang, enabled, created_at）
- `articles`：原文（id, source_id, url, title, summary, body, published_at, lang, simhash, url_hash, fetched_at）
- `translations`：译文（id, article_id, target_lang, title, summary, provider, translated_at）
- `clusters`：事件聚类（id, representative_article_id, size, first_seen_at）
- `cluster_members`：文章 ↔ cluster 映射
- `daily_digests`：每日精选（date, cluster_id, rank, category）

---

## Phase 1：抓取层

- [x] **T1.1** RSS 抓取模块：输入源列表，输出标准化 `Article` 对象，含重试/超时/UA
- [x] **T1.2** 单源跑通（Reuters 或 BBC），写入数据库 → **M1**
- [x] **T1.3** 扩展到 10 个英语 RSS 源，YAML 配置化
- [x] **T1.4** 爬虫模块：`httpx` + `trafilatura` 提取正文，遵守 `robots.txt`
- [x] **T1.5** 爬虫限流：单源 QPS ≤ 0.5，指数退避，失败隔离
- [x] **T1.6** 调度器：APScheduler，每小时一轮，每源独立任务

**验收**：跑一轮后库里 ≥ 100 条当日文章，10 个源都有数据，失败源不影响其他源。

---

## Phase 2：去重与排序

- [x] **T2.1** URL 规范化（去 utm_*、统一 scheme、去 fragment）
- [x] **T2.2** 标题 SimHash 去重，汉明距离阈值可配
- [x] **T2.3** 事件聚类：同一事件的多家报道聚合为一个 cluster
- [x] **T2.4** 排序算法：`cluster_size × exp(-λ * age_hours)`，λ 可调
- [x] **T2.5** 每日 digest 生成任务：早 6 点选 top 20，写入 `daily_digests` → **M2**

**验收**：`daily_digests` 能拿到当日 20 条清单，同一事件不重复出现。

---

## Phase 3：翻译层

- [x] **T3.1** 翻译适配器接口，实现 DeepL provider（key 走 env）
- [x] **T3.2** 只翻译标题 + 摘要，结果缓存至 `translations`
- [x] **T3.3** 批量翻译任务：digest 生成后触发，已译过的跳过
- [x] **T3.4** 降级：DeepL 失败时回落 Google Translate → **M3**

**验收**：20 条 digest 全部有中文标题和摘要，重跑不重复计费。

---

## Phase 4：前端

- [x] **T4.1** Astro 项目初始化，TS + `prefers-color-scheme` 深色模式
- [x] **T4.2** 样式系统：字体栈、配色变量、移动端字号/行高基线
- [x] **T4.3** 首页模板：日期栏 + 分类锚点 + 单列列表
- [x] **T4.4** 新闻条目组件：标题、摘要、来源标签、原文/英文切换
- [x] **T4.5** 归档页 `/archive` + 历史直链 `/YYYY-MM-DD`
- [x] **T4.6** 数据接入：构建时从导出 JSON 读取当日 digest 生成静态页
- [x] **T4.7** 站点 RSS 输出 `/feed.xml`
- [x] **T4.8** Lighthouse 移动端调优至 95+（CI 自动校验） → **M4**

**验收**：手机浏览流畅，Lighthouse Performance/Accessibility 均 ≥ 95。

---

## Phase 5：部署与监控

- [ ] **T5.1** 后端部署：VPS（Hetzner / Fly.io），跑抓取 + DB
- [ ] **T5.2** 前端部署：Cloudflare Pages，每日构建
- [x] **T5.3** 构建流水线：抓取 → 聚类 → digest → 翻译 → 导出 → 触发前端构建（webhook）
- [x] **T5.4** 源健康度仪表盘 `/admin/health`
- [ ] **T5.5** UptimeRobot 监控
- [x] **T5.6** 日志与告警：源连续失败 3 次告警 → **M5** 打 tag `v0.1-mvp`

**验收**：每日早 7 点前自动上线新一期，任一源挂掉有告警。

---

## Phase 6：完善（滚动进行）

- [ ] **T6.1** 扩展到 20+ 源（欧洲、亚洲语种）
- [ ] **T6.2** 爬虫支持 Playwright 渲染类站点
- [ ] **T6.3** 已读标记（localStorage）+ 客户端语言切换
- [ ] **T6.4** 邮件订阅
- [ ] **T6.5** 分类细化（财经 / 科技 / 政治）
- [ ] **T6.6** 翻译质量抽检脚本
- [ ] **T6.7** GDELT 热度交叉验证

---

## 质量与测试（横切）

- [ ] **Q1** 建立测试工程技能库，沉淀项目级 QA 能力模型与实践标准
- [ ] **Q2** 建立功能测试矩阵，覆盖已实现功能与未来功能测试规格
- [ ] **Q3** 为高风险后端链路补齐自动化测试：CLI、调度器、仓储、抓取器、爬虫、翻译
- [ ] **Q4** 完成一次工程级全量回归基线：`python -m pytest`
- [ ] **Q5** 增加覆盖率统计与门槛：`pytest-cov`（当前基线：`--cov-fail-under=85`）
- [ ] **Q6** 接入静态质量门禁：`ruff check .`、`mypy src/news_digest`
- [ ] **Q7** 为日报导出层增加 schema / 契约测试
- [ ] **Q8** 为前端接入增加构建集成测试与关键路径 E2E（无导出/坏 JSON/有效 JSON）
- [ ] **Q9** 将测试、lint、类型检查接入 CI 持续执行（GitHub Actions）

**验收**：已实现功能具备自动化测试，未实现功能具备测试规格，工程级回归可稳定执行。

---

## 依赖关系

```
T0 → T1 → T2 → T3 ─┐
           └───────┼→ T5
              T4 ──┘
```

T4 可与 T1-T3 并行（先用 fixture 数据）。

## 下一步

当前优先进入 **Phase 5 (T5.1-T5.6)**，从部署与监控重新开始。

下一批承接建议：

- Phase 1：扩展到 10 个英语 RSS 源并完成 YAML 配置化校验
- Phase 1：重建正文抓取模块，补 `robots.txt`、提取与失败隔离的最小验收
- Phase 1：落地域名级限流与指数退避门槛，并把失败源隔离为可观测事件
- Phase 1：调度器支持每源独立任务与统计汇总，确保“单源失败不拖垮整轮”
- 质量横切：继续保持“每完成一小步即验收”的节奏
