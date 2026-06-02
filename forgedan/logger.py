# -*- coding: utf-8 -*-
"""
FORGEDAN 结构化日志系统 (优化版)

特性:
- JSON 结构化日志
- 日志轮转
- 上下文追踪 (请求ID、操作ID)
- 性能指标日志
- 安全事件日志
- 异步日志支持
- 多输出目标
"""

import logging
import logging.handlers
import sys
import json
import time
import uuid
import threading
import queue
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
from functools import wraps
import copy

# ============== 日志级别扩展 ==============


class LogLevel(Enum):
    """扩展日志级别"""

    TRACE = 5  # 详细追踪
    DEBUG = 10  # 调试信息
    INFO = 20  # 一般信息
    WARNING = 30  # 警告
    ERROR = 40  # 错误
    CRITICAL = 50  # 严重错误
    SECURITY = 55  # 安全事件
    AUDIT = 60  # 审计日志


# 注册自定义级别
logging.addLevelName(5, "TRACE")
logging.addLevelName(55, "SECURITY")
logging.addLevelName(60, "AUDIT")


# ============== 日志上下文 ==============


class LogContext:
    """线程本地日志上下文"""

    _local = threading.local()

    @classmethod
    def get(cls) -> Dict[str, Any]:
        """获取当前上下文"""
        if not hasattr(cls._local, "context"):
            cls._local.context = {}
        return cls._local.context

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """设置上下文值"""
        ctx = cls.get()
        ctx[key] = value

    @classmethod
    def update(cls, data: Dict[str, Any]) -> None:
        """批量更新上下文"""
        ctx = cls.get()
        ctx.update(data)

    @classmethod
    def clear(cls) -> None:
        """清除上下文"""
        cls._local.context = {}

    @classmethod
    def remove(cls, key: str) -> None:
        """移除指定键"""
        ctx = cls.get()
        ctx.pop(key, None)

    @classmethod
    @contextmanager
    def scope(cls, **kwargs):
        """上下文作用域管理器"""
        old_context = copy.deepcopy(cls.get())
        try:
            cls.update(kwargs)
            yield
        finally:
            cls._local.context = old_context


# ============== 结构化日志记录 ==============


@dataclass
class LogRecord:
    """结构化日志记录"""

    timestamp: str
    level: str
    logger_name: str
    message: str
    module: str = ""
    function: str = ""
    line: int = 0
    # 上下文字段
    request_id: Optional[str] = None
    operation_id: Optional[str] = None
    user_id: Optional[str] = None
    # 扩展字段
    extra: Dict[str, Any] = field(default_factory=dict)
    # 异常信息
    exception: Optional[str] = None
    stack_trace: Optional[str] = None
    # 性能指标
    duration_ms: Optional[float] = None
    # 安全相关
    security_event: Optional[str] = None
    severity: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 移除空值
        return {k: v for k, v in data.items() if v is not None and v != "" and v != {}}

    def to_json(self, indent: Optional[int] = None) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(
            self.to_dict(), ensure_ascii=False, default=str, indent=indent
        )


# ============== JSON 格式化器 ==============


class JSONFormatter(logging.Formatter):
    """JSON 日志格式化器"""

    def __init__(self, include_context: bool = True, pretty: bool = False):
        super().__init__()
        self.include_context = include_context
        self.pretty = pretty

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 基础字段
        log_record = LogRecord(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line=record.lineno,
        )

        # 添加上下文
        if self.include_context:
            ctx = LogContext.get()
            log_record.request_id = ctx.get("request_id")
            log_record.operation_id = ctx.get("operation_id")
            log_record.user_id = ctx.get("user_id")

        # 异常信息
        if record.exc_info:
            log_record.exception = str(record.exc_info[1])
            log_record.stack_trace = "".join(
                traceback.format_exception(*record.exc_info)
            )

        # 额外字段
        if hasattr(record, "extra_data"):
            log_record.extra = record.extra_data

        # 性能指标
        if hasattr(record, "duration_ms"):
            log_record.duration_ms = record.duration_ms

        # 安全事件
        if hasattr(record, "security_event"):
            log_record.security_event = record.security_event
            log_record.severity = getattr(record, "severity", "medium")

        indent = 2 if self.pretty else None
        return log_record.to_json(indent=indent)


class ColoredFormatter(logging.Formatter):
    """彩色控制台格式化器"""

    COLORS = {
        "TRACE": "\033[37m",  # 白色
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
        "SECURITY": "\033[41m",  # 红底
        "AUDIT": "\033[44m",  # 蓝底
    }
    RESET = "\033[0m"

    def __init__(self, format_string: Optional[str] = None, use_color: bool = True):
        if format_string is None:
            format_string = "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s"
        super().__init__(format_string, datefmt="%Y-%m-%d %H:%M:%S")
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 添加上下文到消息
        ctx = LogContext.get()
        if ctx.get("request_id"):
            record.msg = f"[{ctx['request_id'][:8]}] {record.msg}"

        formatted = super().format(record)

        if self.use_color:
            color = self.COLORS.get(record.levelname, "")
            return f"{color}{formatted}{self.RESET}"

        return formatted


# ============== 异步日志处理器 ==============


class AsyncHandler(logging.Handler):
    """异步日志处理器 - 非阻塞写入"""

    def __init__(self, handler: logging.Handler, queue_size: int = 10000):
        super().__init__()
        self._handler = handler
        self._queue: queue.Queue = queue.Queue(maxsize=queue_size)
        self._shutdown = False
        self._worker = threading.Thread(target=self._process_logs, daemon=True)
        self._worker.start()

    def emit(self, record: logging.LogRecord) -> None:
        """非阻塞发送日志"""
        if self._shutdown:
            return

        try:
            self._queue.put_nowait(record)
        except queue.Full:
            # 队列满时丢弃日志
            pass

    def _process_logs(self) -> None:
        """后台处理日志"""
        while not self._shutdown:
            try:
                record = self._queue.get(timeout=1.0)
                self._handler.emit(record)
            except queue.Empty:
                continue
            except Exception:
                pass

    def close(self) -> None:
        """关闭处理器"""
        self._shutdown = True
        self._worker.join(timeout=5.0)
        self._handler.close()
        super().close()


# ============== 日志过滤器 ==============


class LevelRangeFilter(logging.Filter):
    """级别范围过滤器"""

    def __init__(self, min_level: int, max_level: int = logging.CRITICAL + 10):
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return self.min_level <= record.levelno <= self.max_level


class ContextFilter(logging.Filter):
    """上下文过滤器 - 只记录特定上下文的日志"""

    def __init__(self, key: str, value: Any):
        super().__init__()
        self.key = key
        self.value = value

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = LogContext.get()
        return ctx.get(self.key) == self.value


class SecurityFilter(logging.Filter):
    """安全事件过滤器"""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= 55 or hasattr(record, "security_event")


# ============== 结构化日志器 ==============


class StructuredLogger:
    """结构化日志器"""

    def __init__(
        self,
        name: str = "forgedan",
        level: int = logging.INFO,
        log_dir: Optional[Path] = None,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_json: bool = True,
        enable_async: bool = False,
        rotation_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        use_color: bool = True,
    ):
        self.name = name
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 创建底层 logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.handlers.clear()
        self._logger.propagate = False

        self._handlers: List[logging.Handler] = []

        # 控制台处理器
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(ColoredFormatter(use_color=use_color))
            self._add_handler(console_handler)

        # 文件处理器 (文本格式)
        if enable_file:
            text_file = self.log_dir / f"{name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                text_file,
                maxBytes=rotation_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(ColoredFormatter(use_color=False))
            handler = AsyncHandler(file_handler) if enable_async else file_handler
            self._add_handler(handler)

        # JSON 日志处理器
        if enable_json:
            json_file = self.log_dir / f"{name}.json.log"
            json_handler = logging.handlers.RotatingFileHandler(
                json_file,
                maxBytes=rotation_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            json_handler.setFormatter(JSONFormatter(include_context=True))
            handler = AsyncHandler(json_handler) if enable_async else json_handler
            self._add_handler(handler)

        # 安全日志处理器 (单独文件)
        security_file = self.log_dir / f"{name}_security.log"
        security_handler = logging.handlers.RotatingFileHandler(
            security_file,
            maxBytes=rotation_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        security_handler.setFormatter(JSONFormatter(include_context=True))
        security_handler.addFilter(SecurityFilter())
        handler = AsyncHandler(security_handler) if enable_async else security_handler
        self._add_handler(handler)

    def _add_handler(self, handler: logging.Handler) -> None:
        """添加处理器"""
        self._handlers.append(handler)
        self._logger.addHandler(handler)

    def _log(
        self,
        level: int,
        msg: str,
        *args,
        exc_info: bool = False,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """内部日志方法"""
        record_extra = {}

        if extra:
            record_extra["extra_data"] = extra

        for key in ["duration_ms", "security_event", "severity"]:
            if key in kwargs:
                record_extra[key] = kwargs.pop(key)

        self._logger.log(level, msg, *args, exc_info=exc_info, extra=record_extra)

    # 标准日志方法
    def trace(self, msg: str, *args, **kwargs) -> None:
        """追踪级别日志"""
        self._log(5, msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        """调试级别日志"""
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """信息级别日志"""
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """警告级别日志"""
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, exc_info: bool = True, **kwargs) -> None:
        """错误级别日志"""
        self._log(logging.ERROR, msg, *args, exc_info=exc_info, **kwargs)

    def critical(self, msg: str, *args, exc_info: bool = True, **kwargs) -> None:
        """严重错误级别日志"""
        self._log(logging.CRITICAL, msg, *args, exc_info=exc_info, **kwargs)

    def security(
        self, msg: str, event: str, severity: str = "medium", **kwargs
    ) -> None:
        """安全事件日志"""
        self._log(55, msg, security_event=event, severity=severity, **kwargs)

    def audit(self, msg: str, action: str, **kwargs) -> None:
        """审计日志"""
        extra = kwargs.pop("extra", {})
        extra["action"] = action
        self._log(60, msg, extra=extra, **kwargs)

    # 性能日志
    def performance(self, msg: str, duration_ms: float, **kwargs) -> None:
        """性能日志"""
        self._log(logging.INFO, msg, duration_ms=duration_ms, **kwargs)

    @contextmanager
    def timer(self, operation: str, log_level: int = logging.INFO):
        """计时上下文管理器"""
        start_time = time.perf_counter()
        operation_id = str(uuid.uuid4())[:8]

        with LogContext.scope(operation_id=operation_id):
            try:
                self._log(log_level, f"开始: {operation}")
                yield operation_id
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self._log(log_level, f"完成: {operation}", duration_ms=duration_ms)

    def timed(self, func: Optional[Callable] = None, level: int = logging.INFO):
        """计时装饰器"""

        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapper(*args, **kwargs):
                with self.timer(f.__name__, level):
                    return f(*args, **kwargs)

            return wrapper

        if func is not None:
            return decorator(func)
        return decorator

    # 上下文管理
    def with_context(self, **kwargs):
        """创建带上下文的日志作用域"""
        return LogContext.scope(**kwargs)

    def set_request_id(self, request_id: Optional[str] = None) -> str:
        """设置请求ID"""
        request_id = request_id or str(uuid.uuid4())
        LogContext.set("request_id", request_id)
        return request_id

    # 批量日志
    def log_batch(
        self, records: List[Dict[str, Any]], level: int = logging.INFO
    ) -> None:
        """批量记录日志"""
        for record in records:
            msg = record.pop("message", "")
            self._log(level, msg, extra=record)

    # 关闭
    def close(self) -> None:
        """关闭所有处理器"""
        for handler in self._handlers:
            handler.close()
            self._logger.removeHandler(handler)


# ============== 便捷函数 ==============

# 全局日志器实例
_default_logger: Optional[StructuredLogger] = None
_logger_lock = threading.Lock()


def setup_logger(
    name: str = "forgedan",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
    **kwargs,
) -> logging.Logger:
    """配置日志记录器 (兼容旧接口)"""
    global _default_logger

    with _logger_lock:
        log_dir = log_file.parent if log_file else kwargs.get("log_dir")
        _default_logger = StructuredLogger(
            name=name, level=level, log_dir=log_dir, **kwargs
        )
        return _default_logger._logger


def get_logger(name: Optional[str] = None) -> StructuredLogger:
    """获取日志器实例"""
    global _default_logger

    if name is None:
        with _logger_lock:
            if _default_logger is None:
                _default_logger = StructuredLogger()
            return _default_logger

    return StructuredLogger(name=name)


def log_security_event(
    event: str, message: str, severity: str = "medium", **extra
) -> None:
    """记录安全事件"""
    logger = get_logger()
    logger.security(message, event=event, severity=severity, extra=extra)


def log_audit(action: str, message: str, **extra) -> None:
    """记录审计日志"""
    logger = get_logger()
    logger.audit(message, action=action, extra=extra)


@contextmanager
def log_operation(operation: str, **context):
    """操作日志上下文"""
    logger = get_logger()
    operation_id = str(uuid.uuid4())[:8]

    with LogContext.scope(operation_id=operation_id, **context):
        start_time = time.perf_counter()
        logger.info(f"开始操作: {operation}")

        try:
            yield operation_id
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"操作完成: {operation}", duration_ms=duration_ms)
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"操作失败: {operation} - {e}", duration_ms=duration_ms)
            raise


def timed_operation(
    func: Optional[Callable] = None, operation_name: Optional[str] = None
):
    """计时操作装饰器"""

    def decorator(f: Callable) -> Callable:
        name = operation_name or f.__name__

        @wraps(f)
        def wrapper(*args, **kwargs):
            with log_operation(name):
                return f(*args, **kwargs)

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


# ============== 全局日志实例 (兼容性) ==============

logger = setup_logger()
