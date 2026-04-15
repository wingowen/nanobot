# 系统提示词注入分析

## 1. 概述

本文档详细分析了 nanobot 系统中注入的提示词（Prompts），包括硬编码的提示词和通过文件注入的提示词。

## 2. 通过文件注入的提示词

### 2.1 核心引导文件（BOOTSTRAP_FILES）

这些文件在系统启动时被加载，构成了代理的基本指令集：

| 文件名 | 路径 | 作用 |
|--------|------|------|
| AGENTS.md | [nanobot/templates/AGENTS.md](file:///workspace/nanobot/templates/AGENTS.md) | 代理指令，包含提醒和心跳任务的使用指南 |
| SOUL.md | [nanobot/templates/SOUL.md](file:///workspace/nanobot/templates/SOUL.md) | 定义代理的人格、价值观和沟通风格 |
| USER.md | [nanobot/templates/USER.md](file:///workspace/nanobot/templates/USER.md) | 用户配置文件，包含用户基本信息和偏好设置 |
| TOOLS.md | [nanobot/templates/TOOLS.md](file:///workspace/nanobot/templates/TOOLS.md) | 工具使用说明和约束 |

### 2.2 代理模板文件

这些文件定义了代理的身份和行为：

| 文件名 | 路径 | 作用 |
|--------|------|------|
| identity.md | [nanobot/templates/agent/identity.md](file:///workspace/nanobot/templates/agent/identity.md) | 核心身份信息，包含运行时环境和工作空间信息 |
| platform_policy.md | [nanobot/templates/agent/platform_policy.md](file:///workspace/nanobot/templates/agent/platform_policy.md) | 平台特定的政策和指导 |
| skills_section.md | [nanobot/templates/agent/skills_section.md](file:///workspace/nanobot/templates/agent/skills_section.md) | 技能部分的模板 |
| consolidator_archive.md | [nanobot/templates/agent/consolidator_archive.md](file:///workspace/nanobot/templates/agent/consolidator_archive.md) | 整合器存档模板 |
| dream_phase1.md | [nanobot/templates/agent/dream_phase1.md](file:///workspace/nanobot/templates/agent/dream_phase1.md) | 梦想阶段1模板 |
| dream_phase2.md | [nanobot/templates/agent/dream_phase2.md](file:///workspace/nanobot/templates/agent/dream_phase2.md) | 梦想阶段2模板 |
| evaluator.md | [nanobot/templates/agent/evaluator.md](file:///workspace/nanobot/templates/agent/evaluator.md) | 评估器模板 |
| max_iterations_message.md | [nanobot/templates/agent/max_iterations_message.md](file:///workspace/nanobot/templates/agent/max_iterations_message.md) | 最大迭代消息模板 |
| subagent_announce.md | [nanobot/templates/agent/subagent_announce.md](file:///workspace/nanobot/templates/agent/subagent_announce.md) | 子代理公告模板 |
| subagent_system.md | [nanobot/templates/agent/subagent_system.md](file:///workspace/nanobot/templates/agent/subagent_system.md) | 子代理系统模板 |
| untrusted_content.md | [nanobot/templates/agent/_snippets/untrusted_content.md](file:///workspace/nanobot/templates/agent/_snippets/untrusted_content.md) | 不可信内容处理指南 |

### 2.3 内存和心跳模板

| 文件名 | 路径 | 作用 |
|--------|------|------|
| MEMORY.md | [nanobot/templates/memory/MEMORY.md](file:///workspace/nanobot/templates/memory/MEMORY.md) | 长期记忆模板 |
| HEARTBEAT.md | [nanobot/templates/HEARTBEAT.md](file:///workspace/nanobot/templates/HEARTBEAT.md) | 心跳任务模板 |

## 3. 硬编码的提示词

### 3.1 核心系统硬编码提示词

| 位置 | 提示词内容 | 作用 |
|------|-----------|------|
| [ContextBuilder._RUNTIME_CONTEXT_TAG](file:///workspace/nanobot/agent/context.py#L21) | `[Runtime Context — metadata only, not instructions]` | 运行时上下文标签 |
| [ContextBuilder._build_runtime_context](file:///workspace/nanobot/agent/context.py#L70) | 构建包含当前时间、通道和聊天ID的运行时上下文 | 提供运行时元数据 |

### 3.2 工具相关硬编码提示词

| 工具 | 提示词内容 | 作用 |
|------|-----------|------|
| [CronTool](file:///workspace/nanobot/agent/tools/cron.py) | `Tool to schedule reminders and recurring tasks.` |  cron 工具描述 |
| [CronTool 参数说明](file:///workspace/nanobot/agent/tools/cron.py#L13) | 详细的参数说明和示例 | 指导用户如何使用 cron 工具 |

### 3.3 系统消息和警告

| 位置 | 提示词内容 | 作用 |
|------|-----------|------|
| [_warn_deprecated_config_keys](file:///workspace/nanobot/cli/commands.py#L491) | `Hint: `memoryWindow` in your config is no longer used and can be safely removed.` | 弃用配置键的警告 |

## 4. 提示词注入流程

### 4.1 系统提示词构建流程

1. **核心身份**：加载 [identity.md](file:///workspace/nanobot/templates/agent/identity.md) 模板，包含运行时环境和工作空间信息
2. **引导文件**：加载 [AGENTS.md](file:///workspace/nanobot/templates/AGENTS.md)、[SOUL.md](file:///workspace/nanobot/templates/SOUL.md)、[USER.md](file:///workspace/nanobot/templates/USER.md)、[TOOLS.md](file:///workspace/nanobot/templates/TOOLS.md)
3. **记忆上下文**：从内存存储中获取记忆上下文
4. **技能信息**：加载始终激活的技能和技能摘要
5. **运行时上下文**：在用户消息前注入运行时元数据

### 4.2 提示词注入位置

- **系统提示**：在每次会话开始时构建，包含所有引导文件和模板内容
- **运行时上下文**：在每个用户消息前注入，包含时间、通道和聊天ID信息
- **工具调用**：工具描述和参数说明在工具使用时提供

## 5. 自定义和扩展

### 5.1 可自定义的提示词

用户可以通过编辑以下文件来自定义代理行为：

- [USER.md](file:///workspace/nanobot/templates/USER.md)：用户配置文件
- [SOUL.md](file:///workspace/nanobot/templates/SOUL.md)：人格和价值观
- [SKILL.md](file:///workspace/nanobot/skills/README.md)：自定义技能描述

### 5.2 扩展提示词

- **新技能**：在 `skills/{skill-name}/SKILL.md` 中添加技能描述
- **自定义模板**：修改现有的模板文件
- **记忆更新**：系统会自动更新 [MEMORY.md](file:///workspace/nanobot/templates/memory/MEMORY.md) 以存储重要信息

## 6. 总结

| 类型 | 数量 | 位置 | 可定制性 |
|------|------|------|----------|
| 通过文件注入的提示词 | 16+ | `nanobot/templates/` 目录 | 高（可编辑） |
| 硬编码的提示词 | 5+ | 代码中直接定义 | 低（需修改代码） |

nanobot 系统采用了混合的提示词注入方式，既通过文件系统提供了高度可定制的提示词模板，又在代码中硬编码了一些核心的系统提示词。这种设计使得系统既灵活又稳定，用户可以根据自己的需求定制代理行为，同时系统核心功能保持一致。

## 7. 代码引用

- [ContextBuilder 类](file:///workspace/nanobot/agent/context.py)：负责构建系统提示和上下文
- [模板目录](file:///workspace/nanobot/templates/)：包含所有通过文件注入的提示词模板
- [CronTool 类](file:///workspace/nanobot/agent/tools/cron.py)：包含工具相关的硬编码提示词
