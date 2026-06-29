#!/usr/bin/env bash
# =============================================================================
# News Digest - Deploy Script
# =============================================================================
# 一键部署后端 API 到生产/预发环境。
#
# 使用方式:
#   ./scripts/deploy.sh staging    # 部署到预发
#   ./scripts/deploy.sh production # 部署到生产
# =============================================================================

set -euo pipefail

ENV="${1:-staging}"
COMPOSE_FILE="infra/docker-compose.${ENV}.yml"
ENV_FILE=".env.${ENV}"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "ERROR: Compose file not found: $COMPOSE_FILE"
    echo "Usage: $0 [staging|production]"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "WARNING: $ENV_FILE not found. Using default values."
fi

echo "=== Deploying to $ENV environment ==="

# Step 1: Pull latest code (if in a git repo)
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo ">>> Pulling latest code..."
    git pull --ff-only
fi

# Step 2: Build and start services
echo ">>> Building and starting services..."
docker compose -f "$COMPOSE_FILE" up -d --build

# Step 3: Wait for health check
echo ">>> Waiting for API health check..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:8001/api/v1/health > /dev/null 2>&1; then
        echo "API is healthy!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: API health check timed out."
        docker compose -f "$COMPOSE_FILE" logs --tail=20 api
        exit 1
    fi
    sleep 2
done

# Step 4: Run database migrations
echo ">>> Running database migrations..."
docker compose -f "$COMPOSE_FILE" exec -T api alembic upgrade head

echo "=== Deployment to $ENV complete ==="
echo "API: http://127.0.0.1:8001"
echo "Docs: http://127.0.0.1:8001/docs"
echo "Health: http://127.0.0.1:8001/api/v1/health"
echo ""
echo "Run 'docker compose -f $COMPOSE_FILE logs -f -t' to tail logs."
