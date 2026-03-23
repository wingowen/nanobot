"""聊天路由 - 实现 OpenAI 兼容的聊天接口"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from nanobot.agent.loop import AgentLoop
from nanobot.bus.events import InboundMessage
from nanobot.session.manager import Session

from ..core.config import get_settings
from ..core.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamResponse,
    SimpleChatRequest,
    SimpleResponse,
)
from ..core.session_adapter import SessionAdapter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_agent() -> AgentLoop:
    """依赖注入：获取 Agent 实例（从 app_state）"""
    from ..core.app_state import get_agent
    return get_agent()


async def get_session_adapter() -> SessionAdapter:
    """依赖注入：获取 SessionAdapter（从 agent.sessions）"""
    agent = await get_agent()
    if not hasattr(agent, 'sessions') or agent.sessions is None:
        raise HTTPException(status_code=500, detail="Session manager not initialized")
    return SessionAdapter(agent.sessions)


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    agent: AgentLoop = Depends(get_agent),
):
    """
    OpenAI 兼容的聊天完成接口
    
    支持标准 OpenAI 格式请求，返回结构化响应
    """
    try:
        # 提取用户最新消息内容
        if not request.messages:
            raise HTTPException(status_code=400, detail="messages is required")

        # 按请求覆盖模型（兼容 OpenAI API 的 model 参数）
        original_model = getattr(agent, "model", None)
        if request.model:
            agent.model = request.model
        
        # 取最后一条用户/助理消息作为当前输入（通常最后一条是用户）
        last_msg = request.messages[-1]
        content = last_msg.content
        
        # 生成或使用 session_id
        session_key = f"openai:{request.session_id or uuid.uuid4().hex[:8]}"
        
        # 调用 AgentLoop.process_direct - 它自动处理会话历史
        response_text = await agent.process_direct(
            content=content,
            session_key=session_key,
            channel="http_api",
            chat_id=session_key,
        )

        # 构建响应
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
        created = int(datetime.utcnow().timestamp())

        return ChatCompletionResponse(
            id=completion_id,
            object="chat.completion",
            created=created,
            model=request.model or getattr(agent, "model", get_settings().model),
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                    "finish_reason": "stop",
                }
            ],
            usage={
                "prompt_tokens": 0,  # TODO: 实际计算
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        )

    except Exception as e:
        logger.exception("chat_completions_error")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'original_model' in locals() and original_model is not None:
            agent.model = original_model


@router.post("/chat/completions/stream")
async def chat_completions_stream(
    request: ChatCompletionRequest,
    agent: AgentLoop = Depends(get_agent),
):
    """
    流式聊天完成接口（Server-Sent Events）
    
    支持实时流式输出，每块数据格式与 OpenAI Streaming 一致
    """
    if request.stream is False:
        raise HTTPException(status_code=400, detail="This endpoint only supports stream=true")

    queue: asyncio.Queue[str | None] = asyncio.Queue()
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created = int(datetime.utcnow().timestamp())

    async def on_progress(content: str, *, tool_hint: bool = False) -> None:
        stream_chunk = ChatCompletionStreamResponse(
            id=completion_id,
            object="chat.completion.chunk",
            created=created,
            model=request.model or get_settings().model,
            choices=[
                {
                    "index": 0,
                    "delta": {"content": content} if content else {},
                    "finish_reason": None,
                }
            ]
        )
        await queue.put(stream_chunk.model_dump_json())

    async def event_generator():
        try:
            last_msg = request.messages[-1]
            content = last_msg.content
            session_key = f"openai:{request.session_id or uuid.uuid4().hex[:8]}"

            agent_task = asyncio.create_task(
                agent.process_direct(
                    content=content,
                    session_key=session_key,
                    channel="http_api",
                    chat_id=session_key,
                    on_progress=on_progress,
                )
            )

            while True:
                try:
                    chunk_json = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {chunk_json}\n\n"
                except asyncio.TimeoutError:
                    if agent_task.done():
                        break
                    continue
                except asyncio.QueueEmpty:
                    if agent_task.done():
                        break
                    await asyncio.sleep(0.1)
                    continue

            try:
                await agent_task
            except Exception as e:
                logger.exception("agent_task_error")
                yield f"data: {{'error': '{str(e)}'}}\n\n"
                return

            final_chunk = ChatCompletionStreamResponse(
                id=completion_id,
                object="chat.completion.chunk",
                created=created,
                model=request.model or get_settings().model,
                choices=[
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ]
            )
            yield f"data: {final_chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.exception("stream_error")
            yield f"data: {{'error': '{str(e)}'}}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/simple", response_model=SimpleResponse)
async def simple_chat(
    payload: SimpleChatRequest,
    agent: AgentLoop = Depends(get_agent),
    session_adapter: SessionAdapter = Depends(get_session_adapter),
):
    """
    简化的聊天接口（非OpenAI格式）
    
    请求体：
    {
        "query": "用户问题",
        "user_id": "user123",  # 可选
        "session_id": "session456"  # 可选
    }
    
    响应：
    {
        "response": "AI回复",
        "session_id": "user123:default",
        "created_at": "2026-03-21T12:00:00",
        "tokens_used": 123
    }
    """
    try:
        # 获取或创建会话
        user_id = payload.user_id or "api_user"
        session = session_adapter.get_or_create(user_id, payload.session_id)
        
        # 调用 AgentLoop（直接处理消息）
        # 注意：AgentLoop.process_direct 返回回复文本
        response_text = await agent.process_direct(
            content=payload.query,
            session_key=session.key,
            channel="http_api",
            chat_id=session.key,
        )
        
        # 添加用户消息和助手回复到会话历史
        session.add_message("user", payload.query)
        session.add_message("assistant", response_text)
        
        return SimpleResponse(
            response=response_text,
            session_id=session.key,
            created_at=datetime.utcnow(),
            tokens_used=None,  # TODO: 从 provider 获取
        )
        
    except Exception as e:
        logger.exception("simple_chat_error")
        raise HTTPException(status_code=500, detail=str(e))