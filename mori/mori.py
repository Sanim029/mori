"""Mori核心封装类

封装AgentScope功能，提供简洁的API接口。
"""

from pathlib import Path
from typing import List, Optional

from agentscope.message import Msg
from agentscope.model import (
    AnthropicChatModel,
    DashScopeChatModel,
    GeminiChatModel,
    OllamaChatModel,
    OpenAIChatModel,
)
from agentscope.formatter import (
    AnthropicChatFormatter,
    DashScopeChatFormatter,
    GeminiChatFormatter,
    OllamaChatFormatter,
    OpenAIChatFormatter,
)
from agentscope.embedding import (
    DashScopeTextEmbedding,
    GeminiTextEmbedding,
    OllamaTextEmbedding,
    OpenAITextEmbedding,
)
from agentscope.memory import Mem0LongTermMemory
from agentscope.tool import Toolkit

from logger import setup_logger
from mori.agent.factory import create_mori_agent
from mori.config import get_embedding_model_config, load_config
from mori.template.loader import TemplateLoader
from mori.tool.internal_tools.example_tools import register_tools
from mori.utils import NonStreamingModelWrapper


class Mori:
    """Mori核心类

    封装AgentScope的功能，提供简洁的使用接口。
    """

    def __init__(self, config_dir: str = "config"):
        """初始化Mori系统

        Args:
            config_dir: 配置文件目录路径
        """
        # 加载配置
        self.config = load_config(config_dir)

        # 设置日志
        self.logger = setup_logger(
            name="mori",
            level=self.config.global_config.log_level,
            log_dir=self.config.global_config.log_dir,
        )
        self.logger.info("正在初始化Mori系统...")

        # 初始化模板加载器
        self.template_loader = TemplateLoader()

        # 获取第一个agent配置（默认使用第一个）
        if not self.config.agents:
            raise ValueError("配置文件中没有定义任何agent")
        self.agent_config = self.config.agents[0]

        # 加载系统提示词
        sys_prompt = self._load_system_prompt()

        # 创建模型和formatter
        self.model, self.formatter = self._create_model()

        # 创建工具集
        self.toolkit = self._create_toolkit()

        # 创建长期记忆（如果配置了）
        self.long_term_memory = None
        self.long_term_memory_mode = None
        if self.agent_config.long_term_memory and self.agent_config.long_term_memory.get(
            "enabled", False
        ):
            self.long_term_memory = self._create_long_term_memory()
            self.long_term_memory_mode = self.agent_config.long_term_memory.get(
                "mode", "agent_control"
            )
            self.logger.info(f"长期记忆已启用，模式: {self.long_term_memory_mode}")

        # 创建Agent
        self.agent = create_mori_agent(
            name=self.agent_config.name,
            sys_prompt=sys_prompt,
            model=self.model,
            formatter=self.formatter,
            toolkit=self.toolkit,
            parallel_tool_calls=self.agent_config.parallel_tool_calls,
            long_term_memory=self.long_term_memory,
            long_term_memory_mode=self.long_term_memory_mode,
        )

        self.logger.info("Mori系统初始化完成！")

    def _load_system_prompt(self) -> str:
        """加载系统提示词

        Returns:
            系统提示词字符串
        """
        if self.agent_config.sys_prompt:
            return self.agent_config.sys_prompt

        # 准备模板上下文（运行时信息）
        from datetime import datetime

        context = {
            "current_time": datetime.now().strftime("%H:%M:%S"),
            "current_date": datetime.now().strftime("%Y年%m月%d日 %A"),
        }

        # 从模板加载并渲染
        return self.template_loader.render_template(self.agent_config.template, context=context)

    def _create_model(self):
        """创建模型实例和对应的formatter

        Returns:
            (模型实例, formatter实例)

        Raises:
            ValueError: 模型配置不存在或模型类型不支持
        """
        # 模型和Formatter映射
        MODEL_MAPPING = {
            "openai": (OpenAIChatModel, OpenAIChatFormatter),
            "dashscope": (DashScopeChatModel, DashScopeChatFormatter),
            "anthropic": (AnthropicChatModel, AnthropicChatFormatter),
            "gemini": (GeminiChatModel, GeminiChatFormatter),
            "ollama": (OllamaChatModel, OllamaChatFormatter),
        }

        # 获取模型配置
        model_config = None
        for model in self.config.models:
            if model.model_name == self.agent_config.model:
                model_config = model
                break

        if model_config is None:
            raise ValueError(f"找不到模型配置: {self.agent_config.model}")

        # 获取模型类型
        model_type = model_config.model_type.lower()

        # 检查模型类型是否支持
        if model_type not in MODEL_MAPPING:
            raise ValueError(
                f"不支持的模型类型: {model_type}. " f"支持的类型: {', '.join(MODEL_MAPPING.keys())}"
            )

        # 构建模型参数
        model_kwargs = {
            "model_name": model_config.model_name,
        }

        if model_config.api_key:
            model_kwargs["api_key"] = model_config.api_key

        if model_config.generate_kwargs:
            model_kwargs["generate_kwargs"] = model_config.generate_kwargs

        # 处理 base_url（OpenAI 和 Ollama 需要）
        if model_config.base_url and model_type in ["openai", "ollama"]:
            model_kwargs["client_args"] = {"base_url": model_config.base_url}

        # 创建模型和formatter实例
        model_class, formatter_class = MODEL_MAPPING[model_type]
        return model_class(**model_kwargs), formatter_class()

    def _create_embedding_model(self, embedding_model_name: str):
        """创建嵌入模型实例

        Args:
            embedding_model_name: 嵌入模型名称

        Returns:
            嵌入模型实例

        Raises:
            ValueError: 嵌入模型配置不存在或类型不支持
        """
        # 嵌入模型类型映射
        EMBEDDING_MODEL_MAPPING = {
            "dashscope": DashScopeTextEmbedding,
            "openai": OpenAITextEmbedding,
            "gemini": GeminiTextEmbedding,
            "ollama": OllamaTextEmbedding,
        }

        # 获取嵌入模型配置
        embedding_config = get_embedding_model_config(self.config, embedding_model_name)

        if embedding_config is None:
            raise ValueError(f"找不到嵌入模型配置: {embedding_model_name}")

        # 获取模型类型
        model_type = embedding_config.model_type.lower()

        # 检查模型类型是否支持
        if model_type not in EMBEDDING_MODEL_MAPPING:
            raise ValueError(
                f"不支持的嵌入模型类型: {model_type}. "
                f"支持的类型: {', '.join(EMBEDDING_MODEL_MAPPING.keys())}"
            )

        # 构建模型参数 - 注意不同模型类型的参数要求不同
        model_kwargs = {
            "model_name": embedding_config.model_name,
        }

        # API key 是必需的（除了 Ollama）
        if embedding_config.api_key:
            model_kwargs["api_key"] = embedding_config.api_key

        # 关键：必须显式设置 dimensions 参数
        # Mem0 会从这个参数推断向量维度
        if embedding_config.dimensions:
            model_kwargs["dimensions"] = embedding_config.dimensions
            self.logger.info(f"设置嵌入模型维度: {embedding_config.dimensions}")

        # 处理 base_url
        # OpenAI 嵌入模型直接接受 base_url 参数
        # Ollama 需要通过 client_args 传递
        if embedding_config.base_url:
            if model_type == "openai":
                model_kwargs["base_url"] = embedding_config.base_url
            elif model_type == "ollama":
                model_kwargs["client_args"] = {"base_url": embedding_config.base_url}

        # 处理额外的生成参数
        if embedding_config.generate_kwargs:
            model_kwargs.update(embedding_config.generate_kwargs)

        # 创建并返回嵌入模型实例
        embedding_model_class = EMBEDDING_MODEL_MAPPING[model_type]
        self.logger.info(f"嵌入模型创建参数: {model_kwargs}")
        embedding_model = embedding_model_class(**model_kwargs)

        # 验证嵌入模型的维度
        if hasattr(embedding_model, "dimensions"):
            self.logger.info(f"嵌入模型 dimensions 属性: {embedding_model.dimensions}")
        else:
            self.logger.warning("嵌入模型没有 dimensions 属性！")

        return embedding_model

    def _create_long_term_memory(self) -> Optional[Mem0LongTermMemory]:
        """创建长期记忆实例

        Returns:
            Mem0LongTermMemory实例，如果配置不完整则返回None

        Raises:
            ValueError: 配置错误
        """
        ltm_config = self.agent_config.long_term_memory
        if not ltm_config or not ltm_config.get("enabled", False):
            return None

        # 获取必要的配置
        user_name = ltm_config.get("user_name")
        if not user_name:
            raise ValueError("长期记忆配置缺少 user_name")

        embedding_model_name = ltm_config.get("embedding_model")
        if not embedding_model_name:
            raise ValueError("长期记忆配置缺少 embedding_model")

        # 创建嵌入模型
        embedding_model = self._create_embedding_model(embedding_model_name)

        # 获取存储路径
        storage_path = ltm_config.get("storage_path", "data/memory")
        on_disk = ltm_config.get("on_disk", True)

        # 如果启用持久化存储，确保目录存在
        if on_disk:
            Path(storage_path).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"长期记忆存储路径: {storage_path}")

        # 创建长期记忆实例
        # 为 Mem0 创建一个包装的模型，确保禁用流式输出
        # Mem0 不支持处理流式响应，必须使用完整响应
        wrapped_model = NonStreamingModelWrapper(self.model)

        # 获取嵌入模型的维度
        embedding_dim = getattr(embedding_model, "dimensions", 1536)
        self.logger.info(f"嵌入模型维度: {embedding_dim}")

        # 导入 Mem0 的配置类
        try:
            from mem0.vector_stores.configs import VectorStoreConfig
        except ImportError as e:
            raise ImportError(
                "无法导入 mem0.vector_stores.configs.VectorStoreConfig。"
                "请确保已安装 mem0ai 库：pip install mem0ai"
            ) from e

        # 创建向量存储配置，显式指定维度
        # 这是关键：必须通过 VectorStoreConfig 传递 embedding_model_dims
        vector_store_config = VectorStoreConfig(
            provider="qdrant",
            config={
                "collection_name": "mem0migrations",
                "embedding_model_dims": embedding_dim,  # 关键参数！
                "on_disk": on_disk,
                "path": storage_path if on_disk else None,
            },
        )

        ltm_kwargs = {
            "agent_name": self.agent_config.name,
            "user_name": user_name,
            "model": wrapped_model,
            "embedding_model": embedding_model,
            "vector_store_config": vector_store_config,  # 传递向量存储配置
        }

        # 如果启用持久化存储，添加 storage_path 参数
        if on_disk:
            ltm_kwargs["storage_path"] = storage_path

        self.logger.info("准备创建 Mem0LongTermMemory")
        self.logger.info(f"向量存储配置: provider=qdrant, dims={embedding_dim}, on_disk={on_disk}")

        long_term_memory = Mem0LongTermMemory(**ltm_kwargs)

        self.logger.info(
            f"长期记忆已创建 - 用户: {user_name}, "
            f"嵌入模型: {embedding_model_name}, "
            f"持久化: {on_disk}"
        )

        return long_term_memory

    def _create_toolkit(self) -> Toolkit:
        """创建工具集

        Returns:
            配置好的Toolkit实例
        """
        toolkit = Toolkit()
        # 注册内置工具
        register_tools(toolkit)
        return toolkit

    async def chat(self, message: str) -> str:
        """发送消息并获取回复

        Args:
            message: 用户消息

        Returns:
            Agent的回复内容
        """
        self.logger.debug(f"用户消息: {message}")

        # 创建消息对象
        msg = Msg(name="user", content=message, role="user")

        # 调用Agent
        response = await self.agent(msg)

        # 提取文本内容
        reply_text = self._extract_text_from_response(response)

        self.logger.debug(f"Mori回复: {reply_text}")
        return reply_text

    def _extract_text_from_response(self, response: Msg) -> str:
        """从响应消息中提取文本内容

        Args:
            response: Agent的响应消息

        Returns:
            提取的文本内容
        """
        if isinstance(response.content, str):
            return response.content

        if isinstance(response.content, list):
            text_parts = []
            for item in response.content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    text_parts.append(item)
            return "\n".join(text_parts)

        return str(response.content)

    async def reset(self) -> None:
        """重置对话历史"""
        await self.agent.memory.clear()
        self.logger.info("对话历史已重置")

    async def get_history(self) -> List[dict]:
        """获取对话历史

        Returns:
            对话历史列表
        """
        return await self.agent.memory.get_memory()
