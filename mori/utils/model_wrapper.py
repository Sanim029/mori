"""模型包装器工具

提供用于包装 AgentScope 模型的工具类。
"""

from agentscope.model import ChatModelBase


class NonStreamingModelWrapper(ChatModelBase):
    """包装模型类，确保禁用流式输出

    Mem0 库在调用 AgentScope 模型时不支持流式响应，
    此包装类确保模型始终返回完整响应而不是 async_generator。

    使用方法:
        wrapped_model = NonStreamingModelWrapper(original_model)
        response = await wrapped_model(messages)
    """

    def __init__(self, model):
        """初始化包装器

        Args:
            model: 要包装的 AgentScope 模型实例
        """
        # 不调用父类 __init__，因为我们只是包装现有模型
        self.model = model
        # 保存原始的 generate_kwargs
        self._original_generate_kwargs = getattr(model, "generate_kwargs", {})
        # 复制模型的关键属性以满足 ChatModelBase 的要求
        self.model_name = getattr(model, "model_name", "wrapped_model")

    def __getattr__(self, name):
        """代理所有属性访问到原始模型

        Args:
            name: 属性名称

        Returns:
            原始模型的对应属性
        """
        return getattr(self.model, name)

    async def __call__(self, *args, **kwargs):
        """调用模型，强制禁用流式输出

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            ModelResponse: 完整的模型响应（非流式）
        """
        # 强制设置 stream=False 并移除 stream_options
        kwargs["stream"] = False
        kwargs.pop("stream_options", None)  # 移除 stream_options 参数

        # 保存并修改模型的 stream 属性
        original_stream = getattr(self.model, "stream", False)
        self.model.stream = False

        # 如果模型有 generate_kwargs，也确保其中没有 stream=True 和 stream_options
        if hasattr(self.model, "generate_kwargs"):
            original_gk = self.model.generate_kwargs
            # 创建新的 generate_kwargs，确保 stream=False 且没有 stream_options
            new_gk = {k: v for k, v in original_gk.items() if k != "stream_options"}
            new_gk["stream"] = False
            self.model.generate_kwargs = new_gk

            try:
                response = await self.model(*args, **kwargs)
            finally:
                # 恢复原始的 generate_kwargs 和 stream 属性
                self.model.generate_kwargs = original_gk
                self.model.stream = original_stream
        else:
            try:
                response = await self.model(*args, **kwargs)
            finally:
                # 恢复原始的 stream 属性
                self.model.stream = original_stream

        return response
