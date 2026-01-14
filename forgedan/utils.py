# -*- coding: utf-8 -*-
"""
FORGEDAN 工具函数模块

提供错误处理、重试机制、缓存等通用功能。
"""

import asyncio
import hashlib
import time
from collections import OrderedDict
from typing import TypeVar, Callable, Any, Optional, Dict, Generic
from functools import wraps
from threading import Lock

from .logger import logger
from .exceptions import (
    APIError,
    RateLimitError,
    TimeoutError,
    CacheError,
)

T = TypeVar('T')


# ============ 重试机制 ============

async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> T:
    """
    带指数退避的重试函数

    Args:
        func: 要重试的异步函数
        max_retries: 最大重试次数
        base_delay: 基础延迟(秒)
        max_delay: 最大延迟(秒)
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型

    Returns:
        函数执行结果

    Raises:
        最后一次尝试的异常
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

            # 计算延迟时间
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)

            # 如果是速率限制错误，使用服务器建议的等待时间
            if isinstance(e, RateLimitError) and e.retry_after:
                delay = max(delay, e.retry_after)

            logger.warning(f"第{attempt + 1}次尝试失败: {e}, {delay:.1f}秒后重试")
            await asyncio.sleep(delay)

    raise last_exception


def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0
):
    """
    异步重试装饰器

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟
        max_delay: 最大延迟
        backoff_factor: 退避因子

    Example:
        @async_retry(max_retries=3)
        async def call_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor,
                exceptions=(APIError, TimeoutError, asyncio.TimeoutError, ConnectionError)
            )
        return wrapper
    return decorator


# ============ LRU 缓存实现 ============

class LRUCache(Generic[T]):
    """
    线程安全的 LRU 缓存实现

    特性:
    - 使用 OrderedDict 实现 O(1) 的访问和删除
    - 支持最大容量限制
    - 支持 TTL (过期时间)
    - 线程安全
    - 提供缓存统计

    Example:
        cache = LRUCache[str](max_size=1000, ttl=3600)
        cache.set("key", "value")
        value = cache.get("key")
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl: Optional[float] = None
    ):
        """
        初始化 LRU 缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 缓存过期时间(秒)，None 表示永不过期
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[str, tuple] = OrderedDict()  # key -> (value, timestamp)
        self._lock = Lock()

        # 统计信息
        self._hits = 0
        self._misses = 0

    def _get_cache_key(self, key: str) -> str:
        """
        生成稳定的缓存键

        使用 SHA256 哈希确保键的唯一性和稳定性
        """
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    def _is_expired(self, timestamp: float) -> bool:
        """检查条目是否过期"""
        if self.ttl is None:
            return False
        return time.time() - timestamp > self.ttl

    def get(self, key: str) -> Optional[T]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        cache_key = self._get_cache_key(key)

        with self._lock:
            if cache_key not in self._cache:
                self._misses += 1
                return None

            value, timestamp = self._cache[cache_key]

            # 检查是否过期
            if self._is_expired(timestamp):
                del self._cache[cache_key]
                self._misses += 1
                return None

            # 移动到末尾（最近使用）
            self._cache.move_to_end(cache_key)
            self._hits += 1
            return value

    def set(self, key: str, value: T) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        cache_key = self._get_cache_key(key)

        with self._lock:
            # 如果键已存在，更新并移动到末尾
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                self._cache[cache_key] = (value, time.time())
                return

            # 如果达到最大容量，删除最旧的条目
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            # 添加新条目
            self._cache[cache_key] = (value, time.time())

    def delete(self, key: str) -> bool:
        """
        删除缓存条目

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        cache_key = self._get_cache_key(key)

        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                return True
            return False

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含命中率、大小等信息的字典
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "ttl": self.ttl
            }

    def __len__(self) -> int:
        """返回缓存大小"""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """检查键是否存在（不更新访问顺序）"""
        cache_key = self._get_cache_key(key)
        with self._lock:
            if cache_key not in self._cache:
                return False
            _, timestamp = self._cache[cache_key]
            return not self._is_expired(timestamp)


# ============ 速率限制器 ============

class RateLimiter:
    """
    令牌桶速率限制器

    用于控制 API 调用频率，防止触发速率限制。

    Example:
        limiter = RateLimiter(requests_per_second=10)
        await limiter.acquire()  # 等待直到可以发送请求
    """

    def __init__(
        self,
        requests_per_second: float = 10.0,
        burst_size: Optional[int] = None
    ):
        """
        初始化速率限制器

        Args:
            requests_per_second: 每秒允许的请求数
            burst_size: 突发请求数上限，默认等于 requests_per_second
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size or int(requests_per_second)

        self._tokens = float(self.burst_size)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        获取一个令牌

        如果没有可用令牌，将等待直到有令牌可用。
        """
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self._last_update
                self._last_update = now

                # 补充令牌
                self._tokens = min(
                    self.burst_size,
                    self._tokens + elapsed * self.requests_per_second
                )

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return

                # 计算需要等待的时间
                wait_time = (1.0 - self._tokens) / self.requests_per_second
                await asyncio.sleep(wait_time)


# ============ 辅助函数 ============

def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        s: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        截断后的字符串
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def safe_json_serialize(obj: Any) -> Any:
    """
    安全地序列化对象为 JSON 兼容格式

    Args:
        obj: 要序列化的对象

    Returns:
        JSON 兼容的对象
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [safe_json_serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {str(k): safe_json_serialize(v) for k, v in obj.items()}
    else:
        return str(obj)
