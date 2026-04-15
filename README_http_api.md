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
  "user_id": "optional_user_id",
  "session_id": "optional_session_id"
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

#### 4.1 获取会话列表

**GET** `/v1/sessions`

请求头：
```
X-API-Key: your-api-key
```

响应示例：
```json
[
  {
    "session_id": "wingo:wingo",
    "user_id": "wingo",
    "message_count": 2,
    "created_at": "2026-03-22T07:19:56.029105",
    "updated_at": "2026-03-22T07:36:06.064950"
  },
  {
    "session_id": "openai:abc123",
    "user_id": "openai",
    "message_count": 4,
    "created_at": "2026-03-21T15:45:08.471382",
    "updated_at": "2026-03-21T15:45:22.303577"
  }
]
```

#### 4.2 获取会话详情

**GET** `/v1/sessions/{session_id}`

URL编码：`session_id` 需要URL编码，如 `wingo:wingo` 编码为 `wingo%3Awingo`

请求头：
```
X-API-Key: your-api-key
```

响应示例：
```json
{
  "session_id": "wingo:wingo",
  "user_id": "wingo",
  "message_count": 2,
  "created_at": "2026-03-22T07:19:56.029105",
  "updated_at": "2026-03-22T07:36:06.064950",
  "messages": [
    {
      "role": "user",
      "content": "1+1等于多少",
      "timestamp": "2026-03-22T07:20:01.111166"
    },
    {
      "role": "assistant",
      "content": "1+1等于2。",
      "reasoning_content": "...",
      "timestamp": "2026-03-22T07:20:01.111172"
    }
  ]
}
```

#### 4.3 删除会话

**DELETE** `/v1/sessions/{session_id}`

响应：
```json
{
  "session_id": "wingo:wingo",
  "deleted": true
}
```

#### 4.4 清空会话消息

**POST** `/v1/sessions/{session_id}/clear`

响应：
```json
{
  "session_id": "wingo:wingo",
  "cleared": true
}
```

### 5. 工具列表

- **GET** `/v1/tools` - 列出所有可用工具
- **GET** `/v1/tools/{tool_name}` - 获取工具详情
- **GET** `/v1/tools/categories` - 列出工具类别

## 🔐 认证

所有 API 端点（除了 `/health` 和 `/`）都需要 API Key 认证。

在请求头中添加：
```
X-API-Key: your-api-key
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
| `MODEL` | `openrouter/stepfun/step-3.5-flash:free` | 默认模型 |
| `SESSION_TYPE` | `memory` | 会话存储类型 (memory/sqlite/redis) |
| `SESSION_TTL` | `86400` | Session TTL (秒) |
| `API_KEY` | (必填) | HTTP API 认证密钥 |
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `18791` | 监听端口 |
| `CORS_ORIGINS` | `*` | CORS 允许的源 |
| `RATE_LIMIT_ENABLED` | `true` | 是否启用速率限制 |
| `RATE_LIMIT_REQUESTS` | `100` | 每分钟请求数 |
| `NANOBOT_WORKSPACE` | `/app/workspace` | 工作空间路径 |

## 📁 项目结构

```
nanobot/
├── http_api/
│   ├── main.py              # FastAPI 主应用
│   ├── core/
│   │   ├── config.py       # 配置管理
│   │   ├── models.py       # 请求/响应模型
│   │   ├── session_adapter.py  # 会话适配器
│   │   └── app_state.py   # 应用状态管理
│   ├── routers/
│   │   ├── chat_router.py  # 聊天路由
│   │   ├── sessions_router.py  # 会话管理路由
│   │   └── tools_router.py # 工具路由
│   ├── .env.example        # 环境变量示例
│   └── Dockerfile.http     # Docker 配置
├── nanobot/                # NanoBOT 核心（原始项目）
├── .env                    # 环境变量（需自行创建）
└── README_http_api.md      # 本文档
```

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -f Dockerfile.http -t nanobot-http-api:latest .
```

### 运行容器

```bash
docker run -d \
  --name nanobot-http \
  -p 18798:18791 \
  -v $(pwd)/http_api/.env:/app/http_api/.env \
  -v $(pwd)/workspace:/app/workspace \
  nanobot-http-api:latest
```

**参数说明：**
- `-p 18798:18791`: 将容器内的18791端口映射到宿主机的18798端口
- `-v .../.env:/app/http_api/.env`: 挂载环境变量配置文件
- `-v .../workspace:/app/workspace`: 挂载工作空间目录（用于持久化session文件）

## 💻 前端对接指南

### 基础配置

```javascript
const API_BASE_URL = 'http://localhost:18798';
const API_KEY = 'your-api-key';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};
```

### 1. 发送聊天消息

**接口：** `POST /v1/chat/simple`

```javascript
async function sendMessage(query, userId = 'default', sessionId = null) {
  const response = await fetch(`${API_BASE_URL}/v1/chat/simple`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
      query: query,
      user_id: userId,
      session_id: sessionId
    })
  });

  const data = await response.json();
  return {
    response: data.response,
    sessionId: data.session_id,
    createdAt: data.created_at
  };
}
```

### 2. 获取会话列表

**接口：** `GET /v1/sessions`

```javascript
async function getSessions() {
  const response = await fetch(`${API_BASE_URL}/v1/sessions`, {
    method: 'GET',
    headers: headers
  });

  const sessions = await response.json();
  return sessions.map(session => ({
    sessionId: session.session_id,
    userId: session.user_id,
    messageCount: session.message_count,
    createdAt: session.created_at,
    updatedAt: session.updated_at
  }));
}
```

### 3. 获取会话详情（含历史消息）

**接口：** `GET /v1/sessions/{session_id}`

```javascript
async function getSessionDetail(sessionId) {
  // 注意：session_id 中包含冒号需要URL编码
  const encodedSessionId = encodeURIComponent(sessionId);

  const response = await fetch(
    `${API_BASE_URL}/v1/sessions/${encodedSessionId}`,
    {
      method: 'GET',
      headers: headers
    }
  );

  const data = await response.json();
  return {
    sessionId: data.session_id,
    userId: data.user_id,
    messageCount: data.message_count,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    messages: data.messages
  };
}
```

### 4. 完整的前端示例

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>NanoBOT Chat</title>
</head>
<body>
  <div>
    <h3>会话列表</h3>
    <button onclick="loadSessions()">刷新会话</button>
    <ul id="sessionList"></ul>
  </div>

  <div>
    <h3>聊天</h3>
    <select id="sessionSelect">
      <option value="">新建会话</option>
    </select>
    <div id="messages" style="border:1px solid #ccc; height:300px; overflow-y:auto; padding:10px;"></div>
    <input type="text" id="queryInput" placeholder="输入消息..." style="width:70%;">
    <button onclick="sendMessage()">发送</button>
  </div>

  <script>
    const API_BASE_URL = 'http://localhost:18798';
    const API_KEY = 'your-api-key';

    const headers = {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    };

    let currentSessionId = null;

    async function loadSessions() {
      const response = await fetch(`${API_BASE_URL}/v1/sessions`, {
        method: 'GET',
        headers: headers
      });
      const sessions = await response.json();

      const select = document.getElementById('sessionSelect');
      select.innerHTML = '<option value="">新建会话</option>';

      sessions.forEach(session => {
        const option = document.createElement('option');
        option.value = session.session_id;
        option.textContent = `${session.session_id} (${session.message_count}条消息)`;
        select.appendChild(option);
      });
    }

    async function loadSessionHistory(sessionId) {
      const encodedSessionId = encodeURIComponent(sessionId);
      const response = await fetch(
        `${API_BASE_URL}/v1/sessions/${encodedSessionId}`,
        { method: 'GET', headers: headers }
      );
      const data = await response.json();

      const messagesDiv = document.getElementById('messages');
      messagesDiv.innerHTML = '';

      data.messages.forEach(msg => {
        const p = document.createElement('p');
        p.innerHTML = `<strong>${msg.role}:</strong> ${msg.content}`;
        messagesDiv.appendChild(p);
      });
    }

    document.getElementById('sessionSelect').addEventListener('change', async (e) => {
      const sessionId = e.target.value;
      if (sessionId) {
        currentSessionId = sessionId;
        await loadSessionHistory(sessionId);
      } else {
        currentSessionId = null;
        document.getElementById('messages').innerHTML = '';
      }
    });

    async function sendMessage() {
      const query = document.getElementById('queryInput').value;
      if (!query) return;

      const requestBody = {
        query: query,
        user_id: 'web_user'
      };

      if (currentSessionId) {
        requestBody.session_id = currentSessionId;
      }

      const response = await fetch(`${API_BASE_URL}/v1/chat/simple`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      // 更新当前会话ID
      if (!currentSessionId) {
        currentSessionId = data.session_id;
        await loadSessions();
        document.getElementById('sessionSelect').value = currentSessionId;
      }

      // 显示新消息
      const messagesDiv = document.getElementById('messages');
      messagesDiv.innerHTML += `<p><strong>user:</strong> ${query}</p>`;
      messagesDiv.innerHTML += `<p><strong>assistant:</strong> ${data.response}</p>`;
      messagesDiv.scrollTop = messagesDiv.scrollHeight;

      document.getElementById('queryInput').value = '';
    }

    // 初始化
    loadSessions();
  </script>
</body>
</html>
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

1. **Session 持久化**：session文件会保存在workspace目录下的sessions子目录中。确保Docker运行时挂载了workspace目录。
2. **流式实现**：当前 `/chat/completions/stream` 仍使用非流式模拟，实际应扩展 `AgentLoop` 的流式能力。
3. **工具调用**：工具调用能力已在 `AgentLoop` 中实现，但 HTTP 接口需要额外处理工具调用的结构化输出。
4. **生产部署**：务必设置更强的 `API_KEY`，启用 HTTPS（通过 Cloudflare Tunnel 或反向代理），配置防火墙规则。

## 📝 附加说明

### 与原版 NanoBOT 的区别

本 HTTP API 在原版 NanoBOT 基础上添加了以下内容以支持 HTTP 调用：

1. **新增 `http_api/` 目录**：包含所有 HTTP API 相关代码
   - `main.py` - FastAPI 主应用入口
   - `core/config.py` - 环境配置管理
   - `core/models.py` - Pydantic 请求/响应模型
   - `core/session_adapter.py` - SessionManager 适配器
   - `core/app_state.py` - 应用状态管理
   - `routers/chat_router.py` - 聊天相关接口
   - `routers/sessions_router.py` - 会话管理接口
   - `routers/tools_router.py` - 工具列表接口

2. **新增 `Dockerfile.http`**：用于构建 HTTP API Docker 镜像

3. **修复的问题**：
   - 修复了 `sessions_router.py` 中的响应处理逻辑
   - 修复了 `config.py` 中的环境文件路径配置
   - 实现了 `GET /v1/sessions/{session_id}` 接口以支持获取会话历史

### session_id 格式说明

- 通过 `/v1/chat/simple` 创建的session，session_id格式为 `user_id:session_id`
- 通过 `/v1/chat/completions` 创建的session，session_id格式为 `openai:{random_id}`
- 在URL中使用时，需要对特殊字符进行URL编码（如 `:` 编码为 `%3A`）

---

**开发者**: Wingo
**日期**: 2026-03-22
**版本**: 0.1.1
