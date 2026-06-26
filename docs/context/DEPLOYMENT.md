# 部署与上线说明

本文档用于新闻摘要 V2 生产上线。当前部署形态为：

- **后端**：VPS + Docker Compose（FastAPI + PostgreSQL）
- **前端**：Astro 静态站点（SSG），可部署到 Cloudflare Pages / Vercel / 对象存储
- **CI/CD**：GitHub Actions 自动运行测试

## 环境与配置

### 配置管理

所有环境变量在 `.env.example` 集中定义，包含各环境的差异说明。
各环境使用独立的 `.env.{environment}` 文件：

| 环境 | 配置文件 | 数据库 | 说明 |
|------|---------|--------|------|
| 开发 | `.env` | 本地 localhost:5432 | 手动 `docker compose` 或本地运行 |
| 预发 | `.env.staging` | staging 实例 | `docker compose -f infra/docker-compose.staging.yml` |
| 生产 | `.env.production` | 生产实例 | `docker compose -f infra/docker-compose.production.yml` |

生产 `.env.production` 敏感信息通过 Docker Secrets 注入，不要直接写入文件提交到代码库。
`.env.*` 文件已通过 `.gitignore` 排除。

## 后端部署

### 准备工作

```bash
# 1. 在 VPS 上安装 Docker + Docker Compose
# 2. 克隆代码
git clone <your-repo-url> /srv/news-digest
cd /srv/news-digest

# 3. 创建生产配置
cp .env.example .env.production
# 编辑 .env.production 填入实际生产值

# 4. 创建数据库密码 secret
mkdir -p .secrets
echo -n 'your-strong-password' > .secrets/db_password.txt

# 5. 启动服务
docker compose -f infra/docker-compose.production.yml up -d --build

# 6. 运行数据库迁移
docker compose -f infra/docker-compose.production.yml exec api alembic upgrade head

# 7. 验证健康检查
curl http://127.0.0.1:8001/api/v1/health
```

### 一键部署

```bash
./scripts/deploy.sh staging     # 部署预发
./scripts/deploy.sh production   # 部署生产
```

### 健康检查

API 提供 `/api/v1/health` 端点定期监控：

```bash
# 手动检查
./scripts/health-check.sh

# 监控远程 API
./scripts/health-check.sh https://api.newsdigest.app

# 集成到 UptimeRobot / Better Uptime 等外部监控
# 监控 URL: https://api.newsdigest.app/api/v1/health
```

健康检查返回格式：

```json
{
  "status": "ok",
  "service": "news-digest-api",
  "version": "0.1.0",
  "database": "ok",
  "last_digest": {
    "date": "2026-06-26",
    "status": "published",
    "published_at": "2026-06-26T09:00:00+00:00"
  }
}
```

- `status: "error"` → 数据库连接失败
- `database: "error"` → 数据库不可用
- `last_digest: null` → 尚无 digest（非错误，仅新部署时）

### 日志

日志使用 structlog 结构化输出：

```bash
# 查看 API 日志
docker compose -f infra/docker-compose.production.yml logs -f -t api

# 查看最近日志
docker compose logs --tail=100 api

# 日志驱动: json-file (max-size: 10m, max-file: 3)
# 生产环境可切换到 external 日志聚合 (如 Loki, DataDog, etc.)
```

关键日志事件：
- `pipeline_started` — 生产流水线开始
- `pipeline_step_*_success` / `pipeline_step_*_failed` — 各步骤状态
- `translation_provider_error` — 翻译服务异常

### 告警建议

1. **健康检查失败**：使用 UptimeRobot/Better Uptime 监控 `/api/v1/health`
2. **Pipeline 失败**：每日 cron 执行后检查日志是否有 `pipeline_step_*_failed`
3. **数据库连接失败**：`database: "error"` 触发告警
4. **无新鲜 digest**：如果 `last_digest.date` 超过 48 小时未更新，发出告警
5. **磁盘空间**：日志文件 max-size 10m、max-file 3 防止日志撑满磁盘

### 回滚

```bash
# 后端回滚
git checkout <previous-good-commit>
docker compose -f infra/docker-compose.production.yml up -d --build

# 如果数据库 schema 已变更，确认旧版本代码兼容新 schema
```

## 前端部署

前端为 Astro 静态站点（SSG），构建产物在 `apps/web/dist/`。

### 构建

```bash
cd apps/web
PUBLIC_DIGEST_STATE=success PUBLIC_ARCHIVE_STATE=success PUBLIC_CLUSTER_STATE=success npm run build
```

构建产物可直接部署到：
- Cloudflare Pages（推荐）
- Vercel
- S3/对象存储 + CDN

### 环境变量

| 变量 | 说明 |
|------|------|
| `NEWS_DIGEST_API_BASE_URL` | 后端 API 地址（生产 HTTPS） |
| `SITE_URL` | 站点域名（用于 sitemap/RSS） |
| `PUBLIC_*_STATE` | 绝不在生产环境设置 |

## 颁发验证

### 后端验收

```bash
# 检查服务状态
docker compose ps

# 健康检查
curl http://127.0.0.1:8001/api/v1/health

# 查看日志
docker compose logs --tail=50 api
```

### 前端验收

- `/` — 首页能否显示最新 digest
- `/archive` — 归档日期列表是否正常
- `/clusters/{id}` — 详情页路由正常
- `/rss` — RSS 订阅信息页
- `/feed.xml` — RSS XML 输出是否包含正确域名
