#!/bin/bash
# NanoBOT HTTP API 启动脚本

set -e

cd "$(dirname "$0")"

# 检查 .env 文件
if [ ! -f "http_api/.env" ]; then
    echo "⚠️  未找到 http_api/.env 文件"
    echo "正在从示例文件创建..."
    cp http_api/.env.example http_api/.env
    echo "⚠️  请编辑 http_api/.env 并配置必要的 API 密钥"
    exit 1
fi

# 检查依赖
echo "🔍 检查 Python 依赖..."
python3 -c "import fastapi" 2>/dev/null || {
    echo "📦 安装依赖..."
    pip install fastapi uvicorn slowapi pydantic-settings structlog
}

# 启动服务
echo "🚀 启动 NanoBOT HTTP API..."
echo "📍 地址: http://localhost:18791"
echo "📚 文档: http://localhost:18791/docs"
echo "💚 健康检查: http://localhost:18791/health"
echo ""

cd /root/.openclaw/workspace/nanobot
exec uvicorn http_api.main:app --host 0.0.0.0 --port 18791