# -*- coding: utf-8 -*-
"""
FORGEDAN 结果聚合器模块

负责收集和聚合分布式测试的结果，支持：
- 分布式结果收集
- 实时统计
- 报告合并
- 断点续传支持
"""

import asyncio
import json
import time
import pickle
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from collections import defaultdict
import uuid


@dataclass
class TaskResult:
    """单个任务的结果"""
    task_id: str
    worker_id: str
    success: bool
    goal: str = ""
    category: str = ""

    # 进化结果
    best_prompt: str = ""
    best_response: str = ""
    best_fitness: float = 0.0
    generations: int = 0
    total_queries: int = 0

    # 时间统计
    duration_seconds: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0

    # 进化历史（摘要）
    history_summary: List[Dict[str, float]] = field(default_factory=list)

    # 错误信息
    error: Optional[str] = None

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "worker_id": self.worker_id,
            "success": self.success,
            "goal": self.goal,
            "category": self.category,
            "best_prompt": self.best_prompt[:500] if self.best_prompt else "",
            "best_response": self.best_response[:500] if self.best_response else "",
            "best_fitness": self.best_fitness,
            "generations": self.generations,
            "total_queries": self.total_queries,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "history_summary": self.history_summary[-10:],  # 最后10条
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskResult":
        """从字典创建"""
        return cls(
            task_id=data.get("task_id", ""),
            worker_id=data.get("worker_id", ""),
            success=data.get("success", False),
            goal=data.get("goal", ""),
            category=data.get("category", ""),
            best_prompt=data.get("best_prompt", ""),
            best_response=data.get("best_response", ""),
            best_fitness=data.get("best_fitness", 0.0),
            generations=data.get("generations", 0),
            total_queries=data.get("total_queries", 0),
            duration_seconds=data.get("duration_seconds", 0.0),
            started_at=data.get("started_at", 0.0),
            completed_at=data.get("completed_at", 0.0),
            history_summary=data.get("history_summary", []),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AggregatedReport:
    """聚合报告"""
    # 基本信息
    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # 任务统计
    total_tasks: int = 0
    completed_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0

    # 成功率
    success_rate: float = 0.0
    avg_fitness: float = 0.0
    max_fitness: float = 0.0

    # 资源统计
    total_queries: int = 0
    total_generations: int = 0
    total_duration_seconds: float = 0.0
    avg_duration_per_task: float = 0.0

    # 分类统计
    category_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Worker 统计
    worker_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # 结果列表
    results: List[TaskResult] = field(default_factory=list)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "report_id": self.report_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.success_rate,
            "avg_fitness": self.avg_fitness,
            "max_fitness": self.max_fitness,
            "total_queries": self.total_queries,
            "total_generations": self.total_generations,
            "total_duration_seconds": self.total_duration_seconds,
            "avg_duration_per_task": self.avg_duration_per_task,
            "category_stats": self.category_stats,
            "worker_stats": self.worker_stats,
            "results": [r.to_dict() for r in self.results],
            "metadata": self.metadata,
        }


class ResultAggregator:
    """
    分布式结果聚合器

    功能：
    - 收集来自多个 Worker 的测试结果
    - 实时计算统计信息
    - 生成聚合报告
    - 支持断点续传
    """

    def __init__(
        self,
        checkpoint_dir: str = "checkpoints/aggregator",
        checkpoint_interval: float = 60.0,
        max_results: int = 100000,
    ):
        """
        初始化结果聚合器

        Args:
            checkpoint_dir: 检查点保存目录
            checkpoint_interval: 检查点保存间隔（秒）
            max_results: 最大结果保存数量
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_interval = checkpoint_interval
        self.max_results = max_results

        # 结果存储
        self._results: Dict[str, TaskResult] = {}

        # 统计信息
        self._stats = {
            "total_received": 0,
            "total_successful": 0,
            "total_failed": 0,
        }

        # 分类统计
        self._category_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "success": 0, "fitness_sum": 0.0}
        )

        # Worker 统计
        self._worker_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "success": 0, "duration_sum": 0.0}
        )

        # 线程安全
        self._lock = asyncio.Lock()

        # 回调
        self._callbacks: List[Callable[[TaskResult], None]] = []

        # 检查点
        self._last_checkpoint_time = time.time()
        self._checkpoint_task: Optional[asyncio.Task] = None

    async def add_result(self, result: TaskResult) -> bool:
        """
        添加任务结果

        Args:
            result: 任务结果

        Returns:
            是否成功添加
        """
        async with self._lock:
            if len(self._results) >= self.max_results:
                # 移除最旧的结果
                oldest_id = min(self._results.keys(), key=lambda k: self._results[k].completed_at)
                del self._results[oldest_id]

            self._results[result.task_id] = result
            self._stats["total_received"] += 1

            if result.success:
                self._stats["total_successful"] += 1
            else:
                self._stats["total_failed"] += 1

            # 更新分类统计
            if result.category:
                cat_stats = self._category_stats[result.category]
                cat_stats["total"] += 1
                if result.success:
                    cat_stats["success"] += 1
                cat_stats["fitness_sum"] += result.best_fitness

            # 更新 Worker 统计
            if result.worker_id:
                worker_stats = self._worker_stats[result.worker_id]
                worker_stats["total"] += 1
                if result.success:
                    worker_stats["success"] += 1
                worker_stats["duration_sum"] += result.duration_seconds

        # 触发回调
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception:
                pass

        # 检查是否需要保存检查点
        if time.time() - self._last_checkpoint_time > self.checkpoint_interval:
            await self._save_checkpoint()

        return True

    async def add_results_batch(self, results: List[TaskResult]) -> int:
        """
        批量添加结果

        Args:
            results: 结果列表

        Returns:
            成功添加的数量
        """
        count = 0
        for result in results:
            if await self.add_result(result):
                count += 1
        return count

    async def get_result(self, task_id: str) -> Optional[TaskResult]:
        """获取单个结果"""
        async with self._lock:
            return self._results.get(task_id)

    async def get_all_results(self) -> List[TaskResult]:
        """获取所有结果"""
        async with self._lock:
            return list(self._results.values())

    async def get_results_by_category(self, category: str) -> List[TaskResult]:
        """按分类获取结果"""
        async with self._lock:
            return [r for r in self._results.values() if r.category == category]

    async def get_results_by_worker(self, worker_id: str) -> List[TaskResult]:
        """按 Worker 获取结果"""
        async with self._lock:
            return [r for r in self._results.values() if r.worker_id == worker_id]

    async def get_successful_results(self) -> List[TaskResult]:
        """获取成功的结果"""
        async with self._lock:
            return [r for r in self._results.values() if r.success]

    async def get_failed_results(self) -> List[TaskResult]:
        """获取失败的结果"""
        async with self._lock:
            return [r for r in self._results.values() if not r.success]

    async def get_statistics(self) -> Dict[str, Any]:
        """获取实时统计信息"""
        async with self._lock:
            total = len(self._results)
            if total == 0:
                return {
                    "total_results": 0,
                    "success_rate": 0.0,
                    "avg_fitness": 0.0,
                    "max_fitness": 0.0,
                    "total_queries": 0,
                    "total_generations": 0,
                    "total_duration": 0.0,
                }

            successful = [r for r in self._results.values() if r.success]
            all_results = list(self._results.values())

            fitness_values = [r.best_fitness for r in all_results if r.best_fitness > 0]
            avg_fitness = sum(fitness_values) / len(fitness_values) if fitness_values else 0.0
            max_fitness = max(fitness_values) if fitness_values else 0.0

            total_queries = sum(r.total_queries for r in all_results)
            total_generations = sum(r.generations for r in all_results)
            total_duration = sum(r.duration_seconds for r in all_results)

            return {
                "total_results": total,
                "successful_results": len(successful),
                "failed_results": total - len(successful),
                "success_rate": len(successful) / total,
                "avg_fitness": avg_fitness,
                "max_fitness": max_fitness,
                "total_queries": total_queries,
                "total_generations": total_generations,
                "total_duration": total_duration,
                "avg_duration_per_task": total_duration / total,
                "category_stats": dict(self._category_stats),
                "worker_stats": dict(self._worker_stats),
            }

    async def generate_report(self, title: str = "分布式测试报告") -> AggregatedReport:
        """
        生成聚合报告

        Args:
            title: 报告标题

        Returns:
            AggregatedReport 报告对象
        """
        stats = await self.get_statistics()
        results = await self.get_all_results()

        # 计算分类统计
        category_stats = {}
        for cat, cat_data in self._category_stats.items():
            if cat_data["total"] > 0:
                category_stats[cat] = {
                    "total": cat_data["total"],
                    "success": cat_data["success"],
                    "success_rate": cat_data["success"] / cat_data["total"],
                    "avg_fitness": cat_data["fitness_sum"] / cat_data["total"],
                }

        # 计算 Worker 统计
        worker_stats = {}
        for worker_id, worker_data in self._worker_stats.items():
            if worker_data["total"] > 0:
                worker_stats[worker_id] = {
                    "total": worker_data["total"],
                    "success": worker_data["success"],
                    "success_rate": worker_data["success"] / worker_data["total"],
                    "avg_duration": worker_data["duration_sum"] / worker_data["total"],
                }

        report = AggregatedReport(
            total_tasks=stats["total_results"],
            completed_tasks=stats["total_results"],
            successful_tasks=stats["successful_results"],
            failed_tasks=stats["failed_results"],
            success_rate=stats["success_rate"],
            avg_fitness=stats["avg_fitness"],
            max_fitness=stats["max_fitness"],
            total_queries=stats["total_queries"],
            total_generations=stats["total_generations"],
            total_duration_seconds=stats["total_duration"],
            avg_duration_per_task=stats["avg_duration_per_task"],
            category_stats=category_stats,
            worker_stats=worker_stats,
            results=results,
            metadata={"title": title},
        )

        return report

    async def export_json(self, filepath: str) -> bool:
        """
        导出 JSON 报告

        Args:
            filepath: 文件路径

        Returns:
            是否成功
        """
        try:
            report = await self.generate_report()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出 JSON 失败: {e}")
            return False

    async def export_html(self, filepath: str, title: str = "分布式测试报告") -> bool:
        """
        导出 HTML 报告

        Args:
            filepath: 文件路径
            title: 报告标题

        Returns:
            是否成功
        """
        try:
            report = await self.generate_report(title)

            html_content = self._generate_html_report(report, title)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            return True
        except Exception as e:
            print(f"导出 HTML 失败: {e}")
            return False

    def _generate_html_report(self, report: AggregatedReport, title: str) -> str:
        """生成 HTML 报告内容"""
        # 生成分类统计表格行
        category_rows = ""
        for cat, stats in report.category_stats.items():
            category_rows += f"""
            <tr>
                <td>{cat}</td>
                <td>{stats['total']}</td>
                <td>{stats['success']}</td>
                <td>{stats['success_rate']*100:.1f}%</td>
                <td>{stats['avg_fitness']:.4f}</td>
            </tr>
            """

        # 生成 Worker 统计表格行
        worker_rows = ""
        for worker_id, stats in report.worker_stats.items():
            worker_rows += f"""
            <tr>
                <td>{worker_id}</td>
                <td>{stats['total']}</td>
                <td>{stats['success']}</td>
                <td>{stats['success_rate']*100:.1f}%</td>
                <td>{stats['avg_duration']:.2f}s</td>
            </tr>
            """

        # 生成结果表格行（只显示前50条）
        result_rows = ""
        for result in report.results[:50]:
            status_class = "success" if result.success else "failure"
            status_text = "成功" if result.success else "失败"
            result_rows += f"""
            <tr class="{status_class}">
                <td>{result.task_id[:8]}</td>
                <td>{result.goal[:50]}...</td>
                <td>{result.category}</td>
                <td>{status_text}</td>
                <td>{result.best_fitness:.4f}</td>
                <td>{result.generations}</td>
                <td>{result.duration_seconds:.2f}s</td>
            </tr>
            """

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card.success {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .stat-card.warning {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f8f8;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        tr.success {{
            background: #e8f5e9;
        }}
        tr.failure {{
            background: #ffebee;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p class="timestamp">生成时间: {datetime.fromtimestamp(report.created_at).strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>总体统计</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{report.total_tasks}</div>
                <div class="stat-label">总任务数</div>
            </div>
            <div class="stat-card success">
                <div class="stat-value">{report.successful_tasks}</div>
                <div class="stat-label">成功任务</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-value">{report.failed_tasks}</div>
                <div class="stat-label">失败任务</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report.success_rate*100:.1f}%</div>
                <div class="stat-label">成功率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report.avg_fitness:.4f}</div>
                <div class="stat-label">平均适应度</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report.max_fitness:.4f}</div>
                <div class="stat-label">最高适应度</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report.total_queries}</div>
                <div class="stat-label">总查询数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report.total_duration_seconds:.1f}s</div>
                <div class="stat-label">总耗时</div>
            </div>
        </div>

        <h2>分类统计</h2>
        <table>
            <thead>
                <tr>
                    <th>分类</th>
                    <th>总数</th>
                    <th>成功</th>
                    <th>成功率</th>
                    <th>平均适应度</th>
                </tr>
            </thead>
            <tbody>
                {category_rows if category_rows else '<tr><td colspan="5">暂无数据</td></tr>'}
            </tbody>
        </table>

        <h2>Worker 统计</h2>
        <table>
            <thead>
                <tr>
                    <th>Worker ID</th>
                    <th>处理任务</th>
                    <th>成功</th>
                    <th>成功率</th>
                    <th>平均耗时</th>
                </tr>
            </thead>
            <tbody>
                {worker_rows if worker_rows else '<tr><td colspan="5">暂无数据</td></tr>'}
            </tbody>
        </table>

        <h2>任务详情 (前50条)</h2>
        <table>
            <thead>
                <tr>
                    <th>任务ID</th>
                    <th>目标</th>
                    <th>分类</th>
                    <th>状态</th>
                    <th>适应度</th>
                    <th>迭代</th>
                    <th>耗时</th>
                </tr>
            </thead>
            <tbody>
                {result_rows if result_rows else '<tr><td colspan="7">暂无数据</td></tr>'}
            </tbody>
        </table>
    </div>
</body>
</html>
        """

        return html

    async def _save_checkpoint(self) -> bool:
        """保存检查点"""
        try:
            checkpoint_data = {
                "timestamp": time.time(),
                "results": {k: v.to_dict() for k, v in self._results.items()},
                "stats": self._stats,
                "category_stats": dict(self._category_stats),
                "worker_stats": dict(self._worker_stats),
            }

            checkpoint_path = self.checkpoint_dir / f"aggregator_checkpoint.pkl"
            with open(checkpoint_path, "wb") as f:
                pickle.dump(checkpoint_data, f)

            self._last_checkpoint_time = time.time()
            return True
        except Exception as e:
            print(f"保存检查点失败: {e}")
            return False

    async def load_checkpoint(self) -> bool:
        """加载检查点"""
        checkpoint_path = self.checkpoint_dir / f"aggregator_checkpoint.pkl"
        if not checkpoint_path.exists():
            return False

        try:
            with open(checkpoint_path, "rb") as f:
                checkpoint_data = pickle.load(f)

            self._results = {
                k: TaskResult.from_dict(v)
                for k, v in checkpoint_data["results"].items()
            }
            self._stats = checkpoint_data["stats"]
            self._category_stats = defaultdict(
                lambda: {"total": 0, "success": 0, "fitness_sum": 0.0},
                checkpoint_data["category_stats"]
            )
            self._worker_stats = defaultdict(
                lambda: {"total": 0, "success": 0, "duration_sum": 0.0},
                checkpoint_data["worker_stats"]
            )

            print(f"已加载检查点，包含 {len(self._results)} 个结果")
            return True
        except Exception as e:
            print(f"加载检查点失败: {e}")
            return False

    def register_callback(self, callback: Callable[[TaskResult], None]):
        """注册结果回调函数"""
        self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[TaskResult], None]):
        """取消注册回调函数"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def clear(self):
        """清空所有结果"""
        async with self._lock:
            self._results.clear()
            self._stats = {
                "total_received": 0,
                "total_successful": 0,
                "total_failed": 0,
            }
            self._category_stats.clear()
            self._worker_stats.clear()

    async def merge_from(self, other: "ResultAggregator") -> int:
        """
        合并另一个聚合器的结果

        Args:
            other: 另一个结果聚合器

        Returns:
            合并的结果数量
        """
        other_results = await other.get_all_results()
        return await self.add_results_batch(other_results)
