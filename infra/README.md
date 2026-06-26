# News Digest V2 - Infrastructure

## 环境概览

本项目使用三环境策略：开发、预发、生产。配置差异通过 `.env` 文件和环境变量追踪。

| 环境 | 数据库 | 前端地址 | API 地址 |
|------|--------|---------|---------|
| 开发 (Dev) | 本地 PostgreSQL | `http://localhost:4321` | `http://127.0.0.1:8001` |
| 预发 (Staging) | staging 实例 | `https://staging.newsdigest.app` | `https://api-staging.newsdigest.app` |
| 生产 (Production) | 生产实例 | `https://newsdigest.app` | `https://api.newsdigest.app` |

## 预发环境

### 后端 (API + Database)

```bash
# 启动预发环境
docker compose -f infra/docker-compose.staging.yml up -d

# 查看日志
docker compose -f infra/docker-compose.staging.yml logs -f api

# 运行数据库迁移
docker exec news-digest-staging-api alembic upgrade head

# 停止
docker compose -f infra/docker-compose.staging.yml down
```

后端 API 在 `http://localhost:8001` 可用。

### 前端

```bash
cd apps/web
npm run dev
# 或构建后预览:
npm run build && npm run preview
```

前端开发时设置 `NEWS_DIGEST_API_BASE_URL=http://localhost:8001/api/v1` 指向本地 API。

## 配置差异追踪

所有环境变量模板在 `.env.example` 集中维护，包含各环境差异说明。
各环境的差异：

| 变量 | Dev | Staging | Production |
|------|-----|---------|-----------|
| DATABASE_URL | 本地 localhost:5432 | Staging 实例 | 生产实例 |
| NEWS_DIGEST_API_BASE_URL | localhost:8001 | api-staging.* | api.* |
| SITE_URL | localhost:4321 | staging.* | 正式域名 |
| LOG_LEVEL | DEBUG | INFO | INFO/WARNING |
| PUBLIC_\*_STATE | 可设置 | 不设置 | 绝不设置 |

## CI/CD

- **CI**: `.github/workflows/ci.yml` - 每次 push/PR 自动运行测试
- **预览部署**: PR 时的预览部署通过部署平台（如 Vercel/Netlify）的 Preview Deployments 实现
- **预发部署**: 由 CI 流水线触发，将 main 分支部署到预发环境

## Dockerfile

- `Dockerfile.api` - FastAPI 后端容器化
- 前端为静态站点（Astro SSG），无需容器化，可直接部署到对象存储/CDN
