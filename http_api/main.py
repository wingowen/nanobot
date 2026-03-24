"""NanoBOT HTTP API - FastAPI 主应用"""

import os
import uuid
from datetime import datetime
from typing import Optional

import structlog
from fastapi import FastAPI, Depends, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from fastapi import FastAPI, Depends, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .core.config import Settings
from .core.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamResponse,
    SimpleChatRequest,
    SimpleResponse,
    SessionInfo,
    ToolInfo,
    ErrorResponse,
    ChatMessage,
)
from .core.app_state import (
    get_agent,
    get_bus,
    get_session_manager,
    initialize_app,
    shutdown_app,
)
from .routers import chat_router, sessions_router, tools_router

# 初始化结构化日志
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# 初始化 Settings
settings = Settings()

# 创建 FastAPI 应用
app = FastAPI(
    title="NanoBOT HTTP API",
    description="NanoBOT 的 HTTP API 封装，支持 OpenAI 兼容格式",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 速率限制
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 速率限制
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# API Key 认证
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> bool:
    """验证 API Key"""
    expected = settings.api_key
    if x_api_key != expected:
        logger.warning("invalid_api_key", api_key=x_api_key[:8])
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# 包含路由
app.include_router(
    chat_router.router,
    prefix="/v1",
    tags=["chat"],
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    sessions_router.router,
    prefix="/v1",
    tags=["sessions"],
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    tools_router.router,
    prefix="/v1",
    tags=["tools"],
    dependencies=[Depends(verify_api_key)]
)


async def get_agent_dependency():
    """依赖注入：获取 Agent 实例"""
    from .core.app_state import get_agent
    return get_agent()


async def get_session_adapter_dependency():
    """依赖注入：获取 SessionAdapter"""
    from .core.app_state import get_session_manager
    from .core.session_adapter import SessionAdapter
    return SessionAdapter(get_session_manager())


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
async def root():
    """根路径重定向到文档"""
    return {
        "message": "NanoBOT HTTP API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("NanoBOT HTTP API starting", version="0.1.0")
    # 预加载核心组件
    initialize_app()
    logger.info("Agent initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("NanoBOT HTTP API shutting down")
    await shutdown_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )