#!/bin/bash
# 算力明细 API 测试脚本
# 使用前请先获取 Admin Token，替换下方的 TOKEN 变量

BASE_URL="http://localhost:8000/api/v1/admin"
TOKEN="YOUR_ADMIN_TOKEN_HERE"

echo "=== 1. 获取系统算力统计 ==="
curl -s -X GET "${BASE_URL}/compute-logs/stats" \
  -H "Authorization: Bearer ${TOKEN}" | jq .

echo ""
echo "=== 2. 获取用户算力汇总列表 ==="
curl -s -X GET "${BASE_URL}/compute-logs/users?pageNum=1&pageSize=10" \
  -H "Authorization: Bearer ${TOKEN}" | jq .

echo ""
echo "=== 3. 获取指定用户算力流水明细（替换 USER_ID） ==="
USER_ID=1
curl -s -X GET "${BASE_URL}/compute-logs/users/${USER_ID}/logs?pageNum=1&pageSize=10" \
  -H "Authorization: Bearer ${TOKEN}" | jq .
