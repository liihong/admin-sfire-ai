#!/usr/bin/env bash
# 顶妈产品知识库后台管理 API 联调测试
# 使用前设置：export ADMIN_TOKEN=你的管理后台JWT

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
TOKEN="${ADMIN_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "请先设置 ADMIN_TOKEN 环境变量"
  exit 1
fi

API="${BASE_URL}/api/v1/admin/dingma/product-knowledge"
AUTH_HEADER="Authorization: Bearer ${TOKEN}"

echo "=== 1. 获取品类列表 ==="
curl -s -X GET "${API}/categories" -H "${AUTH_HEADER}" | python -m json.tool

echo ""
echo "=== 2. 分页列表（关键词：泡菜） ==="
curl -s -G "${API}" \
  -H "${AUTH_HEADER}" \
  --data-urlencode "pageNum=1" \
  --data-urlencode "pageSize=5" \
  --data-urlencode "keyword=泡菜" | python -m json.tool

echo ""
echo "=== 3. 创建测试产品（幂等：若 product_code 已存在会返回 400） ==="
curl -s -X POST "${API}" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{
    "category_code": "test",
    "category_name": "测试品类",
    "product_code": "test_admin_api_product",
    "product_name": "后台API测试产品",
    "aliases": ["测试产品", "API测试"],
    "pack_formula": "面块1包 泡菜1包50g",
    "recipe_detail": {
      "ingredients": [{"name": "面块", "amount": "1包"}],
      "steps": ["煮面", "加料"],
      "notes": ["仅供联调"]
    },
    "copywriting_facts": "【后台API测试产品】\n含：面块、泡菜\n不含：肉类\n可写：私房早餐\n不可写：治疗、药用",
    "source_version": "2026-01",
    "status": 1,
    "sort_order": 9999
  }' | python -m json.tool

echo ""
echo "=== 4. 查询详情（请将 ITEM_ID 替换为上一步返回的 id） ==="
ITEM_ID="${ITEM_ID:-}"
if [ -n "$ITEM_ID" ]; then
  curl -s -X GET "${API}/${ITEM_ID}" -H "${AUTH_HEADER}" | python -m json.tool
else
  echo "跳过：设置 ITEM_ID 环境变量后可测试详情/更新/删除"
fi
