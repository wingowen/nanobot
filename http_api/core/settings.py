"""HTTP API 配置和依赖管理"""

from typing import AsyncGenerator

from fastapi import HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings


def get_agent() -> "NanoBotAgent":
    """获取 Agent 单例"""
    from .agent_wrapper import NanoBotAgent
    settings = get_settings()
    
    return NanoBotAgent(
        provider=settings.llm_provider,
        model=settings.model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url if settings.llm_provider == "openrouter" else None,
        workspace=settings.nanobot_workspace,
    )


def verify_api_key(api_key: str) -> bool:
    """验证 API Key"""
    expected = get_settings().api_key
    return api_key == expected


async def get_agent_dep() -> AsyncGenerator["NanoBotAgent", None]:
    """FastAPI 依赖注入：获取 Agent"""
    agent = get_agent()
    try:
        yield agent
    finally:
        pass


class RateLimitMiddleware(BaseHTTPMiddleware):
    """自定义速率限制中间件"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)

        client_ip = get_remote_address(request)
        now = __import__("time").time()

        # 清理过期记录
        if client_ip in self.clients:
            self.clients[client_ip] = [t for t in self.clients[client_ip] if now - t < self.period]

        # 检查限制
        if len(self.clients.get(client_ip, [])) >= self.calls:
            raise HTTPException(status_code=429, detail="Too Many Requests")

        # 记录请求
        self.clients.setdefault(client_ip, []).append(now)

        response = await call_next(request)
        return response


def setup_middlewares(app) -> None:
    """配置中间件"""
    settings = get_settings()

    # CORS
    origins = settings.cors_origins.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 可信主机（生产环境建议限制）
    # app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

    # 速率限制
    if settings.rate_limit_enabled:
        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.add_middleware(
            RateLimitMiddleware,
            calls=settings.rate_limit_requests,
            period=settings.rate_limit_window,
        )
