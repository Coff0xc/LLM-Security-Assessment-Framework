# -*- coding: utf-8 -*-
"""
错误处理和重试机制
"""

import asyncio
from typing import TypeVar, Callable, Any
from functools import wraps
from ..logger import logger

T = TypeVar('T')


class APIError(Exception):
    """API调用错误"""
    pass


class RateLimitError(APIError):
    """速率限制错误"""
    pass


class TimeoutError(APIError):
    """超时错误"""
    pass


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> T:
    """
    带指数退避的重试装饰器

    Args:
        func: 要重试的异步函数
        max_retries: 最大重试次数
        base_delay: 基础延迟(秒)
        max_delay: 最大延迟(秒)
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(f"重试{max_retries}次后仍失败: {e}")
                raise

            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            logger.warning(f"第{attempt + 1}次尝试失败: {e}, {delay:.1f}秒后重试")
            await asyncio.sleep(delay)

    raise last_exception


def async_retry(max_retries: int = 3, base_delay: float = 1.0):
    """异步重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay,
                exceptions=(APIError, TimeoutError, asyncio.TimeoutError)
            )
        return wrapper
    return decorator
