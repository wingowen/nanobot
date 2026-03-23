# NanoBOT HTTP API 前端集成文档

## 1. 系统架构

```
┌─────────────────┐     HTTP      ┌─────────────────┐     LLM      ┌─────────────┐
│   前端 (HTML)   │ ────────────► │   FastAPI       │ ────────────► │ OpenRouter │
│   chat.html     │ ◄──────────── │   HTTP API      │ ◄──────────── │   API      │
│                 │   JSON        │   (Port 18798)  │               └─────────────┘
└─────────────────┘               └─────────────────┘
```

## 2. API 端点

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/health` | GET | 健康检查 | ❌ |
| `/v1/chat/simple` | POST | 简化聊天接口 | ✅ X-API-Key |
| `/v1/chat/completions` | POST | OpenAI 兼容格式 | ✅ X-API-Key |
| `/v1/sessions` | GET | 列出会话 | ✅ X-API-Key |
| `/v1/sessions/{id}` | DELETE | 删除会话 | ✅ X-API-Key |

## 3. 认证机制

所有需要认证的接口都需要在请求头中携带：

```
X-API-Key: <你的API_KEY>
```

**当前配置：**
- API 地址：`http://localhost:18798`
- API Key：`JIY0FZIpXZCCh1lUaYT2zdbM9M1oUy6KNsk_kAp35Kw`

## 4. 聊天接口详解

### 4.1 简化接口 `/v1/chat/simple`

**请求：**
```bash
curl -X POST http://localhost:18798/v1/chat/simple \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JIY0FZIpXZCCh1lUaYT2zdbM9M1oUy6KNsk_kAp35Kw" \
  -d '{
    "query": "你好",
    "user_id": "user123",
    "session_id": "可选的会话ID"
  }'
```

**响应：**
```json
{
  "response": "你好！有什么我可以帮你的吗？",
  "session_id": "user123:abc123",
  "created_at": "2026-03-22T06:30:00.000000",
  "tokens_used": null
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | ✅ | 用户问题 |
| `user_id` | string | ❌ | 用户标识，默认 `api_user` |
| `session_id` | string | ❌ | 会话ID，不填自动创建 |

### 4.2 OpenAI 兼容接口 `/v1/chat/completions`

**请求：**
```bash
curl -X POST http://localhost:18798/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer JIY0FZIpXZCCh1lUaYT2zdbM9M1oUy6KNsk_kAp35Kw" \
  -d '{
    "model": "openrouter/anthropic/claude-3-haiku:free",
    "messages": [
      {"role": "system", "content": "你是一个有帮助的助手"},
      {"role": "user", "content": "用一句话介绍Python"}
    ],
    "temperature": 0.7
  }'
```

**响应：**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1713634200,
  "model": "openrouter/anthropic/claude-3-haiku:free",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Python是一门简单易学的高级编程语言..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 15,
    "total_tokens": 35
  }
}
```

## 5. 前端集成示例

### 5.1 纯 HTML/JavaScript（chat.html）

```html
<!DOCTYPE html>
<html>
<head>
    <title>NanoBOT Chat</title>
</head>
<body>
    <div id="messages"></div>
    <textarea id="input" placeholder="输入消息..."></textarea>
    <button onclick="sendMessage()">发送</button>

    <script>
        const API_URL = 'http://localhost:18798';
        const API_KEY = 'JIY0FZIpXZCCh1lUaYT2zdbM9M1oUy6KNsk_kAp35Kw';
        let sessionId = null;

        async function sendMessage() {
            const query = document.getElementById('input').value;
            
            const response = await fetch(`${API_URL}/v1/chat/simple`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY
                },
                body: JSON.stringify({
                    query: query,
                    user_id: 'web_user',
                    session_id: sessionId
                })
            });

            const data = await response.json();
            sessionId = data.session_id;  // 保存会话ID
            
            // 显示回复
            console.log('AI回复:', data.response);
        }
    </script>
</body>
</html>
```

### 5.2 fetch API 封装

```javascript
class NanoBotClient {
    constructor(apiUrl, apiKey) {
        this.apiUrl = apiUrl;
        this.apiKey = apiKey;
    }

    async chat(query, userId = 'user', sessionId = null) {
        const response = await fetch(`${this.apiUrl}/v1/chat/simple`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': this.apiKey
            },
            body: JSON.stringify({
                query,
                user_id: userId,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
    }

    async getSessions(userId = null) {
        const url = userId 
            ? `${this.apiUrl}/v1/sessions?user_id=${userId}`
            : `${this.apiUrl}/v1/sessions`;
            
        const response = await fetch(url, {
            headers: { 'X-API-Key': this.apiKey }
        });
        return response.json();
    }

    async deleteSession(sessionId) {
        await fetch(`${this.apiUrl}/v1/sessions/${sessionId}`, {
            method: 'DELETE',
            headers: { 'X-API-Key': this.apiKey }
        });
    }
}

// 使用
const client = new NanoBotClient(
    'http://localhost:18798',
    'JIY0FZIpXZCCh1lUaYT2zdbM9M1oUy6KNsk_kAp35Kw'
);

const result = await client.chat('你好');
console.log(result.response);
```

### 5.3 Vue 3 示例

```vue
<template>
  <div class="chat">
    <div v-for="msg in messages" :key="msg.id" :class="msg.role">
      {{ msg.content }}
    </div>
    <input v-model="input" @keyup.enter="send" />
    <button @click="send">发送</button>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const API_URL = 'http://localhost:18798';
const API_KEY = 'JIY0FZIpXZCCh1lUaYT2zdbM9M1oUy6KNsk_kAp35Kw';

const input = ref('');
const messages = ref([]);
let sessionId = null;

async function send() {
    if (!input.value) return;

    // 添加用户消息
    messages.value.push({ role: 'user', content: input.value });
    const query = input.value;
    input.value = '';

    // 调用API
    const res = await fetch(`${API_URL}/v1/chat/simple`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        },
        body: JSON.stringify({ query, session_id: sessionId })
    });

    const data = await res.json();
    sessionId = data.session_id;

    // 添加AI回复
    messages.value.push({ role: 'assistant', content: data.response });
}
</script>
```

### 5.4 React 示例

```tsx
import { useState } from 'react';

const API_URL = 'http://localhost:18798';
const API_KEY = 'JIY0FZIpXZCCh1lUaYT2zdbM9M1oUy6KNsk_kAp35Kw';

export default function Chat() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [sessionId, setSessionId] = useState(null);

    const send = async () => {
        if (!input) return;

        setMessages(m => [...m, { role: 'user', content: input }]);
        const query = input;
        setInput('');

        const res = await fetch(`${API_URL}/v1/chat/simple`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({ query, session_id: sessionId })
        });

        const data = await res.json();
        setSessionId(data.session_id);
        setMessages(m => [...m, { role: 'assistant', content: data.response }]);
    };

    return (
        <div>
            {messages.map((m, i) => (
                <div key={i} className={m.role}>{m.content}</div>
            ))}
            <input value={input} onChange={e => setInput(e.target.value)} />
            <button onClick={send}>发送</button>
        </div>
    );
}
```

## 6. 会话管理

### 6.1 会话原理

```
用户A 第一次请求  ──►  API 创建会话 ──► session_id = "userA:xxx"
用户A 第二次请求  ──►  传入 session_id ──► API 复用会话（带历史上下文）
```

### 6.2 列出所有会话

```bash
curl http://localhost:18798/v1/sessions \
  -H "X-API-Key: JIY0FZIpXZCCh1lUaYT2zdbM9M1oUy6KNsk_kAp35Kw"
```

**响应：**
```json
[
  {
    "session_id": "userA:abc123",
    "user_id": "userA",
    "message_count": 5,
    "created_at": "2026-03-22T06:00:00",
    "updated_at": "2026-03-22T06:30:00"
  }
]
```

### 6.3 删除会话

```bash
curl -X DELETE http://localhost:18798/v1/sessions/userA:abc123 \
  -H "X-API-Key: JIY0FZIpXZCCh1lUaYT2zdbM9M1oUy6KNsk_kAp35Kw"
```

## 7. 错误处理

### 7.1 常见错误码

| 状态码 | 原因 | 解决方案 |
|--------|------|----------|
| 400 | 请求格式错误 | 检查 JSON 格式和必填参数 |
| 401 | API Key 无效 | 确认 X-API-Key 正确 |
| 404 | 端点不存在 | 检查 URL 路径 |
| 500 | 服务器内部错误 | 查看 API 日志 |

### 7.2 前端错误处理

```javascript
async function chat(query) {
    try {
        const response = await fetch(`${API_URL}/v1/chat/simple`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('API Key 无效');
            }
            throw new Error(`请求失败: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Chat error:', error);
        return { response: '发生错误，请重试' };
    }
}
```

## 8. 启动服务

### 8.1 启动后端 API

```bash
cd /root/.openclaw/workspace/nanobot
uvicorn http_api.main:app --host 0.0.0.0 --port 18798
```

### 8.2 启动前端服务器

```bash
# 在另一个终端
cd /root/.openclaw/workspace/nanobot
python3 -m http.server 8080 --directory http_api
```

### 8.3 访问

- 前端页面：http://localhost:8080/chat.html
- API 文档：http://localhost:18798/docs

## 9. 配置说明

### 9.1 环境变量 (.env)

```bash
# API 服务配置
API_HOST=0.0.0.0
API_PORT=18798

# 认证
API_KEY=JIY0FZIpXZCCh1lUaYT2zdbM9M1oUy6KNsk_kAp35Kw

# LLM 配置
OPENROUTER_API_KEY=sk-or-v1-你的密钥
MODEL=openrouter/stepfun/step-3.5-flash:free
```

### 9.2 前端配置 (chat.html)

前端支持本地存储配置，可在设置中修改：
- API 地址
- API Key  
- 用户 ID

---

**更新时间**: 2026-03-22
