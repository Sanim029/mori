# Debug Mode - 项目调试规则（仅非显而易见内容）

## 调试关键点

### 长期记忆调试
- Mem0 不支持流式响应，必须使用 [`NonStreamingModelWrapper`](../../mori/utils/model_wrapper.py:9)
- 向量维度必须通过 `VectorStoreConfig` 的 `embedding_model_dims` 显式传递
- 嵌入模型的 `dimensions` 属性是 Mem0 推断向量维度的来源

### 模型配置问题
- OpenAI 兼容接口的 `base_url` 必须在 `client_args` 中传递（聊天模型）
- 嵌入模型的 `base_url` 传递方式：
  - OpenAI 嵌入模型：直接传递 `base_url` 参数（因为内部直接传给 `openai.AsyncClient`）
  - Ollama 嵌入模型：通过 `client_args` 传递 `base_url`

### 响应处理
- Agent 响应格式不统一，可能是字符串或 `TextBlock` 列表
- 使用 [`_extract_text_from_response()`](../../mori/mori.py:383) 统一处理

### 日志位置
- 日志配置在 `config/config.yaml` 的 `global.log_dir` 中
- 默认日志目录：`logs/`
