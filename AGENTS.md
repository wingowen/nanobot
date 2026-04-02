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
│   │   ├── memory.py           # 会话记忆管理
│   │   ├── skills.py           # 技能加载
│   │   └── tools/              # 内置工具（cron, mcp, web 等）
│   ├── bus/                    # 事件总线
│   ├── channels/               # IM 通道（Telegram, Slack, Discord, 飞书等）
│   ├── cli/                    # 命令行入口
│   ├── config/                 # 配置管理
│   ├── cron/                   # 定时任务
│   ├── heartbeat/              # 心跳服务
│   ├── providers/              # LLM 提供商（OpenAI, Azure, MiniMax 等）
│   ├── security/               # 安全模块
│   ├── session/                # 会话管理
│   ├── skills/                 # 内置技能
│   └── utils/                  # 工具函数
├── http_api/                   # HTTP REST API 封装
│   ├── main.py                 # FastAPI 入口
│   ├── routers/                # 路由（chat, sessions, tools）
│   ├── core/                   # 核心模块（配置、模型、依赖）
│   └── requirements.txt        # HTTP API 额外依赖
├── bridge/                     # WhatsApp 桥接（Node.js）
├── tests/                      # 测试用例
├── docker-compose.yml          # Docker 编排
├── Dockerfile                  # 主 Dockerfile
├── config.yaml                 # 示例配置
└── pyproject.toml              # 项目配置
```

## 核心组件

### 1. Agent 系统
- **AgentLoop** (`agent/loop.py`): 核心循环，处理消息和工具调用
- **Memory** (`agent/memory.py`): 基于 token 的会话记忆
- **Skills** (`agent/skills.py`): 动态加载技能系统

### 2. HTTP API
- FastAPI 封装，OpenAI 兼容格式
- 支持流式输出（SSE）
- API Key 认证 + CORS + 速率限制

### 3. 通道系统
- 支持: Telegram, Discord, Slack, 飞书, 钉钉, QQ, WeCom, Matrix
- 每个通道独立实现消息收发

### 4. 提供商系统
- 基于 LiteLLM，支持 100+ LLM
- 主要: OpenAI, Azure, Anthropic, MiniMax, DeepSeek, Moonshot

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

# 运行特定测试
pytest tests/test_<module>.py
```

### 代码规范
- **Linter**: ruff
- **格式化**: 100 字符行宽
- **类型检查**: Python 3.11+ 类型提示

## 常见操作

### 添加新通道
1. 在 `nanobot/channels/` 创建新文件
2. 实现 `BaseChannel` 接口
3. 在 `config.yaml` 启用通道

### 添加新提供商
1. 在 `nanobot/providers/` 创建提供商类
2. 继承 `BaseProvider`
3. 在 `registry.py` 注册

### 修改 HTTP API
- 路由: `http_api/routers/`
- 模型: `http_api/core/models.py`
- 配置: `http_api/core/config.py`

## 注意事项

1. **敏感信息**: 不要提交 `.env` 文件或 API keys
2. **Worktree**: 当前是 worktree 配置，推送到远程需要认证
3. **依赖**: HTTP API 有额外依赖 (`http_api/requirements.txt`)
4. **Docker**: 主 Dockerfile 包含 WhatsApp bridge 的 Node.js 构建
5. **测试**: 使用 `pytest-asyncio`，异步测试自动模式
6. **Git 工作流**: main 分支仅同步上游 Fork，开发在 dev 分支进行，通过 PR 合并到 main

## 相关资源

- **文档**: `README.md`, `http_api/README.md`
- **架构图**: `nanobot_arch.png`
- **交流群**: 见 `COMMUNICATION.md`
- **PyPI**: https://pypi.org/project/nanobot-ai/
