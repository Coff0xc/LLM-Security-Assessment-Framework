# -*- coding: utf-8 -*-
"""
FORGEDAN 监控模块

提供 Prometheus 指标导出、数据收集和告警功能。
支持实时监控 LLM 安全评估任务的各项指标。

主要组件:
- metrics: Prometheus 指标定义
- exporter: 指标导出器 (HTTP 服务 + Push Gateway)
- collectors: 数据收集器 (引擎、适配器、系统资源)
- alerts: 告警规则定义

使用示例:
    from forgedan.monitoring import MetricsExporter, ForgeDanMetrics

    # 启动指标导出服务
    exporter = MetricsExporter(port=8000)
    exporter.start()

    # 记录指标
    from forgedan.monitoring.metrics import metrics
    metrics.record_attack(success=True, model="gpt-4", attack_type="jailbreak")
"""

from .metrics import ForgeDanMetrics, metrics
from .exporter import MetricsExporter, PushGatewayClient
from .collectors import (
    EngineCollector,
    AdapterCollector,
    SystemCollector,
    CollectorRegistry
)
from .alerts import AlertRule, AlertManager, AlertSeverity

__all__ = [
    # 指标
    "ForgeDanMetrics",
    "metrics",
    # 导出器
    "MetricsExporter",
    "PushGatewayClient",
    # 收集器
    "EngineCollector",
    "AdapterCollector",
    "SystemCollector",
    "CollectorRegistry",
    # 告警
    "AlertRule",
    "AlertManager",
    "AlertSeverity",
]

__version__ = "1.0.0"
