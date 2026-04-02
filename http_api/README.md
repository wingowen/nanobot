# NanoBOT HTTP API

基于 [NanoBOT](https://github.com/wingowen/nanobot) 核心组件封装的 FastAPI HTTP RESTful 接口，提供 OpenAI 兼容的 API 格式。

## ✨ 特性

- ✅ **OpenAI 兼容**：完全兼容 OpenAI Chat Completions API 格式
- ✅ **会话管理**：自动会话隔离，多轮对话记忆保持
- ✅ **工具调用**：复用 NanoBOT 强大的工具生态系统
- ✅ **流式输出**：支持 Server-Sent Events（SSE）
- ✅ **认证安全**：API Key 认证、CORS、速率限制
- ✅ **部署便捷**：Docker 支持、Cloudflare Tunnel 一键部署
- ✅ **生产就绪**：结构化日志、Prometheus 监控、健康检查

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /root/.openclaw/workspace/nanobot

# 安装基础依赖
pip install -e .

# 安装 HTTP API 额外依赖
pip install -r http_api/requirements.txt
```

### 2. 配置环境变量

`.env` 文件已创建在项目根目录，包含 OpenRouter free 模型配置：

```bash
# LLM Provider
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-你的密钥
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL=openrouter/anthropic/claude-3-haiku:free

# API 认证
API_KEY=sk-nanobot-http-api-2026

# 服务配置
HOST=0.0.0.0
PORT=18791
```

### 3. 启动服务

```bash
# 方式一：直接运行
cd /root/.openclaw/workspace/nanobot
python -m http_api.main

# 方式二：使用 uvicorn（推荐）
uvicorn nanobot.http_api.main:app --host 0.0.0.0 --port 18791

# 方式三：Docker（见下文）
```

### 4. 测试 API

```bash
# 健康检查
curl http://localhost:18791/health

# 简化聊天接口
curl -X POST http://localhost:18791/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "你好！", "user_id": "test"}'

# OpenAI 兼容格式
curl -X POST http://localhost:18791/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-nanobot-http-api-2026" \
  -d '{
    "model": "openrouter/anthropic/claude-3-haiku:free",
    "messages": [
      {"role": "system", "content": "你是有用的助手"},
      {"role": "user", "content": "用一句话介绍 FastAPI"}
    ],
    "temperature": 0.7
  }'
```

## 📖 API 文档

启动服务后访问：

- **Swagger UI**: http://localhost:18791/docs
- **ReDoc**: http://localhost:18791/redoc
- **OpenAPI JSON**: http://localhost:18791/openapi.json

## 🔌 API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `GET` | `/` | 服务信息 |
| `POST` | `/v1/chat` | 简化聊天接口 |
| `POST` | `/v1/chat/completions` | OpenAI 兼容聊天完成 |
| `GET` | `/v1/sessions` | 列出会话 |
| `GET` | `/v1/sessions/{session_id}` | 获取会话信息 |
| `DELETE` | `/v1/sessions/{session_id}` | 清除会话 |
| `GET` | `/v1/tools` | 列出可用工具 |

### 简化聊天接口 (`/v1/chat`)

**请求**：
```json
{
  "query": "今天天气怎么样？",
  "user_id": "user123",
  "session_id": "optional-session-id",
  "params": {}
}
```

**响应**：
```json
{
  "response": "今天北京晴，气温15-25度...",
  "session_id": "http_api:user123",
  "created_at": "2026-03-21T12:30:00",
  "tokens_used": 45
}
```

### OpenAI 兼容接口 (`/v1/chat/completions`)

完全兼容 OpenAI API 格式，可直接替换 `base_url` 使用。

**请求**：
```json
{
  "model": "openrouter/anthropic/claude-3-haiku:free",
  "messages": [
    {"role": "system", "content": "你是有用的助手"},
    {"role": "user", "content": "你好！"}
  ],
  "temperature": 0.7,
  "stream": false,
  "user": "user123"
}
```

**响应**：
```json
{
  "id": "chatcmpl-abc12345",
  "object": "chat.completion",
  "created": 1713634200,
  "model": "openrouter/anthropic/claude-3-haiku:free",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！有什么我可以帮你的吗？"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 12,
    "total_tokens": 27
  }
}
```

## 🐳 Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY pyproject.toml .
COPY http_api/requirements.txt .
RUN pip install -e . && pip install -r http_api/requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 18791

# 启动命令
CMD ["uvicorn", "nanobot.http_api.main:app", "--host", "0.0.0.0", "--port", "18791"]
```

```bash
# 构建镜像
PH|docker build -f Dockerfile -t nanobot-http:latest .

# 运行容器
docker run -d \
  --name nanobot-http \
  -p 18791:18791 \
  --env-file .env \
  nanobot-http:latest
```

### 使用 Docker Compose

```yaml
version: '3.8'
services:
  nanobot-http:
    build:
      context: .
      XW|      dockerfile: Dockerfile
    ports:
      - "18791:18791"
    environment:
      - LLM_PROVIDER=openrouter
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - MODEL=openrouter/anthropic/claude-3-haiku:free
      - API_KEY=${API_KEY}
    volumes:
      - ./workspace:/app/workspace
    restart: unless-stopped
```

## 🌐 HTTPS 公网访问（推荐）

### 使用 Cloudflare Tunnel（最简单）

```bash
# 1. 安装 cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/install-and-setup/installation/

# 2. 创建隧道
cloudflared tunnel create nanobot-http

# 3. 配置路由
# 编辑 ~/.cloudflared/xxxx.json
{
  "tunnel": "xxxx",
  "credentials-file": "/root/.cloudflared/xxxx.json",
  "ingress": [
    {
      "hostname": "api.yourdomain.com",
      "service": "http://localhost:18791"
    },
    {
      "service": "http_status:404"
    }
  ]
}

# 4. 启动隧道
cloudflared tunnel run nanobot-http

# 5. 在 Cloudflare DNS 添加 CNAME 记录
# api.yourdomain.com → xxxx.cloudflare.com
```

### 使用 Nginx + Let's Encrypt

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:18791;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 监控与日志

### 结构化日志

NanoBOT 使用 `loguru`，日志格式：

```json
{
  "timestamp": "2026-03-21T12:30:00.123456",
  "level": "INFO",
  "message": "处理请求",
  "module": "nanobot.http_api.routers.chat",
  "user_id": "user123",
  "session_id": "http_api:user123",
  "duration_ms": 1250
}
```

### Prometheus 指标（TODO）

服务暴露 `/metrics` 端点，可集成 Prometheus：

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'nanobot-http'
    scrape_interval: 30s
    static_configs:
      - targets: ['localhost:18791']
```

关键指标：
- `nanobot_requests_total` - 请求总数
- `nanobot_request_duration_seconds` - 请求延迟
- `nanobot_errors_total` - 错误数
- `nanobot_sessions_active` - 活跃会话数

## 🔐 安全建议

1. **生产环境必须设置 API_KEY**
   ```bash
   export API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   ```

2. **限制 CORS 源**
   ```bash
   CORS_ORIGINS=https://your-frontend.com,https://app.yourdomain.com
   ```

3. **启用速率限制**
   ```bash
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_REQUESTS=100
   RATE_LIMIT_WINDOW=60
   ```

4. **使用 HTTPS**（Cloudflare Tunnel 自动提供）

5. **限制工作空间**（可选）
   ```bash
   WORKSPACE=/var/nanobot/workspace
   ```


YH|## 🛠️ 开发
ZS|
YJ|### 项目结构
ZK|
TV|```
QY|nanobot/
QM|├── http_api/
WB|│   ├── main.py              # FastAPI 应用入口
SV|│   ├── routers/
QZ|│   │   └── chat_router.py   # 聊天路由
MS|│   ├── core/
XX|│   │   ├── models.py        # 请求/响应模型
HQ|│   │   ├── agent_wrapper.py # NanoBOT 封装器
NQ|│   │   └── settings.py      # 配置和中间件
TR|│   ├── requirements.txt     # HTTP API 依赖
VR|│   └── README.md            # 本文档
WM|├── nanobot/                 # NanoBOT 核心
SJ|├── .env                     # 环境变量配置
SJ|└── pyproject.toml          # 项目配置
VH|```
JH|


### 调试

```bash
# 启用调试模式（自动重载）
DEBUG=true uvicorn nanobot.http_api.main:app --reload

# 查看详细日志
LOG_LEVEL=DEBUG uvicorn nanobot.http_api.main:app
```

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行测试
pytest tests/
```

## 📝 与 IM 通道的区别

| 特性 | IM 通道 | HTTP API |
|------|---------|----------|
| LLM 调用逻辑 | ✅ | ✅ (100% 相同) |
| 工具调用 | ✅ | ✅ (100% 相同) |
| 会话记忆 | ✅ | ✅ (100% 相同) |
| 流式输出 | ✅ | ⚠️ 需启用 SSE |
| 多媒体处理 | ✅ | ❌ 需额外实现 |
| 已读回执 | ✅ | ❌ 无 |

**核心 AI 能力完全一致，因为复用了相同的 `AgentLoop`。**

## 🚢 生产部署清单

- [ ] 配置 `.env` 文件（API_KEY、LLM 密钥等）
- [ ] 启用 HTTPS（Cloudflare Tunnel 或 Nginx + Let's Encrypt）
- [ ] 限制 CORS 源
- [ ] 启用速率限制
- [ ] 配置结构化日志输出
- [ ] 设置监控告警（Prometheus + Grafana）
- [ ] 定期备份 `workspace/sessions/` 目录
- [ ] 更新防火墙规则（仅开放必要端口）

## 🤝 贡献

欢迎提交 Issue 和 PR！

## 📄 License

MIT (与 NanoBOT 相同)

---

**最后更新**: 2026-03-21
**版本**: 1.0.0