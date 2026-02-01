# -*- coding: utf-8 -*-
"""
FORGEDAN 分布式测试模块

提供分布式测试支持，包括：
- 协调器（Coordinator）：负责任务分发、工作节点管理
- 工作节点（Worker）：执行具体测试任务
- 任务队列（TaskQueue）：基于 Redis 或内存的任务队列
- 结果聚合器（ResultAggregator）：收集并聚合测试结果

支持两种部署模式：
1. 单机多进程模式：在一台机器上启动多个 Worker
2. 多机分布式模式：跨多台机器部署 Worker

使用方法：
    # 启动协调器
    python -m forgedan.distributed.start_coordinator --port 8765

    # 启动工作节点
    python -m forgedan.distributed.start_worker --coordinator http://localhost:8765

    # 或使用 CLI
    forgedan distributed start-coordinator
    forgedan distributed start-worker --coordinator http://localhost:8765
"""

from .config import DistributedConfig, WorkerConfig, QueueConfig
from .coordinator import DistributedCoordinator
from .worker import DistributedWorker
from .task_queue import TaskQueue, MemoryTaskQueue, RedisTaskQueue, Task, TaskStatus
from .result_aggregator import ResultAggregator

__all__ = [
    # 配置
    "DistributedConfig",
    "WorkerConfig",
    "QueueConfig",
    # 核心组件
    "DistributedCoordinator",
    "DistributedWorker",
    # 任务队列
    "TaskQueue",
    "MemoryTaskQueue",
    "RedisTaskQueue",
    "Task",
    "TaskStatus",
    # 结果聚合
    "ResultAggregator",
]
