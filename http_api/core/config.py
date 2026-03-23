"""HTTP API 配置"""

import json
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


def load_nanobot_config() -> dict:
    """加载 ~/.nanobot/config.json 配置"""
    config_path = Path("/root/.nanobot/config.json")
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


class Settings(BaseSettings):
    """API 配置设置"""

    # API Server (支持 API_HOST/API_PORT 或 host/port)
    host: str = Field("0.0.0.0", description="监听地址")
    port: int = Field(18791, description="监听端口")
    debug: bool = Field(False, description="调试模式")
    api_host: Optional[str] = Field(None, description="API_HOST 别名")
    api_port: Optional[int] = Field(None, description="API_PORT 别名")

    # CORS 配置 (支持 ALLOWED_ORIGINS 或 cors_origins)
    cors_origins: str = Field("*", description="允许的CORS源，逗号分隔")
    allowed_origins: Optional[str] = Field(None, description="ALLOWED_ORIGINS 别名")

    # API 认证
    api_key: str = Field(..., description="HTTP API API Key")

    # LLM 配置
    llm_provider: str = Field("openrouter", description="LLM 提供商")
    openrouter_api_key: Optional[str] = Field(None, description="OpenRouter API Key")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", description="OpenRouter Base URL")
    model: str = Field("openrouter/stepfun/step-3.5-flash:free", description="默认模型")

    # NanoBOT Core (支持 NANOBOT_CONFIG/NANOBOT_WORKSPACE)
    nanobot_config: str = Field("/app/config.yaml", description="NanoBOT 配置文件路径")
    nanobot_workspace: str = Field("/app/workspace", description="NanoBOT 工作空间路径")
    workspace: Optional[str] = Field(None, description="workspace 别名")

    # Session 配置
    session_type: str = Field("memory", description="Session 存储类型: memory/sqlite/redis")
    session_ttl: int = Field(86400, description="Session TTL（秒）")

    # 速率限制
    rate_limit_enabled: bool = Field(True, description="是否启用速率限制")
    rate_limit_requests: int = Field(100, description="每分钟请求数")
    rate_limit_window: int = Field(60, description="速率限制窗口（秒）")

    # 日志
    log_level: str = Field("INFO", description="日志级别")
    log_format: Optional[str] = Field(None, description="LOG_FORMAT 别名")

    def __init__(self, **kwargs):
        # 加载 nanobot config.json
        nanobot_config = load_nanobot_config()
        
        # 如果没有提供 openrouter_api_key，尝试从 config.json 获取
        agents = nanobot_config.get("agents", {})
        defaults = agents.get("defaults", {})
        provider_name = defaults.get("provider", "dashscope")
        providers = nanobot_config.get("providers", {})
        provider_config = providers.get(provider_name, {})
        
        if not kwargs.get("openrouter_api_key"):
            kwargs["openrouter_api_key"] = provider_config.get("apiKey")
        
        if not kwargs.get("model") or kwargs["model"] == "openrouter/stepfun/step-3.5-flash:free":
            model = defaults.get("model", "")
            if model:
                if provider_name == "openrouter":
                    kwargs["model"] = f"openrouter/{model}"
                elif provider_name == "dashscope":
                    kwargs["model"] = f"dashscope/{model}"
        
        if not kwargs.get("llm_provider"):
            kwargs["llm_provider"] = provider_name
        
        super().__init__(**kwargs)

    @field_validator('port', mode='before')
    @classmethod
    def validate_port(cls, v, info):
        """处理 API_PORT 环境变量（可能是字符串）"""
        if v is None and info.data.get('api_port') is not None:
            return info.data['api_port']
        return v

    @field_validator('host', mode='before')
    @classmethod
    def validate_host(cls, v, info):
        """处理 API_HOST 环境变量"""
        if v is None and info.data.get('api_host') is not None:
            return info.data['api_host']
        return v

    @field_validator('cors_origins', mode='before')
    @classmethod
    def validate_cors(cls, v, info):
        """处理 ALLOWED_ORIGINS 环境变量"""
        if v is None and info.data.get('allowed_origins') is not None:
            return info.data['allowed_origins']
        return v

    @field_validator('workspace', mode='before')
    @classmethod
    def validate_workspace(cls, v, info):
        """处理 NANOBOT_WORKSPACE 环境变量"""
        if v is None and info.data.get('nanobot_workspace') is not None:
            return info.data['nanobot_workspace']
        return v

    class Config:
        env_file = "./http_api/.env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # 环境变量不区分大小写（可选）


# 全局配置实例（懒加载）
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置（单例）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings