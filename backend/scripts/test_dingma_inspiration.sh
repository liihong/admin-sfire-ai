#!/usr/bin/env bash
# 顶妈 dingma 灵感生成联调测试
# 使用前请替换 TOKEN、INSPIRATION_ID、BASE_URL

BASE_URL="${BASE_URL:-http://localhost:8000}"
TOKEN="${TOKEN:-your_jwt_token}"
INSPIRATION_ID="${INSPIRATION_ID:-1}"

echo "=== 测试: 灵感口播生成（含产品名）==="
curl -s -X POST "${BASE_URL}/api/v1/client/dingma/inspirations/${INSPIRATION_ID}/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Tenant-Code: dingma" \
  -H "X-My-Gate-Key: Huoyuan2026" \
  -d '{
    "inspiration_id": '"${INSPIRATION_ID}"',
    "temperature": 0.7,
    "max_tokens": 1024
  }' | head -c 3000

echo ""
