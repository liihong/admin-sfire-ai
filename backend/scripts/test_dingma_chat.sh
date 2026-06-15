#!/usr/bin/env bash
# 顶妈 dingma /dingma/chat 联调测试
# 使用前请替换 TOKEN、AGENT_ID、BASE_URL

BASE_URL="${BASE_URL:-http://localhost:8000}"
TOKEN="${TOKEN:-your_jwt_token}"
AGENT_ID="${AGENT_ID:-1}"

echo "=== 测试1: 含产品名（泡菜朝鲜面）==="
curl -s -N -X POST "${BASE_URL}/api/v1/client/dingma/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Tenant-Code: dingma" \
  -H "X-Wechat-App-Id: ${DINGMA_APPID:-}" \
  -d "{
    \"agent_type\": \"${AGENT_ID}\",
    \"stream\": true,
    \"messages\": [
      {\"role\": \"user\", \"content\": \"帮我写一段泡菜朝鲜面的朋友圈文案，突出私房早餐和真材实料\"}
    ]
  }" | head -c 2000

echo ""
echo ""
echo "=== 测试2: 不含产品名（应引导补充）==="
curl -s -N -X POST "${BASE_URL}/api/v1/client/dingma/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Tenant-Code: dingma" \
  -d "{
    \"agent_type\": \"${AGENT_ID}\",
    \"stream\": true,
    \"messages\": [
      {\"role\": \"user\", \"content\": \"帮我写一段早餐推广文案\"}
    ]
  }" | head -c 2000

echo ""
