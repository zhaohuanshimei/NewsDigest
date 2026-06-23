# 部署与上线说明

本文档用于首版生产上线，默认部署形态为：

- 后端：VPS + Docker Compose
- 数据库：PostgreSQL
- 前端：Cloudflare Pages
- 发布链路：后端生产流水线生成 `exports/*.json` 与 `exports/health.json`，随后触发前端构建 webhook

## 1. 上线前准备

### 1.1 Git 与代码

- 确认当前提交已通过本地检查
- 确认生产环境将拉取正确提交
- 建议为本次上线打 tag，例如 `v0.1.0`

### 1.2 环境变量

基于仓库根目录的 `.env.example` 生成生产 `.env`，至少需要配置：

```env
DATABASE_URL=postgresql+psycopg://news:strong-password@db-host:5432/news_digest
DEEPL_API_KEY=
GOOGLE_TRANSLATE_API_KEY=
LOG_LEVEL=INFO
TZ=Asia/Shanghai
FRONTEND_BUILD_WEBHOOK_URL=https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/...
SITE_URL=https://your-domain.example
```

说明：

- `DATABASE_URL`：后端数据库连接串
- `DEEPL_API_KEY`：主翻译服务，建议生产配置
- `GOOGLE_TRANSLATE_API_KEY`：备选翻译服务，可选
- `FRONTEND_BUILD_WEBHOOK_URL`：后端生产流水线完成后触发前端重新构建
- `SITE_URL`：前端生成 RSS 时使用的正式域名

## 2. 后端部署

### 2.1 准备服务器

建议在 VPS 上安装：

- Docker
- Docker Compose Plugin
- Git

目录示例：

```bash
sudo mkdir -p /srv/news-digest
sudo chown "$USER":"$USER" /srv/news-digest
cd /srv/news-digest
git clone <your-repo-url> .
```

### 2.2 准备配置与持久化目录

```bash
cp .env.example .env
mkdir -p exports
```

按实际生产值编辑 `.env`。

### 2.3 启动数据库与后端

```bash
docker compose up -d --build
```

说明：

- `Dockerfile` 会在容器启动时自动执行 `alembic upgrade head`
- `docker-compose.yml` 会把本地 `./exports` 挂载到容器 `/app/exports`
- `config/sources.yaml` 会以只读方式挂载进容器

### 2.4 手动执行一次生产流水线

首次上线建议手动跑一次，确认抓取、翻译、导出、webhook 都正常：

```bash
docker compose exec app python -m news_digest.cli produce --date 2026-05-29 --target-lang zh
```

执行后应确认：

- `exports/YYYY-MM-DD.json` 已生成
- `exports/health.json` 已生成
- 日志中没有持续失败的源
- 如果配置了 `FRONTEND_BUILD_WEBHOOK_URL`，日志中出现 webhook 成功记录

### 2.5 配置定时任务

当前容器默认命令已是定时调度：

```bash
produce-schedule --config config/sources.yaml
```

如需调整执行时机，可改为显式命令，例如：

```bash
docker compose exec app python -m news_digest.cli produce-schedule --cron "0 6 * * *"
```

如果你希望容器启动后直接使用自定义 cron，建议在 `docker-compose.yml` 中覆盖 `command`。

## 3. 前端部署

### 3.1 Cloudflare Pages 项目配置

建议将 `web/` 目录作为前端根目录：

- Framework preset：`Astro`
- Root directory：`web`
- Build command：`npm run build`
- Build output directory：`dist`
- Node.js version：`20`

### 3.2 前端环境变量

在 Cloudflare Pages 中配置：

- `SITE_URL=https://your-domain.example`
- 可选：`DIGEST_DATE=YYYY-MM-DD`，仅用于临时指定读取某个导出日期
- 通常不需要设置 `DIGEST_JSON_PATH`

### 3.3 配置构建触发 webhook

在 Cloudflare Pages 创建 Deploy Hook，并将其填入后端 `.env` 的：

```env
FRONTEND_BUILD_WEBHOOK_URL=...
```

这样后端 `produce` 流水线在导出成功后会自动触发前端重建。

## 4. 首次上线验收

建议按以下顺序验收：

### 4.1 后端验收

- 查看容器状态：

```bash
docker compose ps
```

- 查看日志：

```bash
docker compose logs app --tail=200
```

- 本机或服务器上验证健康探活：

```bash
python -m news_digest.cli serve-health --host 0.0.0.0 --port 8080
curl http://127.0.0.1:8080/healthz
curl http://127.0.0.1:8080/health.json
```

### 4.2 前端验收

上线后重点检查：

- `/`
- `/archive`
- `/admin/health`
- `/digest.json`
- `/health.json`
- `/feed.xml`

应确认：

- 首页能显示最新日报
- 归档可访问
- 健康页能看到 `health.json` 数据
- RSS 中链接域名为正式 `SITE_URL`

## 5. 回滚建议

### 5.1 后端回滚

```bash
git checkout <previous-good-commit>
docker compose up -d --build
```

如果数据库 schema 已变更，回滚前需要先确认是否兼容旧版本代码。

### 5.2 前端回滚

在 Cloudflare Pages 控制台回滚到上一条稳定部署即可。

## 6. 上线后建议

- 接入 UptimeRobot 监控：
  - 前端：`/health.json`
  - 后端探活：`/healthz`
- 为 webhook 失败增加告警
- 给正式版本打 tag 并记录发布日期
- 在 CI 或独立环境补跑一次 Lighthouse，避免本机浏览器环境导致误报
