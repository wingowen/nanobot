"""NanoBOT HTTP API - Python 客户端"""

import json
from typing import Any, Dict, Generator, List, Optional

import httpx


class NanoBotClient:
    """NanoBOT HTTP API 客户端"""

    def __init__(
        self,
        base_url: str = "http://localhost:18791",
        api_key: str = None,
        timeout: float = 60.0
    ):
        """
        初始化客户端

        Args:
            base_url: API 服务器地址
            api_key: API Key（可选，如果服务器需要认证）
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """连接服务器"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout
        )

        # 健康检查
        resp = await self._client.get("/health")
        if resp.status_code != 200:
            raise ConnectionError(f"无法连接到服务器: {resp.status_code}")

    async def close(self):
        """关闭连接"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def chat(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any] | Generator[str, None, None]:
        """
        发送聊天消息

        Args:
            message: 用户消息
            user_id: 用户ID（用于会话隔离）
            session_id: 会话ID（可选，不传则自动创建）
            model: 模型名称（可选）
            stream: 是否流式输出

        Returns:
            如果 stream=False，返回完整响应字典
            如果 stream=True，返回生成器（逐chunk生成）
        """
        if not self._client:
            raise RuntimeError("客户端未连接，请先调用 connect()")

        payload = {
            "messages": [
                {"role": "user", "content": message}
            ],
            "stream": stream
        }

        if model:
            payload["model"] = model
        if user_id:
            payload["user"] = user_id
        if session_id:
            payload["session_id"] = session_id

        resp = await self._client.post("/v1/chat/completions", json=payload)

        if resp.status_code != 200:
            raise HTTPError(f"请求失败: {resp.status_code} {resp.text}")

        if not stream:
            # 非流式：返回完整响应
            data = resp.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": data["model"],
                "usage": data.get("usage")
            }
        else:
            # 流式：返回生成器
            return self._stream_response(resp)

    async def _stream_response(self, resp: httpx.Response) -> Generator[str, None, None]:
        """处理流式响应"""
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]  # 去掉 "data: " 前缀
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"]
                    if "content" in delta:
                        yield delta["content"]
                except json.JSONDecodeError:
                    continue

    async def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        resp = await self._client.get("/v1/sessions")
        resp.raise_for_status()
        return resp.json()

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """获取会话详情"""
        resp = await self._client.get(f"/v1/sessions/{session_id}")
        resp.raise_for_status()
        return resp.json()

    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """删除会话"""
        resp = await self._client.delete(f"/v1/sessions/{session_id}")
        resp.raise_for_status()
        return resp.json()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出可用工具"""
        resp = await self._client.get("/v1/tools")
        resp.raise_for_status()
        return resp.json()


class HTTPError(Exception):
    """HTTP 请求错误"""
    pass


# ============================================
# 同步客户端（用于同步代码环境）
# ============================================
class NanoBotSyncClient:
    """同步版本的客户端（使用 requests）"""

    def __init__(
        self,
        base_url: str = "http://localhost:18791",
        api_key: str = None,
        timeout: float = 60.0
    ):
        import requests
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._session = requests.Session()

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        self._session.headers.update(headers)

    def chat(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """发送聊天消息（同步）"""
        payload = {
            "messages": [
                {"role": "user", "content": message}
            ],
            "stream": stream
        }

        if model:
            payload["model"] = model
        if user_id:
            payload["user"] = user_id
        if session_id:
            payload["session_id"] = session_id

        resp = self._session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout
        )

        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def close(self):
        """关闭会话"""
        self._session.close()


# ============================================
# 使用示例
# ============================================
if __name__ == "__main__":
    import asyncio

    async def test_async():
        async with NanoBotClient(base_url="http://localhost:18791") as client:
            # 简单对话
            result = await client.chat("你好，今天天气怎么样？", user_id="test_user")
            print("AI 回复:", result)

            # 列出会话
            sessions = await client.list_sessions()
            print("活跃会话:", sessions)

    def test_sync():
        client = NanoBotSyncClient(base_url="http://localhost:18791")
        try:
            result = client.chat("你好，今天天气怎么样？", user_id="test_user")
            print("AI 回复:", result)
        finally:
            client.close()

    # 运行异步测试
    asyncio.run(test_async())
