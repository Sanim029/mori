"""工具工厂模块

负责创建和配置工具集。
"""

from agentscope.tool import Toolkit

from mori.tool.internal_tools.example_tools import register_tools


def create_toolkit() -> Toolkit:
    """创建并配置工具集

    创建一个 Toolkit 实例并注册所有内置工具。
    AgentScope 的 Toolkit 会自动解析工具函数签名为 JSON Schema。

    Returns:
        配置好的 Toolkit 实例
    """
    toolkit = Toolkit()
    # 注册内置工具
    register_tools(toolkit)
    return toolkit
