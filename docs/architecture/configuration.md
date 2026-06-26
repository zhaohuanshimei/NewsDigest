# 环境变量与配置规范

本文档定义 News Digest V2 的环境变量命名规范、来源优先级、各环境差异和密钥管理原则。

## 变量命名规范

### 通用规则

1. **全大写字母**: 所有环境变量使用大写字母,单词间用下划线分隔
2. **语义清晰**: 变量名应明确表达用途,避免缩写
3. **前缀约定**:
   - `PUBLIC_` 前缀: 前端可访问的变量(Astro 的 `import.meta.env.PUBLIC_*`)
   - 无前缀: 后端服务专用变量,不应暴露给前端

### 已定义的变量

| 变量名 | 用途 | 默认值 | 使用位置 |
|--------|------|--------|----------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql+psycopg://news:news@localhost:5432/news_digest` | 后端服务 |
| `API_PREFIX` | API 路由前缀 | `/api/v1` | `services/api/app/core/config.py` |
| `DEEPL_API_KEY` | DeepL 翻译 API 密钥 | (空) | 后端翻译服务 |
| `GOOGLE_TRANSLATE_API_KEY` | Google Translate API 密钥 | (空) | 后端翻译服务 |
| `NEWS_DIGEST_API_BASE_URL` | 前端调用后端 API 的地址 | `http://127.0.0.1:8001/api/v1` | 前端配置 |
| `SITE_URL` | 站点 URL(用于 sitemap、RSS) | `http://localhost:4321` | 前端、RSS 生成 |
| `PUBLIC_DIGEST_STATE` | Mock 日报状态覆盖 | (未设置) | 前端开发调试 |
| `PUBLIC_ARCHIVE_STATE` | Mock 归档状态覆盖 | (未设置) | 前端开发调试 |
| `PUBLIC_CLUSTER_STATE` | Mock 聚类状态覆盖 | (未设置) | 前端开发调试 |
| `FRONTEND_BUILD_WEBHOOK_URL` | 前端构建完成 webhook | (空) | 后端发布流程 |
| `LOG_LEVEL` | 日志级别 | `INFO` | 后端运行时 |
| `TZ` | 时区 | `Asia/Shanghai` | 全系统 |

### 命名示例

**正确**:
- `DATABASE_URL` - 清晰的资源标识
- `DEEPL_API_KEY` - 明确的服务 + 用途
- `NEWS_DIGEST_API_BASE_URL` - 完整的路径描述

**错误**:
- `DB` - 过于简略
- `KEY` - 用途不明
- `api_url` - 未使用大写

## 来源优先级

当同一配置存在多个来源时,按以下优先级从高到低加载:

1. **命令行参数**: 最高优先级,用于临时覆盖
2. **环境变量**: 运行时注入,容器化部署的标准方式
3. **`.env` 文件**: 本地开发使用,不应提交到版本控制
4. **`.env.example` 文件**: 模板文件,提供默认值和文档
5. **代码中的默认值**: 最低优先级,仅在无外部配置时使用

### 优先级示例

```bash
# 命令行参数 (最高优先级)
python -m news_digest.cli produce --webhook-url https://example.com/webhook

# 环境变量 (次高优先级)
export FRONTEND_BUILD_WEBHOOK_URL=https://example.com/webhook
python -m news_digest.cli produce

# .env 文件 (本地开发)
FRONTEND_BUILD_WEBHOOK_URL=https://example.com/webhook

# 代码默认值 (最低优先级)
webhook_url = os.getenv("FRONTEND_BUILD_WEBHOOK_URL", "")
```

## 各环境差异

### 开发环境 (Development)

**目标**: 本地开发调试,快速迭代

**配置特点**:
- 数据库: 本地 PostgreSQL,使用默认凭证
  ```
  DATABASE_URL=postgresql+psycopg://news:news@localhost:5432/news_digest
  ```
- API: 本地服务,HTTP 协议
  ```
  NEWS_DIGEST_API_BASE_URL=http://127.0.0.1:8001/api/v1
  ```
- 前端: 本地开发服务器
  ```
  SITE_URL=http://localhost:4321
  ```
- Mock 状态: 可设置 `PUBLIC_*_STATE` 变量进行前端调试
  ```
  PUBLIC_DIGEST_STATE=success
  PUBLIC_ARCHIVE_STATE=empty
  ```
- 日志: DEBUG 级别,输出详细信息
  ```
  LOG_LEVEL=DEBUG
  ```
- 翻译: 可使用测试密钥或留空(降级到原文)

**启动命令**:
```bash
# 后端
python -m news_digest.cli produce-schedule --config config/sources.yaml

# 前端
npm --prefix apps/web run dev
```

### 测试环境 (Testing)

**目标**: 自动化测试,集成验证

**配置特点**:
- 数据库: 独立的测试数据库实例,避免污染开发数据
  ```
  DATABASE_URL=postgresql+psycopg://test:test@localhost:5433/news_digest_test
  ```
- API: 测试服务地址
  ```
  NEWS_DIGEST_API_BASE_URL=http://test-api:8001/api/v1
  ```
- 前端: 测试环境地址
  ```
  SITE_URL=http://test-web:4321
  ```
- Mock 状态: **不应设置**,确保测试真实数据流
- 日志: INFO 或 WARNING,减少噪音
  ```
  LOG_LEVEL=INFO
  ```
- 翻译: 使用测试密钥或 mock

**CI 环境变量注入**:
```yaml
# GitHub Actions 示例
env:
  DATABASE_URL: postgresql+psycopg://test:test@localhost:5433/news_digest_test
  LOG_LEVEL: INFO
```

### 预发环境 (Staging)

**目标**: 上线前最终验证,模拟生产环境

**配置特点**:
- 数据库: 与生产隔离的独立实例,数据可脱敏
  ```
  DATABASE_URL=postgresql+psycopg://staging_user:***@staging-db:5432/news_digest_staging
  ```
- API: 预发服务地址,HTTPS 协议
  ```
  NEWS_DIGEST_API_BASE_URL=https://staging-api.your-domain.com/api/v1
  ```
- 前端: 预发地址
  ```
  SITE_URL=https://staging.your-domain.com
  ```
- Mock 状态: **不应设置**
- 日志: INFO 级别
  ```
  LOG_LEVEL=INFO
  ```
- 翻译: 使用预发环境的翻译 API 密钥
  ```
  DEEPL_API_KEY=staging_deepl_key
  ```
- Webhook: 预发部署触发 URL
  ```
  FRONTEND_BUILD_WEBHOOK_URL=https://staging-deploy.your-domain.com/webhook
  ```

**部署方式**: 通过容器编排或 PaaS 平台注入环境变量,不使用 `.env` 文件。

### 生产环境 (Production)

**目标**: 稳定运行,服务最终用户

**配置特点**:
- 数据库: 强密码,生产级连接参数
  ```
  DATABASE_URL=postgresql+psycopg://prod_user:***@prod-db:5432/news_digest
  ```
- API: 生产域名,HTTPS,负载均衡
  ```
  NEWS_DIGEST_API_BASE_URL=https://api.your-domain.com/api/v1
  ```
- 前端: 生产域名,HTTPS,CDN 加速
  ```
  SITE_URL=https://your-domain.com
  ```
- Mock 状态: **绝不应设置**
- 日志: INFO 或 WARNING,避免过多输出
  ```
  LOG_LEVEL=INFO
  ```
- 翻译: 生产环境的翻译 API 密钥
  ```
  DEEPL_API_KEY=prod_deepl_key
  ```
- Webhook: 生产部署触发 URL
  ```
  FRONTEND_BUILD_WEBHOOK_URL=https://deploy.your-domain.com/webhook
  ```

**安全要求**:
- 所有敏感信息通过密钥管理服务注入
- 启用 HTTPS/TLS
- 配置防火墙和网络隔离
- 定期备份数据库
- 监控和告警

## 密钥管理原则

### 1. 绝不在代码中硬编码密钥

**错误**:
```python
# 绝对不要这样做
API_KEY = "sk-1234567890abcdef"
DATABASE_URL = "postgresql://user:password123@host:5432/db"
```

**正确**:
```python
# 从环境变量读取
API_KEY = os.getenv("API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL")
```

### 2. 使用占位符而非真实值

在 `.env.example` 和文档中使用占位符:

```bash
# .env.example
DEEPL_API_KEY=your_deepl_api_key_here
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### 3. `.env` 文件不提交到版本控制

确保 `.gitignore` 包含:
```
.env
.env.local
.env.*.local
```

### 4. 生产环境使用密钥管理服务

推荐方案:
- **AWS**: Secrets Manager, Parameter Store
- **GCP**: Secret Manager
- **Azure**: Key Vault
- **自托管**: HashiCorp Vault, SOPS

示例 (AWS Secrets Manager):
```bash
# 从 AWS Secrets Manager 获取密钥
export DEEPL_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id prod/deepl-api-key \
  --query SecretString \
  --output text)
```

### 5. 定期轮换密钥

- 翻译 API 密钥: 每 90 天轮换
- 数据库密码: 每 180 天轮换
- 其他 API 密钥: 按服务提供商建议轮换

轮换流程:
1. 在密钥管理服务中生成新密钥
2. 更新环境变量配置
3. 重启服务以加载新密钥
4. 验证服务正常运行
5. 删除旧密钥

### 6. 不同环境使用不同凭证

**绝对不要**:
- 开发环境密钥用于生产
- 生产密钥提交到测试环境
- 多个环境共享同一密钥

**应该**:
- 为每个环境创建独立的凭证
- 使用命名约定区分环境(如 `dev_deepl_key`, `prod_deepl_key`)
- 在密钥管理服务中使用环境前缀

### 7. 最小权限原则

- 数据库账户只授予必要的权限
- API 密钥只开启必要的功能
- 生产数据库账户不应有 DROP/DELETE 权限(除非必要)

示例 (PostgreSQL):
```sql
-- 生产环境只读账户
CREATE ROLE prod_readonly WITH LOGIN PASSWORD '***';
GRANT CONNECT ON DATABASE news_digest TO prod_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO prod_readonly;
```

## 配置变更流程

### 1. 添加新变量

1. 在 `.env.example` 中添加变量,包含注释说明
2. 在本文档的"已定义的变量"表格中更新
3. 更新相关代码以读取新变量
4. 在 PR 描述中说明新增变量的用途和默认值

### 2. 修改变量默认值

1. 更新 `.env.example` 中的默认值
2. 更新本文档中的对应条目
3. 更新代码中的默认值(如果有)
4. 通知所有团队成员更新本地 `.env` 文件

### 3. 废弃变量

1. 在本文档中标记为 "已废弃"
2. 在代码中保留向后兼容,但输出警告日志
3. 在下一个大版本中完全移除
4. 更新 `.env.example`,移除该变量

## 故障排查

### 常见错误

**错误 1: 数据库连接失败**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

排查步骤:
1. 检查 `DATABASE_URL` 是否正确
2. 确认 PostgreSQL 服务正在运行: `pg_isready -U news`
3. 验证数据库凭证是否正确
4. 检查防火墙规则

**错误 2: 翻译服务不可用**
```
ValueError: DEEPL_API_KEY required for DeepLProvider
```

排查步骤:
1. 检查是否设置了 `DEEPL_API_KEY` 或 `GOOGLE_TRANSLATE_API_KEY`
2. 验证 API 密钥是否有效
3. 检查 API 配额是否用尽
4. 查看翻译服务状态页面

**错误 3: 前端无法连接 API**
```
FetchError: request to http://127.0.0.1:8001/api/v1/digests/latest failed
```

排查步骤:
1. 检查 `NEWS_DIGEST_API_BASE_URL` 是否正确
2. 确认 API 服务正在运行
3. 验证 CORS 配置(开发环境)
4. 检查网络连通性

**错误 4: Mock 状态在生产环境生效**

排查步骤:
1. 检查生产环境是否意外设置了 `PUBLIC_*_STATE` 变量
2. 从环境变量中移除这些变量
3. 重启前端服务

## 相关文档

- [架构总览](./overview.md)
- [API 边界](./api-boundary.md)
- [非功能目标](./non-functional-targets.md)
- [领域模型](./domain-model.md)

## 更新日志

- 2026-06-26: 初始版本,定义环境变量规范和密钥管理原则
