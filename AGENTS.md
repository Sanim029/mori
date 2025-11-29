# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## 项目特定约定

### 模板系统优先级
- 模板查找顺序：`config/template/` (自定义) > `mori/template/internal_template/` (内置)
- 简短名称（如 `mori`）自动添加 `.jinja2` 扩展名并按优先级查找
- 运行时信息（`current_time`, `current_date`）在 [`mori.py:_load_system_prompt()`](mori/mori.py:85) 中注入，不在模板中硬编码

### 配置加载机制
- 环境变量格式：`${ENV_VAR_NAME}` 在 [`config.py:resolve_env_var()`](mori/config.py:25) 中解析
- 配置文件必须分离：`models.yaml` (模型), `agents.yaml` (agent), `config.yaml` (全局)
- Agent 通过 `model` 字段引用 `models.yaml` 中的模型名称，不是直接配置

### Model 和 Formatter 配对
- 每个模型类型必须配对对应的 Formatter（见 [`mori.py:_create_model()`](mori/mori.py:108)）
- OpenAI 兼容接口使用 `model_type: openai` + `base_url` 参数
- `client_args` 用于传递额外的客户端参数（如 `base_url`）

### 工具注册模式
- 工具函数必须返回 [`ToolResponse`](mori/tool/internal_tools/example_tools.py:13) 对象，不是普通字符串
- 使用 [`toolkit.register_tool_function()`](mori/tool/internal_tools/example_tools.py:92) 注册，AgentScope 自动解析函数签名为 JSON Schema
- 工具函数支持 async/await

### 响应内容提取
- Agent 响应可能是字符串或包含 `TextBlock` 的列表
- 使用 [`_extract_text_from_response()`](mori/mori.py:197) 统一处理不同格式

### 长期记忆配置
- 嵌入模型配置在 `models.yaml` 的 `embedding_models` 部分
- Agent 通过 `long_term_memory.embedding_model` 字段引用嵌入模型名称
- 支持的嵌入模型类型：`dashscope`, `openai`, `gemini`, `ollama`
- 长期记忆模式：
  - `agent_control`: Agent 自主管理记忆（通过工具调用）
  - `static_control`: 开发者通过代码显式控制
  - `both`: 同时支持两种模式
- 存储配置：
  - `on_disk: true`: 持久化存储到 `storage_path` 指定的目录
  - `on_disk: false`: 内存存储（重启后丢失）
- 用户隔离：通过 `user_name` 区分不同用户的记忆数据

### 嵌入模型创建
- 在 [`mori.py:_create_embedding_model()`](mori/mori.py:157) 中实现
- 根据 `model_type` 创建对应的嵌入模型实例
- 支持 `api_key`, `base_url`, `dimensions` 等参数配置

### 长期记忆实例化
- 在 [`mori.py:_create_long_term_memory()`](mori/mori.py:213) 中实现
- 使用 `Mem0LongTermMemory` 类
- 需要提供：主模型、嵌入模型、用户名、存储配置
- 在 `agent_control` 模式下自动注册 `record_to_memory` 和 `retrieve_from_memory` 工具

## 测试命令

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_config.py

# 带详细输出
pytest tests/ -v
```

## 代码风格

- Line length: 100 (black/ruff 配置)
- Python 3.10+ 语法
- 使用 pre-commit hooks: `pre-commit run --all-files`
