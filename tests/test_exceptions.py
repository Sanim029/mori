"""异常处理测试

测试自定义异常类的功能。
"""

import pytest

from mori.exceptions import (
    AgentConfigError,
    AgentError,
    AgentNotFoundError,
    ConfigError,
    ConfigFileNotFoundError,
    ConfigParseError,
    ConfigValidationError,
    MemoryConfigError,
    MemoryError,
    ModelConfigError,
    ModelError,
    ModelNotFoundError,
    MoriError,
    TemplateError,
    TemplateNotFoundError,
    TemplateRenderError,
    ToolError,
    ToolExecutionError,
)


class TestMoriError:
    """测试基础异常类"""

    def test_basic_error(self):
        """测试基本错误消息"""
        error = MoriError("测试错误")
        assert str(error) == "测试错误"
        assert error.message == "测试错误"
        assert error.details is None

    def test_error_with_details(self):
        """测试带详情的错误"""
        error = MoriError("测试错误", "这是详细信息")
        assert "测试错误" in str(error)
        assert "这是详细信息" in str(error)
        assert error.details == "这是详细信息"


class TestConfigErrors:
    """测试配置相关异常"""

    def test_config_file_not_found(self):
        """测试配置文件不存在异常"""
        error = ConfigFileNotFoundError("config/test.yaml")
        assert "config/test.yaml" in str(error)
        assert error.file_path == "config/test.yaml"

    def test_config_parse_error(self):
        """测试配置解析错误"""
        original_error = ValueError("invalid yaml")
        error = ConfigParseError("config/test.yaml", original_error)
        assert "config/test.yaml" in str(error)
        assert error.file_path == "config/test.yaml"
        assert error.original_error == original_error

    def test_config_validation_error(self):
        """测试配置验证错误"""
        errors = ["字段1: 必填项", "字段2: 类型错误"]
        error = ConfigValidationError("配置验证失败", errors)
        assert "配置验证失败" in str(error)
        assert "字段1" in str(error)
        assert "字段2" in str(error)
        assert error.validation_errors == errors

    def test_config_validation_error_without_list(self):
        """测试无错误列表的配置验证错误"""
        error = ConfigValidationError("配置验证失败")
        assert "配置验证失败" in str(error)
        assert error.validation_errors == []


class TestModelErrors:
    """测试模型相关异常"""

    def test_model_config_error(self):
        """测试模型配置错误"""
        error = ModelConfigError("gpt-4", "API密钥无效")
        assert "gpt-4" in str(error)
        assert "API密钥无效" in str(error)
        assert error.model_name == "gpt-4"

    def test_model_not_found_error(self):
        """测试模型不存在异常"""
        available = ["model1", "model2"]
        error = ModelNotFoundError("model3", available)
        assert "model3" in str(error)
        assert "model1" in str(error)
        assert "model2" in str(error)
        assert error.model_name == "model3"
        assert error.available_models == available

    def test_model_not_found_error_without_available_list(self):
        """测试无可用模型列表的模型不存在异常"""
        error = ModelNotFoundError("model3")
        assert "model3" in str(error)
        assert error.available_models == []


class TestAgentErrors:
    """测试 Agent 相关异常"""

    def test_agent_config_error(self):
        """测试 Agent 配置错误"""
        error = AgentConfigError("mori", "模型引用无效")
        assert "mori" in str(error)
        assert "模型引用无效" in str(error)
        assert error.agent_name == "mori"

    def test_agent_not_found_error(self):
        """测试 Agent 不存在异常"""
        available = ["agent1", "agent2"]
        error = AgentNotFoundError("agent3", available)
        assert "agent3" in str(error)
        assert "agent1" in str(error)
        assert "agent2" in str(error)
        assert error.agent_name == "agent3"
        assert error.available_agents == available


class TestToolErrors:
    """测试工具相关异常"""

    def test_tool_execution_error(self):
        """测试工具执行错误"""
        original_error = RuntimeError("执行失败")
        error = ToolExecutionError("search_tool", original_error)
        assert "search_tool" in str(error)
        assert error.tool_name == "search_tool"
        assert error.original_error == original_error


class TestMemoryErrors:
    """测试记忆系统相关异常"""

    def test_memory_config_error(self):
        """测试记忆系统配置错误"""
        error = MemoryConfigError("嵌入模型配置缺失")
        assert "嵌入模型配置缺失" in str(error)


class TestTemplateErrors:
    """测试模板相关异常"""

    def test_template_not_found_error(self):
        """测试模板不存在异常"""
        search_paths = ["config/template", "mori/template/internal_template"]
        error = TemplateNotFoundError("mori.jinja2", search_paths)
        assert "mori.jinja2" in str(error)
        assert "config/template" in str(error)
        assert error.template_name == "mori.jinja2"
        assert error.search_paths == search_paths

    def test_template_render_error(self):
        """测试模板渲染错误"""
        original_error = ValueError("未定义变量")
        error = TemplateRenderError("mori.jinja2", original_error)
        assert "mori.jinja2" in str(error)
        assert error.template_name == "mori.jinja2"
        assert error.original_error == original_error


class TestExceptionInheritance:
    """测试异常继承关系"""

    def test_all_inherit_from_mori_error(self):
        """测试所有异常都继承自 MoriError"""
        exceptions = [
            ConfigError("test"),
            ModelError("test"),
            AgentError("test"),
            ToolError("test"),
            MemoryError("test"),
            TemplateError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, MoriError)

    def test_config_exceptions_inherit_from_config_error(self):
        """测试配置异常继承关系"""
        exceptions = [
            ConfigFileNotFoundError("test.yaml"),
            ConfigParseError("test.yaml", ValueError()),
            ConfigValidationError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, ConfigError)
            assert isinstance(exc, MoriError)

    def test_model_exceptions_inherit_from_model_error(self):
        """测试模型异常继承关系"""
        exceptions = [
            ModelConfigError("model", "reason"),
            ModelNotFoundError("model"),
        ]
        for exc in exceptions:
            assert isinstance(exc, ModelError)
            assert isinstance(exc, MoriError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
