"""应用状态管理 - 解决循环依赖"""

from typing import Optional

from nanobot.agent.loop import AgentLoop
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider
from nanobot.session.manager import SessionManager

# 全局状态
_bus: Optional[MessageBus] = None
_session_mgr: Optional[SessionManager] = None
_agent: Optional[AgentLoop] = None
_provider: Optional[LLMProvider] = None


def initialize_app():
    """初始化应用状态"""
    global _bus, _session_mgr, _agent, _provider

    from nanobot.providers.litellm_provider import LiteLLMProvider
    from nanobot.session.manager import SessionManager
    from nanobot.utils.helpers import ensure_dir
    import os
    from pathlib import Path

    # 加载 .env 文件（从项目根目录）
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent.parent
    load_dotenv(project_root / ".env")
    load_dotenv(project_root / ".env.api", override=True)

    # 懒加载配置
    from .config import get_settings
    settings = get_settings()

    # 初始化 Provider - 使用 HTTP API settings 作为主配置来源
    # （避免误读 ~/.nanobot/config.json 的默认模型）
    api_key = os.getenv("OPENROUTER_API_KEY") or settings.openrouter_api_key
    api_base = os.getenv("OPENROUTER_BASE_URL") or settings.openrouter_base_url
    provider_name = os.getenv("LLM_PROVIDER") or settings.llm_provider

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set (check .env or env vars)")

    _provider = LiteLLMProvider(
        api_key=api_key,
        api_base=api_base,
        default_model=settings.model,
        provider_name=provider_name,
    )

    # 初始化 Bus
    _bus = MessageBus()

    # 初始化 SessionManager - 只需要 workspace
    workspace = Path(os.getenv("WORKSPACE") or settings.nanobot_workspace or "/app/workspace")
    ensure_dir(workspace)
    _session_mgr = SessionManager(workspace=workspace)

    # 初始化 Agent
    model = os.getenv("MODEL") or settings.model

    _agent = AgentLoop(
        bus=_bus,
        provider=_provider,
        workspace=workspace,
        model=model,
        session_manager=_session_mgr,
    )


def get_agent() -> AgentLoop:
    """获取 Agent 实例"""
    global _agent
    if _agent is None:
        initialize_app()
    return _agent


def get_bus() -> MessageBus:
    """获取 MessageBus 实例"""
    global _bus
    if _bus is None:
        initialize_app()
    return _bus


def get_session_manager() -> SessionManager:
    """获取 SessionManager 实例"""
    global _session_mgr
    if _session_mgr is None:
        initialize_app()
    return _session_mgr


async def shutdown_app():
    """关闭应用"""
    global _bus, _agent
    if _bus:
        # MessageBus 没有 stop() 方法，尝试优雅关闭
        try:
            if hasattr(_bus, 'stop'):
                await _bus.stop()
        except Exception:
            pass
    _agent = None
    _bus = None