# AGENTS.md - nanobot 项目指南

## 项目概述

**nanobot** 是一个超轻量级的个人 AI 助手框架，灵感来自 OpenClaw，代码量减少 99%。

- **仓库**: https://github.com/wingowen/nanobot
- **版本**: v0.1.4.post5
- **Python**: >=3.11
- **许可证**: MIT

## 项目结构

```
nanobot-github-dev/
├── nanobot/                    # 核心代码
│   ├── agent/                  # Agent 循环、记忆、技能
│   │   ├── loop.py             # AgentLoop 核心逻辑
│   │   ├── context.py          # 上下文构建器
│   │   ├── hook.py             # AgentHook 生命周期钩子
│   │   ├── runner.py           # AgentRunner 执行器
│   │   ├── memory.py           # 会话记忆管理
│   │   ├── skills.py           # 技能加载
│   │   ├── subagent.py         # 子代理管理
│   │   └── tools/              # 内置工具（cron, mcp, web 等）
│   ├── api/                    # Python SDK API
│   │   └── server.py           # API 服务器
│   ├── bus/                    # 事件总线
│   ├── channels/               # IM 通道
│   │   ├── telegram.py         # Telegram
│   │   ├── discord.py          # Discord
│   │   ├── slack.py            # Slack
│   │   ├── feishu.py           # 飞书
│   │   ├── dingtalk.py         # 钉钉
│   │   ├── qq.py               # QQ
│   │   ├── wecom.py            # 企业微信
│   │   ├── weixin.py           # 微信（新增）
│   │   ├── matrix.py           # Matrix
│   │   └── whatsapp.py         # WhatsApp
│   ├── cli/                    # 命令行入口
│   │   ├── commands.py         # CLI 命令
│   │   ├── models.py           # 模型信息
│   │   ├── onboard.py          # 引导向导
│   │   └── stream.py           # 流式输出
│   ├── command/                # 命令路由系统（新增）
│   │   ├── router.py           # CommandRouter 路由器
│   │   └── builtin.py          # 内置命令
│   ├── config/                 # 配置管理
│   │   ├── schema.py           # 配置 schema
│   │   └── paths.py            # 路径工具
│   ├── cron/                   # 定时任务
│   ├── heartbeat/              # 心跳服务
│   ├── providers/              # LLM 提供商
│   │   ├── base.py             # 基类
│   │   ├── registry.py         # 提供商注册表
│   │   ├── openai_compat_provider.py  # OpenAI 兼容（通用）
│   │   ├── anthropic_provider.py       # Anthropic（新增）
│   │   ├── azure_openai_provider.py    # Azure OpenAI
│   │   ├── openai_codex_provider.py    # OpenAI Codex
│   │   └── github_copilot_provider.py  # GitHub Copilot（新增）
│   ├── security/               # 安全模块
│   ├── session/                # 会话管理
│   │   └── manager.py          # SessionManager
│   ├── skills/                 # 内置技能
│   └── utils/                  # 工具函数
├── http_api/                   # HTTP REST API 封装（dev 分支）
│   ├── main.py                 # FastAPI 入口
│   ├── routers/                # 路由（chat, sessions, tools）
│   ├── core/                   # 核心模块（配置、模型、依赖）
│   └── requirements.txt        # HTTP API 额外依赖
├── bridge/                     # WhatsApp 桥接（Node.js）
├── docs/                       # 文档
│   ├── CHANNEL_PLUGIN_GUIDE.md # 通道插件指南
│   └── PYTHON_SDK.md           # Python SDK 文档
├── tests/                      # 测试用例（按模块组织）
│   ├── agent/                  # Agent 测试
│   ├── channels/               # 通道测试
│   ├── cli/                    # CLI 测试
│   ├── config/                 # 配置测试
│   ├── cron/                   # 定时任务测试
│   ├── providers/              # 提供商测试
│   ├── security/               # 安全测试
│   └── tools/                  # 工具测试
├── docker-compose.yml          # Docker 编排
├── Dockerfile                  # 主 Dockerfile
├── config.yaml                 # 示例配置
└── pyproject.toml              # 项目配置
```

## 核心组件

### 1. Agent 系统（已重构）
- **AgentLoop** (`agent/loop.py`): 核心循环，处理消息和工具调用
- **AgentHook** (`agent/hook.py`): 生命周期钩子，处理流式输出、进度报告
- **AgentRunner** (`agent/runner.py`): 执行器，管理 Agent 运行
- **ContextBuilder** (`agent/context.py`): 上下文构建器
- **Memory** (`agent/memory.py`): 基于 token 的会话记忆
- **SubagentManager** (`agent/subagent.py`): 子代理管理
- **CommandRouter** (`command/router.py`): 模块化命令路由系统

### 2. HTTP API（dev 分支特有）
- FastAPI 封装，OpenAI 兼容格式
- 支持流式输出（SSE）
- API Key 认证 + CORS + 速率限制

### 3. 通道系统
- **支持通道**: Telegram, Discord, Slack, 飞书, 钉钉, QQ, 企业微信, 微信, Matrix, WhatsApp
- 每个通道独立实现消息收发
- 支持通道插件系统

### 4. 提供商系统（已重构）
- **注册表模式**: `providers/registry.py` 中的 `PROVIDERS` 元组
- **通用后端**: `openai_compat_provider.py` 覆盖大部分 OpenAI 兼容 API
- **专用后端**: Anthropic、Azure OpenAI、GitHub Copilot
- **添加新提供商**: 只需在 `PROVIDERS` 中添加 `ProviderSpec`

### 5. 命令系统（新增）
- `CommandRouter`: 模块化命令分发
- 内置命令: `/new`, `/help`, `/stop`, `/restart`
- 支持自定义命令注册

## 操作注意事项

### Git 工作流
- **main 分支**: 仅用于同步上游 Fork，**不要直接修改**
- **dev 分支**: 主要开发分支，所有功能在此开发
- **当前环境**: Worktree 配置，主仓库在 `~/code/nanobot-github`

**⚠️ 重要**: main 分支用于同步上游仓库，只能通过 PR 从 dev 合并到 main

### 部署配置
```bash
# 启动 HTTP API
./start_http_api.sh

# 测试 HTTP API
./test_http_api.sh

# Docker 部署
docker compose up -d
```

### 端口分配
- `18790`: Gateway (主服务)
- `18791`: HTTP API
- `18792`: HTTP API (Docker 内部)
- `18798-18799`: Docker 映射端口

### 配置文件
- **config.yaml**: 主配置（providers, agents, tools, channels）
- **.env**: 环境变量（API keys）
- **http_api/.env.example**: HTTP API 配置模板

### 测试
```bash
# 运行所有测试
pytest tests/

# 运行特定模块测试
pytest tests/agent/
pytest tests/channels/
pytest tests/providers/
```

### 代码规范
- **Linter**: ruff
- **格式化**: 100 字符行宽
- **类型检查**: Python 3.11+ 类型提示

## 常见操作

### 添加新通道
1. 在 `nanobot/channels/` 创建新文件
2. 继承 `BaseChannel` 接口
3. 在 `config.yaml` 启用通道
4. 参考 `docs/CHANNEL_PLUGIN_GUIDE.md`

### 添加新提供商
1. 在 `providers/registry.py` 添加 `ProviderSpec`
2. 如需特殊处理，创建专用 provider 文件
3. 更新 `config/schema.py` 添加配置字段

### 修改 HTTP API
- 路由: `http_api/routers/`
- 模型: `http_api/core/models.py`
- 配置: `http_api/core/config.py`

### 添加新命令
1. 在 `command/builtin.py` 添加命令实现
2. 使用 `CommandRouter` 注册

## 注意事项

1. **敏感信息**: 不要提交 `.env` 文件或 API keys
2. **Worktree**: 当前是 worktree 配置，推送到远程需要认证
3. **依赖**: HTTP API 有额外依赖 (`http_api/requirements.txt`)
4. **Docker**: 主 Dockerfile 包含 WhatsApp bridge 的 Node.js 构建
5. **测试**: 使用 `pytest-asyncio`，异步测试自动模式
6. **Git 工作流**: main 分支仅同步上游 Fork，开发在 dev 分支进行，通过 PR 合并到 main
7. **提供商系统**: 已从 LiteLLM 重构为 OpenAI 兼容模式，使用注册表管理

## 相关资源

- **文档**: `README.md`, `http_api/README.md`, `docs/`
- **架构图**: `nanobot_arch.png`
- **交流群**: 见 `COMMUNICATION.md`
- **PyPI**: https://pypi.org/project/nanobot-ai/

## 最近更新（2026-04-02）

### 合并 main 分支
- 新增 CommandRouter 模块化命令系统
- 新增 AgentHook、AgentRunner 生命周期管理
- 新增 Anthropic、GitHub Copilot 提供商
- 新增微信通道
- 测试目录重组（按模块分类）
- 提供商系统重构为注册表模式

### HTTP API 清理（dev 分支）
- 移除冗余文件（前端、客户端库、重复配置）
- 保留核心 API 功能
- 更新 README 同步项目结构
