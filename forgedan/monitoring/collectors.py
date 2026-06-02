# -*- coding: utf-8 -*-
"""
FORGEDAN 数据收集器

从各个组件收集运行数据并更新指标。

主要收集器:
- EngineCollector: 收集进化引擎数据
- AdapterCollector: 收集 LLM 适配器数据
- SystemCollector: 收集系统资源数据

使用示例:
    registry = CollectorRegistry()
    registry.register(EngineCollector(engine))
    registry.register(SystemCollector())
    registry.start_collection()
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from abc import ABC, abstractmethod
from weakref import ref, WeakValueDictionary

# 条件导入，避免循环引用
if TYPE_CHECKING:
    from ..engine import ForgeDAN_Engine
    from ..adapters.base import BaseModelAdapter

# 系统监控
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from .metrics import ForgeDanMetrics, metrics as global_metrics

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    收集器基类

    所有收集器必须实现 collect() 方法。
    """

    def __init__(self, metrics_instance: ForgeDanMetrics = None, interval: float = 5.0):
        """
        初始化收集器

        Args:
            metrics_instance: 指标实例
            interval: 收集间隔 (秒)
        """
        self.metrics = metrics_instance or global_metrics
        self.interval = interval
        self._enabled = True
        self._last_collection = 0.0

    @abstractmethod
    def collect(self) -> None:
        """执行数据收集"""
        pass

    def enable(self) -> None:
        """启用收集器"""
        self._enabled = True

    def disable(self) -> None:
        """禁用收集器"""
        self._enabled = False

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled

    def should_collect(self) -> bool:
        """检查是否应该收集"""
        if not self._enabled:
            return False
        now = time.time()
        if now - self._last_collection >= self.interval:
            self._last_collection = now
            return True
        return False


class EngineCollector(BaseCollector):
    """
    进化引擎数据收集器

    收集进化算法的运行状态和统计数据。
    """

    def __init__(
        self,
        engine: "ForgeDAN_Engine" = None,
        metrics_instance: ForgeDanMetrics = None,
        interval: float = 1.0,
    ):
        """
        初始化引擎收集器

        Args:
            engine: 进化引擎实例
            metrics_instance: 指标实例
            interval: 收集间隔
        """
        super().__init__(metrics_instance, interval)
        self._engine_ref = ref(engine) if engine else None
        self._task_start_times: Dict[str, float] = {}

    def set_engine(self, engine: "ForgeDAN_Engine") -> None:
        """设置引擎实例"""
        self._engine_ref = ref(engine)

    def get_engine(self) -> Optional["ForgeDAN_Engine"]:
        """获取引擎实例"""
        if self._engine_ref:
            return self._engine_ref()
        return None

    def collect(self) -> None:
        """收集引擎数据"""
        engine = self.get_engine()
        if not engine:
            return

        try:
            # 获取引擎状态
            state = engine.get_state()

            # 更新适应度指标
            task_id = state.get("task_id", "default")
            model_name = getattr(engine, "model_name", "unknown")

            if state.get("best_fitness", 0) > 0:
                self.metrics.update_fitness(
                    task_id=task_id,
                    model=model_name,
                    best_fitness=state.get("best_fitness", 0),
                    avg_fitness=state.get("avg_fitness"),
                    generation=state.get("current_generation"),
                    population_size=getattr(engine.config, "population_size", 10),
                )

            # 更新查询计数
            total_queries = state.get("total_queries", 0)
            if total_queries > 0:
                self.metrics.queries_total.inc(
                    value=0, model=model_name, status="success"  # 仅触发标签创建
                )

            # 检查缓存统计
            cache_stats = engine.get_cache_stats()
            if cache_stats:
                size = cache_stats.get("size", 0)

                self.metrics.update_cache_size(size, cache_type="response")

            # 更新变异策略统计
            if hasattr(engine, "mutator"):
                perf = engine.get_mutation_performance()
                for strategy, stats in perf.items():
                    success_rate = stats.get("success_rate", 0)
                    self.metrics.update_mutation_success_rate(strategy, success_rate)

        except Exception as e:
            logger.error(f"收集引擎数据失败: {e}")

    def on_attack_complete(
        self,
        success: bool,
        model: str,
        attack_type: str = "jailbreak",
        category: str = "unknown",
        duration: float = None,
    ) -> None:
        """
        攻击完成回调

        Args:
            success: 是否成功
            model: 模型名称
            attack_type: 攻击类型
            category: 类别
            duration: 耗时
        """
        self.metrics.record_attack(
            success=success,
            model=model,
            attack_type=attack_type,
            category=category,
            duration=duration,
        )

    def on_task_start(self, task_id: str, task_type: str = "evolution") -> None:
        """任务开始回调"""
        self._task_start_times[task_id] = time.time()
        self.metrics.record_task_start(task_type)

    def on_task_complete(
        self, task_id: str, task_type: str = "evolution", success: bool = True
    ) -> None:
        """任务完成回调"""
        start_time = self._task_start_times.pop(task_id, None)
        duration = None
        if start_time:
            duration = time.time() - start_time

        self.metrics.record_task_complete(
            task_type=task_type, success=success, duration=duration
        )


class AdapterCollector(BaseCollector):
    """
    LLM 适配器数据收集器

    收集 LLM API 调用的延迟和错误信息。
    """

    def __init__(self, metrics_instance: ForgeDanMetrics = None, interval: float = 5.0):
        """
        初始化适配器收集器

        Args:
            metrics_instance: 指标实例
            interval: 收集间隔
        """
        super().__init__(metrics_instance, interval)
        self._adapters: WeakValueDictionary = WeakValueDictionary()
        self._call_stats: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register_adapter(self, name: str, adapter: "BaseModelAdapter") -> None:
        """
        注册适配器

        Args:
            name: 适配器名称
            adapter: 适配器实例
        """
        self._adapters[name] = adapter
        self._call_stats[name] = {
            "total_calls": 0,
            "success_calls": 0,
            "error_calls": 0,
            "total_latency": 0.0,
            "errors_by_type": {},
        }

    def unregister_adapter(self, name: str) -> None:
        """注销适配器"""
        self._adapters.pop(name, None)
        self._call_stats.pop(name, None)

    def record_call(
        self,
        adapter_name: str,
        latency: float,
        success: bool = True,
        error_type: str = None,
    ) -> None:
        """
        记录 API 调用

        Args:
            adapter_name: 适配器名称
            latency: 延迟 (秒)
            success: 是否成功
            error_type: 错误类型
        """
        with self._lock:
            stats = self._call_stats.get(
                adapter_name,
                {
                    "total_calls": 0,
                    "success_calls": 0,
                    "error_calls": 0,
                    "total_latency": 0.0,
                    "errors_by_type": {},
                },
            )

            stats["total_calls"] += 1
            stats["total_latency"] += latency

            if success:
                stats["success_calls"] += 1
            else:
                stats["error_calls"] += 1
                if error_type:
                    stats["errors_by_type"][error_type] = (
                        stats["errors_by_type"].get(error_type, 0) + 1
                    )

            self._call_stats[adapter_name] = stats

        # 记录到 Prometheus 指标
        self.metrics.record_llm_query(
            model=adapter_name, latency=latency, success=success, error_type=error_type
        )

    def collect(self) -> None:
        """收集适配器数据"""
        with self._lock:
            for name, stats in self._call_stats.items():
                # 这里主要是同步累积的统计数据
                # 实际的指标记录在 record_call 中已完成
                pass

    def get_stats(self, adapter_name: str = None) -> Dict[str, Any]:
        """
        获取调用统计

        Args:
            adapter_name: 适配器名称 (None 表示所有)

        Returns:
            统计数据
        """
        with self._lock:
            if adapter_name:
                return self._call_stats.get(adapter_name, {})
            return dict(self._call_stats)


class SystemCollector(BaseCollector):
    """
    系统资源收集器

    收集 CPU、内存、线程等系统资源使用情况。
    """

    def __init__(
        self,
        metrics_instance: ForgeDanMetrics = None,
        interval: float = 5.0,
        process_only: bool = True,
    ):
        """
        初始化系统收集器

        Args:
            metrics_instance: 指标实例
            interval: 收集间隔
            process_only: 是否只收集当前进程的数据
        """
        super().__init__(metrics_instance, interval)
        self.process_only = process_only

        if HAS_PSUTIL:
            self._process = psutil.Process()
        else:
            self._process = None
            logger.warning("psutil 未安装，系统资源监控功能受限")

    def collect(self) -> None:
        """收集系统资源数据"""
        if not HAS_PSUTIL or not self._process:
            return

        try:
            # CPU 使用率
            if self.process_only:
                cpu_percent = self._process.cpu_percent(interval=0.1)
            else:
                cpu_percent = psutil.cpu_percent(interval=0.1)

            # 内存使用
            memory_info = self._process.memory_info()
            memory_resident = memory_info.rss
            memory_virtual = memory_info.vms

            # 线程数
            thread_count = self._process.num_threads()

            # 更新指标
            self.metrics.update_system_metrics(
                cpu_percent=cpu_percent,
                memory_resident=memory_resident,
                memory_virtual=memory_virtual,
                threads=thread_count,
            )

        except Exception as e:
            logger.error(f"收集系统资源数据失败: {e}")

    def get_process_info(self) -> Dict[str, Any]:
        """
        获取进程详细信息

        Returns:
            进程信息字典
        """
        if not HAS_PSUTIL or not self._process:
            return {"error": "psutil 未安装"}

        try:
            with self._process.oneshot():
                return {
                    "pid": self._process.pid,
                    "name": self._process.name(),
                    "cpu_percent": self._process.cpu_percent(),
                    "memory_rss": self._process.memory_info().rss,
                    "memory_vms": self._process.memory_info().vms,
                    "memory_percent": self._process.memory_percent(),
                    "threads": self._process.num_threads(),
                    "open_files": len(self._process.open_files()),
                    "connections": len(self._process.connections()),
                    "create_time": self._process.create_time(),
                }
        except Exception as e:
            return {"error": str(e)}


class CollectorRegistry:
    """
    收集器注册表

    管理多个收集器，提供统一的启动/停止接口。

    使用示例:
        registry = CollectorRegistry()
        registry.register(EngineCollector(engine))
        registry.register(SystemCollector())
        registry.start_collection()
    """

    def __init__(
        self, metrics_instance: ForgeDanMetrics = None, default_interval: float = 5.0
    ):
        """
        初始化注册表

        Args:
            metrics_instance: 指标实例
            default_interval: 默认收集间隔
        """
        self.metrics = metrics_instance or global_metrics
        self.default_interval = default_interval
        self._collectors: Dict[str, BaseCollector] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def register(self, collector: BaseCollector, name: str = None) -> str:
        """
        注册收集器

        Args:
            collector: 收集器实例
            name: 收集器名称 (可选)

        Returns:
            收集器名称
        """
        with self._lock:
            if name is None:
                name = f"{collector.__class__.__name__}_{len(self._collectors)}"

            self._collectors[name] = collector
            logger.debug(f"注册收集器: {name}")
            return name

    def unregister(self, name: str) -> bool:
        """
        注销收集器

        Args:
            name: 收集器名称

        Returns:
            是否成功
        """
        with self._lock:
            if name in self._collectors:
                del self._collectors[name]
                logger.debug(f"注销收集器: {name}")
                return True
            return False

    def get_collector(self, name: str) -> Optional[BaseCollector]:
        """获取收集器"""
        return self._collectors.get(name)

    def list_collectors(self) -> List[str]:
        """列出所有收集器"""
        return list(self._collectors.keys())

    def start_collection(self, background: bool = True) -> None:
        """
        启动数据收集

        Args:
            background: 是否在后台运行
        """
        if self._running:
            logger.warning("收集已在运行")
            return

        self._running = True

        if background:
            self._thread = threading.Thread(target=self._collection_loop, daemon=True)
            self._thread.start()
            logger.info("数据收集已启动 (后台模式)")
        else:
            self._collection_loop()

    def stop_collection(self) -> None:
        """停止数据收集"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.default_interval + 1)
        logger.info("数据收集已停止")

    def _collection_loop(self) -> None:
        """收集循环"""
        while self._running:
            with self._lock:
                collectors = list(self._collectors.values())

            for collector in collectors:
                if collector.should_collect():
                    try:
                        collector.collect()
                    except Exception as e:
                        logger.error(f"收集器执行失败: {e}")

            time.sleep(0.1)  # 小间隔，精确控制

    def collect_once(self) -> None:
        """执行一次收集"""
        with self._lock:
            collectors = list(self._collectors.values())

        for collector in collectors:
            if collector.is_enabled():
                try:
                    collector.collect()
                except Exception as e:
                    logger.error(f"收集器执行失败: {e}")

    def is_running(self) -> bool:
        """检查是否运行中"""
        return self._running


def create_default_registry(
    engine: "ForgeDAN_Engine" = None, metrics_instance: ForgeDanMetrics = None
) -> CollectorRegistry:
    """
    创建默认的收集器注册表

    Args:
        engine: 进化引擎
        metrics_instance: 指标实例

    Returns:
        配置好的注册表
    """
    registry = CollectorRegistry(metrics_instance=metrics_instance)

    # 注册引擎收集器
    engine_collector = EngineCollector(
        engine=engine, metrics_instance=metrics_instance, interval=1.0
    )
    registry.register(engine_collector, "engine")

    # 注册适配器收集器
    adapter_collector = AdapterCollector(
        metrics_instance=metrics_instance, interval=5.0
    )
    registry.register(adapter_collector, "adapter")

    # 注册系统收集器
    system_collector = SystemCollector(metrics_instance=metrics_instance, interval=5.0)
    registry.register(system_collector, "system")

    return registry
