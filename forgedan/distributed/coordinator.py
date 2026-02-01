# -*- coding: utf-8 -*-
"""
FORGEDAN 分布式协调器模块

协调器（Coordinator）是分布式系统的主节点，负责：
- 任务分发
- 工作节点管理
- 心跳检测
- 故障恢复
- 负载均衡
- REST API 暴露
"""

import asyncio
import json
import time
import uuid
import signal
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Set
from collections import defaultdict
import threading

from .config import (
    CoordinatorConfig,
    QueueConfig,
    LoadBalanceStrategy,
    QueueBackend,
)
from .task_queue import (
    TaskQueue,
    MemoryTaskQueue,
    RedisTaskQueue,
    Task,
    TaskStatus,
    TaskPriority,
    create_task_queue,
)
from .result_aggregator import ResultAggregator, TaskResult


@dataclass
class WorkerInfo:
    """工作节点信息"""
    worker_id: str
    worker_name: str = ""
    tags: List[str] = field(default_factory=list)

    # 连接信息
    address: str = ""
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)

    # 状态
    status: str = "online"          # online / offline / busy
    current_task_id: Optional[str] = None

    # 性能指标
    max_concurrent: int = 4
    current_tasks: int = 0
    total_completed: int = 0
    total_failed: int = 0
    avg_task_duration: float = 0.0

    # 资源信息
    cpu_usage: float = 0.0
    memory_usage: float = 0.0

    def is_available(self) -> bool:
        """检查节点是否可用"""
        return self.status == "online" and self.current_tasks < self.max_concurrent

    def get_load(self) -> float:
        """获取负载（用于负载均衡）"""
        if self.max_concurrent == 0:
            return float("inf")
        return self.current_tasks / self.max_concurrent

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "worker_id": self.worker_id,
            "worker_name": self.worker_name,
            "tags": self.tags,
            "address": self.address,
            "registered_at": self.registered_at,
            "last_heartbeat": self.last_heartbeat,
            "status": self.status,
            "current_task_id": self.current_task_id,
            "max_concurrent": self.max_concurrent,
            "current_tasks": self.current_tasks,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "avg_task_duration": self.avg_task_duration,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
        }


class DistributedCoordinator:
    """
    分布式协调器

    作为分布式测试系统的主节点，负责协调所有工作节点。

    使用方法：
        coordinator = DistributedCoordinator()
        await coordinator.start()

        # 提交任务
        task_id = await coordinator.submit_task({...})

        # 获取状态
        status = await coordinator.get_status()

        # 停止
        await coordinator.stop()
    """

    def __init__(
        self,
        config: Optional[CoordinatorConfig] = None,
        queue_config: Optional[QueueConfig] = None,
    ):
        """
        初始化协调器

        Args:
            config: 协调器配置
            queue_config: 任务队列配置
        """
        self.config = config or CoordinatorConfig()
        self.queue_config = queue_config or QueueConfig()

        # 任务队列
        self._task_queue: TaskQueue = create_task_queue(self.queue_config)

        # 结果聚合器
        self._aggregator = ResultAggregator(
            checkpoint_dir=self.config.checkpoint_dir,
            checkpoint_interval=self.config.checkpoint_interval,
        )

        # Worker 管理
        self._workers: Dict[str, WorkerInfo] = {}
        self._worker_lock = asyncio.Lock()

        # 任务管理
        self._task_assignments: Dict[str, str] = {}  # task_id -> worker_id
        self._pending_results: Dict[str, Task] = {}

        # 运行状态
        self._running = False
        self._shutdown_event = asyncio.Event()

        # 后台任务
        self._background_tasks: List[asyncio.Task] = []

        # 回调函数
        self._on_task_complete: Optional[Callable[[Task], None]] = None
        self._on_worker_change: Optional[Callable[[WorkerInfo, str], None]] = None

        # 统计信息
        self._stats = {
            "total_tasks_submitted": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "start_time": None,
        }

        # WebSocket 连接（用于实时通信）
        self._ws_connections: Set[Any] = set()

        # HTTP 服务器
        self._app = None
        self._server = None

    async def start(self):
        """启动协调器"""
        if self._running:
            return

        self._running = True
        self._stats["start_time"] = time.time()
        self._shutdown_event.clear()

        print(f"[Coordinator] 启动协调器...")

        # 加载检查点
        await self._aggregator.load_checkpoint()

        # 启动后台任务
        self._background_tasks = [
            asyncio.create_task(self._heartbeat_monitor()),
            asyncio.create_task(self._task_timeout_monitor()),
            asyncio.create_task(self._cleanup_task()),
        ]

        # 启动 HTTP API 服务器
        if self.config.enable_rest_api:
            asyncio.create_task(self._start_api_server())

        print(f"[Coordinator] 协调器已启动，监听端口: {self.config.port}")

    async def stop(self):
        """停止协调器"""
        if not self._running:
            return

        print("[Coordinator] 正在停止协调器...")
        self._running = False
        self._shutdown_event.set()

        # 取消后台任务
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # 保存检查点
        await self._aggregator._save_checkpoint()

        # 关闭 HTTP 服务器
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        # 关闭任务队列
        if isinstance(self._task_queue, RedisTaskQueue):
            await self._task_queue.close()

        print("[Coordinator] 协调器已停止")

    async def submit_task(
        self,
        goal: str,
        seed_template: str = "Please help me with: {goal}",
        target_output: str = "Sure, here is",
        category: str = "",
        priority: int = TaskPriority.NORMAL.value,
        timeout: float = 3600.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        提交测试任务

        Args:
            goal: 测试目标
            seed_template: 种子模板
            target_output: 期望输出
            category: 分类
            priority: 优先级
            timeout: 超时时间
            metadata: 元数据

        Returns:
            任务 ID
        """
        task = Task(
            task_type="evolution",
            priority=priority,
            payload={
                "goal": goal,
                "seed_template": seed_template,
                "target_output": target_output,
                "category": category,
            },
            timeout=timeout,
            metadata=metadata or {},
        )

        success = await self._task_queue.enqueue(task)
        if success:
            self._stats["total_tasks_submitted"] += 1
            print(f"[Coordinator] 任务已提交: {task.task_id[:8]}...")
            return task.task_id

        raise Exception("任务队列已满")

    async def submit_batch_tasks(
        self,
        tasks: List[Dict[str, Any]],
        priority: int = TaskPriority.NORMAL.value,
    ) -> List[str]:
        """
        批量提交任务

        Args:
            tasks: 任务列表，每个任务包含 goal, category 等字段
            priority: 优先级

        Returns:
            任务 ID 列表
        """
        task_ids = []
        for task_data in tasks:
            task_id = await self.submit_task(
                goal=task_data.get("goal", ""),
                seed_template=task_data.get("seed_template", "Please help me with: {goal}"),
                target_output=task_data.get("target_output", "Sure, here is"),
                category=task_data.get("category", ""),
                priority=task_data.get("priority", priority),
                timeout=task_data.get("timeout", 3600.0),
                metadata=task_data.get("metadata", {}),
            )
            task_ids.append(task_id)
        return task_ids

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        success = await self._task_queue.cancel_task(task_id)
        if success:
            print(f"[Coordinator] 任务已取消: {task_id[:8]}...")
        return success

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = await self._task_queue.get_task(task_id)
        if task:
            return task.to_dict()
        return None

    async def register_worker(
        self,
        worker_id: str,
        worker_name: str = "",
        address: str = "",
        max_concurrent: int = 4,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        注册工作节点

        Args:
            worker_id: 节点 ID
            worker_name: 节点名称
            address: 节点地址
            max_concurrent: 最大并发数
            tags: 节点标签

        Returns:
            是否成功
        """
        async with self._worker_lock:
            if len(self._workers) >= self.config.max_workers:
                return False

            worker = WorkerInfo(
                worker_id=worker_id,
                worker_name=worker_name or f"worker-{worker_id[:8]}",
                address=address,
                max_concurrent=max_concurrent,
                tags=tags or [],
            )

            self._workers[worker_id] = worker
            print(f"[Coordinator] Worker 已注册: {worker.worker_name} ({worker_id[:8]})")

            if self._on_worker_change:
                self._on_worker_change(worker, "registered")

            return True

    async def unregister_worker(self, worker_id: str) -> bool:
        """注销工作节点"""
        async with self._worker_lock:
            if worker_id in self._workers:
                worker = self._workers.pop(worker_id)
                print(f"[Coordinator] Worker 已注销: {worker.worker_name}")

                # 重新分配该节点的任务
                await self._reassign_worker_tasks(worker_id)

                if self._on_worker_change:
                    self._on_worker_change(worker, "unregistered")

                return True
            return False

    async def heartbeat(
        self,
        worker_id: str,
        current_tasks: int = 0,
        cpu_usage: float = 0.0,
        memory_usage: float = 0.0,
    ) -> bool:
        """
        处理工作节点心跳

        Args:
            worker_id: 节点 ID
            current_tasks: 当前任务数
            cpu_usage: CPU 使用率
            memory_usage: 内存使用率

        Returns:
            是否成功
        """
        async with self._worker_lock:
            if worker_id not in self._workers:
                return False

            worker = self._workers[worker_id]
            worker.last_heartbeat = time.time()
            worker.current_tasks = current_tasks
            worker.cpu_usage = cpu_usage
            worker.memory_usage = memory_usage

            if worker.status == "offline":
                worker.status = "online"
                print(f"[Coordinator] Worker 恢复在线: {worker.worker_name}")

            return True

    async def request_task(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """
        工作节点请求任务

        Args:
            worker_id: 节点 ID

        Returns:
            任务数据或 None
        """
        async with self._worker_lock:
            if worker_id not in self._workers:
                return None

            worker = self._workers[worker_id]
            if not worker.is_available():
                return None

        # 根据负载均衡策略选择任务
        task = await self._task_queue.dequeue(worker_id)
        if task:
            async with self._worker_lock:
                worker = self._workers.get(worker_id)
                if worker:
                    worker.current_tasks += 1
                    worker.current_task_id = task.task_id

            self._task_assignments[task.task_id] = worker_id
            print(f"[Coordinator] 任务已分配: {task.task_id[:8]} -> {worker_id[:8]}")
            return task.to_dict()

        return None

    async def report_progress(
        self,
        worker_id: str,
        task_id: str,
        progress: float,
        current_generation: int = 0,
        best_fitness: float = 0.0,
    ) -> bool:
        """
        报告任务进度

        Args:
            worker_id: 节点 ID
            task_id: 任务 ID
            progress: 进度 (0.0 - 1.0)
            current_generation: 当前代数
            best_fitness: 当前最优适应度

        Returns:
            是否成功
        """
        task = await self._task_queue.get_task(task_id)
        if task and task.worker_id == worker_id:
            task.progress = progress
            task.metadata["current_generation"] = current_generation
            task.metadata["best_fitness"] = best_fitness
            await self._task_queue.update_task(task)
            return True
        return False

    async def report_result(
        self,
        worker_id: str,
        task_id: str,
        success: bool,
        result: Dict[str, Any],
        error: Optional[str] = None,
    ) -> bool:
        """
        报告任务结果

        Args:
            worker_id: 节点 ID
            task_id: 任务 ID
            success: 是否成功
            result: 结果数据
            error: 错误信息

        Returns:
            是否成功
        """
        task = await self._task_queue.get_task(task_id)
        if not task or task.worker_id != worker_id:
            return False

        # 更新任务状态
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = time.time()
        task.result = result
        task.last_error = error
        await self._task_queue.update_task(task)

        # 更新 Worker 统计
        async with self._worker_lock:
            worker = self._workers.get(worker_id)
            if worker:
                worker.current_tasks = max(0, worker.current_tasks - 1)
                worker.current_task_id = None
                if success:
                    worker.total_completed += 1
                else:
                    worker.total_failed += 1

                # 更新平均耗时
                duration = task.completed_at - (task.started_at or task.created_at)
                total = worker.total_completed + worker.total_failed
                worker.avg_task_duration = (
                    (worker.avg_task_duration * (total - 1) + duration) / total
                )

        # 添加到结果聚合器
        task_result = TaskResult(
            task_id=task_id,
            worker_id=worker_id,
            success=success,
            goal=task.payload.get("goal", ""),
            category=task.payload.get("category", ""),
            best_prompt=result.get("best_prompt", ""),
            best_response=result.get("best_response", ""),
            best_fitness=result.get("best_fitness", 0.0),
            generations=result.get("generations", 0),
            total_queries=result.get("total_queries", 0),
            duration_seconds=result.get("duration_seconds", 0.0),
            started_at=task.started_at or 0.0,
            completed_at=task.completed_at or 0.0,
            history_summary=result.get("history", [])[-10:],
            error=error,
        )
        await self._aggregator.add_result(task_result)

        # 更新统计
        if success:
            self._stats["total_tasks_completed"] += 1
        else:
            self._stats["total_tasks_failed"] += 1

        # 清理分配记录
        if task_id in self._task_assignments:
            del self._task_assignments[task_id]

        # 触发回调
        if self._on_task_complete:
            self._on_task_complete(task)

        print(f"[Coordinator] 任务完成: {task_id[:8]} ({'成功' if success else '失败'})")
        return True

    async def get_status(self) -> Dict[str, Any]:
        """获取协调器状态"""
        queue_stats = await self._task_queue.get_queue_stats()
        aggregator_stats = await self._aggregator.get_statistics()

        async with self._worker_lock:
            workers = [w.to_dict() for w in self._workers.values()]
            online_workers = len([w for w in self._workers.values() if w.status == "online"])

        uptime = time.time() - self._stats["start_time"] if self._stats["start_time"] else 0

        return {
            "status": "running" if self._running else "stopped",
            "uptime_seconds": uptime,
            "queue": queue_stats,
            "results": aggregator_stats,
            "workers": {
                "total": len(workers),
                "online": online_workers,
                "list": workers,
            },
            "stats": self._stats,
        }

    async def get_workers(self) -> List[Dict[str, Any]]:
        """获取所有工作节点"""
        async with self._worker_lock:
            return [w.to_dict() for w in self._workers.values()]

    async def get_results(
        self,
        limit: int = 100,
        category: Optional[str] = None,
        success_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """获取测试结果"""
        if success_only:
            results = await self._aggregator.get_successful_results()
        elif category:
            results = await self._aggregator.get_results_by_category(category)
        else:
            results = await self._aggregator.get_all_results()

        return [r.to_dict() for r in results[:limit]]

    async def export_report(
        self,
        filepath: str,
        format: str = "html",
        title: str = "分布式测试报告",
    ) -> bool:
        """导出报告"""
        if format == "html":
            return await self._aggregator.export_html(filepath, title)
        elif format == "json":
            return await self._aggregator.export_json(filepath)
        return False

    # ==================== 私有方法 ====================

    async def _heartbeat_monitor(self):
        """心跳监控任务"""
        while self._running:
            try:
                await asyncio.sleep(self.config.worker_timeout / 3)

                current_time = time.time()
                async with self._worker_lock:
                    for worker in self._workers.values():
                        if current_time - worker.last_heartbeat > self.config.worker_timeout:
                            if worker.status == "online":
                                worker.status = "offline"
                                print(f"[Coordinator] Worker 离线: {worker.worker_name}")

                                # 重新分配任务
                                await self._reassign_worker_tasks(worker.worker_id)

                                if self._on_worker_change:
                                    self._on_worker_change(worker, "offline")

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Coordinator] 心跳监控错误: {e}")

    async def _task_timeout_monitor(self):
        """任务超时监控"""
        while self._running:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                cleaned = await self._task_queue.cleanup_expired()
                if cleaned > 0:
                    print(f"[Coordinator] 清理超时任务: {cleaned}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Coordinator] 超时监控错误: {e}")

    async def _cleanup_task(self):
        """定期清理任务"""
        while self._running:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次

                # 重新入队停滞的任务
                if isinstance(self._task_queue, MemoryTaskQueue):
                    requeued = await self._task_queue.requeue_stalled_tasks(300)
                    if requeued > 0:
                        print(f"[Coordinator] 重新入队停滞任务: {requeued}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Coordinator] 清理任务错误: {e}")

    async def _reassign_worker_tasks(self, worker_id: str):
        """重新分配离线节点的任务"""
        tasks_to_reassign = [
            task_id for task_id, wid in self._task_assignments.items()
            if wid == worker_id
        ]

        for task_id in tasks_to_reassign:
            task = await self._task_queue.get_task(task_id)
            if task and task.status == TaskStatus.RUNNING:
                # 重新入队
                task.status = TaskStatus.QUEUED
                task.worker_id = None
                task.started_at = None
                task.retry_count += 1
                await self._task_queue.update_task(task)
                del self._task_assignments[task_id]
                print(f"[Coordinator] 任务重新入队: {task_id[:8]}")

    async def _select_worker(self) -> Optional[str]:
        """
        根据负载均衡策略选择工作节点

        Returns:
            选中的 Worker ID 或 None
        """
        async with self._worker_lock:
            available_workers = [
                w for w in self._workers.values()
                if w.is_available()
            ]

            if not available_workers:
                return None

            strategy = self.config.load_balance_strategy

            if strategy == LoadBalanceStrategy.ROUND_ROBIN:
                # 轮询：选择完成任务最少的
                worker = min(available_workers, key=lambda w: w.total_completed)
                return worker.worker_id

            elif strategy == LoadBalanceStrategy.LEAST_LOADED:
                # 最少负载
                worker = min(available_workers, key=lambda w: w.get_load())
                return worker.worker_id

            elif strategy == LoadBalanceStrategy.RANDOM:
                # 随机
                import random
                worker = random.choice(available_workers)
                return worker.worker_id

            elif strategy == LoadBalanceStrategy.WEIGHTED:
                # 加权（根据历史性能）
                # 性能越好（耗时越短），权重越高
                weights = []
                for w in available_workers:
                    # 计算权重：(1 - 负载) * (1 / (平均耗时 + 1))
                    weight = (1 - w.get_load()) * (1 / (w.avg_task_duration + 1))
                    weights.append(weight)

                total_weight = sum(weights)
                if total_weight == 0:
                    worker = available_workers[0]
                else:
                    import random
                    r = random.uniform(0, total_weight)
                    cumsum = 0
                    for w, weight in zip(available_workers, weights):
                        cumsum += weight
                        if r <= cumsum:
                            worker = w
                            break
                    else:
                        worker = available_workers[-1]

                return worker.worker_id

            return available_workers[0].worker_id if available_workers else None

    async def _start_api_server(self):
        """启动 REST API 服务器"""
        try:
            from aiohttp import web

            app = web.Application()
            self._app = app

            # 添加路由
            app.router.add_get("/status", self._handle_status)
            app.router.add_get("/workers", self._handle_workers)
            app.router.add_get("/tasks", self._handle_tasks)
            app.router.add_get("/tasks/{task_id}", self._handle_task_detail)
            app.router.add_post("/tasks", self._handle_submit_task)
            app.router.add_delete("/tasks/{task_id}", self._handle_cancel_task)
            app.router.add_get("/results", self._handle_results)
            app.router.add_get("/results/export", self._handle_export)

            # Worker API（供 Worker 调用）
            app.router.add_post("/worker/register", self._handle_worker_register)
            app.router.add_post("/worker/heartbeat", self._handle_worker_heartbeat)
            app.router.add_post("/worker/request", self._handle_worker_request)
            app.router.add_post("/worker/progress", self._handle_worker_progress)
            app.router.add_post("/worker/result", self._handle_worker_result)

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(
                runner,
                self.config.host,
                self.config.port,
            )
            await site.start()

            print(f"[Coordinator] REST API 已启动: http://{self.config.host}:{self.config.port}")

        except ImportError:
            print("[Coordinator] 警告: aiohttp 未安装，REST API 不可用")
        except Exception as e:
            print(f"[Coordinator] API 服务器启动失败: {e}")

    # ==================== HTTP 处理器 ====================

    async def _handle_status(self, request):
        """处理状态查询"""
        from aiohttp import web
        status = await self.get_status()
        return web.json_response(status)

    async def _handle_workers(self, request):
        """处理工作节点查询"""
        from aiohttp import web
        workers = await self.get_workers()
        return web.json_response({"workers": workers})

    async def _handle_tasks(self, request):
        """处理任务列表查询"""
        from aiohttp import web
        stats = await self._task_queue.get_queue_stats()
        return web.json_response(stats)

    async def _handle_task_detail(self, request):
        """处理任务详情查询"""
        from aiohttp import web
        task_id = request.match_info["task_id"]
        task = await self.get_task_status(task_id)
        if task:
            return web.json_response(task)
        return web.json_response({"error": "Task not found"}, status=404)

    async def _handle_submit_task(self, request):
        """处理任务提交"""
        from aiohttp import web
        try:
            data = await request.json()
            task_id = await self.submit_task(
                goal=data.get("goal", ""),
                seed_template=data.get("seed_template", "Please help me with: {goal}"),
                target_output=data.get("target_output", "Sure, here is"),
                category=data.get("category", ""),
                priority=data.get("priority", TaskPriority.NORMAL.value),
                timeout=data.get("timeout", 3600.0),
            )
            return web.json_response({"task_id": task_id})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def _handle_cancel_task(self, request):
        """处理任务取消"""
        from aiohttp import web
        task_id = request.match_info["task_id"]
        success = await self.cancel_task(task_id)
        return web.json_response({"success": success})

    async def _handle_results(self, request):
        """处理结果查询"""
        from aiohttp import web
        limit = int(request.query.get("limit", 100))
        category = request.query.get("category")
        success_only = request.query.get("success_only", "false").lower() == "true"
        results = await self.get_results(limit, category, success_only)
        return web.json_response({"results": results})

    async def _handle_export(self, request):
        """处理报告导出"""
        from aiohttp import web
        format_type = request.query.get("format", "html")
        title = request.query.get("title", "分布式测试报告")

        filepath = f"reports/distributed_report.{format_type}"
        Path("reports").mkdir(parents=True, exist_ok=True)

        success = await self.export_report(filepath, format_type, title)
        if success:
            return web.json_response({"filepath": filepath})
        return web.json_response({"error": "Export failed"}, status=500)

    async def _handle_worker_register(self, request):
        """处理 Worker 注册"""
        from aiohttp import web
        try:
            data = await request.json()
            success = await self.register_worker(
                worker_id=data.get("worker_id", str(uuid.uuid4())),
                worker_name=data.get("worker_name", ""),
                address=data.get("address", request.remote),
                max_concurrent=data.get("max_concurrent", 4),
                tags=data.get("tags", []),
            )
            return web.json_response({"success": success})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def _handle_worker_heartbeat(self, request):
        """处理 Worker 心跳"""
        from aiohttp import web
        try:
            data = await request.json()
            success = await self.heartbeat(
                worker_id=data.get("worker_id"),
                current_tasks=data.get("current_tasks", 0),
                cpu_usage=data.get("cpu_usage", 0.0),
                memory_usage=data.get("memory_usage", 0.0),
            )
            return web.json_response({"success": success})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def _handle_worker_request(self, request):
        """处理 Worker 任务请求"""
        from aiohttp import web
        try:
            data = await request.json()
            task = await self.request_task(data.get("worker_id"))
            if task:
                return web.json_response({"task": task})
            return web.json_response({"task": None})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def _handle_worker_progress(self, request):
        """处理 Worker 进度上报"""
        from aiohttp import web
        try:
            data = await request.json()
            success = await self.report_progress(
                worker_id=data.get("worker_id"),
                task_id=data.get("task_id"),
                progress=data.get("progress", 0.0),
                current_generation=data.get("current_generation", 0),
                best_fitness=data.get("best_fitness", 0.0),
            )
            return web.json_response({"success": success})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def _handle_worker_result(self, request):
        """处理 Worker 结果上报"""
        from aiohttp import web
        try:
            data = await request.json()
            success = await self.report_result(
                worker_id=data.get("worker_id"),
                task_id=data.get("task_id"),
                success=data.get("success", False),
                result=data.get("result", {}),
                error=data.get("error"),
            )
            return web.json_response({"success": success})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)


async def run_coordinator(
    config: Optional[CoordinatorConfig] = None,
    queue_config: Optional[QueueConfig] = None,
):
    """
    运行协调器的便捷函数

    Args:
        config: 协调器配置
        queue_config: 队列配置
    """
    coordinator = DistributedCoordinator(config, queue_config)

    # 设置信号处理
    loop = asyncio.get_event_loop()

    def signal_handler():
        print("\n[Coordinator] 收到停止信号...")
        asyncio.create_task(coordinator.stop())

    try:
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    except NotImplementedError:
        # Windows 不支持 add_signal_handler
        pass

    await coordinator.start()

    # 保持运行直到收到停止信号
    while coordinator._running:
        await asyncio.sleep(1)
