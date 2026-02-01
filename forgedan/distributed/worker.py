# -*- coding: utf-8 -*-
"""
FORGEDAN 分布式工作节点模块

工作节点（Worker）负责：
- 注册到协调器
- 接收并执行测试任务
- 上报进度和结果
- 支持多进程执行
- 优雅退出
"""

import asyncio
import json
import os
import platform
import signal
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from multiprocessing import cpu_count, Process, Queue
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import threading

from .config import WorkerConfig


@dataclass
class WorkerState:
    """工作节点状态"""
    status: str = "idle"                    # idle / running / stopping
    current_tasks: int = 0
    total_completed: int = 0
    total_failed: int = 0
    start_time: float = 0.0
    last_heartbeat: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0


class DistributedWorker:
    """
    分布式工作节点

    负责执行具体的测试任务，支持：
    - 自动注册到协调器
    - 心跳保活
    - 任务执行
    - 进度上报
    - 多进程并行

    使用方法：
        worker = DistributedWorker(coordinator_url="http://localhost:8765")
        await worker.start()

        # 工作节点会自动获取并执行任务
        # ...

        await worker.stop()
    """

    def __init__(
        self,
        config: Optional[WorkerConfig] = None,
        engine_factory: Optional[Callable] = None,
    ):
        """
        初始化工作节点

        Args:
            config: 工作节点配置
            engine_factory: 引擎工厂函数，用于创建 ForgeDAN_Engine 实例
        """
        self.config = config or WorkerConfig()

        # 生成 Worker ID
        self.worker_id = self.config.worker_id or str(uuid.uuid4())
        self.worker_name = self.config.worker_name or f"worker-{self.worker_id[:8]}"

        # 引擎工厂
        self._engine_factory = engine_factory

        # 运行状态
        self._running = False
        self._state = WorkerState()
        self._shutdown_event = asyncio.Event()

        # HTTP 客户端
        self._session = None

        # 后台任务
        self._background_tasks: List[asyncio.Task] = []

        # 任务执行
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._current_tasks: Dict[str, asyncio.Task] = {}

        # 进程池（多进程模式）
        self._process_pool: Optional[ProcessPoolExecutor] = None
        self._max_processes = self.config.max_processes or cpu_count()

        # 线程池（异步任务）
        self._thread_pool: Optional[ThreadPoolExecutor] = None

    async def start(self):
        """启动工作节点"""
        if self._running:
            return

        self._running = True
        self._state.status = "running"
        self._state.start_time = time.time()
        self._shutdown_event.clear()

        print(f"[Worker {self.worker_name}] 启动工作节点...")

        # 创建 HTTP 会话
        try:
            import aiohttp
            self._session = aiohttp.ClientSession()
        except ImportError:
            print("[Worker] 警告: aiohttp 未安装")
            raise ImportError("需要安装 aiohttp: pip install aiohttp")

        # 创建线程池
        self._thread_pool = ThreadPoolExecutor(max_workers=self.config.max_concurrent_tasks)

        # 注册到协调器
        success = await self._register()
        if not success:
            print(f"[Worker {self.worker_name}] 注册失败，退出...")
            await self.stop()
            return

        # 启动后台任务
        self._background_tasks = [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._task_fetch_loop()),
            asyncio.create_task(self._resource_monitor_loop()),
        ]

        print(f"[Worker {self.worker_name}] 工作节点已启动")

    async def stop(self):
        """停止工作节点"""
        if not self._running:
            return

        print(f"[Worker {self.worker_name}] 正在停止...")
        self._running = False
        self._state.status = "stopping"
        self._shutdown_event.set()

        # 等待当前任务完成（优雅退出）
        if self._current_tasks:
            print(f"[Worker {self.worker_name}] 等待 {len(self._current_tasks)} 个任务完成...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._current_tasks.values(), return_exceptions=True),
                    timeout=self.config.graceful_shutdown_timeout
                )
            except asyncio.TimeoutError:
                print(f"[Worker {self.worker_name}] 超时，强制停止任务")
                for task in self._current_tasks.values():
                    task.cancel()

        # 取消后台任务
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # 关闭资源
        if self._session:
            await self._session.close()

        if self._thread_pool:
            self._thread_pool.shutdown(wait=False)

        if self._process_pool:
            self._process_pool.shutdown(wait=False)

        self._state.status = "idle"
        print(f"[Worker {self.worker_name}] 工作节点已停止")

    async def _register(self) -> bool:
        """注册到协调器"""
        try:
            url = f"{self.config.coordinator_url}/worker/register"
            data = {
                "worker_id": self.worker_id,
                "worker_name": self.worker_name,
                "max_concurrent": self.config.max_concurrent_tasks,
                "tags": self.config.worker_tags,
            }

            headers = {}
            if self.config.coordinator_token:
                headers["Authorization"] = f"Bearer {self.config.coordinator_token}"

            async with self._session.post(url, json=data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("success"):
                        print(f"[Worker {self.worker_name}] 注册成功")
                        return True

            print(f"[Worker {self.worker_name}] 注册失败")
            return False

        except Exception as e:
            print(f"[Worker {self.worker_name}] 注册异常: {e}")
            return False

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.config.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Worker {self.worker_name}] 心跳发送失败: {e}")
                await asyncio.sleep(5)  # 失败后短暂等待重试

    async def _send_heartbeat(self):
        """发送心跳"""
        try:
            url = f"{self.config.coordinator_url}/worker/heartbeat"
            data = {
                "worker_id": self.worker_id,
                "current_tasks": len(self._current_tasks),
                "cpu_usage": self._state.cpu_usage,
                "memory_usage": self._state.memory_usage,
            }

            headers = {}
            if self.config.coordinator_token:
                headers["Authorization"] = f"Bearer {self.config.coordinator_token}"

            async with self._session.post(url, json=data, headers=headers) as resp:
                if resp.status == 200:
                    self._state.last_heartbeat = time.time()

        except Exception as e:
            print(f"[Worker {self.worker_name}] 心跳异常: {e}")

    async def _task_fetch_loop(self):
        """任务获取循环"""
        while self._running:
            try:
                # 检查是否有空闲容量
                if len(self._current_tasks) >= self.config.max_concurrent_tasks:
                    await asyncio.sleep(1)
                    continue

                # 请求任务
                task_data = await self._request_task()
                if task_data:
                    # 创建任务执行
                    task_id = task_data["task_id"]
                    exec_task = asyncio.create_task(self._execute_task(task_data))
                    self._current_tasks[task_id] = exec_task

                    # 添加完成回调
                    exec_task.add_done_callback(
                        lambda t, tid=task_id: self._on_task_done(tid)
                    )
                else:
                    # 没有任务，等待一段时间
                    await asyncio.sleep(2)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Worker {self.worker_name}] 任务获取失败: {e}")
                await asyncio.sleep(5)

    async def _request_task(self) -> Optional[Dict[str, Any]]:
        """请求任务"""
        try:
            url = f"{self.config.coordinator_url}/worker/request"
            data = {"worker_id": self.worker_id}

            headers = {}
            if self.config.coordinator_token:
                headers["Authorization"] = f"Bearer {self.config.coordinator_token}"

            async with self._session.post(url, json=data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("task")

            return None

        except Exception as e:
            print(f"[Worker {self.worker_name}] 请求任务异常: {e}")
            return None

    async def _execute_task(self, task_data: Dict[str, Any]):
        """
        执行任务

        Args:
            task_data: 任务数据
        """
        task_id = task_data["task_id"]
        payload = task_data.get("payload", {})

        print(f"[Worker {self.worker_name}] 开始执行任务: {task_id[:8]}...")

        start_time = time.time()
        success = False
        result = {}
        error = None

        try:
            # 获取任务参数
            goal = payload.get("goal", "")
            seed_template = payload.get("seed_template", "Please help me with: {goal}")
            target_output = payload.get("target_output", "Sure, here is")
            category = payload.get("category", "")

            # 创建引擎并执行
            if self._engine_factory:
                engine = self._engine_factory()
            else:
                # 使用默认引擎
                from forgedan import ForgeDAN_Engine, ForgeDanConfig
                from forgedan.adapters import ModelAdapterFactory

                config = ForgeDanConfig()
                engine = ForgeDAN_Engine(config=config, enable_logging=False)

                # 使用 Mock 模式（实际使用时应配置真实 LLM）
                def mock_llm(prompt: str) -> str:
                    import random
                    if random.random() < 0.7:
                        return "I cannot help with that request."
                    return f"Sure, here is how to {prompt[:30]}..."

                engine.set_target_llm(mock_llm, model_name="mock")

            # 定义进度回调
            async def progress_callback(progress_data: Dict[str, Any]):
                await self._report_progress(
                    task_id=task_id,
                    progress=progress_data.get("current_generation", 0) / progress_data.get("max_generations", 1),
                    current_generation=progress_data.get("current_generation", 0),
                    best_fitness=progress_data.get("best_fitness", 0.0),
                )

            # 在线程池中执行引擎
            def run_engine():
                return engine.run(
                    seed_template=seed_template,
                    goal=goal,
                    target_output=target_output,
                    category=category,
                    generate_report=False,
                )

            loop = asyncio.get_event_loop()
            evolution_result = await loop.run_in_executor(
                self._thread_pool,
                run_engine
            )

            success = evolution_result.success
            result = {
                "best_prompt": evolution_result.best_prompt,
                "best_response": evolution_result.best_response,
                "best_fitness": evolution_result.best_fitness,
                "generations": evolution_result.generations,
                "total_queries": evolution_result.total_queries,
                "duration_seconds": evolution_result.duration_seconds,
                "history": evolution_result.history[-10:],  # 只保留最后10条
            }

        except Exception as e:
            import traceback
            error = f"{str(e)}\n{traceback.format_exc()}"
            print(f"[Worker {self.worker_name}] 任务执行失败: {e}")

        # 上报结果
        duration = time.time() - start_time
        result["duration_seconds"] = duration

        await self._report_result(
            task_id=task_id,
            success=success,
            result=result,
            error=error,
        )

        # 更新统计
        if success:
            self._state.total_completed += 1
        else:
            self._state.total_failed += 1

        print(f"[Worker {self.worker_name}] 任务完成: {task_id[:8]} ({'成功' if success else '失败'}) 耗时: {duration:.1f}s")

    async def _report_progress(
        self,
        task_id: str,
        progress: float,
        current_generation: int,
        best_fitness: float,
    ):
        """上报进度"""
        try:
            url = f"{self.config.coordinator_url}/worker/progress"
            data = {
                "worker_id": self.worker_id,
                "task_id": task_id,
                "progress": progress,
                "current_generation": current_generation,
                "best_fitness": best_fitness,
            }

            headers = {}
            if self.config.coordinator_token:
                headers["Authorization"] = f"Bearer {self.config.coordinator_token}"

            async with self._session.post(url, json=data, headers=headers) as resp:
                pass  # 忽略响应

        except Exception as e:
            pass  # 进度上报失败不影响任务执行

    async def _report_result(
        self,
        task_id: str,
        success: bool,
        result: Dict[str, Any],
        error: Optional[str],
    ):
        """上报结果"""
        try:
            url = f"{self.config.coordinator_url}/worker/result"
            data = {
                "worker_id": self.worker_id,
                "task_id": task_id,
                "success": success,
                "result": result,
                "error": error,
            }

            headers = {}
            if self.config.coordinator_token:
                headers["Authorization"] = f"Bearer {self.config.coordinator_token}"

            async with self._session.post(url, json=data, headers=headers) as resp:
                if resp.status != 200:
                    print(f"[Worker {self.worker_name}] 结果上报失败: {resp.status}")

        except Exception as e:
            print(f"[Worker {self.worker_name}] 结果上报异常: {e}")

    def _on_task_done(self, task_id: str):
        """任务完成回调"""
        if task_id in self._current_tasks:
            del self._current_tasks[task_id]
        self._state.current_tasks = len(self._current_tasks)

    async def _resource_monitor_loop(self):
        """资源监控循环"""
        while self._running:
            try:
                # 获取 CPU 和内存使用率
                self._state.cpu_usage = self._get_cpu_usage()
                self._state.memory_usage = self._get_memory_usage()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)

    def _get_cpu_usage(self) -> float:
        """获取 CPU 使用率"""
        try:
            import psutil
            return psutil.cpu_percent() / 100.0
        except ImportError:
            return 0.0

    def _get_memory_usage(self) -> float:
        """获取内存使用率"""
        try:
            import psutil
            return psutil.virtual_memory().percent / 100.0
        except ImportError:
            return 0.0

    def get_status(self) -> Dict[str, Any]:
        """获取节点状态"""
        return {
            "worker_id": self.worker_id,
            "worker_name": self.worker_name,
            "status": self._state.status,
            "current_tasks": len(self._current_tasks),
            "max_concurrent": self.config.max_concurrent_tasks,
            "total_completed": self._state.total_completed,
            "total_failed": self._state.total_failed,
            "uptime": time.time() - self._state.start_time if self._state.start_time else 0,
            "cpu_usage": self._state.cpu_usage,
            "memory_usage": self._state.memory_usage,
        }


class MultiProcessWorker:
    """
    多进程工作节点

    在单机上启动多个 Worker 进程，充分利用多核 CPU。

    使用方法：
        mp_worker = MultiProcessWorker(
            coordinator_url="http://localhost:8765",
            num_workers=4,
        )
        mp_worker.start()
        # ...
        mp_worker.stop()
    """

    def __init__(
        self,
        coordinator_url: str = "http://localhost:8765",
        num_workers: int = 0,
        worker_config: Optional[WorkerConfig] = None,
    ):
        """
        初始化多进程工作节点

        Args:
            coordinator_url: 协调器 URL
            num_workers: Worker 进程数（0 = CPU 核心数）
            worker_config: Worker 配置模板
        """
        self.coordinator_url = coordinator_url
        self.num_workers = num_workers or cpu_count()
        self.worker_config = worker_config or WorkerConfig()
        self.worker_config.coordinator_url = coordinator_url

        self._processes: List[Process] = []
        self._running = False

    def start(self):
        """启动所有 Worker 进程"""
        if self._running:
            return

        self._running = True
        print(f"[MultiProcessWorker] 启动 {self.num_workers} 个 Worker 进程...")

        for i in range(self.num_workers):
            # 为每个进程创建独立的配置
            config = WorkerConfig(
                worker_id=str(uuid.uuid4()),
                worker_name=f"worker-{i+1}",
                coordinator_url=self.coordinator_url,
                coordinator_token=self.worker_config.coordinator_token,
                max_concurrent_tasks=self.worker_config.max_concurrent_tasks,
                heartbeat_interval=self.worker_config.heartbeat_interval,
                worker_tags=self.worker_config.worker_tags + [f"process-{i+1}"],
            )

            p = Process(target=self._run_worker_process, args=(config,))
            p.start()
            self._processes.append(p)
            print(f"[MultiProcessWorker] Worker {i+1} 已启动 (PID: {p.pid})")

    def stop(self, timeout: float = 30.0):
        """停止所有 Worker 进程"""
        if not self._running:
            return

        print("[MultiProcessWorker] 正在停止所有 Worker 进程...")
        self._running = False

        # 发送终止信号
        for p in self._processes:
            if p.is_alive():
                p.terminate()

        # 等待进程结束
        for p in self._processes:
            p.join(timeout=timeout)
            if p.is_alive():
                print(f"[MultiProcessWorker] 强制终止进程 {p.pid}")
                p.kill()

        self._processes.clear()
        print("[MultiProcessWorker] 所有 Worker 已停止")

    @staticmethod
    def _run_worker_process(config: WorkerConfig):
        """在子进程中运行 Worker"""
        import asyncio

        async def run():
            worker = DistributedWorker(config=config)

            # 设置信号处理
            def signal_handler():
                asyncio.create_task(worker.stop())

            try:
                loop = asyncio.get_event_loop()
                loop.add_signal_handler(signal.SIGTERM, signal_handler)
                loop.add_signal_handler(signal.SIGINT, signal_handler)
            except NotImplementedError:
                pass

            await worker.start()

            # 保持运行
            while worker._running:
                await asyncio.sleep(1)

        asyncio.run(run())


async def run_worker(
    config: Optional[WorkerConfig] = None,
    coordinator_url: str = "http://localhost:8765",
):
    """
    运行工作节点的便捷函数

    Args:
        config: Worker 配置
        coordinator_url: 协调器 URL
    """
    if config is None:
        config = WorkerConfig(coordinator_url=coordinator_url)

    worker = DistributedWorker(config=config)

    # 设置信号处理
    loop = asyncio.get_event_loop()

    def signal_handler():
        print("\n[Worker] 收到停止信号...")
        asyncio.create_task(worker.stop())

    try:
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    except NotImplementedError:
        pass

    await worker.start()

    # 保持运行直到停止
    while worker._running:
        await asyncio.sleep(1)
