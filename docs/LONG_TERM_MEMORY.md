# Mori 长期记忆功能使用指南

本文档详细介绍如何在 Mori 项目中使用长期记忆功能。

## 概述

Mori 的长期记忆功能基于 AgentScope 的 `Mem0LongTermMemory` 实现，允许 Agent 记住用户的偏好、习惯和重要信息，使对话更加个性化和连贯。

### 主要特性

- ✅ **多嵌入模型支持**: DashScope、OpenAI、Gemini、Ollama
- ✅ **灵活的记忆模式**: Agent 自主管理或开发者控制
- ✅ **持久化存储**: 支持磁盘存储，重启后记忆不丢失
- ✅ **用户隔离**: 通过 user_name 区分不同用户的记忆
- ✅ **自动工具注册**: Agent 自动获得记忆管理工具

## 快速开始

### 1. 配置嵌入模型

在 `config/models.yaml` 中添加嵌入模型配置：

```yaml
# 嵌入模型配置
embedding_models:
  # DashScope 嵌入模型（推荐）
  - model_name: text-embedding-v2
    model_type: dashscope
    api_key: ${DASHSCOPE_API_KEY}

  # OpenAI 嵌入模型
  - model_name: text-embedding-3-small
    model_type: openai
    api_key: ${OPENAI_API_KEY}
    dimensions: 1536
```

### 2. 配置 Agent 长期记忆

在 `config/agents.yaml` 中为 Agent 添加长期记忆配置：

```yaml
agents:
  - name: mori
    model: gpt-4
    template: mori
    sys_prompt: null
    memory_config:
      type: memory
      max_length: 100
    parallel_tool_calls: true

    # 长期记忆配置
    long_term_memory:
      enabled: true                      # 启用长期记忆
      mode: "agent_control"              # 记忆管理模式
      user_name: "default_user"          # 用户标识
      embedding_model: "text-embedding-v2"  # 嵌入模型名称
      storage_path: "data/memory"        # 存储路径
      on_disk: true                      # 持久化存储
```

### 3. 设置环境变量

确保设置了相应的 API 密钥：

```bash
# DashScope (阿里云)
export DASHSCOPE_API_KEY="your_dashscope_api_key"

# OpenAI
export OPENAI_API_KEY="your_openai_api_key"
```

### 4. 运行 Mori

```python
import asyncio
from mori.mori import Mori

async def main():
    # 初始化 Mori（会自动加载长期记忆配置）
    mori = Mori(config_dir="config")

    # 开始对话
    response = await mori.chat("我喜欢喝咖啡")
    print(response)

    # Agent 会自动记录这个偏好
    # 下次对话时可以检索到这个信息

if __name__ == "__main__":
    asyncio.run(main())
```

## 配置详解

### 记忆管理模式

长期记忆支持三种管理模式：

#### 1. agent_control（推荐）

Agent 自主决定何时记录和检索记忆。

```yaml
long_term_memory:
  enabled: true
  mode: "agent_control"
  # ... 其他配置
```

**特点**：
- Agent 自动判断何时需要记录信息
- Agent 自动在需要时检索相关记忆
- 需要在系统提示词中说明记忆管理指南

**适用场景**：
- 日常对话场景
- 需要 Agent 自主管理记忆的场景

#### 2. static_control

开发者通过代码显式控制记忆操作。

```yaml
long_term_memory:
  enabled: true
  mode: "static_control"
  # ... 其他配置
```

**特点**：
- 开发者完全控制何时记录和检索
- 需要手动调用记忆方法
- 更精确的控制

**适用场景**：
- 需要精确控制记忆时机的场景
- 特定业务逻辑需要的场景

#### 3. both

同时支持 Agent 自主管理和开发者控制。

```yaml
long_term_memory:
  enabled: true
  mode: "both"
  # ... 其他配置
```

### 存储配置

#### 持久化存储（推荐）

```yaml
long_term_memory:
  storage_path: "data/memory"  # 存储目录
  on_disk: true                # 启用持久化
```

**特点**：
- 记忆保存在磁盘上
- 重启后记忆不丢失
- 适合生产环境

#### 内存存储

```yaml
long_term_memory:
  on_disk: false  # 仅内存存储
```

**特点**：
- 记忆仅保存在内存中
- 重启后记忆丢失
- 适合测试和开发

### 用户隔离

通过 `user_name` 区分不同用户的记忆：

```yaml
long_term_memory:
  user_name: "user_123"  # 用户唯一标识
```

**建议**：
- 使用用户的唯一 ID 作为 user_name
- 不同用户使用不同的 user_name
- 可以在运行时动态设置（需要修改代码）

## 嵌入模型选择

### DashScope（阿里云通义千问）

```yaml
embedding_models:
  - model_name: text-embedding-v2
    model_type: dashscope
    api_key: ${DASHSCOPE_API_KEY}
```

**优点**：
- 中文支持优秀
- 性价比高
- 国内访问速度快

**推荐场景**：中文为主的应用

### OpenAI

```yaml
embedding_models:
  - model_name: text-embedding-3-small
    model_type: openai
    api_key: ${OPENAI_API_KEY}
    dimensions: 1536
```

**优点**：
- 质量高
- 多语言支持好
- 生态完善

**推荐场景**：多语言应用、对质量要求高的场景

### Gemini

```yaml
embedding_models:
  - model_name: text-embedding-004
    model_type: gemini
    api_key: ${GEMINI_API_KEY}
```

**优点**：
- Google 生态集成
- 多模态支持

**推荐场景**：使用 Google 服务的应用

### Ollama（本地部署）

```yaml
embedding_models:
  - model_name: nomic-embed-text
    model_type: ollama
    base_url: http://localhost:11434
```

**优点**：
- 完全本地化
- 无需 API 密钥
- 数据隐私保护

**推荐场景**：对数据隐私要求高的场景

## 使用示例

### 示例 1：基本对话与记忆

```python
import asyncio
from mori.mori import Mori

async def basic_example():
    mori = Mori(config_dir="config")

    # 用户分享偏好
    response1 = await mori.chat("我喜欢喝拿铁咖啡")
    print(f"Mori: {response1}")
    # Agent 会自动记录这个偏好

    # 清空短期记忆（模拟新会话）
    await mori.reset()

    # 询问偏好
    response2 = await mori.chat("我喜欢喝什么咖啡？")
    print(f"Mori: {response2}")
    # Agent 会从长期记忆中检索到之前的偏好

asyncio.run(basic_example())
```

### 示例 2：多轮对话

```python
async def multi_turn_example():
    mori = Mori(config_dir="config")

    conversations = [
        "我是一名软件工程师",
        "我喜欢远程工作",
        "我通常早上9点开始工作",
        "我喜欢喝咖啡提神",
    ]

    for msg in conversations:
        response = await mori.chat(msg)
        print(f"用户: {msg}")
        print(f"Mori: {response}\n")

    # 新会话
    await mori.reset()

    # Agent 应该能记住之前的信息
    response = await mori.chat("你对我了解多少？")
    print(f"Mori: {response}")

asyncio.run(multi_turn_example())
```

### 示例 3：Static Control 模式

```python
async def static_control_example():
    # 注意：需要修改 agents.yaml 中的 mode 为 "static_control"
    mori = Mori(config_dir="config")

    # 手动记录记忆
    if mori.long_term_memory:
        from agentscope.message import Msg
        await mori.long_term_memory.record([
            Msg("user", "我喜欢户外运动", "user")
        ])

    # 手动检索记忆
    if mori.long_term_memory:
        memories = await mori.long_term_memory.retrieve([
            Msg("user", "我的运动偏好", "user")
        ])
        print(f"检索到的记忆: {memories}")

asyncio.run(static_control_example())
```

## 系统提示词配置

在 `agent_control` 模式下，系统提示词中已包含记忆管理指南。如果使用自定义模板，建议包含以下内容：

```jinja2
## 记忆管理能力

你具有长期记忆功能，可以记住用户的偏好、习惯和重要信息。

### 记忆管理指南

1. **记录记忆**: 当用户分享个人信息、偏好、习惯或关于自己的事实时，
   使用 `record_to_memory` 工具记录这些信息。

2. **检索记忆**: 在回答关于用户偏好、过去信息或个人详细信息的问题之前，
   使用 `retrieve_from_memory` 工具检查是否有相关的存储信息。

3. **何时使用**:
   - 用户询问"我喜欢什么？"、"我的偏好是什么？"
   - 用户提到之前说过的信息
   - 需要个性化响应时

在声称不了解用户的某些信息之前，始终先检查长期记忆。
```

## 故障排查

### 问题 1：长期记忆未启用

**症状**：Agent 无法记住之前的对话

**解决方案**：
1. 检查 `agents.yaml` 中 `long_term_memory.enabled` 是否为 `true`
2. 检查日志中是否有"长期记忆已启用"的消息
3. 确认嵌入模型配置正确

### 问题 2：嵌入模型 API 错误

**症状**：初始化时报错，提示 API 密钥无效

**解决方案**：
1. 检查环境变量是否正确设置
2. 验证 API 密钥是否有效
3. 检查网络连接（特别是 OpenAI 等国外服务）

### 问题 3：存储路径权限问题

**症状**：无法创建存储目录

**解决方案**：
1. 确保应用有写入权限
2. 手动创建存储目录：`mkdir -p data/memory`
3. 检查目录权限：`chmod 755 data/memory`

### 问题 4：记忆检索不准确

**症状**：Agent 检索到不相关的记忆

**解决方案**：
1. 尝试使用不同的嵌入模型
2. 调整检索查询的表述
3. 清理旧的记忆数据

## 最佳实践

### 1. 选择合适的嵌入模型

- **中文应用**：优先选择 DashScope
- **多语言应用**：选择 OpenAI 或 Gemini
- **隐私敏感**：使用 Ollama 本地部署

### 2. 合理设置用户标识

```python
# 推荐：使用用户的唯一 ID
user_name = f"user_{user_id}"

# 不推荐：使用固定值（所有用户共享记忆）
user_name = "default_user"
```

### 3. 定期清理记忆

对于长期运行的应用，建议定期清理过期或无用的记忆数据。

### 4. 监控存储空间

持久化存储会占用磁盘空间，建议：
- 监控存储目录大小
- 设置存储上限
- 定期归档旧数据

### 5. 测试记忆功能

在部署前充分测试：
- 记录和检索功能
- 用户隔离
- 持久化存储
- 错误处理

## 性能优化

### 1. 使用缓存

嵌入模型调用会增加延迟，建议：
- 使用 AgentScope 的内置缓存
- 避免重复计算相同内容的嵌入

### 2. 批量操作

如果需要记录多条信息，尽量批量操作：

```python
# 推荐：批量记录
await long_term_memory.record([msg1, msg2, msg3])

# 不推荐：逐条记录
await long_term_memory.record([msg1])
await long_term_memory.record([msg2])
await long_term_memory.record([msg3])
```

### 3. 异步操作

长期记忆的所有操作都是异步的，确保正确使用 `await`。

## 安全考虑

### 1. 数据隐私

- 用户的记忆数据包含敏感信息
- 建议加密存储
- 遵守数据保护法规（GDPR、个人信息保护法等）

### 2. 访问控制

- 确保只有授权用户可以访问其记忆
- 实现适当的身份验证和授权机制

### 3. 数据备份

- 定期备份记忆数据
- 实现灾难恢复计划

## 参考资料

- [AgentScope 长期记忆文档](https://doc.agentscope.io/zh_CN/tutorial/task_long_term_memory.html)
- [AgentScope 嵌入模型文档](https://doc.agentscope.io/zh_CN/tutorial/task_embedding.html)
- [Mem0 项目](https://github.com/mem0ai/mem0)

## 常见问题

**Q: 长期记忆和短期记忆有什么区别？**

A: 短期记忆（InMemoryMemory）只保存当前会话的对话历史，会话结束后清空。长期记忆（Mem0LongTermMemory）持久化保存用户的偏好和重要信息，跨会话保持。

**Q: 可以同时使用多个嵌入模型吗？**

A: 每个 Agent 实例只能使用一个嵌入模型。如果需要使用不同的嵌入模型，可以创建多个 Agent 实例。

**Q: 如何迁移到不同的嵌入模型？**

A: 更换嵌入模型后，之前的记忆数据可能无法直接使用（因为向量维度可能不同）。建议：
1. 备份旧数据
2. 清空存储目录
3. 使用新模型重新开始

**Q: 长期记忆会影响响应速度吗？**

A: 会有一定影响，主要来自：
1. 嵌入模型的调用延迟
2. 向量检索的计算时间

建议使用缓存和优化检索策略来减少影响。

## 更新日志

- **2025-01-29**: 初始版本，支持 Mem0 长期记忆
- 支持多种嵌入模型（DashScope、OpenAI、Gemini、Ollama）
- 支持 agent_control、static_control、both 三种模式
- 支持持久化存储和用户隔离
