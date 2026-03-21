"""HTTP API 请求/响应模型"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, validator


# ========== 请求模型 ==========

class ChatMessage(BaseModel):
    """单条聊天消息"""
    role: str = Field(..., description="消息角色：user/assistant/system")
    content: str = Field(..., description="消息内容")
    name: Optional[str] = Field(None, description="工具调用者名称")


class ChatCompletionRequest(BaseModel):
    """OpenAI 兼容的聊天完成请求"""
    model: Optional[str] = Field(None, description="模型名称（可选，使用环境变量默认）")
    messages: list[ChatMessage] = Field(..., description="消息列表")
    stream: bool = Field(False, description="是否流式输出")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="采样温度")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大生成token数")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="top-p采样")
    user: Optional[str] = Field(None, description="用户标识（用于会话隔离）")
    session_id: Optional[str] = Field(None, description="会话ID（可选）")

    @validator("messages")
    def validate_messages(cls, v):
        if not v:
            raise ValueError("messages 不能为空")
        return v


class SimpleChatRequest(BaseModel):
    """简化的聊天请求（非OpenAI格式）"""
    query: str = Field(..., description="用户问题")
    user_id: Optional[str] = Field("api_user", description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    params: Optional[dict[str, Any]] = Field(None, description="额外参数")


# ========== 响应模型 ==========

class ChatCompletionChoice(BaseModel):
    """聊天完成选项"""
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    """OpenAI 兼容的聊天完成响应"""
    id: str = Field(..., description="完成ID")
    object: str = Field("chat.completion", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="使用的模型")
    choices: list[ChatCompletionChoice]
    usage: dict[str, int] = Field(..., description="token使用情况")


class StreamChoiceDelta(BaseModel):
    """流式输出增量"""
    role: Optional[str] = None
    content: Optional[str] = None


class StreamChoice(BaseModel):
    """流式输出选项"""
    index: int
    delta: StreamChoiceDelta
    finish_reason: Optional[str] = None


class ChatCompletionStreamResponse(BaseModel):
    """流式响应（Server-Sent Events）"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[StreamChoice]


class SimpleResponse(BaseModel):
    """简化响应格式"""
    response: str = Field(..., description="AI回复")
    session_id: str = Field(..., description="会话标识")
    created_at: datetime = Field(..., description="创建时间")
    tokens_used: Optional[int] = Field(None, description="消耗token数")


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    user_id: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ToolInfo(BaseModel):
    """工具信息"""
    name: str
    description: str
    parameters: dict[str, Any]


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    message: str
    detail: Optional[dict[str, Any]] = None