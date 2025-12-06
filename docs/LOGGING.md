
# 日志系统使用指南

本文档介绍Mori项目的结构化日志系统及其使用方法。

## 功能特性

- ✅ **结构化日志**：支持JSON格式输出，便于日志分析和处理
- ✅ **日志轮转**：按文件大小自动轮转，防止日志文件过大
- ✅ **上下文追踪**：支持添加请求ID、会话ID、用户ID等上下文信息
- ✅ **错误日志分离**：错误级别日志单独存储，便于快速定位问题
- ✅ **人类可读输出**：控制台输出使用易读格式，文件支持JSON格式

## 基础使用

### 1. 设置日志器

```python
from logger import setup_logger

# 基础设置
logger = setup_logger(
    name="my_app",
    level="INFO",
    log_dir="logs",
    console=True,
    json_format=True,  # 文件使用JSON格式
    max_bytes=10 * 1024 * 1024,  # 10MB轮转
    backup_count=5,  # 保留5个备份
)

# 使用日志
logger.info("应用启动")
logger.debug("调试信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 2. 获取已存在的日志器

```python
from logger import get_logger

# 获取默认日志器
logger = get_logger()

# 获取指定名称的日志器
logger = get_logger("my_app")
```

## 结构化日志

### JSON格式输出

启用`json_format=True`后，日志文件将以JSON格式存储：

```json
{
  "timestamp": "2025-12-06 12:00:00",
  "level": "INFO",
  "logger": "my_app",
  "message": "用户登录成功",
  "module": "auth",
  "function": "login",
  "line": 42,
  "context": {
    "request_id": "req-123",
    "user_id": "user-456",
    "session_id": "sess-789"
  }
}
```

### 添加上下文信息

#### 方式1：使用上下文管理器（推荐）

```python
from logger import LogContext, get_logger

logger = get_logger()

# 在上下文中的所有日志都会包含这些信息
with LogContext(request_id="req-123", user_id="user-456"):
    logger.info("处理用户请求")
    # 日志会自动包含 request_id 和 user_id

    # 嵌套上下文
    with LogContext(action="update_profile"):
        logger.info("更新用户资料")
        # 日志会包含所有上下文：request_id, user_id, action
```

#### 方式2：手动设置和清除

```python
from logger import set_log_context, clear_log_context, get_logger

logger = get_logger()

# 设置上下文
set_log_context(request_id="req-123", user_id="user-456")
logger.info("处理请求")

# 清除上下文
clear_log_context()
```

#### 方式3：获取当前上下文

```python
from logger import get_log_context

context = get_log_context()
print(f"当前上下文: {context}")
```

## 实际应用场景

### 场景1：Web API请求追踪

```python
import uuid
from logger import LogContext, get_logger

logger = get_logger()

async def handle_request(user_id: str):
    request_id = str(uuid.uuid4())

    with LogContext(request_id=request_id, user_id=user_id):
        logger.info("开始处理API请求")

        try:
            # 业务逻辑
            result = await process_data()
            logger.info("请求处理成功", extra_fields={"result_size": len(result)})
            return result
        except Exception as e:
            logger.exception("请求处理失败")
            raise
```

### 场景2：多Agent对话追踪

```python
from logger import LogContext, get_logger

logger = get_logger()

async def chat(session_id: str, message: str):
    with LogContext(session_id=session_id):
        logger.info(f"收到用户消息: {message}")

        # 主Agent处理
        with LogContext(agent="main"):
            logger.info("主Agent开始处理")
            response = await main_agent.process(message)

        # 如果需要调用子Agent
        if needs_sub_agent(response):
            with LogContext(agent="specialist"):
                logger.info("调用专家Agent")
                response = await specialist_agent.process(message)

        logger.info(f"返回响应: {response}")
        return response
```

### 场景3：异常日志记录

```python
from logger import get_logger

logger = get_logger()

try:
    risky_operation()
except ValueError as e:
    # exception() 会自动记录完整的堆栈信息
    logger.exception("操作失败")
    # 在JSON格式中，异常信息会包含在 "exception" 字段中
except Exception as e:
    logger.error(f"未预期的错误: {e}")
    raise
```

## 日志轮转

日志文件会在达到指定大小时自动轮转：

```
logs/
├── my_app.log          # 当前日志文件
├── my_app.log.1        # 第一个备份
├── my_app.log.2        # 第二个备份
├── my_app_error.log    # 当前错误日志
└── my_app_error.log.1  # 错误日志备份
```

## 配置建议

### 开发环境

```python
logger = setup_logger(
    name="mori_dev",
    level="DEBUG",  # 显示所有日志
    log_dir="logs",
    console=True,  # 在控制台显示
    json_format=False,  # 使用易读格式
)
```

### 生产环境

```python
logger = setup_logger(
    name="mori_prod",
    level="INFO",  # 只记录重要信息
    log_dir="/var/log/mori",
    console=False,  # 不输出到控制台
    json_format=True,  # 使用JSON便于分析
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=10,  # 保留更多备份
)
```

## 最佳实践

1. **始终使用上下文管理器**：在处理请求、任务时使用`LogContext`添加追踪信息

2. **合理设置日志级别**：
   - DEBUG: 详细的调试信息
   - INFO: 正常的业务流程
   - WARNING: 警告但不影响运行
   - ERROR: 错误需要关注
   - CRITICAL: 严重错误

3. **避免敏感信息**：不要在日志中记录密码、令牌等敏感信息

4. **使用结构化数据**：在JSON模式下，利用上下文字段而不是字符串拼接

5. **异常处理**：使用`logger.exception()`而不是`logger.error()`来自动记录堆栈信息

## 日志分析

### 查看JSON日志

```bash
# 美化输出
cat logs/mori.log | jq '.'

# 过滤特定用户的日志
cat logs/mori.log | jq 'select(.context.user_id == "user-456")'

# 查看错误日志
cat logs/mori.log | jq 'select(.level == "ERROR")'

# 统计请求数
cat logs/mori.log | jq -r '.context.request_id' | sort | uniq | wc -l
```

## 性能考虑

- JSON格式化会增加少量性能开销，但对于大多数应用可以忽略
- 日志轮转在文件达到大小限制时会有短暂的锁定
- 上下文变量使用`contextvars`，在异步环境中自动隔离

## 故障排查

### 日志文件未创建

检查日志目录权限：
```bash
ls -la logs/
chmod 755 logs/
```

### Windows文件锁定问题

确保在程序退出前关闭所有日志处理器：
```python
for handler in logger.handlers[:]:
    handler.close()
    logger.removeHandler(handler)
```

### 上下文信息丢失

确保在异步函数中正确使用上下文管理器，避免跨任务传递。
