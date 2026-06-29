#!/usr/bin/env bash
# =============================================================================
# News Digest V2 — 服务器部署脚本
# =============================================================================
# 处理 SSG 构建顺序：API 必须先运行，前端才能在构建时拉取数据。
#
# 使用方式 (在服务器上):
#   ./scripts/deploy-server.sh           # 完整部署
#   ./scripts/deploy-server.sh --api-only # 只更新 API
#   ./scripts/deploy-server.sh --web-only # 只更新前端
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/infra/docker-compose.server.yml"
cd "$PROJECT_DIR"

API_ONLY=false
WEB_ONLY=false

for arg in "$@"; do
    case $arg in
        --api-only) API_ONLY=true ;;
        --web-only) WEB_ONLY=true ;;
    esac
done

echo "=== News Digest V2 部署 ==="
echo "项目目录: $PROJECT_DIR"
echo ""

# Step 1: 拉取最新代码
echo ">>> 拉取最新代码..."
git pull --ff-only

# Step 2: 部署 API
if [ "$WEB_ONLY" = false ]; then
    echo ""
    echo ">>> 构建 + 启动 API..."
    docker compose -f "$COMPOSE_FILE" up -d --build api

    echo ">>> 等待 API 健康..."
    for i in $(seq 1 30); do
        if docker exec news-digest-v2-api curl -s http://127.0.0.1:8001/api/v1/health > /dev/null 2>&1; then
            echo "API 健康!"
            break
        fi
        if [ "$i" -eq 30 ]; then
            echo "ERROR: API 健康检查超时"
            docker logs news-digest-v2-api --tail 20
            exit 1
        fi
        sleep 2
    done

    echo ">>> 运行数据库迁移..."
    docker exec news-digest-v2-api alembic upgrade head
fi

# Step 3: 部署前端 (SSG 构建时从 API 拉数据)
if [ "$API_ONLY" = false ]; then
    echo ""
    echo ">>> 构建 + 启动前端 (SSG 从 API 拉数据)..."
    docker compose -f "$COMPOSE_FILE" up -d --build web
fi

# Step 4: 状态检查
echo ""
echo ">>> 容器状态:"
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "=== 部署完成 ==="
echo "API:   http://127.0.0.1:8001/api/v1/health"
echo "前端:  https://news-v2.maczhao.com (Caddy 反代)"
echo ""
echo "查看日志: docker compose -f $COMPOSE_FILE logs -f"
