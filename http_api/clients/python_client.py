"""Python client for NanoBOT HTTP API."""

import json
from typing import Any, AsyncGenerator, Optional

import httpx


class NanoBotClient:
    """Async client for NanoBOT HTTP API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 60.0
    ) -> None:
        """
        Initialize client.

        Args:
            base_url: API base URL
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key

    async def chat(
        self,
        message: str,
        user_id: str = "api_user",
        session_id: Optional[str] = None,
        stream: bool = False,
        model: Optional[str] = None,
        **kwargs: Any
    ) -> str | AsyncGenerator[str, None]:
        """
        Send a chat message.

        Args:
            message: User message
            user_id: User identifier
            session_id: Optional session identifier
            stream: Stream response
            model: Model override
            **kwargs: Additional parameters

        Returns:
            Response string or async generator for streaming
        """
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "stream": stream,
            "user": user_id,
            "session_id": session_id,
            **kwargs
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()

            if stream:
                # Return generator for SSE stream
                async def generate() -> AsyncGenerator[str, None]:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    delta = chunk["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue

                return generate()
            else:
                data = response.json()
                return data["choices"][0]["message"]["content"]

    async def list_sessions(self, user_id: str = "api_user") -> list[dict[str, Any]]:
        """List sessions for a user."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/v1/sessions/{user_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def delete_session(self, session_id: str, user_id: str = "api_user") -> dict[str, str]:
        """Delete a session."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base_url}/v1/sessions/{session_id}",
                headers=self.headers,
                params={"user_id": user_id}
            )
            response.raise_for_status()
            return response.json()

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/v1/tools",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data["tools"]


# Synchronous wrapper for convenience
class SyncNanoBotClient:
    """Synchronous client wrapper."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 60.0
    ) -> None:
        import asyncio
        self._async_client = NanoBotClient(base_url, api_key, timeout)
        self._loop = asyncio.new_event_loop()

    def chat(
        self,
        message: str,
        user_id: str = "api_user",
        session_id: Optional[str] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> str:
        """Synchronous chat."""
        return self._loop.run_until_complete(
            self._async_client.chat(message, user_id, session_id, stream, **kwargs)
        )

    def list_sessions(self, user_id: str = "api_user") -> list[dict[str, Any]]:
        """Synchronous list sessions."""
        return self._loop.run_until_complete(
            self._async_client.list_sessions(user_id)
        )

    def close(self) -> None:
        """Close event loop."""
        self._loop.close()


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        client = NanoBotClient(
            base_url="http://localhost:8000",
            api_key="your-api-key-here"
        )

        # Simple query
        response = await client.chat("Hello! What can you do?")
        print("Response:", response)

        # Streaming query
        print("\nStreaming:")
        async for chunk in await client.chat("Tell me a story", stream=True):
            print(chunk, end="", flush=True)
        print()

        # List sessions
        sessions = await client.list_sessions()
        print(f"\nSessions: {sessions}")

    asyncio.run(main())
