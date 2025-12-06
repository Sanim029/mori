# 多Agent架构设计方案

## 概述

将Mori从单agent架构改造为多agent架构，支持在配置文件中定义多个agent，每个agent可以使用不同的模型配置，并能够根据任务类型动态选择合适的agent。

## 核心设计理念

1. **配置名区分**: 使用配置名（config_name）作为唯一标识符来区分不同的模型和agent配置
2. **向后兼容**: 保持单agent使用方式的兼容性（默认使用第一个agent）
3. **灵活切换**: 支持通过agent名称在运行时切换agent
4. **任务路由**: 支持根据任务类型自动选择最合适的agent（可选功能）

## 配置文件改造

### 1. models.yaml 改造

**当前结构**:
```yaml
models:
  - model_name: gpt-4
    model_type: openai
    api_key: ${OPENAI_API_KEY}
```

**改造后**:
```yaml
models:
  # 使用 config_name 作为唯一标识
  default_gpt4:
    model_name: gpt-4
    model_type: openai
    api_key: ${OPENAI_API_KEY}
    generate_kwargs:
      temperature: 0.7
      max_tokens: 2000

  fast_gpt35:
    model_name: gpt-3.5-turbo
    model_type: openai
    api_key: ${OPENAI_API_KEY}
    generate_kwargs:
      temperature: 0.8
      max_tokens: 1500

  local_qwen:
    model_name: qwen-max
    model_type: dashscope
    api_key: ${DASHSCOPE_API_KEY}

embedding_models:
  default_embedding:
    model_name: text-embedding-v2
    model_type: dashscope
    api_key: ${DASHSCOPE_API_KEY}

  openai_embedding:
    model_name: text-embedding-3-small
    model_type: openai
    api_key: ${OPENAI_API_KEY}
    dimensions: 1536
```

### 2. agents.yaml 改造

**当前结构**:
```yaml
agents:
  - name: mori
    model: gpt-4  # 引用model_name
    template: mori
```

**改造后**:
```yaml
agents:
  # 虚拟女友角色
  mori:
    model_config: default_gpt4  # 引用models.yaml中的config_name
    template: mori
    sys_prompt: null
    memory_config:
      type: memory
      max_length: 100
    parallel_tool_calls: true
    long_term_memory:
      enabled: true
      mode: "agent_control"
      user_name: "user"
      embedding_model_config: default_embedding
      storage_path: "data/memory/mori"
      on_disk: true
    # 任务标签（可选，用于任务路由）
    task_types:
      - conversation
      - emotional_support
      - entertainment

  # 专业助手角色
  assistant:
    model_config: fast_gpt35  # 使用更快的模型
    template: assistant
    sys_prompt: null
    memory_config:
      type: memory
      max_length: 50
    parallel_tool_calls: true
    task_types:
      - technical_support
      - information_query
      - task_execution

  # 创意写作角色
  writer:
    model_config: default_gpt4  # 使用更强的模型
    template: writer
    sys_prompt: null
    memory_config:
      type: memory
      max_length: 200
    parallel_tool_calls: false
    long_term_memory:
      enabled: true
      mode: "agent_control"
      user_name: "user"
      embedding_model_config: openai_embedding
      storage_path: "data/memory/writer"
      on_disk: true
    task_types:
      - creative_writing
      - content_generation

# 默认agent（可选，如果不指定则使用第一个）
default_agent: mori

# 任务路由规则（可选）
task_routing:
  enabled: false  # 初期先关闭，后续可扩展
  rules:
    - task_pattern: "写.*|创作.*|生成.*"
      agent: writer
    - task_pattern: "帮我.*|查询.*|搜索.*"
      agent: assistant
```

## 代码改造

### 1. 配置模型改造 (mori/config.py)

```python
class ModelConfig(BaseModel):
    """模型配置"""
    model_name: str
    model_type: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    generate_kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AgentConfig(BaseModel):
    """Agent配置"""
    model_config: str = Field(..., description="引用models.yaml中的配置名")
    template: str
    sys_prompt: Optional[str] = None
    memory_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parallel_tool_calls: bool = False
    long_term_memory: Optional[Dict[str, Any]] = None
    task_types: Optional[List[str]] = None

class Config(BaseModel):
    """完整配置"""
    models: Dict[str, ModelConfig]  # 改为字典，key为配置名
    agents: Dict[str, AgentConfig]  # 改为字典，key为agent名
    embedding_models: Dict[str, EmbeddingModelConfig] = Field(default_factory=dict)
    default_agent: Optional[str] = None
    task_routing: Optional[Dict[str, Any]] = None
    global_config: GlobalConfig = Field(default_factory=GlobalConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
```

### 2. Agent管理器 (mori/agent/manager.py)

新建agent管理器，负责管理多个agent实例：

```python
class AgentManager:
    """Agent管理器，负责管理多个agent实例"""

    def __init__(self, config: Config, logger=None):
        self.config = config
        self.logger = logger
        self.agents: Dict[str, ReActAgent] = {}
        self.template_loader = TemplateLoader()
        self.toolkit = create_toolkit()

    def initialize_agent(self, agent_name: str) -> ReActAgent:
        """初始化指定名称的agent"""
        # 获取agent配置
        # 获取模型配置
        # 加载系统提示词
        # 创建agent
        # 缓存agent实例
        pass

    def get_agent(self, agent_name: Optional[str] = None) -> ReActAgent:
        """获取agent实例，如果不存在则创建"""
        pass

    def list_agents(self) -> List[str]:
        """列出所有可用的agent名称"""
        return list(self.config.agents.keys())

    def route_task(self, message: str) -> str:
        """根据任务内容路由到合适的agent（可选功能）"""
        pass
```

### 3. Mori核心类改造 (mori/mori.py)

```python
class Mori:
    """Mori核心类 - 支持多agent"""

    def __init__(self, config_dir: str = "config"):
        # 加载配置
        self.config = load_config(config_dir)

        # 创建agent管理器
        self.agent_manager = AgentManager(self.config, self.logger)

        # 确定默认agent
        self.default_agent_name = (
            self.config.default_agent
            or list(self.config.agents.keys())[0]
        )

        # 初始化默认agent
        self.current_agent_name = self.default_agent_name
        self.current_agent = self.agent_manager.get_agent(self.default_agent_name)

    async def chat(
        self,
        message: str,
        agent_name: Optional[str] = None
    ) -> str:
        """发送消息并获取回复

        Args:
            message: 用户消息
            agent_name: 指定使用的agent名称，如果为None则使用当前agent
        """
        # 如果指定了agent_name，切换agent
        if agent_name and agent_name != self.current_agent_name:
            self.switch_agent(agent_name)

        # 调用当前agent
        msg = Msg(name="user", content=message, role="user")
        response = await self.current_agent(msg)
        reply_text = extract_text_from_response(response)

        return reply_text

    def switch_agent(self, agent_name: str) -> None:
        """切换到指定的agent"""
        if agent_name not in self.agent_manager.list_agents():
            raise ValueError(f"Agent不存在: {agent_name}")

        self.current_agent_name = agent_name
        self.current_agent = self.agent_manager.get_agent(agent_name)
        self.logger.info(f"已切换到agent: {agent_name}")

    def list_agents(self) -> List[str]:
        """列出所有可用的agent"""
        return self.agent_manager.list_agents()

    def get_current_agent_name(self) -> str:
        """获取当前使用的agent名称"""
        return self.current_agent_name
```

## 使用示例

### 示例1: 向后兼容的单agent使用

```python
# 配置文件中只定义一个agent，使用方式不变
mori = Mori(config_dir="config")
response = await mori.chat("你好")
```

### 示例2: 切换agent

```python
mori = Mori(config_dir="config")

# 使用默认agent（mori）聊天
response1 = await mori.chat("今天心情不好")

# 切换到专业助手
mori.switch_agent("assistant")
response2 = await mori.chat("帮我查询天气")

# 或者直接在chat时指定agent
response3 = await mori.chat("写一篇文章", agent_name="writer")
```

### 示例3: 列出所有agent

```python
mori = Mori(config_dir="config")
agents = mori.list_agents()
print(f"可用的agents: {agents}")
# 输出: 可用的agents: ['mori', 'assistant', 'writer']
```

## 实施步骤

1. ✅ 设计文档（当前文件）
2. [ ] 更新配置模型（config.py）
3. [ ] 创建agent管理器（agent/manager.py）
4. [ ] 更新Mori核心类（mori.py）
5. [ ] 更新配置示例文件
6. [ ] 更新测试用例
7. [ ] 更新文档和使用指南
8. [ ] 可选：实现任务路由功能

## 注意事项

1. **配置兼容性**: 新格式与旧格式不兼容，需要提供迁移指南
2. **性能考虑**: agent实例会被缓存，避免重复创建
3. **内存管理**: 每个agent有独立的memory，互不干扰
4. **长期记忆隔离**: 不同agent的长期记忆存储在不同路径
5. **工具共享**: 所有agent共享同一个toolkit（可根据需要扩展为每个agent独立工具集）

## 后续扩展

1. **任务路由**: 根据用户消息内容自动选择最合适的agent
2. **Agent协作**: 多个agent协同完成复杂任务
3. **动态加载**: 支持运行时动态添加新的agent
4. **Agent权限**: 不同agent有不同的工具访问权限
5. **负载均衡**: 多个相同类型的agent负载均衡
