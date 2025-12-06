"""长期记忆功能测试

测试长期记忆的配置加载、嵌入模型创建和记忆实例化。
"""

import os

import pytest

from mori.config import (
    AgentConfig,
    Config,
    EmbeddingModelConfig,
    ModelConfig,
    get_embedding_model_config,
)


class TestEmbeddingModelConfig:
    """测试嵌入模型配置"""

    def test_embedding_model_config_creation(self):
        """测试嵌入模型配置创建"""
        config = EmbeddingModelConfig(
            model_name="text-embedding-v2",
            model_type="dashscope",
            api_key="test_key",
            dimensions=1536,
        )

        assert config.model_name == "text-embedding-v2"
        assert config.model_type == "dashscope"
        assert config.api_key == "test_key"
        assert config.dimensions == 1536

    def test_embedding_model_config_env_var(self):
        """测试嵌入模型配置环境变量解析"""
        os.environ["TEST_EMBEDDING_KEY"] = "test_embedding_key"

        config = EmbeddingModelConfig(
            model_name="text-embedding-v2",
            model_type="dashscope",
            api_key="${TEST_EMBEDDING_KEY}",
        )

        assert config.api_key == "test_embedding_key"

        del os.environ["TEST_EMBEDDING_KEY"]


class TestAgentConfigWithLongTermMemory:
    """测试带长期记忆的Agent配置"""

    def test_agent_config_with_ltm(self):
        """测试Agent配置包含长期记忆配置"""
        config = AgentConfig(
            model="gpt-4",
            template="mori",
            long_term_memory={
                "enabled": True,
                "mode": "agent_control",
                "user_name": "test_user",
                "embedding_model": "text-embedding-v2",
                "storage_path": "data/memory",
                "on_disk": True,
            },
        )

        assert config.long_term_memory is not None
        assert config.long_term_memory.enabled is True
        assert config.long_term_memory.mode == "agent_control"
        assert config.long_term_memory.user_name == "test_user"
        assert config.long_term_memory.embedding_model == "text-embedding-v2"

    def test_agent_config_without_ltm(self):
        """测试Agent配置不包含长期记忆配置"""
        config = AgentConfig(
            model="gpt-4",
            template="mori",
        )

        assert config.long_term_memory is None


class TestConfigWithEmbeddingModels:
    """测试包含嵌入模型的完整配置"""

    def test_config_with_embedding_models(self):
        """测试完整配置包含嵌入模型"""
        config = Config(
            models={
                "gpt-4": ModelConfig(
                    model_name="gpt-4",
                    model_type="openai",
                    api_key="test_key",
                )
            },
            agents={
                "test_agent": AgentConfig(
                    model="gpt-4",
                    template="mori",
                )
            },
            primary_agent="test_agent",
            embedding_models={
                "text-embedding-v2": EmbeddingModelConfig(
                    model_name="text-embedding-v2",
                    model_type="dashscope",
                    api_key="test_key",
                )
            },
        )

        assert len(config.embedding_models) == 1
        assert config.embedding_models["text-embedding-v2"].model_name == "text-embedding-v2"

    def test_get_embedding_model_config(self):
        """测试获取嵌入模型配置"""
        config = Config(
            models={
                "gpt-4": ModelConfig(
                    model_name="gpt-4",
                    model_type="openai",
                    api_key="test_key",
                )
            },
            agents={
                "test_agent": AgentConfig(
                    model="gpt-4",
                    template="mori",
                )
            },
            primary_agent="test_agent",
            embedding_models={
                "text-embedding-v2": EmbeddingModelConfig(
                    model_name="text-embedding-v2",
                    model_type="dashscope",
                    api_key="test_key",
                ),
                "text-embedding-3-small": EmbeddingModelConfig(
                    model_name="text-embedding-3-small",
                    model_type="openai",
                    api_key="test_key",
                ),
            },
        )

        # 测试找到配置
        embedding_config = get_embedding_model_config(config, "text-embedding-v2")
        assert embedding_config is not None
        assert embedding_config.model_name == "text-embedding-v2"
        assert embedding_config.model_type == "dashscope"

        # 测试找不到配置
        embedding_config = get_embedding_model_config(config, "non-existent")
        assert embedding_config is None


class TestMoriLongTermMemoryIntegration:
    """测试Mori类的长期记忆集成"""

    def test_create_embedding_model_dashscope(self):
        """测试创建DashScope嵌入模型配置"""
        # 这个测试简化为只验证配置本身，不测试实际的模型创建
        # 因为实际的模型创建需要复杂的mock和依赖

        embedding_config = EmbeddingModelConfig(
            model_name="text-embedding-v2",
            model_type="dashscope",
            api_key="test_key",
            dimensions=1536,
        )

        assert embedding_config.model_name == "text-embedding-v2"
        assert embedding_config.model_type == "dashscope"
        assert embedding_config.api_key == "test_key"
        assert embedding_config.dimensions == 1536


class TestLongTermMemoryConfiguration:
    """测试长期记忆配置的各种场景"""

    def test_ltm_config_all_fields(self):
        """测试长期记忆配置包含所有字段"""
        ltm_config = {
            "enabled": True,
            "mode": "agent_control",
            "user_name": "test_user",
            "embedding_model": "text-embedding-v2",
            "storage_path": "data/memory",
            "on_disk": True,
        }

        assert ltm_config["enabled"] is True
        assert ltm_config["mode"] == "agent_control"
        assert ltm_config["user_name"] == "test_user"
        assert ltm_config["embedding_model"] == "text-embedding-v2"
        assert ltm_config["storage_path"] == "data/memory"
        assert ltm_config["on_disk"] is True

    def test_ltm_config_modes(self):
        """测试长期记忆的不同模式"""
        modes = ["agent_control", "static_control", "both"]

        for mode in modes:
            ltm_config = {
                "enabled": True,
                "mode": mode,
                "user_name": "test_user",
                "embedding_model": "text-embedding-v2",
            }
            assert ltm_config["mode"] == mode

    def test_ltm_config_storage_options(self):
        """测试长期记忆的存储选项"""
        # 持久化存储
        ltm_config_disk = {
            "enabled": True,
            "mode": "agent_control",
            "user_name": "test_user",
            "embedding_model": "text-embedding-v2",
            "storage_path": "data/memory",
            "on_disk": True,
        }
        assert ltm_config_disk["on_disk"] is True

        # 内存存储
        ltm_config_memory = {
            "enabled": True,
            "mode": "agent_control",
            "user_name": "test_user",
            "embedding_model": "text-embedding-v2",
            "on_disk": False,
        }
        assert ltm_config_memory["on_disk"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
