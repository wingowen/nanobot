# NanoBOT HTTP API

基于 FastAPI 的 NanoBOT HTTP 接口封装，提供 OpenAI 兼容的 REST API 和流式输出。

## 🚀 快速开始

### 前置条件

- Python 3.11+
- NanoBOT 项目（已安装在工作空间）
- OpenRouter API Key（已配置在 `.env`）

### 安装依赖

```bash
cd /root/.openclaw/workspace/nanobot
pip install -e .
pip install fastapi uvicorn slowapi pydantic-settings structlog
```

### 配置环境

```bash
# 复制并修改 .env 文件
cp http_api/.env.example http_api/.env
# 编辑 http_api/.env，确保配置正确
```

### 启动服务

```bash
# 本地运行
cd /root/.openclaw/workspace/nanobot
uvicorn http_api.main:app --host 0.0.0.0 --port 18791

# 或使用 python 直接运行
python -m http_api.main
```

### 测试接口

```bash
# 健康检查
curl http://localhost:18791/health

# 查看 API 文档
# 浏览器访问: http://localhost:18791/docs
```

## 📡 API 端点

### 1. 聊天完成（OpenAI 兼容）

**POST** `/v1/chat/completions`

**请求示例**：
```bash
curl -X POST http://localhost:18791/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-nanobot-http-api-2026" \
  -d '{
    "model": "openrouter/anthropic/claude-3-haiku:free",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
    "stream": false,
    "temperature": 0.7
  }'
```

**响应示例**：
```json
{
  "id": "chatcmpl-abc12345",
  "object": "chat.completion",
  "created": 1716283200,
  "model": "openrouter/anthropic/claude-3-haiku:free",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！我是 NanoBOT..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

### 2. 流式输出

**POST** `/v1/chat/completions/stream`

请求体相同，设置 `"stream": true`

响应为 Server-Sent Events 格式：
```
data: {"id":"...","choices":[{"delta":{"content":"Hello"}]}}
data: {"id":"...","choices":[{"delta":{"content":" World"}]}}
data: [DONE]
```

### 3. 简化聊天接口

**POST** `/v1/chat/simple`

更简洁的请求格式：
```json
{
  "query": "用户问题",
  "user_id": "optional_user_id"
}
```

响应：
```json
{
  "response": "AI回复内容",
  "session_id": "user123:default",
  "created_at": "2026-03-21T12:00:00",
  "tokens_used": 123
}
```

### 4. 会话管理

- **GET** `/v1/sessions` - 列出所有会话
- **GET** `/v1/sessions/{session_id}` - 获取会话详情
- **DELETE** `/v1/sessions/{session_id}` - 删除会话
- **POST** `/v1/sessions/{session_id}/clear` - 清空会话消息

### 5. 工具列表

- **GET** `/v1/tools` - 列出所有可用工具
- **GET** `/v1/tools/{tool_name}` - 获取工具详情
- **GET** `/v1/tools/categories` - 列出工具类别

## 🔐 认证

所有 API 端点（除了 `/health` 和 `/`）都需要 API Key 认证。

在请求头中添加：
```
X-API-Key: sk-nanobot-http-api-2026
```

配置项：
- `.env` 文件中的 `API_KEY` 设置此值
- 生产环境请使用强随机密钥

## ⚙️ 配置

环境变量配置（`.env` 文件）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_PROVIDER` | `openrouter` | LLM 提供商 |
| `OPENROUTER_API_KEY` | (必填) | OpenRouter API Key |
| `MODEL` | `openrouter/anthropic/claude-3-haiku:free` | 默认模型 |
| `SESSION_TYPE` | `memory` | 会话存储类型 (memory/sqlite/redis) |
| `SESSION_TTL` | `86400` | Session TTL (秒) |
| `API_KEY` | (必填) | HTTP API 认证密钥 |
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `18791` | 监听端口 |
| `CORS_ORIGINS` | `*` | CORS 允许的源 |
| `RATE_LIMIT_ENABLED` | `true` | 是否启用速率限制 |
| `RATE_LIMIT_REQUESTS` | `100` | 每分钟请求数 |
| `WORKSPACE` | `/root/.openclaw/workspace/nanobot_workspace` | 工作空间路径 |

## 📁 项目结构

```
nanobot/
├── http_api/
│   ├── main.py              # FastAPI 主应用
│   ├── core/
│   │   ├── config.py       # 配置管理
│   │   ├── models.py       # 请求/响应模型
│   │   └── session_adapter.py  # 会话适配器
│   ├── routers/
│   │   ├── chat_router.py  # 聊天路由
│   │   ├── sessions_router.py  # 会话管理路由
│   │   └── tools_router.py # 工具路由
│   ├── .env.example        # 环境变量示例
│   └── Dockerfile.http     # Docker 配置（可选）
├── nanobot/                # NanoBOT 核心（原始项目）
├── .env                    # 环境变量（需自行创建）
└── README_http_api.md      # 本文档
```

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -f Dockerfile.http -t nanobot-http-api .

# 运行
docker run -d \
  --name nanobot-http \
  -p 18791:18791 \
  --env-file .env \
  nanobot-http-api
```

## 🧪 Python 客户端示例

```python
import requests

BASE_URL = "http://localhost:18791"
API_KEY = "sk-nanobot-http-api-2026"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 简单聊天
response = requests.post(
    f"{BASE_URL}/v1/chat/simple",
    json={"query": "今天天气怎么样？"},
    headers=headers
)

print(response.json()["response"])
```

## 🔧 开发调试

### 查看日志

```bash
# 本地运行时会直接输出到控制台
# Docker 运行：
docker logs -f nanobot-http
```

### 重载模式（开发）

```bash
uvicorn http_api.main:app --reload --host 0.0.0.0 --port 18791
```

### 调试会话

```python
# 在 Python 交互环境中
from nanobot.http_api.core.session_adapter import SessionAdapter
from nanobot.session.manager import SessionManager

session_mgr = SessionManager()
adapter = SessionAdapter(session_mgr)

# 创建会话
session = adapter.get_or_create("test_user")
print(f"Session ID: {session.key}")
```

## ⚠️ 注意事项

1. **Session 持久化**：当前默认使用内存存储，重启后会话丢失。如需持久化，配置 `SESSION_TYPE=sqlite` 或 `redis`。
2. **流式实现**：当前 `/chat/completions/stream` 仍使用非流式模拟，实际应扩展 `AgentLoop` 的流式能力。
3. **工具调用**：工具调用能力已在 `AgentLoop` 中实现，但 HTTP 接口需要额外处理工具调用的结构化输出。
4. **生产部署**：务必设置更强的 `API_KEY`，启用 HTTPS（通过 Cloudflare Tunnel 或反向代理），配置防火墙规则。

## 🔄 与 NanoBOT 的集成

本封装直接复用 NanoBOT 的核心组件：
- `AgentLoop.process_direct()` - 核心消息处理
- `SessionManager` - 会话管理
- `MessageBus` - 事件总线
- `LLMProvider` - 模型提供商

因此，**功能上与 IM 通道（Telegram/Discord）完全一致**，只是通信协议不同。

## 📝 许可证

MIT License (同 NanoBOT 项目)

---

**开发者**: Wingo  
**日期**: 2026-03-21  
**版本**: 0.1.0