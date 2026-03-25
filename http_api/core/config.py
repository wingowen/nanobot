"""HTTP API 配置"""

import json
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging
from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_ENV_LOADED = False
logger = logging.getLogger(__name__)


def load_env_files() -> None:
    """Load HTTP API env files once with explicit precedence."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")
    load_dotenv(project_root / ".env.api", override=True)
    _ENV_LOADED = True


load_env_files()


def load_nanobot_config() -> dict:
    """加载 nanobot 配置 (~/.nanobot/config.json)"""
    config_path = os.getenv("NANOBOT_CONFIG_JSON")
    if not config_path:
        config_path = str(Path.home() / ".nanobot" / "config.json")
    
    config_file = Path(config_path)
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("failed to load nanobot config: %s (%s)", config_file, exc)
    return {}


class Settings(BaseSettings):
    """API 配置设置"""

    # API Server (支持 API_HOST/API_PORT 或 host/port)
    host: str = Field(
        "0.0.0.0",
        description="监听地址",
        validation_alias=AliasChoices("API_HOST", "HOST", "host"),
    )
    port: int = Field(
        18791,
        description="监听端口",
        validation_alias=AliasChoices("API_PORT", "PORT", "port"),
    )
    debug: bool = Field(False, description="调试模式")

    # CORS 配置 (支持 ALLOWED_ORIGINS 或 cors_origins)
    cors_origins: str = Field(
        "*",
        description="允许的CORS源，逗号分隔",
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "CORS_ORIGINS", "cors_origins"),
    )

    # API 认证
    api_key: str = Field(
        ...,
        description="HTTP API API Key",
        validation_alias=AliasChoices("API_KEY", "api_key"),
    )

    # LLM 配置
    llm_provider: str = Field(
        "openrouter",
        description="LLM 提供商",
        validation_alias=AliasChoices("LLM_PROVIDER", "llm_provider"),
    )
    openrouter_api_key: Optional[str] = Field(
        None,
        description="OpenRouter API Key",
        validation_alias=AliasChoices("OPENROUTER_API_KEY", "openrouter_api_key"),
    )
    openrouter_base_url: str = Field(
        "https://openrouter.ai/api/v1",
        description="OpenRouter Base URL",
        validation_alias=AliasChoices("OPENROUTER_BASE_URL", "openrouter_base_url"),
    )
    model: str = Field(
        "openrouter/stepfun/step-3.5-flash:free",
        description="默认模型",
        validation_alias=AliasChoices("MODEL", "model"),
    )

    # NanoBOT Core
    nanobot_workspace: str = Field(
        "~/.nanobot/workspace",
        description="NanoBOT 工作空间路径",
        validation_alias=AliasChoices("WORKSPACE", "NANOBOT_WORKSPACE", "nanobot_workspace"),
    )

    # Session 配置
    session_type: str = Field("memory", description="Session 存储类型: memory/sqlite/redis")
    session_ttl: int = Field(86400, description="Session TTL（秒）")

    # 速率限制
    rate_limit_enabled: bool = Field(
        True,
        description="是否启用速率限制",
        validation_alias=AliasChoices("RATE_LIMIT_ENABLED", "rate_limit_enabled"),
    )
    rate_limit_requests: int = Field(
        100,
        description="每分钟请求数",
        validation_alias=AliasChoices("RATE_LIMIT_REQUESTS", "rate_limit_requests"),
    )
    rate_limit_window: int = Field(
        60,
        description="速率限制窗口（秒）",
        validation_alias=AliasChoices("RATE_LIMIT_WINDOW", "rate_limit_window"),
    )

    # 日志
    log_level: str = Field("INFO", description="日志级别")
    log_format: Optional[str] = Field(None, description="LOG_FORMAT 别名")

    @model_validator(mode="after")
    def apply_nanobot_config_fallback(self) -> "Settings":
        """从 ~/.nanobot/config.json 回填缺失字段，不覆盖环境变量/显式输入。"""
        nanobot_config = load_nanobot_config()

        agents = nanobot_config.get("agents", {})
        defaults = agents.get("defaults", {})
        provider_name = defaults.get("provider", "openrouter")
        providers = nanobot_config.get("providers", {})
        provider_config = providers.get(provider_name, {})

        if "openrouter_api_key" not in self.model_fields_set and not self.openrouter_api_key:
            self.openrouter_api_key = provider_config.get("apiKey")

        if "llm_provider" not in self.model_fields_set:
            self.llm_provider = provider_name or self.llm_provider

        if "model" not in self.model_fields_set:
            model = defaults.get("model", "")
            if model:
                if provider_name == "openrouter":
                    self.model = f"openrouter/{model}"
                elif provider_name == "dashscope":
                    self.model = f"dashscope/{model}"
                elif provider_name == "minimax":
                    self.model = f"minimax/{model}"

        return self

    model_config = SettingsConfigDict(
        env_file="./http_api/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# 全局配置实例（懒加载）
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置（单例）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
