#!/bin/bash
echo "=== NanoBOT HTTP API 测试 ==="
echo "服务地址: http://localhost:18792"
echo ""

echo "1. 健康检查"
curl -s http://localhost:18792/health | python3 -m json.tool
echo ""

echo "2. 获取工具列表"
curl -s -H "X-API-Key: sk-nanobot-http-api-2026" http://localhost:18792/v1/tools | python3 -m json.tool
echo ""

echo "3. 简单聊天（不加密）"
curl -s -X POST "http://localhost:18792/v1/chat/completions" \
  -H "X-API-Key: sk-nanobot-http-api-2026" \
  -H "Content-Type: application/json" \
  -d '{"message":"今天A股大盘怎么样？"}' | python3 -m json.tool 2>/dev/null
echo ""

echo "4. 获取会话历史"
curl -s -H "X-API-Key: sk-nanobot-http-api-2026" "http://localhost:18792/v1/sessions/api_user/history" | python3 -m json.tool 2>/dev/null
echo ""

echo "=== 测试完成 ==="
