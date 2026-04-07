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


def _resolve_provider(provider_name: str, nanobot_providers: dict, fallback_api_key: str | None = None):
    """Resolve provider spec, api_key, api_base using the new registry."""
    import os
    from nanobot.providers.registry import find_by_name

    spec = find_by_name(provider_name)
    backend = spec.backend if spec else "openai_compat"

    provider_config = nanobot_providers.get(provider_name, {})
    env_key = spec.env_key if spec else "OPENROUTER_API_KEY"
    api_key = os.getenv(env_key) if env_key else None
    api_key = api_key or provider_config.get("apiKey") or fallback_api_key

    api_base = os.getenv(f"{provider_name.upper()}_BASE_URL") if provider_name else None
    api_base = api_base or provider_config.get("apiBase")
    if spec and spec.default_api_base and not api_base:
        api_base = spec.default_api_base

    return backend, spec, api_key, api_base


def _create_provider(backend: str, spec, api_key: str, api_base: str, default_model: str):
    """Create the appropriate provider instance based on backend type."""
    if backend == "anthropic":
        from nanobot.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(
            api_key=api_key, api_base=api_base, default_model=default_model,
        )
    elif backend == "azure_openai":
        from nanobot.providers.azure_openai_provider import AzureOpenAIProvider
        return AzureOpenAIProvider(
            api_key=api_key, api_base=api_base, default_model=default_model,
        )
    elif backend == "openai_codex":
        from nanobot.providers.openai_codex_provider import OpenAICodexProvider
        return OpenAICodexProvider(default_model=default_model)
    elif backend == "github_copilot":
        from nanobot.providers.github_copilot_provider import GitHubCopilotProvider
        return GitHubCopilotProvider(default_model=default_model)
    else:
        from nanobot.providers.openai_compat_provider import OpenAICompatProvider
        return OpenAICompatProvider(
            api_key=api_key,
            api_base=api_base,
            default_model=default_model,
            spec=spec,
        )


def initialize_app():
    """初始化应用状态"""
    global _bus, _session_mgr, _agent, _provider

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

    # Resolve provider using new registry
    backend, spec, api_key, api_base = _resolve_provider(
        provider_name, nanobot_providers, settings.openrouter_api_key
    )

    if not api_key:
        env_key = spec.env_key if spec else "OPENROUTER_API_KEY"
        raise RuntimeError(f"{env_key} not set (check .env or env vars)")

    model = os.getenv("MODEL") or settings.model

    _provider = _create_provider(backend, spec, api_key, api_base, model)

    # 初始化 Bus
    _bus = MessageBus()

    # 初始化 SessionManager
    workspace = Path(os.getenv("WORKSPACE") or settings.nanobot_workspace or "/app/workspace")
    ensure_dir(workspace)
    _session_mgr = SessionManager(workspace=workspace)

    # 如果 ~/.nanobot/config.json 中有不同的 model/provider，重新创建
    agent_provider = provider_name
    if not os.getenv("MODEL") and nanobot_defaults:
        default_model = nanobot_defaults.get("model", "")
        default_provider = nanobot_defaults.get("provider", provider_name)
        if default_model:
            if default_provider == "dashscope":
                model = f"dashscope/{default_model}"
            elif default_provider == "openrouter":
                model = f"openrouter/{default_model}"
            else:
                model = default_model
        agent_provider = default_provider

        if agent_provider != provider_name:
            agent_backend, agent_spec, agent_api_key, agent_api_base = _resolve_provider(
                agent_provider, nanobot_providers, api_key
            )
            _provider = _create_provider(
                agent_backend, agent_spec, agent_api_key, agent_api_base, model
            )

    _agent = AgentLoop(
        bus=_bus,
        provider=_provider,
        workspace=workspace,
        model=model,
        session_manager=_session_mgr,
        context_window_tokens=nanobot_defaults.get("context_window_tokens", 128_000),
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
