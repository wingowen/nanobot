"""HTTP API 聊天路由"""

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from nanobot.http_api.core.agent_wrapper import NanoBotAgent
from nanobot.http_api.core.settings import get_agent_dep, verify_api_key
from nanobot.http_api.core.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    SimpleChatRequest,
    SimpleResponse,
    SessionInfo,
    ToolInfo,
    ErrorResponse,
)

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    agent: NanoBotAgent = Depends(get_agent_dep),
    authorization: str | None = Header(None, alias="Authorization"),
):
    """
    OpenAI 兼容的聊天完成接口

    - **model**: 可选，默认使用环境变量配置的模型
    - **messages**: 消息列表（OpenAI 格式）
    - **stream**: 是否流式输出（暂未支持）
    - **temperature/max_tokens/top_p**: 生成参数（暂忽略）
    - **user/session_id**: 会话标识
    """
    # API Key 验证
    if authorization:
        api_key = authorization.replace("Bearer ", "")
        if not verify_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        response = await agent.chat_completion(
            messages=request.messages,
            user_id=request.user or "api_user",
            session_id=request.session_id,
            stream=request.stream,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 处理失败: {str(e)}")


@router.post("/chat", response_model=SimpleResponse)
async def chat_simple(
    request: SimpleChatRequest,
    agent: NanoBotAgent = Depends(get_agent_dep),
):
    """
    简化聊天接口

    - **query**: 用户问题
    - **user_id**: 用户标识（默认 api_user）
    - **session_id**: 会话ID（可选）
    - **params**: 额外参数
    """
    try:
        response = await agent.chat_simple(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            **(request.params or {}),
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 处理失败: {str(e)}")


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions(
    user_id: str | None = None,
    agent: NanoBotAgent = Depends(get_agent_dep),
    authorization: str | None = Header(None, alias="Authorization"),
):
    """
    列出所有会话

    - **user_id**: 可选，过滤特定用户的会话
    """
    if authorization:
        api_key = authorization.replace("Bearer ", "")
        if not verify_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

    sessions = agent.list_sessions(user_id)
    return sessions


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(
    session_id: str,
    agent: NanoBotAgent = Depends(get_agent_dep),
    authorization: str | None = Header(None, alias="Authorization"),
):
    """获取特定会话信息"""
    if authorization:
        api_key = authorization.replace("Bearer ", "")
        if not verify_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

    session = agent.get_session_info(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
async def clear_session(
    session_id: str,
    agent: NanoBotAgent = Depends(get_agent_dep),
    authorization: str | None = Header(None, alias="Authorization"),
):
    """清除会话"""
    if authorization:
        api_key = authorization.replace("Bearer ", "")
        if not verify_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

    success = agent.clear_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session cleared", "session_id": session_id}


@router.get("/tools", response_model=list[ToolInfo])
async def list_tools(
    agent: NanoBotAgent = Depends(get_agent_dep),
):
    """列出可用工具"""
    # TODO: 从 agent.tools 获取真实工具列表
    # 暂时返回示例
    return [
        ToolInfo(
            name="search_web",
            description="搜索网页内容",
            parameters={"query": "string", "max_results": "number"},
        ),
        ToolInfo(
            name="read_file",
            description="读取文件内容",
            parameters={"path": "string"},
        ),
    ]


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": __import__("datetime").datetime.now().isoformat()}