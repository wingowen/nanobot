"""NanoBOT AgentLoop HTTP 封装器"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from nanobot.agent.loop import AgentLoop
from nanobot.bus.events import InboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.config.loader import load_config
from nanobot.providers.base import LLMProvider, get_provider
from nanobot.session.manager import Session, SessionManager

from .models import ChatCompletionResponse, ChatMessage, SimpleResponse


class NanoBotAgent:
    """NanoBOT Agent 的 HTTP API 封装"""

    def __init__(
        self,
        provider: str = "openrouter",
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        workspace: str | None = None,
        **kwargs: Any
    ):
        """
        初始化 NanoBOT Agent

        Args:
            provider: LLM 提供商名称（openrouter, anthropic, openai 等）
            model: 模型名称（如 openrouter/anthropic/claude-3-haiku:free）
            api_key: API 密钥（从环境变量读取如果未提供）
            base_url: API 基础 URL
            workspace: 工作空间路径（用于文件操作限制）
        """
        # 配置
        self.provider_name = provider
        self.model = model or os.getenv("MODEL", "openrouter/anthropic/claude-3-haiku:free")
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.workspace = Path(workspace or os.getenv("WORKSPACE", "/root/.openclaw/workspace/nanobot_workspace"))
        self.workspace.mkdir(parents=True, exist_ok=True)

        # 初始化 NanoBOT 核心组件
        self._init_nanobot()

    def _init_nanobot(self) -> None:
        """初始化 NanoBOT 核心组件"""
        # 1. 创建 MessageBus
        self.bus = MessageBus()

        # 2. 初始化 LLM Provider
        provider_config = {
            "api_key": self.api_key,
            "api_base": self.base_url,
            "model": self.model,
        }
        self.provider: LLMProvider = get_provider(self.provider_name, provider_config)

        # 3. 创建 SessionManager（内存模式）
        self.session_mgr = SessionManager(self.workspace)

        # 4. 创建 AgentLoop
        self.agent = AgentLoop(
            bus=self.bus,
            provider=self.provider,
            workspace=self.workspace,
            model=self.model,
            session_manager=self.session_mgr,
        )

    async def chat_simple(
        self,
        query: str,
        user_id: str = "api_user",
        session_id: str | None = None,
        **kwargs: Any
    ) -> SimpleResponse:
        """
        简化的聊天接口

        Args:
            query: 用户问题
            user_id: 用户标识
            session_id: 可选会话ID（不传则自动创建）

        Returns:
            SimpleResponse 包含回复和会话信息
        """
        # 生成 session_key
        # session_key 格式: "channel:session_id"
        session_key = f"http_api:{session_id or user_id}"

        # 直接调用 AgentLoop.process_direct
        # 参数: content, session_key, channel, chat_id
        response_text = await self.agent.process_direct(
            content=query,
            session_key=session_key,
            channel="http_api",
            chat_id=session_id or user_id,
        )

        # 计算 token 使用（简化版）
        tokens_used = len(query.split()) + len(response_text.split())

        return SimpleResponse(
            response=response_text,
            session_id=session_key,
            created_at=datetime.now(),
            tokens_used=tokens_used,
        )

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        user_id: str = "api_user",
        session_id: str | None = None,
        stream: bool = False,
        **kwargs: Any
    ) -> ChatCompletionResponse | list[ChatCompletionStreamResponse]:
        """
        OpenAI 兼容的聊天完成接口

        Args:
            messages: 消息列表
            user_id: 用户标识
            session_id: 会话ID
            stream: 是否流式

        Returns:
            完整响应或流式响应列表
        """
        # 生成 session_key
        session_key = f"http_api:{session_id or user_id}"

        # 将 OpenAI 格式消息转换为 NanoBOT 消息
        # 这里简化处理：只取最后一条用户消息作为 query
        last_user_msg = None
        for msg in reversed(messages):
            if msg.role == "user":
                last_user_msg = msg.content
                break

        if not last_user_msg:
            raise ValueError("消息列表中必须包含用户消息")

        # 直接调用 process_direct
        response_text = await self.agent.process_direct(
            content=last_user_msg,
            session_key=session_key,
            channel="http_api",
            chat_id=session_id or user_id,
        )

        if stream:
            # TODO: 实现流式输出
            raise NotImplementedError("流式输出暂未实现")
        else:
            # 构造 OpenAI 兼容响应
            return ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                object="chat.completion",
                created=int(datetime.now().timestamp()),
                model=self.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=response_text),
                        finish_reason="stop",
                    )
                ],
                usage={
                    "prompt_tokens": sum(len(m.content.split()) for m in messages),
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": sum(len(m.content.split()) for m in messages) + len(response_text.split()),
                },
            )

    def get_session_info(self, session_id: str) -> SessionInfo | None:
        """获取会话信息"""
        session = self.session_mgr.get(session_id)
        if not session:
            return None
        return SessionInfo(
            session_id=session.key,
            user_id=session.key.split(":")[0] if ":" in session.key else "unknown",
            message_count=len(session.messages),
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def list_sessions(self, user_id: str | None = None) -> list[SessionInfo]:
        """列出会话"""
        sessions = self.session_mgr.list_sessions()
        result = []
        for session in sessions:
            # 过滤用户
            if user_id and not session.key.startswith(f"http_api:{user_id}"):
                continue
            result.append(
                SessionInfo(
                    session_id=session.key,
                    user_id=session.key.split(":")[0] if ":" in session.key else "unknown",
                    message_count=len(session.messages),
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                )
            )
        return result

    def clear_session(self, session_id: str) -> bool:
        """清除会话"""
        session = self.session_mgr.get(session_id)
        if session:
            session.clear()
            return True
        return False