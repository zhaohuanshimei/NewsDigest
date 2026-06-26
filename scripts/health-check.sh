#!/usr/bin/env bash
# =============================================================================
# News Digest - Health Check & Monitoring Script
# =============================================================================
# 用于 UptimeRobot 等外部监控服务，或作为 cron job 周期性检查。
#
# 使用方式:
#   ./scripts/health-check.sh                    # 检查本地 API
#   ./scripts/health-check.sh https://api.newsdigest.app  # 检查远程 API
# =============================================================================

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8001}"
HEALTH_URL="${BASE_URL}/api/v1/health"

check_health() {
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$HEALTH_URL" 2>/dev/null)

    if [ "$response" = "200" ]; then
        echo "OK - Health endpoint returned $response"
        return 0
    else
        echo "CRITICAL - Health endpoint returned $response"
        return 2
    fi
}

check_health_body() {
    local body
    body=$(curl -s --max-time 10 "$HEALTH_URL" 2>/dev/null)

    if echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status'] in ('ok','degraded','error'); assert d['database'] in ('ok','error')" 2>/dev/null; then
        local status
        status=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
        echo "Status: $status"

        if [ "$status" = "error" ]; then
            echo "CRITICAL - Service status is 'error'"
            return 2
        fi
        return 0
    else
        echo "CRITICAL - Invalid health response format"
        return 2
    fi
}

echo "Checking health at: $HEALTH_URL"
check_health || exit $?
check_health_body || exit $?
echo "Health check passed."
