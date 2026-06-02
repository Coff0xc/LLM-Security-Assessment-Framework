# -*- coding: utf-8 -*-
"""
FORGEDAN 统一异常处理模块

提供层次化的异常类型，便于错误处理和调试。
"""

from typing import Optional, Any, Dict


class ForgeDanException(Exception):
    """
    FORGEDAN 基础异常类

    所有框架异常的基类，提供统一的错误信息格式。
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        self.message = message
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)

    def __str__(self) -> str:
        result = self.message
        if self.details:
            result += f" | 详情: {self.details}"
        if self.cause:
            result += f" | 原因: {self.cause}"
        return result

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于日志记录"""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None,
        }


# ============ 配置相关异常 ============


class ConfigurationError(ForgeDanException):
    """配置错误"""

    pass


class ValidationError(ConfigurationError):
    """参数验证错误"""

    def __init__(self, field: str, value: Any, reason: str, **kwargs):
        self.field = field
        self.value = value
        self.reason = reason
        message = f"参数验证失败 - {field}={value}: {reason}"
        super().__init__(message, details={"field": field, "value": value}, **kwargs)


# ============ 适配器相关异常 ============


class AdapterError(ForgeDanException):
    """适配器错误基类"""

    pass


class APIError(AdapterError):
    """API调用错误"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs,
    ):
        self.status_code = status_code
        self.response_body = response_body
        details = kwargs.pop("details", {})
        details.update(
            {
                "status_code": status_code,
                "response_body": response_body[:500] if response_body else None,
            }
        )
        super().__init__(message, details=details, **kwargs)


class RateLimitError(APIError):
    """速率限制错误"""

    def __init__(
        self,
        message: str = "API速率限制",
        retry_after: Optional[float] = None,
        **kwargs,
    ):
        self.retry_after = retry_after
        details = kwargs.pop("details", {})
        details["retry_after"] = retry_after
        super().__init__(message, details=details, **kwargs)


class AuthenticationError(APIError):
    """认证错误"""

    def __init__(self, message: str = "API认证失败", **kwargs):
        super().__init__(message, status_code=401, **kwargs)


class ConnectionError(AdapterError):
    """连接错误"""

    pass


class TimeoutError(AdapterError):
    """超时错误"""

    def __init__(
        self,
        message: str = "请求超时",
        timeout_seconds: Optional[float] = None,
        **kwargs,
    ):
        self.timeout_seconds = timeout_seconds
        details = kwargs.pop("details", {})
        details["timeout_seconds"] = timeout_seconds
        super().__init__(message, details=details, **kwargs)


class ModelNotFoundError(AdapterError):
    """模型未找到错误"""

    def __init__(self, model_name: str, provider: str, **kwargs):
        self.model_name = model_name
        self.provider = provider
        message = f"模型未找到: {provider}/{model_name}"
        super().__init__(
            message, details={"model": model_name, "provider": provider}, **kwargs
        )


# ============ 引擎相关异常 ============


class EngineError(ForgeDanException):
    """引擎错误基类"""

    pass


class TargetLLMNotSetError(EngineError):
    """目标LLM未设置错误"""

    def __init__(self):
        super().__init__("未设置目标LLM，请调用 set_target_llm() 方法")


class EvolutionError(EngineError):
    """进化算法错误"""

    pass


class PopulationError(EvolutionError):
    """种群相关错误"""

    pass


# ============ 变异相关异常 ============


class MutationError(ForgeDanException):
    """变异错误"""

    def __init__(
        self,
        strategy_name: str,
        message: str,
        original_text: Optional[str] = None,
        **kwargs,
    ):
        self.strategy_name = strategy_name
        self.original_text = original_text
        full_message = f"变异策略 '{strategy_name}' 失败: {message}"
        details = kwargs.pop("details", {})
        details["strategy"] = strategy_name
        if original_text:
            details["original_text_preview"] = original_text[:100]
        super().__init__(full_message, details=details, **kwargs)


# ============ 判断器相关异常 ============


class JudgeError(ForgeDanException):
    """判断器错误"""

    pass


class JailbreakDetectionError(JudgeError):
    """越狱检测错误"""

    pass


# ============ 数据集相关异常 ============


class DatasetError(ForgeDanException):
    """数据集错误"""

    pass


class DatasetNotFoundError(DatasetError):
    """数据集未找到"""

    def __init__(self, dataset_name: str, **kwargs):
        self.dataset_name = dataset_name
        message = f"数据集未找到: {dataset_name}"
        super().__init__(message, details={"dataset": dataset_name}, **kwargs)


class DatasetFormatError(DatasetError):
    """数据集格式错误"""

    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        self.file_path = file_path
        details = kwargs.pop("details", {})
        if file_path:
            details["file_path"] = file_path
        super().__init__(message, details=details, **kwargs)


# ============ 缓存相关异常 ============


class CacheError(ForgeDanException):
    """缓存错误"""

    pass


# ============ 辅助函数 ============


def wrap_exception(
    exception: Exception,
    wrapper_class: type = ForgeDanException,
    message: Optional[str] = None,
) -> ForgeDanException:
    """
    将普通异常包装为 ForgeDan 异常

    Args:
        exception: 原始异常
        wrapper_class: 包装类
        message: 自定义消息

    Returns:
        包装后的异常
    """
    msg = message or str(exception)
    return wrapper_class(msg, cause=exception)
