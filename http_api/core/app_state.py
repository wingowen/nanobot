"""应用状态管理 - 解决循环依赖"""

import logging
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
logger = logging.getLogger(__name__)


class MCPServerConfig:
    """将字典格式的 MCP 配置转换为对象格式，兼容 nanobot 原有代码"""

    def __init__(self, config: dict):
        self._config = config

    @property
    def type(self) -> Optional[str]:
        return self._config.get("type")

    @property
    def command(self) -> Optional[str]:
        return self._config.get("command")

    @property
    def args(self) -> list:
        return self._config.get("args", [])

    @property
    def env(self) -> Optional[dict]:
        return self._config.get("env")

    @property
    def url(self) -> Optional[str]:
        return self._config.get("url")

    @property
    def headers(self) -> Optional[dict]:
        return self._config.get("headers")

    @property
    def enabled_tools(self) -> list:
        return self._config.get("enabled_tools", ["*"])

    @property
    def tool_timeout(self) -> int:
        return self._config.get("tool_timeout", 30)


def _convert_mcp_servers(mcp_servers: dict) -> dict:
    """将 MCP 配置从字典格式转换为对象格式"""
    converted = {}
    for name, config in mcp_servers.items():
        if isinstance(config, dict):
            converted[name] = MCPServerConfig(config)
        else:
            converted[name] = config
    return converted


def initialize_app():
    """初始化应用状态"""
    global _bus, _session_mgr, _agent, _provider

    from nanobot.providers.litellm_provider import LiteLLMProvider
    from nanobot.session.manager import SessionManager
    from nanobot.utils.helpers import ensure_dir
    import os
    from pathlib import Path

    # 懒加载配置
    from .config import get_settings
    settings = get_settings()

    # 尝试从 ~/.nanobot/config.json 读取默认模型配置作为 fallback
    nanobot_config_path = Path.home() / ".nanobot" / "config.json"
    nanobot_defaults = {}
    nanobot_providers = {}
    nanobot_config = {}
    if nanobot_config_path.exists():
        try:
            import json
            with open(nanobot_config_path) as f:
                nanobot_data = json.load(f)
            nanobot_defaults = nanobot_data.get("agents", {}).get("defaults", {})
            nanobot_providers = nanobot_data.get("providers", {})
            nanobot_config = nanobot_data
        except Exception as exc:
            logger.warning("failed to load nanobot config %s: %s", nanobot_config_path, exc)

    # 获取 provider 名称
    provider_name = os.getenv("LLM_PROVIDER") or settings.llm_provider
    
    # 根据 provider 获取对应的 API Key
    # 优先级: 环境变量 > .nanobot/config.json > settings
    provider_api_key_map = {
        "dashscope": "DASHSCOPE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "moonshot": "MOONSHOT_API_KEY",
        "minimax": "MINIMAX_API_KEY",
    }
    
    # provider 默认 base_url（如果为 None 则使用 litellm 默认）
    provider_default_base_url = {
        "dashscope": None,
        "openrouter": "https://openrouter.ai/api/v1",
        "openai": None,
        "anthropic": None,
        "google": None,
        "moonshot": None,
        "minimax": None,
    }
    
    env_api_key = os.getenv(provider_api_key_map.get(provider_name, "OPENROUTER_API_KEY"))
    
    # 从 nanobot_providers 获取 API Key
    provider_config = nanobot_providers.get(provider_name, {})
    config_api_key = provider_config.get("apiKey")
    config_api_base = provider_config.get("apiBase") or provider_default_base_url.get(provider_name)
    
    # 从 settings 获取 fallback
    settings_api_key = settings.openrouter_api_key
    
    api_key = env_api_key or config_api_key or settings_api_key
    env_base_url = os.getenv(f"{provider_name.upper()}_BASE_URL")
    api_base = env_base_url or config_api_base or provider_default_base_url.get(provider_name)

    if not api_key:
        raise RuntimeError(f"{provider_api_key_map.get(provider_name, 'OPENROUTER_API_KEY')} not set (check .env or env vars)")

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

    # 初始化 Agent - 优先级: 环境变量 > settings > ~/.nanobot/config.json
    model = os.getenv("MODEL") or settings.model
    agent_provider = provider_name
    
    if not os.getenv("MODEL") and nanobot_defaults:
        default_model = nanobot_defaults.get("model", "")
        default_provider = nanobot_defaults.get("provider", provider_name)
        if default_model:
            # 根据 provider 添加前缀
            if default_provider == "dashscope":
                model = f"dashscope/{default_model}"
            elif default_provider == "openrouter":
                model = f"openrouter/{default_model}"
            else:
                model = default_model
        agent_provider = default_provider
        
        # 如果 agent 的 provider 和初始 provider 不同，重新创建 provider
        if agent_provider != provider_name:
            agent_provider_config = nanobot_providers.get(agent_provider, {})
            agent_api_key = (
                os.getenv(provider_api_key_map.get(agent_provider, "OPENROUTER_API_KEY"))
                or agent_provider_config.get("apiKey")
                or api_key
            )
            agent_env_base_url = os.getenv(f"{agent_provider.upper()}_BASE_URL")
            agent_default_base_url = provider_default_base_url.get(agent_provider)
            agent_api_base = (
                agent_env_base_url
                or agent_provider_config.get("apiBase")
                or agent_default_base_url
            )
            _provider = LiteLLMProvider(
                api_key=agent_api_key,
                api_base=agent_api_base,
                default_model=model,
                provider_name=agent_provider,
            )

    _agent = AgentLoop(
        bus=_bus,
        provider=_provider,
        workspace=workspace,
        model=model,
        session_manager=_session_mgr,
        mcp_servers=_convert_mcp_servers(nanobot_config.get("tools", {}).get("mcpServers", {})),
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
