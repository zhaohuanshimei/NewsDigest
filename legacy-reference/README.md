# News Digest

每日一份国际要闻中文聚合站。来源可靠、机器翻译、前端简洁清爽、移动端友好。

## 项目定位

- **一日一期**，早上发布，读完即走，不做信息流
- **来源**：Reuters / BBC / AP / Guardian / NYT 等国际主流媒体 RSS + 正文爬虫
- **翻译**：DeepL 翻译标题与摘要，保留原文对照
- **前端**：Astro 静态生成，Mobile-first，零或极少 JS
- **无 AI 摘要**、无广告、无推荐算法

## 技术栈

- 后端：Python + httpx + feedparser + trafilatura + APScheduler
- 存储：PostgreSQL
- 翻译：DeepL API（主）/ Google Translate（备）
- 前端：Astro + 系统字体栈
- 部署：VPS（后端）+ Cloudflare Pages（前端）

## 文档

- 开发计划：`docs/DEVELOPMENT_PLAN.md`
- 北极星计划：`docs/NORTH_STAR_PLAN.md`
- 部署与上线：`docs/DEPLOYMENT.md`
- 测试工程技能库：`docs/QA_SKILL_LIBRARY.md`
- 功能测试矩阵：`docs/TEST_MATRIX.md`
- 工作流约定：`docs/WORKFLOW.md`

## 当前阶段

当前项目已切换到“按北极星计划从零重新开发”的模式。

说明：

- 仓库内存在一批历史实现，它们仅作为参考基线
- 本轮开发进度以 `docs/DEVELOPMENT_PLAN.md` 的任务状态为准
- 当前已完成到 `Phase 4`（前端静态站 + 数据接入 + RSS）
- 当前处于 `Phase 5`（部署与监控），仓库侧已具备可运行的生产流水线与健康页/健康 JSON

当前优先开发项：

- 后端部署到 VPS / 平台（接入真实 PostgreSQL 与定时跑批）
- 前端部署到 Cloudflare Pages（每日构建并发布静态站）
- 站点探活与告警接入（UptimeRobot 等）

## 本地运行

### 导出日报数据

```bash
python -m news_digest.cli export-digest --date 2026-05-01
```

### 执行全链路流水线（抓取→聚类→digest→翻译→导出→webhook）

```bash
python -m news_digest.cli produce --date 2026-05-01 --target-lang zh
```

### 定时执行全链路流水线（cron）

```bash
python -m news_digest.cli produce-schedule --cron "0 6 * * *"
```

可选参数：

- `--no-translate`：跳过翻译
- `--no-export`：跳过导出
- `--output path/to/export.json`：指定导出文件路径
- `--webhook-url https://...`：指定 webhook（默认读取 `FRONTEND_BUILD_WEBHOOK_URL`）

### 启动前端

```bash
cd web
npm install
npm run dev
```

### 前端构建与质量门禁

```bash
cd web
npm run check
npm run test:build
npm run lighthouse
```

可选环境变量：

- `DIGEST_DATE=YYYY-MM-DD`：指定构建时读取哪一天的导出数据
- `DIGEST_JSON_PATH=path/to/export.json`：显式指定导出 JSON 路径（相对仓库根目录或绝对路径）
- `SITE_URL=https://example.com`：生成 RSS 时使用的站点域名

### 健康与探活入口（前端构建产物）

- `/admin/health`：健康页面（读取 `exports/health.json`）
- `/health.json`：健康 JSON（读取 `exports/health.json`，缺失则返回占位）
- `/digest.json`：digest JSON（读取当日或最新导出，缺失则返回空 digest）
