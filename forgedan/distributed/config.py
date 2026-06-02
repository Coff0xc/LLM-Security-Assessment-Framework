# -*- coding: utf-8 -*-
"""
FORGEDAN 分布式配置模块

定义分布式系统的所有配置项，包括：
- DistributedConfig: 全局分布式配置
- WorkerConfig: 工作节点配置
- QueueConfig: 任务队列配置
- CoordinatorConfig: 协调器配置
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import os


class QueueBackend(Enum):
    """任务队列后端类型"""

    MEMORY = "memory"  # 内存队列（单机模式）
    REDIS = "redis"  # Redis 队列（分布式模式）


class LoadBalanceStrategy(Enum):
    """负载均衡策略"""

    ROUND_ROBIN = "round_robin"  # 轮询
    LEAST_LOADED = "least_loaded"  # 最少负载
    RANDOM = "random"  # 随机
    WEIGHTED = "weighted"  # 加权（根据性能指标）


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class QueueConfig:
    """任务队列配置"""

    # 队列后端
    backend: QueueBackend = QueueBackend.MEMORY

    # Redis 配置（仅当 backend=REDIS 时使用）
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_prefix: str = "forgedan:"

    # 队列参数
    max_queue_size: int = 10000  # 最大队列容量
    task_timeout: float = 3600.0  # 任务超时时间（秒）
    max_retries: int = 3  # 失败重试次数
    retry_delay: float = 5.0  # 重试延迟（秒）
    result_ttl: int = 86400  # 结果保存时间（秒）

    # 优先级队列
    enable_priority: bool = True  # 启用优先级队列

    @classmethod
    def from_env(cls) -> "QueueConfig":
        """从环境变量加载配置"""
        backend_str = os.getenv("FORGEDAN_QUEUE_BACKEND", "memory")
        backend = (
            QueueBackend.REDIS
            if backend_str.lower() == "redis"
            else QueueBackend.MEMORY
        )

        return cls(
            backend=backend,
            redis_host=os.getenv("FORGEDAN_REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("FORGEDAN_REDIS_PORT", "6379")),
            redis_db=int(os.getenv("FORGEDAN_REDIS_DB", "0")),
            redis_password=os.getenv("FORGEDAN_REDIS_PASSWORD"),
            redis_prefix=os.getenv("FORGEDAN_REDIS_PREFIX", "forgedan:"),
            max_queue_size=int(os.getenv("FORGEDAN_QUEUE_MAX_SIZE", "10000")),
            task_timeout=float(os.getenv("FORGEDAN_TASK_TIMEOUT", "3600")),
            max_retries=int(os.getenv("FORGEDAN_MAX_RETRIES", "3")),
        )


@dataclass
class WorkerConfig:
    """工作节点配置"""

    # 节点标识
    worker_id: Optional[str] = None  # 节点ID（自动生成）
    worker_name: str = ""  # 节点名称
    worker_tags: List[str] = field(default_factory=list)  # 节点标签

    # 协调器连接
    coordinator_url: str = "http://localhost:8765"
    coordinator_token: Optional[str] = None  # 认证令牌

    # 性能配置
    max_concurrent_tasks: int = 4  # 最大并发任务数
    max_processes: int = 0  # 最大进程数（0=CPU数量）

    # 心跳配置
    heartbeat_interval: float = 10.0  # 心跳间隔（秒）
    heartbeat_timeout: float = 30.0  # 心跳超时（秒）

    # 资源限制
    max_memory_mb: int = 0  # 最大内存限制（0=不限制）
    max_task_duration: float = 3600.0  # 单任务最大执行时间

    # 优雅退出
    graceful_shutdown_timeout: float = 60.0  # 优雅退出超时

    @classmethod
    def from_env(cls) -> "WorkerConfig":
        """从环境变量加载配置"""
        return cls(
            worker_id=os.getenv("FORGEDAN_WORKER_ID"),
            worker_name=os.getenv("FORGEDAN_WORKER_NAME", ""),
            coordinator_url=os.getenv(
                "FORGEDAN_COORDINATOR_URL", "http://localhost:8765"
            ),
            coordinator_token=os.getenv("FORGEDAN_COORDINATOR_TOKEN"),
            max_concurrent_tasks=int(os.getenv("FORGEDAN_MAX_CONCURRENT_TASKS", "4")),
            max_processes=int(os.getenv("FORGEDAN_MAX_PROCESSES", "0")),
            heartbeat_interval=float(os.getenv("FORGEDAN_HEARTBEAT_INTERVAL", "10")),
        )


@dataclass
class CoordinatorConfig:
    """协调器配置"""

    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8765

    # 认证
    enable_auth: bool = False
    auth_token: Optional[str] = None

    # 负载均衡
    load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.LEAST_LOADED

    # 节点管理
    worker_timeout: float = 60.0  # Worker 超时时间（秒）
    max_workers: int = 100  # 最大 Worker 数量

    # 故障恢复
    enable_task_recovery: bool = True  # 启用任务恢复
    checkpoint_interval: float = 60.0  # 检查点间隔（秒）
    checkpoint_dir: str = "checkpoints/distributed"

    # API 配置
    enable_rest_api: bool = True  # 启用 REST API
    enable_websocket: bool = True  # 启用 WebSocket
    cors_origins: List[str] = field(default_factory=lambda: ["*"])

    @classmethod
    def from_env(cls) -> "CoordinatorConfig":
        """从环境变量加载配置"""
        strategy_str = os.getenv("FORGEDAN_LB_STRATEGY", "least_loaded")
        strategy = LoadBalanceStrategy.LEAST_LOADED
        try:
            strategy = LoadBalanceStrategy(strategy_str)
        except ValueError:
            pass

        return cls(
            host=os.getenv("FORGEDAN_COORDINATOR_HOST", "0.0.0.0"),
            port=int(os.getenv("FORGEDAN_COORDINATOR_PORT", "8765")),
            enable_auth=os.getenv("FORGEDAN_ENABLE_AUTH", "false").lower() == "true",
            auth_token=os.getenv("FORGEDAN_AUTH_TOKEN"),
            load_balance_strategy=strategy,
            worker_timeout=float(os.getenv("FORGEDAN_WORKER_TIMEOUT", "60")),
        )


@dataclass
class DistributedConfig:
    """分布式全局配置"""

    # 模式
    mode: str = "standalone"  # standalone / distributed

    # 子配置
    queue: QueueConfig = field(default_factory=QueueConfig)
    worker: WorkerConfig = field(default_factory=WorkerConfig)
    coordinator: CoordinatorConfig = field(default_factory=CoordinatorConfig)

    # 日志配置
    log_level: str = "INFO"
    log_dir: str = "logs/distributed"

    # 监控
    enable_metrics: bool = True  # 启用指标收集
    metrics_port: int = 9100  # Prometheus 指标端口

    @classmethod
    def from_env(cls) -> "DistributedConfig":
        """从环境变量加载配置"""
        return cls(
            mode=os.getenv("FORGEDAN_MODE", "standalone"),
            queue=QueueConfig.from_env(),
            worker=WorkerConfig.from_env(),
            coordinator=CoordinatorConfig.from_env(),
            log_level=os.getenv("FORGEDAN_LOG_LEVEL", "INFO"),
            log_dir=os.getenv("FORGEDAN_LOG_DIR", "logs/distributed"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "mode": self.mode,
            "queue": {
                "backend": self.queue.backend.value,
                "redis_host": self.queue.redis_host,
                "redis_port": self.queue.redis_port,
                "max_queue_size": self.queue.max_queue_size,
                "task_timeout": self.queue.task_timeout,
            },
            "worker": {
                "coordinator_url": self.worker.coordinator_url,
                "max_concurrent_tasks": self.worker.max_concurrent_tasks,
                "heartbeat_interval": self.worker.heartbeat_interval,
            },
            "coordinator": {
                "host": self.coordinator.host,
                "port": self.coordinator.port,
                "load_balance_strategy": self.coordinator.load_balance_strategy.value,
            },
            "log_level": self.log_level,
        }
