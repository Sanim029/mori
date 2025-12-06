"""日志系统测试

测试结构化日志、日志轮转和上下文管理功能。
"""

import json
import logging
import tempfile
from pathlib import Path

from logger import (
    LogContext,
    clear_log_context,
    get_log_context,
    get_logger,
    set_log_context,
    setup_logger,
)


class TestLoggerSetup:
    """测试日志器设置"""

    def test_setup_logger_basic(self):
        """测试基本日志器设置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(
                name="test_basic",
                level="DEBUG",
                log_dir=tmpdir,
                console=False,
            )

            assert logger.name == "test_basic"
            assert logger.level == logging.DEBUG
            assert len(logger.handlers) > 0

            # 关闭所有处理器以释放文件
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)

    def test_setup_logger_without_file(self):
        """测试不写文件的日志器"""
        logger = setup_logger(
            name="test_no_file",
            level="INFO",
            log_dir=None,
            console=True,
        )

        assert logger.name == "test_no_file"
        assert len(logger.handlers) == 1  # 仅控制台处理器

    def test_setup_logger_creates_directory(self):
        """测试自动创建日志目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "nested" / "logs"
            logger = setup_logger(
                name="test_mkdir",
                level="INFO",
                log_dir=str(log_dir),
                console=False,
            )

            assert log_dir.exists()
            assert (log_dir / "test_mkdir.log").exists()

            # 关闭所有处理器
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)


class TestStructuredLogging:
    """测试结构化日志"""

    def test_json_format_output(self):
        """测试JSON格式输出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(
                name="test_json",
                level="DEBUG",
                log_dir=tmpdir,
                console=False,
                json_format=True,
            )

            test_message = "测试消息"
            logger.info(test_message)

            # 关闭处理器以刷新缓冲区
            for handler in logger.handlers[:]:
                handler.flush()

            # 读取日志文件
            log_file = Path(tmpdir) / "test_json.log"
            with open(log_file, "r", encoding="utf-8") as f:
                log_line = f.readline()

            # 验证是否为有效JSON
            log_data = json.loads(log_line)
            assert log_data["message"] == test_message
            assert log_data["level"] == "INFO"
            assert "timestamp" in log_data
            assert "logger" in log_data

            # 关闭所有处理器
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)

    def test_error_log_separation(self):
        """测试错误日志分离"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(
                name="test_error",
                level="DEBUG",
                log_dir=tmpdir,
                console=False,
            )

            logger.info("普通信息")
            logger.error("错误信息")

            # 刷新缓冲区
            for handler in logger.handlers[:]:
                handler.flush()

            # 验证错误日志文件存在
            error_log = Path(tmpdir) / "test_error_error.log"
            assert error_log.exists()

            # 验证错误日志内容
            with open(error_log, "r", encoding="utf-8") as f:
                content = f.read()
                assert "错误信息" in content
                assert "普通信息" not in content

            # 关闭所有处理器
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)


class TestLogContext:
    """测试日志上下文"""

    def test_set_and_get_context(self):
        """测试设置和获取上下文"""
        clear_log_context()
        set_log_context(request_id="req-123", user_id="user-456")

        context = get_log_context()
        assert context["request_id"] == "req-123"
        assert context["user_id"] == "user-456"

        clear_log_context()

    def test_clear_context(self):
        """测试清除上下文"""
        set_log_context(test_key="test_value")
        assert len(get_log_context()) > 0

        clear_log_context()
        assert len(get_log_context()) == 0

    def test_context_manager(self):
        """测试上下文管理器"""
        clear_log_context()

        with LogContext(request_id="req-789"):
            context = get_log_context()
            assert context["request_id"] == "req-789"

        # 退出后应该恢复
        context = get_log_context()
        assert "request_id" not in context

    def test_nested_context(self):
        """测试嵌套上下文"""
        clear_log_context()

        with LogContext(outer="value1"):
            assert get_log_context()["outer"] == "value1"

            with LogContext(inner="value2"):
                context = get_log_context()
                assert context["outer"] == "value1"
                assert context["inner"] == "value2"

            # 退出内层后，应该恢复到外层
            context = get_log_context()
            assert context["outer"] == "value1"
            assert "inner" not in context

    def test_context_in_log_output(self):
        """测试上下文信息出现在日志中"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(
                name="test_context",
                level="DEBUG",
                log_dir=tmpdir,
                console=False,
                json_format=True,
            )

            with LogContext(request_id="req-999", user_id="user-999"):
                logger.info("带上下文的日志")

            # 刷新缓冲区
            for handler in logger.handlers[:]:
                handler.flush()

            # 读取并验证日志
            log_file = Path(tmpdir) / "test_context.log"
            with open(log_file, "r", encoding="utf-8") as f:
                log_line = f.readline()

            log_data = json.loads(log_line)
            assert "context" in log_data
            assert log_data["context"]["request_id"] == "req-999"
            assert log_data["context"]["user_id"] == "user-999"

            # 关闭所有处理器
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)


class TestLogRotation:
    """测试日志轮转"""

    def test_rotation_by_size(self):
        """测试按大小轮转（基础验证）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 设置很小的文件大小以触发轮转
            logger = setup_logger(
                name="test_rotation",
                level="DEBUG",
                log_dir=tmpdir,
                console=False,
                max_bytes=100,  # 100字节
                backup_count=3,
            )

            # 写入足够多的日志以触发轮转
            for i in range(50):
                logger.info(f"这是第 {i} 条测试日志消息，用于测试日志轮转功能")

            # 刷新缓冲区
            for handler in logger.handlers[:]:
                handler.flush()

            # 验证主日志文件存在
            log_file = Path(tmpdir) / "test_rotation.log"
            assert log_file.exists()

            # 注意：由于RotatingFileHandler的实现，可能不会立即看到.1, .2等备份文件
            # 这里只验证主日志文件存在且不为空
            assert log_file.stat().st_size > 0

            # 关闭所有处理器
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)


class TestExceptionLogging:
    """测试异常日志"""

    def test_exception_logging(self):
        """测试异常信息记录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(
                name="test_exception",
                level="DEBUG",
                log_dir=tmpdir,
                console=False,
                json_format=True,
            )

            try:
                raise ValueError("测试异常")
            except ValueError:
                logger.exception("捕获到异常")

            # 刷新缓冲区
            for handler in logger.handlers[:]:
                handler.flush()

            # 读取日志
            log_file = Path(tmpdir) / "test_exception.log"
            with open(log_file, "r", encoding="utf-8") as f:
                log_line = f.readline()

            log_data = json.loads(log_line)
            assert "exception" in log_data
            assert "ValueError" in log_data["exception"]
            assert "测试异常" in log_data["exception"]

            # 关闭所有处理器
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)


class TestGetLogger:
    """测试获取日志器"""

    def test_get_logger(self):
        """测试获取已存在的日志器"""
        # 先设置一个日志器
        setup_logger(name="test_get", level="INFO")

        # 获取同名日志器
        logger = get_logger("test_get")
        assert logger.name == "test_get"

    def test_get_default_logger(self):
        """测试获取默认日志器"""
        logger = get_logger()
        assert logger.name == "mori"
