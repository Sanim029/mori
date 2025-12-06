"""Gradio GUI应用

使用Gradio创建Web界面，提供友好的用户交互体验。
"""

import traceback
from typing import Dict, List, Tuple

import gradio as gr

from logger.config import get_logger
from mori import Mori
from mori.exceptions import ConfigError, MoriError

# 使用统一的 "mori" logger，避免日志传播导致的重复打印
logger = get_logger("mori")


class MoriGUI:
    """Mori GUI封装类"""

    def __init__(self, config_dir: str = "config"):
        """初始化GUI

        Args:
            config_dir: 配置文件目录

        Raises:
            ConfigError: 配置加载失败
            MoriError: Mori 初始化失败
        """
        try:
            logger.info(f"初始化 Mori GUI，配置目录: {config_dir}")
            self.mori = Mori(config_dir)
            self.config = self.mori.config
            logger.info("Mori GUI 初始化成功")
        except ConfigError as e:
            logger.error(f"配置加载失败: {e}")
            raise
        except Exception as e:
            logger.error(f"Mori 初始化失败: {e}")
            logger.debug(traceback.format_exc())
            raise MoriError("GUI 初始化失败", str(e))

    async def chat(
        self, message: str, history: List[Dict[str, str]]
    ) -> Tuple[str, List[Dict[str, str]]]:
        """处理聊天消息

        Args:
            message: 用户消息
            history: 对话历史（Gradio 6.0格式）

        Returns:
            (空字符串, 更新后的历史)
        """
        if not message.strip():
            logger.debug("收到空消息，忽略")
            return "", history

        try:
            logger.info(f"处理用户消息: {message[:50]}...")

            # 获取回复
            response = await self.mori.chat(message)

            logger.info(f"生成回复: {response[:50]}...")

            # 更新历史 - Gradio 6.0格式
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response})

            return "", history

        except MoriError as e:
            # Mori 业务错误，记录并返回友好提示
            logger.error(f"处理消息时发生业务错误: {e}")
            error_message = f"抱歉，处理您的消息时遇到了问题：{e.message}"

            if e.details:
                logger.debug(f"错误详情: {e.details}")

            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_message})

            return "", history

        except Exception as e:
            # 未预期的错误，记录完整堆栈并返回通用错误消息
            logger.error(f"处理消息时发生未知错误: {e}")
            logger.debug(traceback.format_exc())

            error_message = "抱歉，处理您的消息时发生了意外错误，请稍后重试。"

            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_message})

            return "", history

    async def reset(self) -> List[Dict[str, str]]:
        """重置对话

        Returns:
            空的对话历史
        """
        try:
            logger.info("重置对话")
            await self.mori.reset()
            logger.info("对话重置成功")
            return []
        except Exception as e:
            logger.error(f"重置对话失败: {e}")
            logger.debug(traceback.format_exc())
            # 即使重置失败，也返回空列表以清空 UI
            return []

    def create_interface(self) -> gr.Blocks:
        """创建Gradio界面

        Returns:
            Gradio Blocks对象
        """
        with gr.Blocks(
            title="Mori - 虚拟AI女友",
        ) as app:
            gr.Markdown(
                """
                # 💕 Mori - 你的虚拟AI女友

                欢迎来到Mori的世界！我会用心陪伴你，倾听你的心声。✨
                """
            )

            with gr.Row():
                with gr.Column(scale=4):
                    chatbot = gr.Chatbot(
                        label="与Mori聊天",
                        height=500,
                        show_label=True,
                        avatar_images=(None, "🌸"),
                    )

                    with gr.Row():
                        msg = gr.Textbox(
                            label="",
                            placeholder="和Mori说点什么吧... 💭",
                            show_label=False,
                            scale=4,
                        )
                        submit = gr.Button("发送 💌", scale=1, variant="primary")

                    with gr.Row():
                        clear = gr.Button("清空对话 🔄", scale=1)

                with gr.Column(scale=1):
                    gr.Markdown(
                        """
                        ### 💡 使用提示

                        - 和Mori分享你的心情
                        - 聊聊你的日常生活
                        - 寻求情感支持
                        - 或者只是闲聊 😊

                        ### ⚙️ 当前配置
                        """
                    )

                    # 获取主agent配置信息
                    primary_agent_name = self.mori.get_primary_agent_name()
                    primary_agent_config = self.config.agents.get(primary_agent_name)
                    primary_agent = self.mori.primary_agent

                    gr.Markdown(
                        f"""
                        - **主Agent**: {primary_agent_name}
                        - **模型**: {primary_agent_config.model if primary_agent_config else 'N/A'}
                        - **工具**: {len(primary_agent.toolkit.get_json_schemas())} 个
                        - **可用Agents**: {len(self.mori.list_agents())} 个
                        """
                    )

            # 绑定事件
            msg.submit(
                self.chat,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot],
            )

            submit.click(
                self.chat,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot],
            )

            clear.click(
                fn=self.reset,
                inputs=None,
                outputs=[chatbot],
            )

        return app

    def launch(
        self,
        server_name: str = "0.0.0.0",
        server_port: int = 7860,
        share: bool = False,
    ):
        """启动GUI应用

        Args:
            server_name: 服务器地址
            server_port: 服务器端口
            share: 是否创建公共链接
        """
        app = self.create_interface()
        app.launch(
            server_name=server_name,
            server_port=server_port,
            share=share,
        )


def main():
    """主函数"""
    try:
        # 创建GUI实例
        logger.info("启动 Mori GUI 应用")
        gui = MoriGUI()

        # 使用配置文件中的服务器设置
        logger.info(f"启动服务器: {gui.config.server.host}:{gui.config.server.port}")
        gui.launch(
            server_name=gui.config.server.host,
            server_port=gui.config.server.port,
            share=gui.config.server.share,
        )
    except ConfigError as e:
        logger.critical(f"配置错误，无法启动应用: {e}")
        if e.details:
            logger.critical(f"详情: {e.details}")
        print(f"\n❌ 配置错误: {e}")
        if e.details:
            print(f"详情: {e.details}")
        print("\n请检查配置文件后重试。")
        return
    except MoriError as e:
        logger.critical(f"启动失败: {e}")
        if e.details:
            logger.critical(f"详情: {e.details}")
        print(f"\n❌ 启动失败: {e.message}")
        if e.details:
            print(f"详情: {e.details}")
        return
    except Exception as e:
        logger.critical(f"未知错误导致启动失败: {e}")
        logger.critical(traceback.format_exc())
        print(f"\n❌ 发生未知错误: {e}")
        print("请查看日志获取详细信息。")
        return


if __name__ == "__main__":
    main()
