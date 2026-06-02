# -*- coding: utf-8 -*-
"""
FORGEDAN 告警规则

定义告警规则和告警管理器，支持基于指标的条件告警。

支持功能:
- 阈值告警
- 变化率告警
- 状态持续时间告警
- 多条件组合告警
- 告警分级 (critical, warning, info)
- 告警通知 (回调函数)

使用示例:
    manager = AlertManager()

    # 添加规则: 成功率低于 10% 时告警
    manager.add_rule(AlertRule(
        name="low_success_rate",
        condition=lambda m: m.get_success_rate() < 0.1,
        severity=AlertSeverity.WARNING,
        message="攻击成功率低于 10%"
    ))

    # 检查告警
    alerts = manager.check()
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .metrics import ForgeDanMetrics, metrics as global_metrics

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """告警严重级别"""

    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    CRITICAL = "critical"  # 严重


class AlertState(Enum):
    """告警状态"""

    OK = "ok"  # 正常
    PENDING = "pending"  # 待确认
    FIRING = "firing"  # 触发中
    RESOLVED = "resolved"  # 已解决


@dataclass
class AlertRule:
    """
    告警规则

    定义何时触发告警的条件。
    """

    name: str  # 规则名称
    condition: Callable[[ForgeDanMetrics], bool]  # 条件函数
    severity: AlertSeverity = AlertSeverity.WARNING  # 严重级别
    message: str = ""  # 告警消息模板
    labels: Dict[str, str] = field(default_factory=dict)  # 标签
    for_duration: float = 0.0  # 持续多久才触发 (秒)
    repeat_interval: float = 300.0  # 重复告警间隔 (秒)
    annotations: Dict[str, str] = field(default_factory=dict)  # 注释

    def __post_init__(self):
        if not self.message:
            self.message = f"告警: {self.name}"


@dataclass
class Alert:
    """
    告警实例

    表示一个触发的告警。
    """

    rule_name: str
    severity: AlertSeverity
    state: AlertState
    message: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    starts_at: float
    ends_at: Optional[float] = None
    fired_at: Optional[float] = None
    value: Any = None
    fingerprint: str = ""

    def __post_init__(self):
        if not self.fingerprint:
            # 基于规则名和标签生成指纹
            label_str = ",".join(f"{k}={v}" for k, v in sorted(self.labels.items()))
            self.fingerprint = f"{self.rule_name}:{label_str}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "state": self.state.value,
            "message": self.message,
            "labels": self.labels,
            "annotations": self.annotations,
            "starts_at": datetime.fromtimestamp(self.starts_at).isoformat(),
            "ends_at": (
                datetime.fromtimestamp(self.ends_at).isoformat()
                if self.ends_at
                else None
            ),
            "fired_at": (
                datetime.fromtimestamp(self.fired_at).isoformat()
                if self.fired_at
                else None
            ),
            "value": self.value,
            "fingerprint": self.fingerprint,
        }


class AlertManager:
    """
    告警管理器

    管理告警规则，检查告警条件，发送告警通知。

    使用示例:
        manager = AlertManager()
        manager.add_rule(rule)
        manager.add_callback(lambda alert: print(alert))
        manager.start_checking()
    """

    def __init__(
        self, metrics_instance: ForgeDanMetrics = None, check_interval: float = 15.0
    ):
        """
        初始化告警管理器

        Args:
            metrics_instance: 指标实例
            check_interval: 检查间隔 (秒)
        """
        self.metrics = metrics_instance or global_metrics
        self.check_interval = check_interval

        self._rules: Dict[str, AlertRule] = {}
        self._alerts: Dict[str, Alert] = {}
        self._pending_starts: Dict[str, float] = {}  # 待确认的告警开始时间
        self._last_fired: Dict[str, float] = {}  # 上次触发时间
        self._callbacks: List[Callable[[Alert], None]] = []
        self._inhibit_rules: List[Callable[[Alert], bool]] = []

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def add_rule(self, rule: AlertRule) -> None:
        """
        添加告警规则

        Args:
            rule: 告警规则
        """
        with self._lock:
            self._rules[rule.name] = rule
            logger.debug(f"添加告警规则: {rule.name}")

    def remove_rule(self, name: str) -> bool:
        """
        移除告警规则

        Args:
            name: 规则名称

        Returns:
            是否成功
        """
        with self._lock:
            if name in self._rules:
                del self._rules[name]
                # 同时移除相关的告警
                to_remove = [
                    fp for fp, alert in self._alerts.items() if alert.rule_name == name
                ]
                for fp in to_remove:
                    del self._alerts[fp]
                logger.debug(f"移除告警规则: {name}")
                return True
            return False

    def add_callback(self, callback: Callable[[Alert], None]) -> None:
        """
        添加告警回调

        Args:
            callback: 回调函数，接收 Alert 参数
        """
        self._callbacks.append(callback)

    def add_inhibit_rule(self, inhibit_func: Callable[[Alert], bool]) -> None:
        """
        添加抑制规则

        Args:
            inhibit_func: 抑制函数，返回 True 表示抑制该告警
        """
        self._inhibit_rules.append(inhibit_func)

    def check(self) -> List[Alert]:
        """
        检查所有规则

        Returns:
            触发的告警列表
        """
        now = time.time()
        fired_alerts = []

        with self._lock:
            rules = list(self._rules.values())

        for rule in rules:
            try:
                condition_met = rule.condition(self.metrics)
            except Exception as e:
                logger.error(f"检查规则 {rule.name} 失败: {e}")
                continue

            fingerprint = rule.name  # 简化版，实际应包含标签

            if condition_met:
                # 条件满足
                if fingerprint not in self._pending_starts:
                    # 开始计时
                    self._pending_starts[fingerprint] = now

                pending_duration = now - self._pending_starts[fingerprint]

                if pending_duration >= rule.for_duration:
                    # 达到持续时间要求
                    with self._lock:
                        existing_alert = self._alerts.get(fingerprint)

                        if existing_alert:
                            # 已存在的告警
                            if existing_alert.state == AlertState.RESOLVED:
                                # 重新触发
                                existing_alert.state = AlertState.FIRING
                                existing_alert.starts_at = now
                                existing_alert.fired_at = now
                                existing_alert.ends_at = None
                                fired_alerts.append(existing_alert)
                            elif existing_alert.state == AlertState.FIRING:
                                # 检查是否需要重复通知
                                last_fire = self._last_fired.get(fingerprint, 0)
                                if now - last_fire >= rule.repeat_interval:
                                    fired_alerts.append(existing_alert)
                        else:
                            # 新告警
                            alert = Alert(
                                rule_name=rule.name,
                                severity=rule.severity,
                                state=AlertState.FIRING,
                                message=rule.message,
                                labels=rule.labels.copy(),
                                annotations=rule.annotations.copy(),
                                starts_at=self._pending_starts[fingerprint],
                                fired_at=now,
                                fingerprint=fingerprint,
                            )
                            self._alerts[fingerprint] = alert
                            fired_alerts.append(alert)

                        self._last_fired[fingerprint] = now
            else:
                # 条件不满足
                self._pending_starts.pop(fingerprint, None)

                with self._lock:
                    existing_alert = self._alerts.get(fingerprint)
                    if existing_alert and existing_alert.state == AlertState.FIRING:
                        # 告警解决
                        existing_alert.state = AlertState.RESOLVED
                        existing_alert.ends_at = now
                        # 发送解决通知
                        fired_alerts.append(existing_alert)

        # 触发回调
        for alert in fired_alerts:
            # 检查抑制
            inhibited = any(inhibit(alert) for inhibit in self._inhibit_rules)
            if inhibited:
                logger.debug(f"告警被抑制: {alert.fingerprint}")
                continue

            for callback in self._callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"告警回调失败: {e}")

        return fired_alerts

    def get_active_alerts(self) -> List[Alert]:
        """获取所有活跃告警"""
        with self._lock:
            return [
                alert
                for alert in self._alerts.values()
                if alert.state == AlertState.FIRING
            ]

    def get_all_alerts(self) -> List[Alert]:
        """获取所有告警 (包括已解决)"""
        with self._lock:
            return list(self._alerts.values())

    def silence(self, fingerprint: str, duration: float = 3600.0) -> bool:
        """
        静默指定告警

        Args:
            fingerprint: 告警指纹
            duration: 静默时长 (秒)

        Returns:
            是否成功
        """
        # 简化实现：添加临时抑制规则
        end_time = time.time() + duration

        def silence_rule(alert: Alert) -> bool:
            if alert.fingerprint == fingerprint and time.time() < end_time:
                return True
            return False

        self.add_inhibit_rule(silence_rule)
        logger.info(f"告警已静默: {fingerprint}, 时长: {duration}秒")
        return True

    def start_checking(self, background: bool = True) -> None:
        """
        启动定期检查

        Args:
            background: 是否在后台运行
        """
        if self._running:
            logger.warning("告警检查已在运行")
            return

        self._running = True

        if background:
            self._thread = threading.Thread(target=self._check_loop, daemon=True)
            self._thread.start()
            logger.info(f"告警检查已启动，间隔: {self.check_interval}秒")
        else:
            self._check_loop()

    def stop_checking(self) -> None:
        """停止定期检查"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.check_interval + 1)
        logger.info("告警检查已停止")

    def _check_loop(self) -> None:
        """检查循环"""
        while self._running:
            try:
                self.check()
            except Exception as e:
                logger.error(f"告警检查失败: {e}")

            # 分段睡眠
            for _ in range(int(self.check_interval * 10)):
                if not self._running:
                    break
                time.sleep(0.1)

    def get_status(self) -> Dict[str, Any]:
        """获取告警管理器状态"""
        with self._lock:
            firing = sum(
                1 for a in self._alerts.values() if a.state == AlertState.FIRING
            )
            resolved = sum(
                1 for a in self._alerts.values() if a.state == AlertState.RESOLVED
            )

            return {
                "running": self._running,
                "rules_count": len(self._rules),
                "alerts_total": len(self._alerts),
                "alerts_firing": firing,
                "alerts_resolved": resolved,
                "callbacks_count": len(self._callbacks),
            }


# ============== 预定义告警规则 ==============


def create_default_rules(metrics_instance: ForgeDanMetrics = None) -> List[AlertRule]:
    """
    创建默认告警规则

    Args:
        metrics_instance: 指标实例

    Returns:
        规则列表
    """
    rules = [
        # 高错误率告警
        AlertRule(
            name="high_query_error_rate",
            condition=lambda m: _calc_error_rate(m) > 0.1,
            severity=AlertSeverity.WARNING,
            message="LLM 查询错误率超过 10%",
            for_duration=60.0,
            annotations={"description": "最近一段时间的 LLM 查询错误率过高"},
        ),
        # 内存使用告警
        AlertRule(
            name="high_memory_usage",
            condition=lambda m: m.memory_usage.get(type="resident")
            > 2 * 1024 * 1024 * 1024,  # 2GB
            severity=AlertSeverity.WARNING,
            message="内存使用超过 2GB",
            for_duration=120.0,
            annotations={"description": "进程内存使用量过高，可能需要释放缓存"},
        ),
        # 长时间无进展告警
        AlertRule(
            name="no_fitness_improvement",
            condition=lambda m: _check_fitness_stagnation(m),
            severity=AlertSeverity.INFO,
            message="适应度长时间无改进",
            for_duration=300.0,
            annotations={"description": "进化算法可能陷入局部最优"},
        ),
        # 无活跃任务告警 (如果服务应该持续运行)
        # AlertRule(
        #     name="no_active_tasks",
        #     condition=lambda m: m.active_tasks.get(task_type="evolution") == 0,
        #     severity=AlertSeverity.INFO,
        #     message="当前无活跃任务",
        #     for_duration=1800.0,  # 30分钟
        # ),
        # 缓存命中率低告警
        AlertRule(
            name="low_cache_hit_rate",
            condition=lambda m: _calc_cache_hit_rate(m) < 0.3,
            severity=AlertSeverity.INFO,
            message="缓存命中率低于 30%",
            for_duration=300.0,
            annotations={"description": "缓存效率较低，可能需要调整缓存策略"},
        ),
    ]

    return rules


def _calc_error_rate(metrics: ForgeDanMetrics) -> float:
    """计算错误率"""
    success = 0
    error = 0
    for model in ["gpt-4", "gpt-3.5-turbo", "claude-3", "unknown"]:
        success += metrics.queries_total.get(model=model, status="success")
        error += metrics.queries_total.get(model=model, status="error")

    total = success + error
    if total == 0:
        return 0.0
    return error / total


def _check_fitness_stagnation(metrics: ForgeDanMetrics) -> bool:
    """检查适应度是否停滞"""
    # 简化实现：检查最近的适应度值
    # 实际应该检查历史趋势
    fitness = metrics.fitness_score.get(task_id="default", model="unknown")
    return 0 < fitness < 0.5  # 低适应度且未成功


def _calc_cache_hit_rate(metrics: ForgeDanMetrics) -> float:
    """计算缓存命中率"""
    hits = metrics.cache_hits.get(cache_type="response")
    misses = metrics.cache_misses.get(cache_type="response")
    total = hits + misses
    if total == 0:
        return 1.0  # 无访问时返回 100%
    return hits / total


def create_alert_manager_with_defaults(
    metrics_instance: ForgeDanMetrics = None,
) -> AlertManager:
    """
    创建带默认规则的告警管理器

    Args:
        metrics_instance: 指标实例

    Returns:
        配置好的告警管理器
    """
    manager = AlertManager(metrics_instance=metrics_instance)

    # 添加默认规则
    for rule in create_default_rules(metrics_instance):
        manager.add_rule(rule)

    # 添加日志回调
    def log_alert(alert: Alert):
        if alert.state == AlertState.FIRING:
            logger.warning(
                f"[ALERT] {alert.severity.value.upper()}: {alert.message} "
                f"(rule: {alert.rule_name})"
            )
        elif alert.state == AlertState.RESOLVED:
            logger.info(f"[RESOLVED] {alert.rule_name}: {alert.message}")

    manager.add_callback(log_alert)

    return manager
