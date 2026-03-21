"""NanoBOT HTTP API Python 客户端示例"""

import json
from typing import Any, AsyncIterator, Optional

import httpx


class NanoBotClient:
    """NanoBOT HTTP API 客户端"""

    def __init__(
        self,
        base_url: str = "http://localhost:18791",
        api_key: Optional[str] = None,
        timeout: int = 60,
    ):
        """
        初始化客户端

        Args:
            base_url: API 基础 URL
            api_key: API 密钥（可选）
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat(
        self,
        query: str,
        user_id: str = "api_user",
        session_id: Optional[str] = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        发送聊天请求（简化接口）

        Args:
            query: 用户问题
            user_id: 用户标识
            session_id: 会话ID（可选）

        Returns:
            包含回复和会话信息的字典
        """
        payload = {
            "query": query,
            "user_id": user_id,
            "session_id": session_id,
            **kwargs,
        }

        response = await self.client.post(
            f"{self.base_url}/v1/chat",
            json=payload,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        user: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        OpenAI 兼容的聊天完成接口

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}, ...]
            model: 模型名称（可选）
            stream: 是否流式输出
            user: 用户标识
            session_id: 会话ID

        Returns:
            OpenAI 兼容的响应
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "user": user,
            "session_id": session_id,
            **kwargs,
        }

        response = await self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def list_sessions(self, user_id: Optional[str] = None) -> list[dict[str, Any]]:
        """列出会话"""
        params = {}
        if user_id:
            params["user_id"] = user_id

        response = await self.client.get(
            f"{self.base_url}/v1/sessions",
            params=params,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """获取会话信息"""
        response = await self.client.get(
            f"{self.base_url}/v1/sessions/{session_id}",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def clear_session(self, session_id: str) -> dict[str, Any]:
        """清除会话"""
        response = await self.client.delete(
            f"{self.base_url}/v1/sessions/{session_id}",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def list_tools(self) -> list[dict[str, Any]]:
        """列出可用工具"""
        response = await self.client.get(
            f"{self.base_url}/v1/tools",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        response = await self.client.get(
            f"{self.base_url}/health",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


# 同步版本（包装异步方法）
import asyncio


class SyncNanoBotClient:
    """同步客户端，便于脚本中使用"""

    def __init__(
        self,
        base_url: str = "http://localhost:18791",
        api_key: Optional[str] = None,
        timeout: int = 60,
    ):
        self._async_client = NanoBotClient(base_url, api_key, timeout)

    def chat(self, *args, **kwargs) -> dict[str, Any]:
        return asyncio.run(self._async_client.chat(*args, **kwargs))

    def chat_completion(self, *args, **kwargs) -> dict[str, Any]:
        return asyncio.run(self._async_client.chat_completion(*args, **kwargs))

    def list_sessions(self, *args, **kwargs) -> list[dict[str, Any]]:
        return asyncio.run(self._async_client.list_sessions(*args, **kwargs))

    def get_session(self, *args, **kwargs) -> dict[str, Any]:
        return asyncio.run(self._async_client.get_session(*args, **kwargs))

    def clear_session(self, *args, **kwargs) -> dict[str, Any]:
        return asyncio.run(self._async_client.clear_session(*args, **kwargs))

    def list_tools(self, *args, **kwargs) -> list[dict[str, Any]]:
        return asyncio.run(self._async_client.list_tools(*args, **kwargs))

    def health_check(self, *args, **kwargs) -> dict[str, Any]:
        return asyncio.run(self._async_client.health_check(*args, **kwargs))


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def example():
        client = NanoBotClient(
            base_url="http://localhost:18791",
            api_key="sk-nanobot-http-api-2026"
        )

        try:
            # 健康检查
            health = await client.health_check()
            print(f"✅ 服务状态: {health}")

            # 简单聊天
            result = await client.chat("今天天气怎么样？", user_id="test_user")
            print(f"🤖 回复: {result['response']}")
            print(f"📝 会话ID: {result['session_id']}")

            # OpenAI 兼容格式
            openai_result = await client.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个有用的助手"},
                    {"role": "user", "content": "用一句话介绍 Python"},
                ],
                user="test_user",
            )
            print(f"🤖 OpenAI 格式回复: {openai_result['choices'][0]['message']['content']}")

            # 列出会话
            sessions = await client.list_sessions(user_id="test_user")
            print(f"📊 会话列表: {sessions}")

        finally:
            await client.close()

    asyncio.run(example())