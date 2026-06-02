# -*- coding: utf-8 -*-
"""
FORGEDAN 工具函数模块 (优化版)

提供错误处理、重试机制、缓存、熔断器等通用功能。
优化点:
- 添加熔断器 (Circuit Breaker) 防止级联失败
- 缓存预热和统计增强
- 请求去重器
- 结构化日志支持
"""

import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from pathlib import Path
from typing import TypeVar, Callable, Any, Optional, Dict, Generic, List
from functools import wraps
from threading import Lock
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .logger import logger
from .exceptions import (
    APIError,
    RateLimitError,
    TimeoutError,
)

T = TypeVar("T")


# ============ 熔断器状态枚举 ============


class CircuitState(Enum):
    """熔断器状态"""

    CLOSED = "closed"  # 正常工作
    OPEN = "open"  # 熔断，拒绝请求
    HALF_OPEN = "half_open"  # 半开，允许部分请求


@dataclass
class CircuitBreakerStats:
    """熔断器统计"""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: List[Dict] = field(default_factory=list)


class CircuitBreaker:
    """
    熔断器实现 (Circuit Breaker Pattern)

    防止对失败服务的重复调用，实现快速失败和自动恢复。

    状态转换:
    - CLOSED -> OPEN: 连续失败次数达到阈值
    - OPEN -> HALF_OPEN: 超过恢复超时时间
    - HALF_OPEN -> CLOSED: 探测请求成功
    - HALF_OPEN -> OPEN: 探测请求失败

    Example:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

        @breaker
        async def call_api():
            ...
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
        excluded_exceptions: tuple = (),
    ):
        """
        初始化熔断器

        Args:
            failure_threshold: 触发熔断的连续失败次数
            recovery_timeout: 熔断后等待恢复的时间(秒)
            half_open_max_calls: 半开状态允许的最大探测请求数
            success_threshold: 半开状态需要连续成功的次数才能关闭熔断
            excluded_exceptions: 不计入失败的异常类型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        self.excluded_exceptions = excluded_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = Lock()

        # 统计信息
        self._stats = CircuitBreakerStats()

    @property
    def state(self) -> CircuitState:
        """获取当前状态（考虑超时自动转换）"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if (
                    self._last_failure_time
                    and time.time() - self._last_failure_time >= self.recovery_timeout
                ):
                    self._transition_to(CircuitState.HALF_OPEN)
            return self._state

    def _transition_to(self, new_state: CircuitState):
        """状态转换"""
        old_state = self._state
        self._state = new_state

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._success_count = 0
        elif new_state == CircuitState.CLOSED:
            self._failure_count = 0

        # 记录状态变化
        self._stats.state_changes.append(
            {
                "from": old_state.value,
                "to": new_state.value,
                "time": datetime.now().isoformat(),
            }
        )

        logger.info(f"熔断器状态变化: {old_state.value} -> {new_state.value}")

    def _record_success(self):
        """记录成功调用"""
        with self._lock:
            self._stats.total_calls += 1
            self._stats.successful_calls += 1
            self._stats.last_success_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0  # 重置失败计数

    def _record_failure(self, exception: Exception):
        """记录失败调用"""
        # 检查是否为排除的异常
        if isinstance(exception, self.excluded_exceptions):
            return

        with self._lock:
            self._stats.total_calls += 1
            self._stats.failed_calls += 1
            self._stats.last_failure_time = time.time()
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

    def allow_request(self) -> bool:
        """检查是否允许请求"""
        current_state = self.state  # 触发可能的状态转换

        with self._lock:
            if current_state == CircuitState.CLOSED:
                return True
            elif current_state == CircuitState.OPEN:
                self._stats.rejected_calls += 1
                return False
            else:  # HALF_OPEN
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "state": self.state.value,
            "total_calls": self._stats.total_calls,
            "successful_calls": self._stats.successful_calls,
            "failed_calls": self._stats.failed_calls,
            "rejected_calls": self._stats.rejected_calls,
            "failure_count": self._failure_count,
            "success_rate": (
                self._stats.successful_calls / self._stats.total_calls
                if self._stats.total_calls > 0
                else 0
            ),
            "state_changes": self._stats.state_changes[-10:],  # 最近10次状态变化
        }

    def reset(self):
        """重置熔断器"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0

    def __call__(self, func: Callable) -> Callable:
        """装饰器用法"""

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not self.allow_request():
                raise APIError(f"熔断器开启，请求被拒绝 (状态: {self.state.value})")

            try:
                result = await func(*args, **kwargs)
                self._record_success()
                return result
            except Exception as e:
                self._record_failure(e)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not self.allow_request():
                raise APIError(f"熔断器开启，请求被拒绝 (状态: {self.state.value})")

            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result
            except Exception as e:
                self._record_failure(e)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper


# ============ 重试机制 ============


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    circuit_breaker: Optional[CircuitBreaker] = None,
) -> T:
    """
    带指数退避的重试函数（支持熔断器）

    Args:
        func: 要重试的异步函数
        max_retries: 最大重试次数
        base_delay: 基础延迟(秒)
        max_delay: 最大延迟(秒)
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型
        circuit_breaker: 可选的熔断器实例

    Returns:
        函数执行结果

    Raises:
        最后一次尝试的异常
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        # 检查熔断器
        if circuit_breaker and not circuit_breaker.allow_request():
            raise APIError("熔断器开启，请求被拒绝")

        try:
            result = await func()
            if circuit_breaker:
                circuit_breaker._record_success()
            return result
        except exceptions as e:
            last_exception = e

            if circuit_breaker:
                circuit_breaker._record_failure(e)

            if attempt == max_retries:
                logger.error(f"重试{max_retries}次后仍失败: {e}")
                raise

            # 计算延迟时间（带抖动）
            jitter = 0.1 * base_delay * (backoff_factor**attempt)
            delay = min(base_delay * (backoff_factor**attempt), max_delay)
            delay += jitter * (0.5 - time.time() % 1)  # 添加随机抖动

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
    backoff_factor: float = 2.0,
    circuit_breaker: Optional[CircuitBreaker] = None,
):
    """
    异步重试装饰器（支持熔断器）

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟
        max_delay: 最大延迟
        backoff_factor: 退避因子
        circuit_breaker: 可选的熔断器实例

    Example:
        breaker = CircuitBreaker()

        @async_retry(max_retries=3, circuit_breaker=breaker)
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
                exceptions=(
                    APIError,
                    TimeoutError,
                    asyncio.TimeoutError,
                    ConnectionError,
                ),
                circuit_breaker=circuit_breaker,
            )

        return wrapper

    return decorator


# ============ LRU 缓存实现 (增强版) ============


class LRUCache(Generic[T]):
    """
    线程安全的 LRU 缓存实现 (增强版)

    特性:
    - 使用 OrderedDict 实现 O(1) 的访问和删除
    - 支持最大容量限制
    - 支持 TTL (过期时间)
    - 线程安全
    - 提供缓存统计和命中率
    - 支持缓存预热
    - 支持多级缓存键
    - 支持批量操作

    Example:
        cache = LRUCache[str](max_size=1000, ttl=3600)
        cache.set("key", "value")
        value = cache.get("key")

        # 预热缓存
        cache.warm_up({"key1": "value1", "key2": "value2"})
    """

    def __init__(
        self, max_size: int = 1000, ttl: Optional[float] = None, name: str = "default"
    ):
        """
        初始化 LRU 缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 缓存过期时间(秒)，None 表示永不过期
            name: 缓存名称（用于日志）
        """
        self.max_size = max_size
        self.ttl = ttl
        self.name = name
        self._cache: OrderedDict[str, tuple] = (
            OrderedDict()
        )  # key -> (value, timestamp, access_count)
        self._lock = Lock()

        # 增强统计信息
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expired = 0
        self._total_access_time = 0.0
        self._access_count = 0
        self._created_at = time.time()

    def _get_cache_key(self, key: str) -> str:
        """
        生成稳定的缓存键

        使用 SHA256 哈希确保键的唯一性和稳定性
        """
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _is_expired(self, timestamp: float) -> bool:
        """检查条目是否过期"""
        if self.ttl is None:
            return False
        return time.time() - timestamp > self.ttl

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值，如果不存在或已过期则返回 default
        """
        start_time = time.time()
        cache_key = self._get_cache_key(key)

        with self._lock:
            self._access_count += 1

            if cache_key not in self._cache:
                self._misses += 1
                self._total_access_time += time.time() - start_time
                return default

            value, timestamp, access_count = self._cache[cache_key]

            # 检查是否过期
            if self._is_expired(timestamp):
                del self._cache[cache_key]
                self._misses += 1
                self._expired += 1
                self._total_access_time += time.time() - start_time
                return default

            # 移动到末尾（最近使用）并更新访问计数
            self._cache.move_to_end(cache_key)
            self._cache[cache_key] = (value, timestamp, access_count + 1)
            self._hits += 1
            self._total_access_time += time.time() - start_time
            return value

    def set(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 可选的单独 TTL（覆盖默认）
        """
        cache_key = self._get_cache_key(key)
        timestamp = time.time()

        # 如果指定了单独的 TTL，使用负时间戳编码
        if ttl is not None:
            # 存储过期时间而不是创建时间
            timestamp = -(time.time() + ttl)

        with self._lock:
            # 如果键已存在，更新并移动到末尾
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                _, _, access_count = self._cache[cache_key]
                self._cache[cache_key] = (value, timestamp, access_count)
                return

            # 如果达到最大容量，删除最旧的条目
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self._evictions += 1

            # 添加新条目
            self._cache[cache_key] = (value, timestamp, 0)

    def get_or_set(
        self, key: str, factory: Callable[[], T], ttl: Optional[float] = None
    ) -> T:
        """
        获取值，如果不存在则使用工厂函数创建并缓存

        Args:
            key: 缓存键
            factory: 创建值的工厂函数
            ttl: 可选的 TTL

        Returns:
            缓存值或新创建的值
        """
        value = self.get(key)
        if value is not None:
            return value

        value = factory()
        self.set(key, value, ttl)
        return value

    def mget(self, keys: List[str]) -> Dict[str, Optional[T]]:
        """
        批量获取多个键的值

        Args:
            keys: 键列表

        Returns:
            键值字典
        """
        return {key: self.get(key) for key in keys}

    def mset(self, items: Dict[str, T], ttl: Optional[float] = None) -> None:
        """
        批量设置多个键值对

        Args:
            items: 键值字典
            ttl: 可选的 TTL
        """
        for key, value in items.items():
            self.set(key, value, ttl)

    def warm_up(self, data: Dict[str, T], ttl: Optional[float] = None) -> int:
        """
        缓存预热

        Args:
            data: 预热数据字典
            ttl: 可选的 TTL

        Returns:
            成功预热的条目数
        """
        count = 0
        for key, value in data.items():
            self.set(key, value, ttl)
            count += 1
        logger.info(f"缓存 '{self.name}' 预热完成: {count} 条目")
        return count

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
            self._evictions = 0
            self._expired = 0

    def cleanup_expired(self) -> int:
        """
        清理过期条目

        Returns:
            清理的条目数
        """
        if self.ttl is None:
            return 0

        cleaned = 0
        with self._lock:
            expired_keys = []
            for key, (_, timestamp, _) in self._cache.items():
                if self._is_expired(timestamp):
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                cleaned += 1
                self._expired += 1

        if cleaned > 0:
            logger.debug(f"缓存 '{self.name}' 清理了 {cleaned} 个过期条目")
        return cleaned

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含命中率、大小等信息的字典
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0
            avg_access_time = (
                self._total_access_time / self._access_count
                if self._access_count > 0
                else 0.0
            )
            uptime = time.time() - self._created_at

            # 计算热点键
            hot_keys = []
            for key, (_, _, access_count) in sorted(
                self._cache.items(), key=lambda x: x[1][2], reverse=True
            )[:5]:
                hot_keys.append({"key": key[:16] + "...", "access_count": access_count})

            return {
                "name": self.name,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "hit_rate_percent": f"{hit_rate * 100:.2f}%",
                "evictions": self._evictions,
                "expired": self._expired,
                "avg_access_time_ms": avg_access_time * 1000,
                "ttl": self.ttl,
                "uptime_seconds": uptime,
                "hot_keys": hot_keys,
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
            _, timestamp, _ = self._cache[cache_key]
            return not self._is_expired(timestamp)

    def save_to_file(self, filepath: str) -> bool:
        """
        将缓存持久化到文件

        Args:
            filepath: 保存路径

        Returns:
            是否成功保存
        """
        try:
            with self._lock:
                # 过滤掉过期的条目
                valid_entries = {}
                for key, (value, timestamp, access_count) in self._cache.items():
                    if not self._is_expired(timestamp):
                        valid_entries[key] = {
                            "value": value,
                            "timestamp": timestamp,
                            "access_count": access_count,
                        }

                data = {
                    "name": self.name,
                    "max_size": self.max_size,
                    "ttl": self.ttl,
                    "entries": valid_entries,
                    "stats": {
                        "hits": self._hits,
                        "misses": self._misses,
                        "evictions": self._evictions,
                        "expired": self._expired,
                    },
                    "saved_at": datetime.now().isoformat(),
                }

            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(
                f"缓存 '{self.name}' 已保存到 {filepath}，共 {len(valid_entries)} 条"
            )
            return True

        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False

    def load_from_file(self, filepath: str) -> bool:
        """
        从文件加载缓存

        Args:
            filepath: 缓存文件路径

        Returns:
            是否成功加载
        """
        try:
            if not Path(filepath).exists():
                logger.debug(f"缓存文件不存在: {filepath}")
                return False

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            with self._lock:
                # 加载配置
                self.max_size = data.get("max_size", self.max_size)
                self.ttl = data.get("ttl", self.ttl)
                self.name = data.get("name", self.name)

                # 加载统计
                stats = data.get("stats", {})
                self._hits = stats.get("hits", 0)
                self._misses = stats.get("misses", 0)
                self._evictions = stats.get("evictions", 0)
                self._expired = stats.get("expired", 0)

                # 加载条目（过滤过期的）
                self._cache.clear()
                entries = data.get("entries", {})
                loaded_count = 0

                for key, entry in entries.items():
                    timestamp = entry.get("timestamp", 0)
                    if not self._is_expired(timestamp):
                        self._cache[key] = (
                            entry["value"],
                            timestamp,
                            entry.get("access_count", 0),
                        )
                        loaded_count += 1

            logger.info(f"从 {filepath} 加载了 {loaded_count} 条缓存")
            return True

        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return False

    @classmethod
    def from_file(
        cls,
        filepath: str,
        max_size: int = 1000,
        ttl: Optional[float] = None,
        name: str = "default",
    ) -> "LRUCache":
        """
        从文件创建缓存实例

        Args:
            filepath: 缓存文件路径
            max_size: 默认最大大小
            ttl: 默认过期时间
            name: 缓存名称

        Returns:
            LRUCache 实例
        """
        cache = cls(max_size=max_size, ttl=ttl, name=name)
        cache.load_from_file(filepath)
        return cache


# ============ 速率限制器 ============


class RateLimiter:
    """
    令牌桶速率限制器（增强版）

    用于控制 API 调用频率，防止触发速率限制。
    支持动态调整速率和统计。

    Example:
        limiter = RateLimiter(requests_per_second=10)
        await limiter.acquire()  # 等待直到可以发送请求
    """

    def __init__(
        self, requests_per_second: float = 10.0, burst_size: Optional[int] = None
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

        # 统计
        self._total_acquired = 0
        self._total_waited = 0.0

    async def acquire(self, tokens: int = 1) -> float:
        """
        获取令牌

        如果没有可用令牌，将等待直到有令牌可用。

        Args:
            tokens: 要获取的令牌数

        Returns:
            等待的时间（秒）
        """
        waited = 0.0

        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self._last_update
                self._last_update = now

                # 补充令牌
                self._tokens = min(
                    self.burst_size, self._tokens + elapsed * self.requests_per_second
                )

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    self._total_acquired += tokens
                    self._total_waited += waited
                    return waited

                # 计算需要等待的时间
                wait_time = (tokens - self._tokens) / self.requests_per_second
                await asyncio.sleep(wait_time)
                waited += wait_time

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        尝试获取令牌（非阻塞）

        Returns:
            是否成功获取
        """
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now

        self._tokens = min(
            self.burst_size, self._tokens + elapsed * self.requests_per_second
        )

        if self._tokens >= tokens:
            self._tokens -= tokens
            self._total_acquired += tokens
            return True
        return False

    def update_rate(self, requests_per_second: float, burst_size: Optional[int] = None):
        """动态更新速率"""
        self.requests_per_second = requests_per_second
        if burst_size:
            self.burst_size = burst_size

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "requests_per_second": self.requests_per_second,
            "burst_size": self.burst_size,
            "current_tokens": self._tokens,
            "total_acquired": self._total_acquired,
            "total_waited_seconds": self._total_waited,
            "avg_wait_time": (
                self._total_waited / self._total_acquired
                if self._total_acquired > 0
                else 0
            ),
        }


# ============ 请求去重器 ============


class RequestDeduplicator:
    """
    请求去重器

    防止短时间内重复提交相同请求。

    Example:
        dedup = RequestDeduplicator(window_seconds=5)

        if not dedup.is_duplicate(request_hash):
            # 处理请求
            pass
    """

    def __init__(self, window_seconds: float = 5.0, max_entries: int = 10000):
        """
        初始化去重器

        Args:
            window_seconds: 去重窗口时间(秒)
            max_entries: 最大记录数
        """
        self.window = window_seconds
        self.max_entries = max_entries
        self._requests: OrderedDict[str, float] = OrderedDict()
        self._lock = Lock()
        self._duplicates_blocked = 0

    def _cleanup(self):
        """清理过期条目"""
        now = time.time()
        expired = []

        for key, timestamp in self._requests.items():
            if now - timestamp > self.window:
                expired.append(key)
            else:
                break  # OrderedDict 保持插入顺序，后面的都是新的

        for key in expired:
            del self._requests[key]

    def is_duplicate(self, request_hash: str) -> bool:
        """
        检查请求是否重复

        Args:
            request_hash: 请求的哈希值

        Returns:
            是否为重复请求
        """
        now = time.time()

        with self._lock:
            self._cleanup()

            if request_hash in self._requests:
                if now - self._requests[request_hash] < self.window:
                    self._duplicates_blocked += 1
                    return True

            # 限制最大条目数
            while len(self._requests) >= self.max_entries:
                self._requests.popitem(last=False)

            self._requests[request_hash] = now
            return False

    def get_request_hash(self, *args, **kwargs) -> str:
        """
        生成请求哈希

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            请求的哈希值
        """
        content = json.dumps(
            [args, sorted(kwargs.items())], sort_keys=True, default=str
        )
        return hashlib.md5(content.encode()).hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "window_seconds": self.window,
            "current_entries": len(self._requests),
            "max_entries": self.max_entries,
            "duplicates_blocked": self._duplicates_blocked,
        }


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
    return s[: max_length - len(suffix)] + suffix


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
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return str(obj)


def compute_hash(content: str) -> str:
    """计算内容的哈希值"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def format_duration(seconds: float) -> str:
    """格式化持续时间"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}m"
    else:
        return f"{seconds / 3600:.1f}h"
