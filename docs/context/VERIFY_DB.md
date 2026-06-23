# 验证 T0.2 + T0.3

## 前置条件

启动 Docker Desktop。

## 运行验证

```bash
./scripts/verify_db.sh
```

该脚本会：
1. 启动 PostgreSQL 容器
2. 等待数据库就绪
3. 运行 Alembic migration
4. 验证表已创建

## 手动验证

```bash
# 启动数据库
docker compose up -d

# 等待就绪
docker compose exec db pg_isready -U news

# 运行 migration
.venv/bin/alembic upgrade head

# 查看表
docker compose exec db psql -U news -d news_digest -c "\dt"

# 停止
docker compose down
```

## 预期输出

应看到以下表：
- sources
- articles
- translations
- clusters
- cluster_members
- daily_digests
- alembic_version
