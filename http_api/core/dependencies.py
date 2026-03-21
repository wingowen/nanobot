"""依赖注入管理"""

from typing import Optional

from nanobot.agent.loop import AgentLoop
from nanobot.bus.queue import MessageBus
from nanobot.session.manager import SessionManager
from nanobot.providers.base import LLMProvider

from .core.config import get_settings


class Dependencies:
    """依赖容器（单例）"""
    
    _instance: Optional["Dependencies"] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._provider: Optional[LLMProvider] = None
            self._bus: Optional[MessageBus] = None
            self._session_mgr: Optional[SessionManager] = None
            self._agent: Optional[AgentLoop] = None
            self._initialized = True
    
    async def get_provider(self) -> LLMProvider:
        """懒加载 LLM Provider"""
        if self._provider is None:
            from nanobot.config.loader import load_config
            from nanobot.providers import create_provider
            
            config = load_config()
            self._provider = create_provider(config.provider)
        return self._provider
    
    async def get_bus(self) -> MessageBus:
        """懒加载 MessageBus"""
        if self._bus is None:
            self._bus = MessageBus()
        return self._bus
    
    async def get_session_manager(self) -> SessionManager:
        """懒加载 SessionManager"""
        if self._session_mgr is None:
            settings = get_settings()
            
            # 根据配置选择存储类型
            if settings.session_type == "sqlite":
                from nanobot.session.storage import SQLiteStorage
                storage = SQLiteStorage(settings.workspace / "sessions.db")
            elif settings.session_type == "redis":
                from nanobot.session.storage import RedisStorage
                storage = RedisStorage()
            else:
                from nanobot.session.storage import MemoryStorage
                storage = MemoryStorage()
            
            self._session_mgr = SessionManager(storage=storage, ttl=settings.session_ttl)
        return self._session_mgr
    
    async def get_agent(self) -> AgentLoop:
        """懒加载 AgentLoop"""
        if self._agent is None:
            provider = await self.get_provider()
            bus = await self.get_bus()
            session_mgr = await self.get_session_manager()
            
            settings = get_settings()
            workspace = settings.workspace
            import os
            from nanobot.utils.helpers import ensure_dir
            ensure_dir(workspace)
            
            self._agent = AgentLoop(
                bus=bus,
                provider=provider,
                workspace=workspace,
                session_manager=session_mgr,
            )
        return self._agent
    
    async def shutdown(self):
        """清理资源"""
        if self._bus:
            await self._bus.stop()
        self._agent = None
        self._bus = None
        self._provider = None


# 全局依赖容器
_deps = Dependencies()


async def get_agent_dep() -> AgentLoop:
    """FastAPI 依赖：获取 Agent"""
    return await _deps.get_agent()


async def get_session_adapter_dep():
    """FastAPI 依赖：获取会话适配器"""
    from .core.session_adapter import SessionAdapter
    session_mgr = await _deps.get_session_manager()
    return SessionAdapter(session_mgr)


async def get_tool_registry_dep():
    """FastAPI 依赖：获取工具注册表"""
    agent = await _deps.get_agent()
    return agent.tools