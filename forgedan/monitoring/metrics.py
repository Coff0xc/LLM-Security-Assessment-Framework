# -*- coding: utf-8 -*-
"""
FORGEDAN Prometheus 指标定义

定义所有用于监控 FORGEDAN 系统运行状态的 Prometheus 指标。
包含攻击统计、LLM 调用、性能指标和缓存统计等。

指标命名规范:
- 前缀: forgedan_
- Counter: _total 后缀
- Histogram: _seconds/_bytes 等单位后缀
- Gauge: 无特定后缀

标签规范:
- model: 模型名称 (如 gpt-4, claude-3)
- attack_type: 攻击类型 (如 jailbreak, injection)
- status: 状态 (如 success, failed, blocked)
- category: 类别 (如 harmful, illegal)
"""

import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json


class MetricType(Enum):
    """指标类型枚举"""

    COUNTER = "counter"  # 只增不减的计数器
    GAUGE = "gauge"  # 可增可减的仪表
    HISTOGRAM = "histogram"  # 分布直方图
    SUMMARY = "summary"  # 摘要 (分位数)


@dataclass
class MetricLabel:
    """指标标签定义"""

    name: str
    description: str
    allowed_values: Optional[List[str]] = None  # None 表示任意值


@dataclass
class MetricDefinition:
    """指标定义"""

    name: str
    description: str
    type: MetricType
    labels: List[MetricLabel] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # 仅用于 Histogram
    objectives: Optional[Dict[float, float]] = None  # 仅用于 Summary


class Counter:
    """Prometheus Counter 实现"""

    def __init__(self, name: str, description: str, labels: List[str] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, value: float = 1.0, **labels) -> None:
        """增加计数"""
        if value < 0:
            raise ValueError("Counter 只能增加正值")
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] += value

    def get(self, **labels) -> float:
        """获取当前值"""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._values.get(label_key, 0.0)

    def _make_label_key(self, labels: Dict[str, str]) -> tuple:
        """生成标签键"""
        return tuple(labels.get(ln, "") for ln in self.label_names)

    def collect(self) -> List[Dict[str, Any]]:
        """收集所有指标数据"""
        result = []
        with self._lock:
            for label_key, value in self._values.items():
                labels = dict(zip(self.label_names, label_key))
                result.append(
                    {
                        "name": self.name,
                        "type": "counter",
                        "value": value,
                        "labels": labels,
                        "description": self.description,
                    }
                )
        return result


class Gauge:
    """Prometheus Gauge 实现"""

    def __init__(self, name: str, description: str, labels: List[str] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, float] = {}
        self._lock = threading.Lock()

    def set(self, value: float, **labels) -> None:
        """设置值"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] = value

    def inc(self, value: float = 1.0, **labels) -> None:
        """增加值"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] = self._values.get(label_key, 0.0) + value

    def dec(self, value: float = 1.0, **labels) -> None:
        """减少值"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] = self._values.get(label_key, 0.0) - value

    def get(self, **labels) -> float:
        """获取当前值"""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._values.get(label_key, 0.0)

    def _make_label_key(self, labels: Dict[str, str]) -> tuple:
        return tuple(labels.get(ln, "") for ln in self.label_names)

    def collect(self) -> List[Dict[str, Any]]:
        """收集所有指标数据"""
        result = []
        with self._lock:
            for label_key, value in self._values.items():
                labels = dict(zip(self.label_names, label_key))
                result.append(
                    {
                        "name": self.name,
                        "type": "gauge",
                        "value": value,
                        "labels": labels,
                        "description": self.description,
                    }
                )
        return result


class Histogram:
    """Prometheus Histogram 实现"""

    # 默认桶边界
    DEFAULT_BUCKETS = (
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
        float("inf"),
    )

    def __init__(
        self,
        name: str,
        description: str,
        labels: List[str] = None,
        buckets: tuple = None,
    ):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._buckets: Dict[tuple, Dict[float, int]] = defaultdict(
            lambda: {b: 0 for b in self.buckets}
        )
        self._sums: Dict[tuple, float] = defaultdict(float)
        self._counts: Dict[tuple, int] = defaultdict(int)
        self._lock = threading.Lock()

    def observe(self, value: float, **labels) -> None:
        """记录观察值"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._sums[label_key] += value
            self._counts[label_key] += 1
            for bucket in self.buckets:
                if value <= bucket:
                    self._buckets[label_key][bucket] += 1

    def time(self, **labels) -> "HistogramTimer":
        """计时上下文管理器"""
        return HistogramTimer(self, labels)

    def _make_label_key(self, labels: Dict[str, str]) -> tuple:
        return tuple(labels.get(ln, "") for ln in self.label_names)

    def collect(self) -> List[Dict[str, Any]]:
        """收集所有指标数据"""
        result = []
        with self._lock:
            for label_key in self._buckets:
                labels = dict(zip(self.label_names, label_key))

                # 累积桶计数
                cumulative = 0
                for bucket in sorted(b for b in self.buckets if b != float("inf")):
                    cumulative += self._buckets[label_key].get(bucket, 0)
                    result.append(
                        {
                            "name": f"{self.name}_bucket",
                            "type": "histogram",
                            "value": cumulative,
                            "labels": {**labels, "le": str(bucket)},
                            "description": self.description,
                        }
                    )

                # +Inf 桶
                result.append(
                    {
                        "name": f"{self.name}_bucket",
                        "type": "histogram",
                        "value": self._counts[label_key],
                        "labels": {**labels, "le": "+Inf"},
                        "description": self.description,
                    }
                )

                # sum 和 count
                result.append(
                    {
                        "name": f"{self.name}_sum",
                        "type": "histogram",
                        "value": self._sums[label_key],
                        "labels": labels,
                        "description": self.description,
                    }
                )
                result.append(
                    {
                        "name": f"{self.name}_count",
                        "type": "histogram",
                        "value": self._counts[label_key],
                        "labels": labels,
                        "description": self.description,
                    }
                )
        return result


class HistogramTimer:
    """Histogram 计时器上下文管理器"""

    def __init__(self, histogram: Histogram, labels: Dict[str, str]):
        self.histogram = histogram
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.histogram.observe(duration, **self.labels)
        return False


class ForgeDanMetrics:
    """
    FORGEDAN 指标管理器

    统一管理所有 Prometheus 指标的定义和记录。
    提供便捷的指标记录方法和数据导出功能。

    使用示例:
        metrics = ForgeDanMetrics()
        metrics.record_attack(success=True, model="gpt-4")
        metrics.record_llm_query(model="gpt-4", latency=0.5)
    """

    def __init__(self, prefix: str = "forgedan"):
        """
        初始化指标管理器

        Args:
            prefix: 指标名称前缀
        """
        self.prefix = prefix
        self._lock = threading.Lock()

        # ============== 攻击相关指标 ==============

        # 攻击总数
        self.attacks_total = Counter(
            name=f"{prefix}_attacks_total",
            description="攻击尝试总数",
            labels=["model", "attack_type", "category"],
        )

        # 成功攻击数
        self.attacks_success = Counter(
            name=f"{prefix}_attacks_success_total",
            description="成功攻击总数",
            labels=["model", "attack_type", "category"],
        )

        # 攻击失败数 (被拒绝)
        self.attacks_blocked = Counter(
            name=f"{prefix}_attacks_blocked_total",
            description="被拦截的攻击总数",
            labels=["model", "attack_type", "category"],
        )

        # 攻击耗时分布
        self.attack_duration = Histogram(
            name=f"{prefix}_attack_duration_seconds",
            description="单次攻击耗时分布 (秒)",
            labels=["model", "attack_type"],
            buckets=(
                0.1,
                0.5,
                1.0,
                2.0,
                5.0,
                10.0,
                30.0,
                60.0,
                120.0,
                300.0,
                float("inf"),
            ),
        )

        # ============== LLM 查询相关指标 ==============

        # LLM 查询总数
        self.queries_total = Counter(
            name=f"{prefix}_queries_total",
            description="LLM 查询总数",
            labels=["model", "status"],
        )

        # 模型响应延迟分布
        self.model_latency = Histogram(
            name=f"{prefix}_model_latency_seconds",
            description="模型响应延迟分布 (秒)",
            labels=["model"],
            buckets=(
                0.01,
                0.05,
                0.1,
                0.25,
                0.5,
                1.0,
                2.0,
                5.0,
                10.0,
                30.0,
                float("inf"),
            ),
        )

        # 查询错误数
        self.query_errors = Counter(
            name=f"{prefix}_query_errors_total",
            description="查询错误总数",
            labels=["model", "error_type"],
        )

        # ============== 进化算法指标 ==============

        # 当前适应度
        self.fitness_score = Gauge(
            name=f"{prefix}_fitness_score",
            description="当前最佳适应度分数",
            labels=["task_id", "model"],
        )

        # 平均适应度
        self.fitness_avg = Gauge(
            name=f"{prefix}_fitness_avg",
            description="种群平均适应度",
            labels=["task_id", "model"],
        )

        # 当前代数
        self.current_generation = Gauge(
            name=f"{prefix}_current_generation",
            description="当前进化代数",
            labels=["task_id"],
        )

        # 种群大小
        self.population_size = Gauge(
            name=f"{prefix}_population_size",
            description="当前种群大小",
            labels=["task_id"],
        )

        # ============== 任务管理指标 ==============

        # 活跃任务数
        self.active_tasks = Gauge(
            name=f"{prefix}_active_tasks",
            description="当前活跃任务数",
            labels=["task_type"],
        )

        # 任务总数
        self.tasks_total = Counter(
            name=f"{prefix}_tasks_total",
            description="任务总数",
            labels=["task_type", "status"],
        )

        # 任务执行时间
        self.task_duration = Histogram(
            name=f"{prefix}_task_duration_seconds",
            description="任务执行时间分布 (秒)",
            labels=["task_type"],
            buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600, float("inf")),
        )

        # ============== 缓存指标 ==============

        # 缓存命中数
        self.cache_hits = Counter(
            name=f"{prefix}_cache_hits_total",
            description="缓存命中总数",
            labels=["cache_type"],
        )

        # 缓存未命中数
        self.cache_misses = Counter(
            name=f"{prefix}_cache_misses_total",
            description="缓存未命中总数",
            labels=["cache_type"],
        )

        # 缓存大小
        self.cache_size = Gauge(
            name=f"{prefix}_cache_size",
            description="当前缓存大小",
            labels=["cache_type"],
        )

        # ============== 系统资源指标 ==============

        # CPU 使用率
        self.cpu_usage = Gauge(
            name=f"{prefix}_cpu_usage_percent",
            description="CPU 使用率百分比",
            labels=[],
        )

        # 内存使用量
        self.memory_usage = Gauge(
            name=f"{prefix}_memory_usage_bytes",
            description="内存使用量 (字节)",
            labels=["type"],  # resident, virtual
        )

        # 线程数
        self.thread_count = Gauge(
            name=f"{prefix}_thread_count", description="当前线程数", labels=[]
        )

        # ============== 变异策略指标 ==============

        # 变异策略使用次数
        self.mutation_usage = Counter(
            name=f"{prefix}_mutation_usage_total",
            description="变异策略使用次数",
            labels=["strategy"],
        )

        # 变异策略成功率
        self.mutation_success_rate = Gauge(
            name=f"{prefix}_mutation_success_rate",
            description="变异策略成功率",
            labels=["strategy"],
        )

        # 收集所有指标实例
        self._all_metrics = [
            self.attacks_total,
            self.attacks_success,
            self.attacks_blocked,
            self.attack_duration,
            self.queries_total,
            self.model_latency,
            self.query_errors,
            self.fitness_score,
            self.fitness_avg,
            self.current_generation,
            self.population_size,
            self.active_tasks,
            self.tasks_total,
            self.task_duration,
            self.cache_hits,
            self.cache_misses,
            self.cache_size,
            self.cpu_usage,
            self.memory_usage,
            self.thread_count,
            self.mutation_usage,
            self.mutation_success_rate,
        ]

    # ============== 便捷记录方法 ==============

    def record_attack(
        self,
        success: bool,
        model: str = "unknown",
        attack_type: str = "jailbreak",
        category: str = "unknown",
        duration: float = None,
    ) -> None:
        """
        记录一次攻击

        Args:
            success: 是否成功
            model: 目标模型
            attack_type: 攻击类型
            category: 攻击类别
            duration: 攻击耗时 (秒)
        """
        self.attacks_total.inc(model=model, attack_type=attack_type, category=category)

        if success:
            self.attacks_success.inc(
                model=model, attack_type=attack_type, category=category
            )
        else:
            self.attacks_blocked.inc(
                model=model, attack_type=attack_type, category=category
            )

        if duration is not None:
            self.attack_duration.observe(duration, model=model, attack_type=attack_type)

    def record_llm_query(
        self, model: str, latency: float, success: bool = True, error_type: str = None
    ) -> None:
        """
        记录 LLM 查询

        Args:
            model: 模型名称
            latency: 响应延迟 (秒)
            success: 是否成功
            error_type: 错误类型 (失败时)
        """
        status = "success" if success else "error"
        self.queries_total.inc(model=model, status=status)
        self.model_latency.observe(latency, model=model)

        if not success and error_type:
            self.query_errors.inc(model=model, error_type=error_type)

    def update_fitness(
        self,
        task_id: str,
        model: str,
        best_fitness: float,
        avg_fitness: float = None,
        generation: int = None,
        population_size: int = None,
    ) -> None:
        """
        更新适应度指标

        Args:
            task_id: 任务 ID
            model: 模型名称
            best_fitness: 最佳适应度
            avg_fitness: 平均适应度
            generation: 当前代数
            population_size: 种群大小
        """
        self.fitness_score.set(best_fitness, task_id=task_id, model=model)

        if avg_fitness is not None:
            self.fitness_avg.set(avg_fitness, task_id=task_id, model=model)

        if generation is not None:
            self.current_generation.set(generation, task_id=task_id)

        if population_size is not None:
            self.population_size.set(population_size, task_id=task_id)

    def record_task_start(self, task_type: str = "evolution") -> None:
        """记录任务开始"""
        self.active_tasks.inc(task_type=task_type)
        self.tasks_total.inc(task_type=task_type, status="started")

    def record_task_complete(
        self, task_type: str = "evolution", success: bool = True, duration: float = None
    ) -> None:
        """记录任务完成"""
        self.active_tasks.dec(task_type=task_type)
        status = "success" if success else "failed"
        self.tasks_total.inc(task_type=task_type, status=status)

        if duration is not None:
            self.task_duration.observe(duration, task_type=task_type)

    def record_cache_access(self, hit: bool, cache_type: str = "response") -> None:
        """记录缓存访问"""
        if hit:
            self.cache_hits.inc(cache_type=cache_type)
        else:
            self.cache_misses.inc(cache_type=cache_type)

    def update_cache_size(self, size: int, cache_type: str = "response") -> None:
        """更新缓存大小"""
        self.cache_size.set(size, cache_type=cache_type)

    def record_mutation(self, strategy: str, success: bool = True) -> None:
        """记录变异策略使用"""
        self.mutation_usage.inc(strategy=strategy)

    def update_mutation_success_rate(self, strategy: str, rate: float) -> None:
        """更新变异策略成功率"""
        self.mutation_success_rate.set(rate, strategy=strategy)

    def update_system_metrics(
        self,
        cpu_percent: float = None,
        memory_resident: int = None,
        memory_virtual: int = None,
        threads: int = None,
    ) -> None:
        """更新系统资源指标"""
        if cpu_percent is not None:
            self.cpu_usage.set(cpu_percent)

        if memory_resident is not None:
            self.memory_usage.set(memory_resident, type="resident")

        if memory_virtual is not None:
            self.memory_usage.set(memory_virtual, type="virtual")

        if threads is not None:
            self.thread_count.set(threads)

    # ============== 数据导出 ==============

    def collect_all(self) -> List[Dict[str, Any]]:
        """收集所有指标数据"""
        result = []
        for metric in self._all_metrics:
            result.extend(metric.collect())
        return result

    def to_prometheus_format(self) -> str:
        """
        导出为 Prometheus 文本格式

        Returns:
            Prometheus exposition format 文本
        """
        lines = []
        collected = self.collect_all()

        # 按指标名分组
        by_name: Dict[str, List[Dict]] = defaultdict(list)
        for item in collected:
            by_name[item["name"]].append(item)

        for name, items in sorted(by_name.items()):
            if not items:
                continue

            # HELP 和 TYPE 行
            description = items[0].get("description", "")
            metric_type = items[0].get("type", "untyped")

            lines.append(f"# HELP {name} {description}")
            lines.append(f"# TYPE {name} {metric_type}")

            # 数据行
            for item in items:
                labels = item.get("labels", {})
                value = item.get("value", 0)

                if labels:
                    label_str = ",".join(
                        f'{k}="{v}"' for k, v in sorted(labels.items())
                    )
                    lines.append(f"{name}{{{label_str}}} {value}")
                else:
                    lines.append(f"{name} {value}")

            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        """导出为 JSON 格式"""
        return json.dumps(self.collect_all(), indent=2, ensure_ascii=False)

    def get_summary(self) -> Dict[str, Any]:
        """
        获取指标摘要

        Returns:
            包含关键指标的摘要字典
        """
        return {
            "attacks": {
                "total": sum(
                    self.attacks_total.get(model=m)
                    for m in ["gpt-4", "gpt-3.5-turbo", "claude-3", "unknown"]
                ),
                "success": sum(
                    self.attacks_success.get(model=m)
                    for m in ["gpt-4", "gpt-3.5-turbo", "claude-3", "unknown"]
                ),
            },
            "queries": {
                "total": sum(
                    self.queries_total.get(model=m, status=s)
                    for m in ["gpt-4", "gpt-3.5-turbo", "claude-3", "unknown"]
                    for s in ["success", "error"]
                ),
            },
            "cache": {
                "hits": self.cache_hits.get(cache_type="response"),
                "misses": self.cache_misses.get(cache_type="response"),
            },
            "tasks": {
                "active": self.active_tasks.get(task_type="evolution"),
            },
        }


# 全局单例
metrics = ForgeDanMetrics()


def get_metrics() -> ForgeDanMetrics:
    """获取全局指标实例"""
    return metrics
