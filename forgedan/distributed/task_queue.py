# -*- coding: utf-8 -*-
"""
FORGEDAN 任务队列模块

提供任务队列的抽象接口和两种实现：
1. MemoryTaskQueue: 基于内存的任务队列（单机模式）
2. RedisTaskQueue: 基于 Redis 的任务队列（分布式模式）

支持特性：
- 任务优先级
- 任务超时处理
- 失败重试
- 任务状态追踪
"""

import asyncio
import json
import time
import uuid
import heapq
import pickle
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Callable, Awaitable
from collections import defaultdict


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"         # 等待执行
    QUEUED = "queued"          # 已入队
    RUNNING = "running"        # 执行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    TIMEOUT = "timeout"        # 超时
    CANCELLED = "cancelled"    # 已取消
    RETRYING = "retrying"      # 重试中


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class Task:
    """任务数据结构"""
    # 基本信息
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = "evolution"          # evolution / batch / single
    priority: int = TaskPriority.NORMAL.value

    # 任务内容
    payload: Dict[str, Any] = field(default_factory=dict)

    # 状态信息
    status: TaskStatus = TaskStatus.PENDING
    worker_id: Optional[str] = None
    progress: float = 0.0                 # 0.0 - 1.0

    # 时间戳
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    updated_at: float = field(default_factory=time.time)

    # 重试信息
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None

    # 超时配置
    timeout: float = 3600.0               # 任务超时（秒）

    # 结果
    result: Optional[Dict[str, Any]] = None

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "priority": self.priority,
            "payload": self.payload,
            "status": self.status.value,
            "worker_id": self.worker_id,
            "progress": self.progress,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "updated_at": self.updated_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "last_error": self.last_error,
            "timeout": self.timeout,
            "result": self.result,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """从字典创建任务"""
        task = cls()
        task.task_id = data.get("task_id", task.task_id)
        task.task_type = data.get("task_type", "evolution")
        task.priority = data.get("priority", TaskPriority.NORMAL.value)
        task.payload = data.get("payload", {})
        task.status = TaskStatus(data.get("status", "pending"))
        task.worker_id = data.get("worker_id")
        task.progress = data.get("progress", 0.0)
        task.created_at = data.get("created_at", time.time())
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        task.updated_at = data.get("updated_at", time.time())
        task.retry_count = data.get("retry_count", 0)
        task.max_retries = data.get("max_retries", 3)
        task.last_error = data.get("last_error")
        task.timeout = data.get("timeout", 3600.0)
        task.result = data.get("result")
        task.metadata = data.get("metadata", {})
        return task

    def is_timed_out(self) -> bool:
        """检查任务是否超时"""
        if self.started_at and self.status == TaskStatus.RUNNING:
            return time.time() - self.started_at > self.timeout
        return False

    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.max_retries

    def __lt__(self, other: "Task") -> bool:
        """优先级比较（用于堆排序）"""
        # 优先级高的先执行，优先级相同时先创建的先执行
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.created_at < other.created_at


class TaskQueue(ABC):
    """任务队列抽象基类"""

    @abstractmethod
    async def enqueue(self, task: Task) -> bool:
        """将任务加入队列"""
        pass

    @abstractmethod
    async def dequeue(self, worker_id: str) -> Optional[Task]:
        """从队列获取任务"""
        pass

    @abstractmethod
    async def update_task(self, task: Task) -> bool:
        """更新任务状态"""
        pass

    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        pass

    @abstractmethod
    async def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """清理过期任务"""
        pass


class MemoryTaskQueue(TaskQueue):
    """
    基于内存的任务队列实现

    适用于单机多进程模式，不支持跨机器分布式。
    使用优先级堆实现任务优先级。
    """

    def __init__(
        self,
        max_size: int = 10000,
        task_timeout: float = 3600.0,
        max_retries: int = 3,
        retry_delay: float = 5.0,
    ):
        """
        初始化内存任务队列

        Args:
            max_size: 最大队列容量
            task_timeout: 任务超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.max_size = max_size
        self.task_timeout = task_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # 任务存储
        self._pending_queue: List[Task] = []    # 优先级堆
        self._tasks: Dict[str, Task] = {}       # 所有任务
        self._running: Dict[str, Task] = {}     # 运行中的任务
        self._completed: Dict[str, Task] = {}   # 已完成的任务

        # 线程安全锁
        self._lock = asyncio.Lock()

        # 统计信息
        self._stats = {
            "total_enqueued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_retried": 0,
            "total_timeout": 0,
        }

    async def enqueue(self, task: Task) -> bool:
        """将任务加入队列"""
        async with self._lock:
            if len(self._pending_queue) >= self.max_size:
                return False

            # 设置默认值
            task.status = TaskStatus.QUEUED
            task.timeout = task.timeout or self.task_timeout
            task.max_retries = task.max_retries or self.max_retries
            task.updated_at = time.time()

            # 加入优先级堆
            heapq.heappush(self._pending_queue, task)
            self._tasks[task.task_id] = task

            self._stats["total_enqueued"] += 1
            return True

    async def dequeue(self, worker_id: str) -> Optional[Task]:
        """从队列获取任务"""
        async with self._lock:
            if not self._pending_queue:
                return None

            # 从优先级堆弹出
            task = heapq.heappop(self._pending_queue)

            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.worker_id = worker_id
            task.started_at = time.time()
            task.updated_at = time.time()

            self._running[task.task_id] = task

            return task

    async def update_task(self, task: Task) -> bool:
        """更新任务状态"""
        async with self._lock:
            if task.task_id not in self._tasks:
                return False

            task.updated_at = time.time()
            self._tasks[task.task_id] = task

            # 处理状态变化
            if task.status == TaskStatus.COMPLETED:
                if task.task_id in self._running:
                    del self._running[task.task_id]
                task.completed_at = time.time()
                self._completed[task.task_id] = task
                self._stats["total_completed"] += 1

            elif task.status == TaskStatus.FAILED:
                if task.task_id in self._running:
                    del self._running[task.task_id]

                # 检查是否可以重试
                if task.can_retry():
                    task.retry_count += 1
                    task.status = TaskStatus.RETRYING
                    task.worker_id = None
                    task.started_at = None
                    # 延迟重新入队
                    await asyncio.sleep(self.retry_delay)
                    task.status = TaskStatus.QUEUED
                    heapq.heappush(self._pending_queue, task)
                    self._stats["total_retried"] += 1
                else:
                    self._completed[task.task_id] = task
                    self._stats["total_failed"] += 1

            elif task.status == TaskStatus.TIMEOUT:
                if task.task_id in self._running:
                    del self._running[task.task_id]
                self._completed[task.task_id] = task
                self._stats["total_timeout"] += 1

            return True

    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        async with self._lock:
            return self._tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
                task.status = TaskStatus.CANCELLED
                task.updated_at = time.time()
                # 从待处理队列移除
                self._pending_queue = [t for t in self._pending_queue if t.task_id != task_id]
                heapq.heapify(self._pending_queue)
                return True

            elif task.status == TaskStatus.RUNNING:
                # 运行中的任务标记为取消（需要 Worker 处理）
                task.status = TaskStatus.CANCELLED
                task.updated_at = time.time()
                return True

            return False

    async def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        async with self._lock:
            return {
                "pending_count": len(self._pending_queue),
                "running_count": len(self._running),
                "completed_count": len(self._completed),
                "total_tasks": len(self._tasks),
                **self._stats,
            }

    async def cleanup_expired(self) -> int:
        """清理过期任务"""
        cleaned = 0
        async with self._lock:
            current_time = time.time()

            # 检查超时的运行中任务
            timeout_tasks = []
            for task_id, task in list(self._running.items()):
                if task.is_timed_out():
                    timeout_tasks.append(task)

            for task in timeout_tasks:
                task.status = TaskStatus.TIMEOUT
                task.updated_at = current_time
                del self._running[task.task_id]
                self._completed[task.task_id] = task
                self._stats["total_timeout"] += 1
                cleaned += 1

            # 清理过期的已完成任务（超过 24 小时）
            expired_threshold = current_time - 86400
            expired_ids = [
                task_id for task_id, task in self._completed.items()
                if task.completed_at and task.completed_at < expired_threshold
            ]
            for task_id in expired_ids:
                del self._completed[task_id]
                if task_id in self._tasks:
                    del self._tasks[task_id]
                cleaned += 1

            return cleaned

    async def get_pending_tasks(self, limit: int = 100) -> List[Task]:
        """获取待处理任务列表"""
        async with self._lock:
            # 返回排序后的待处理任务（不改变堆）
            sorted_tasks = sorted(self._pending_queue, key=lambda t: (-t.priority, t.created_at))
            return sorted_tasks[:limit]

    async def get_running_tasks(self) -> List[Task]:
        """获取运行中任务列表"""
        async with self._lock:
            return list(self._running.values())

    async def requeue_stalled_tasks(self, stall_timeout: float = 300.0) -> int:
        """重新入队停滞的任务"""
        requeued = 0
        async with self._lock:
            current_time = time.time()

            stalled_tasks = []
            for task_id, task in list(self._running.items()):
                if task.updated_at and current_time - task.updated_at > stall_timeout:
                    stalled_tasks.append(task)

            for task in stalled_tasks:
                if task.can_retry():
                    task.retry_count += 1
                    task.status = TaskStatus.QUEUED
                    task.worker_id = None
                    task.started_at = None
                    task.updated_at = current_time
                    del self._running[task.task_id]
                    heapq.heappush(self._pending_queue, task)
                    requeued += 1
                else:
                    task.status = TaskStatus.FAILED
                    task.last_error = "Task stalled and max retries exceeded"
                    del self._running[task.task_id]
                    self._completed[task.task_id] = task
                    self._stats["total_failed"] += 1

            return requeued


class RedisTaskQueue(TaskQueue):
    """
    基于 Redis 的任务队列实现

    适用于多机分布式模式，支持：
    - 任务持久化
    - 跨机器任务分发
    - 断点续传
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "forgedan:",
        max_size: int = 10000,
        task_timeout: float = 3600.0,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        result_ttl: int = 86400,
    ):
        """
        初始化 Redis 任务队列

        Args:
            host: Redis 主机
            port: Redis 端口
            db: Redis 数据库编号
            password: Redis 密码
            prefix: 键前缀
            max_size: 最大队列容量
            task_timeout: 任务超时时间
            max_retries: 最大重试次数
            retry_delay: 重试延迟
            result_ttl: 结果保存时间
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self.max_size = max_size
        self.task_timeout = task_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.result_ttl = result_ttl

        # Redis 连接（延迟初始化）
        self._redis = None
        self._initialized = False

        # 键名
        self._pending_key = f"{prefix}pending"          # 待处理队列（有序集合）
        self._running_key = f"{prefix}running"          # 运行中任务（哈希）
        self._completed_key = f"{prefix}completed"      # 已完成任务（哈希）
        self._tasks_key = f"{prefix}tasks"              # 所有任务（哈希）
        self._stats_key = f"{prefix}stats"              # 统计信息（哈希）

    async def _ensure_connected(self):
        """确保 Redis 连接"""
        if self._initialized:
            return

        try:
            import redis.asyncio as redis
            self._redis = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,  # 使用二进制以支持 pickle
            )
            # 测试连接
            await self._redis.ping()
            self._initialized = True
        except ImportError:
            raise ImportError("Redis 支持需要安装 redis 库: pip install redis")
        except Exception as e:
            raise ConnectionError(f"无法连接到 Redis: {e}")

    def _serialize_task(self, task: Task) -> bytes:
        """序列化任务"""
        return pickle.dumps(task.to_dict())

    def _deserialize_task(self, data: bytes) -> Task:
        """反序列化任务"""
        return Task.from_dict(pickle.loads(data))

    async def enqueue(self, task: Task) -> bool:
        """将任务加入队列"""
        await self._ensure_connected()

        # 检查队列容量
        queue_size = await self._redis.zcard(self._pending_key)
        if queue_size >= self.max_size:
            return False

        # 设置默认值
        task.status = TaskStatus.QUEUED
        task.timeout = task.timeout or self.task_timeout
        task.max_retries = task.max_retries or self.max_retries
        task.updated_at = time.time()

        # 使用事务保证原子性
        async with self._redis.pipeline() as pipe:
            # 计算优先级分数（优先级高的分数小，先被取出）
            score = -task.priority * 1000000 + task.created_at

            pipe.zadd(self._pending_key, {task.task_id: score})
            pipe.hset(self._tasks_key, task.task_id, self._serialize_task(task))
            pipe.hincrby(self._stats_key, "total_enqueued", 1)

            await pipe.execute()

        return True

    async def dequeue(self, worker_id: str) -> Optional[Task]:
        """从队列获取任务"""
        await self._ensure_connected()

        # 使用 WATCH 实现乐观锁
        while True:
            try:
                async with self._redis.pipeline() as pipe:
                    # 获取最高优先级任务
                    results = await self._redis.zrange(
                        self._pending_key, 0, 0, withscores=False
                    )

                    if not results:
                        return None

                    task_id = results[0].decode() if isinstance(results[0], bytes) else results[0]

                    # 原子操作：移除并更新
                    pipe.zrem(self._pending_key, task_id)
                    await pipe.execute()

                    # 获取并更新任务
                    task_data = await self._redis.hget(self._tasks_key, task_id)
                    if not task_data:
                        continue

                    task = self._deserialize_task(task_data)
                    task.status = TaskStatus.RUNNING
                    task.worker_id = worker_id
                    task.started_at = time.time()
                    task.updated_at = time.time()

                    # 保存更新
                    await self._redis.hset(
                        self._tasks_key, task.task_id, self._serialize_task(task)
                    )
                    await self._redis.hset(
                        self._running_key, task.task_id, self._serialize_task(task)
                    )

                    return task

            except Exception as e:
                # 竞争条件，重试
                continue

    async def update_task(self, task: Task) -> bool:
        """更新任务状态"""
        await self._ensure_connected()

        task.updated_at = time.time()

        async with self._redis.pipeline() as pipe:
            pipe.hset(self._tasks_key, task.task_id, self._serialize_task(task))

            if task.status == TaskStatus.COMPLETED:
                task.completed_at = time.time()
                pipe.hdel(self._running_key, task.task_id)
                pipe.hset(self._completed_key, task.task_id, self._serialize_task(task))
                pipe.hincrby(self._stats_key, "total_completed", 1)
                # 设置过期
                pipe.expire(f"{self.prefix}result:{task.task_id}", self.result_ttl)

            elif task.status == TaskStatus.FAILED:
                pipe.hdel(self._running_key, task.task_id)

                if task.can_retry():
                    task.retry_count += 1
                    task.status = TaskStatus.QUEUED
                    task.worker_id = None
                    task.started_at = None
                    # 重新入队
                    score = -task.priority * 1000000 + time.time() + self.retry_delay
                    pipe.zadd(self._pending_key, {task.task_id: score})
                    pipe.hincrby(self._stats_key, "total_retried", 1)
                else:
                    pipe.hset(self._completed_key, task.task_id, self._serialize_task(task))
                    pipe.hincrby(self._stats_key, "total_failed", 1)

            elif task.status == TaskStatus.TIMEOUT:
                pipe.hdel(self._running_key, task.task_id)
                pipe.hset(self._completed_key, task.task_id, self._serialize_task(task))
                pipe.hincrby(self._stats_key, "total_timeout", 1)

            await pipe.execute()

        return True

    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        await self._ensure_connected()

        task_data = await self._redis.hget(self._tasks_key, task_id)
        if task_data:
            return self._deserialize_task(task_data)
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        await self._ensure_connected()

        task = await self.get_task(task_id)
        if not task:
            return False

        if task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            task.status = TaskStatus.CANCELLED
            task.updated_at = time.time()

            async with self._redis.pipeline() as pipe:
                pipe.zrem(self._pending_key, task_id)
                pipe.hset(self._tasks_key, task_id, self._serialize_task(task))
                await pipe.execute()

            return True

        elif task.status == TaskStatus.RUNNING:
            task.status = TaskStatus.CANCELLED
            task.updated_at = time.time()
            await self._redis.hset(self._tasks_key, task_id, self._serialize_task(task))
            return True

        return False

    async def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        await self._ensure_connected()

        pending_count = await self._redis.zcard(self._pending_key)
        running_count = await self._redis.hlen(self._running_key)
        completed_count = await self._redis.hlen(self._completed_key)
        total_tasks = await self._redis.hlen(self._tasks_key)

        stats = await self._redis.hgetall(self._stats_key)
        decoded_stats = {}
        for k, v in stats.items():
            key = k.decode() if isinstance(k, bytes) else k
            decoded_stats[key] = int(v)

        return {
            "pending_count": pending_count,
            "running_count": running_count,
            "completed_count": completed_count,
            "total_tasks": total_tasks,
            **decoded_stats,
        }

    async def cleanup_expired(self) -> int:
        """清理过期任务"""
        await self._ensure_connected()

        cleaned = 0
        current_time = time.time()

        # 获取运行中的任务
        running_tasks = await self._redis.hgetall(self._running_key)

        for task_id, task_data in running_tasks.items():
            task = self._deserialize_task(task_data)
            if task.is_timed_out():
                task.status = TaskStatus.TIMEOUT
                await self.update_task(task)
                cleaned += 1

        return cleaned

    async def close(self):
        """关闭连接"""
        if self._redis:
            await self._redis.close()
            self._initialized = False


def create_task_queue(config) -> TaskQueue:
    """
    根据配置创建任务队列

    Args:
        config: QueueConfig 配置对象

    Returns:
        TaskQueue 实例
    """
    from .config import QueueBackend, QueueConfig

    if isinstance(config, dict):
        # 从字典创建配置
        backend = config.get("backend", "memory")
        if backend == "redis":
            return RedisTaskQueue(
                host=config.get("redis_host", "localhost"),
                port=config.get("redis_port", 6379),
                db=config.get("redis_db", 0),
                password=config.get("redis_password"),
                prefix=config.get("redis_prefix", "forgedan:"),
                max_size=config.get("max_queue_size", 10000),
                task_timeout=config.get("task_timeout", 3600.0),
                max_retries=config.get("max_retries", 3),
                retry_delay=config.get("retry_delay", 5.0),
                result_ttl=config.get("result_ttl", 86400),
            )
        else:
            return MemoryTaskQueue(
                max_size=config.get("max_queue_size", 10000),
                task_timeout=config.get("task_timeout", 3600.0),
                max_retries=config.get("max_retries", 3),
                retry_delay=config.get("retry_delay", 5.0),
            )

    # QueueConfig 对象
    if config.backend == QueueBackend.REDIS:
        return RedisTaskQueue(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            password=config.redis_password,
            prefix=config.redis_prefix,
            max_size=config.max_queue_size,
            task_timeout=config.task_timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
            result_ttl=config.result_ttl,
        )
    else:
        return MemoryTaskQueue(
            max_size=config.max_queue_size,
            task_timeout=config.task_timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
        )
