# NanoBOT HTTP API 接口文档

## 基础信息

- **基础 URL**: `http://localhost:18798` (本地) / `https://your-domain.com` (生产)
- **认证方式**: Header 认证
- **认证 Header**: `X-API-Key`
- **认证 Key**: `SUWEN_NANOBOT_TEST`

## 通用响应格式

### 成功响应
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "openrouter/stepfun/step-3.5-flash:free",
  "choices": [...],
  "usage": {...}
}
```

### 错误响应
```json
{
  "detail": "错误信息"
}
```

---

## 接口列表

### 1. 健康检查

**GET** `/health`

检查服务是否正常运行。

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-23T06:00:00.000000"
}
```

---

### 2. 聊天完成 (流式)

**POST** `/v1/chat/completions/stream`

流式输出聊天响应，支持实时流式推送。

**请求头:**
| Header | 值 |
|--------|-----|
| Content-Type | application/json |
| X-API-Key | SUWEN_NANOBOT_TEST |

**请求体:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好，请介绍一下自己"
    }
  ],
  "stream": true,
  "session_id": "可选的会话ID"
}
```

**请求参数说明:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| messages | array | 是 | 消息列表，最后一条为用户消息 |
| messages[].role | string | 是 | 角色: user/assistant/system |
| messages[].content | string | 是 | 消息内容 |
| stream | boolean | 是 | 必须设置为 true |
| session_id | string | 否 | 会话ID，不填则自动生成 |
| model | string | 否 | 模型名称，默认使用配置 |

**响应格式 (SSE):**
```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1234567890,"model":"xxx","choices":[{"index":0,"delta":{"content":"你好"},"finish_reason":null}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1234567890,"model":"xxx","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**curl 示例:**
```bash
curl -N -X POST "http://localhost:18798/v1/chat/completions/stream" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: SUWEN_NANOBOT_TEST" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "stream": true
  }'
```

---

### 3. 聊天完成 (非流式)

**POST** `/v1/chat/completions`

一次性返回完整聊天响应。

**请求体:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好，请介绍一下自己"
    }
  ],
  "session_id": "可选的会话ID"
}
```

**响应示例:**
```json
{
  "id": "chatcmpl-6f8211c1",
  "object": "chat.completion",
  "created": 1774248705,
  "model": "openrouter/stepfun/step-3.5-flash:free",
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
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

---

### 4. 简单聊天

**POST** `/v1/chat/simple`

简化版聊天接口。

**请求体:**
```json
{
  "query": "用户问题",
  "user_id": "user123",
  "session_id": "session456"
}
```

**响应示例:**
```json
{
  "response": "AI回复内容",
  "session_id": "openai:abc123",
  "created_at": "2026-03-23T06:00:00",
  "tokens_used": null
}
```

---

### 5. 获取会话列表

**GET** `/v1/sessions`

获取所有会话列表。

**响应示例:**
```json
[
  {
    "session_id": "openai:abc123",
    "user_id": "api_user",
    "message_count": 10,
    "created_at": "2026-03-23T06:00:00",
    "updated_at": "2026-03-23T06:00:00"
  }
]
```

---

### 6. 获取会话详情

**GET** `/v1/sessions/{session_id}`

获取指定会话的详细信息和消息历史。

**响应示例:**
```json
{
  "session_id": "openai:abc123",
  "user_id": "api_user",
  "message_count": 10,
  "created_at": "2026-03-23T06:00:00",
  "updated_at": "2026-03-23T06:00:00",
  "messages": [
    {
      "role": "user",
      "content": "你好"
    },
    {
      "role": "assistant",
      "content": "你好！有什么可以帮你的吗？"
    }
  ]
}
```

---

### 7. 删除会话

**DELETE** `/v1/sessions/{session_id}`

删除指定会话。

**响应:** 204 No Content

---

### 8. 清空会话历史

**POST** `/v1/sessions/{session_id}/clear`

清空指定会话的历史消息。

**响应:**
```json
{
  "message": "Session cleared"
}
```

---

### 9. 获取可用工具列表

**GET** `/v1/tools`

获取所有可用的工具列表。

**响应示例:**
```json
[
  {
    "name": "message",
    "description": "Send a message to a user",
    "parameters": {
      "type": "object",
      "properties": {
        "content": {"type": "string"}
      },
      "required": ["content"]
    }
  },
  {
    "name": "web",
    "description": "Search the web for information",
    "parameters": {...}
  }
]
```

---

### 10. 获取工具详情

**GET** `/v1/tools/{tool_name}`

获取指定工具的详细信息。

---

### 11. 获取工具分类

**GET** `/v1/tools/categories`

获取工具分类列表。

---

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败 (X-API-Key 错误) |
| 404 | 接口不存在 |
| 422 | 请求体验证失败 |
| 500 | 服务器内部错误 |

---

## 前端对接示例

### JavaScript / TypeScript

```javascript
async function chatWithBot(message, sessionId = null) {
  const response = await fetch('http://localhost:18798/v1/chat/completions/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'SUWEN_NANOBOT_TEST'
    },
    body: JSON.stringify({
      messages: [{ role: 'user', content: message }],
      stream: true,
      session_id: sessionId
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;

        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices[0].delta.content;
          if (content) {
            console.log('Received:', content);
          }
        } catch (e) {}
      }
    }
  }
}
```

### Python

```python
import requests
import sseclient
import json

def stream_chat(message, session_id=None):
    url = "http://localhost:18798/v1/chat/completions/stream"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "SUWEN_NANOBOT_TEST"
    }
    data = {
        "messages": [{"role": "user", "content": message}],
        "stream": True,
        "session_id": session_id
    }

    response = requests.post(url, headers=headers, json=data, stream=True)
    client = sseclient.SSEClient(response)

    for event in client.events():
        if event.data == "[DONE]":
            break

        parsed = json.loads(event.data)
        content = parsed["choices"][0]["delta"].get("content", "")
        if content:
            print(content, end="", flush=True)
```
