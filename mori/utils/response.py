"""响应处理工具模块

提供统一的响应内容提取功能。
"""

from agentscope.message import Msg


def extract_text_from_response(response: Msg) -> str:
    """从响应消息中提取文本内容

    AgentScope 的 Agent 响应可能是字符串或包含 TextBlock 的列表，
    本函数统一处理这些不同格式。

    Args:
        response: Agent 的响应消息

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
