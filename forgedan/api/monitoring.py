# -*- coding: utf-8 -*-
"""
监控 API Blueprint

提供系统指标和健康检查端点。
"""

from datetime import datetime
from flask import Blueprint, jsonify, current_app

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')


def _get_task_manager():
    return current_app.extensions['task_manager']


def _get_cache():
    return current_app.extensions['response_cache']


def _get_perf_monitor():
    return current_app.extensions['perf_monitor']


@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    monitoring_available = False
    try:
        from forgedan.monitoring import metrics as global_metrics
        monitoring_available = global_metrics is not None
    except ImportError:
        pass

    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.2.0',
        'monitoring_enabled': monitoring_available,
    })


@monitoring_bp.route('/metrics', methods=['GET'])
def system_metrics():
    """系统指标"""
    task_manager = _get_task_manager()
    cache = _get_cache()
    perf = _get_perf_monitor()

    result = {
        'timestamp': datetime.now().isoformat(),
        'tasks': task_manager.get_stats(),
        'cache': cache.get_stats(),
        'performance': perf.get_stats(),
    }

    # 尝试添加 Prometheus 指标
    try:
        from forgedan.monitoring import metrics as global_metrics
        if global_metrics:
            attacks_total = sum(global_metrics.attacks_total._values.values())
            attacks_success = sum(global_metrics.attacks_success._values.values())
            queries_total = sum(global_metrics.queries_total._values.values())
            active_tasks = sum(global_metrics.active_tasks._values.values())
            fitness_score = max(global_metrics.fitness_score._values.values()) if global_metrics.fitness_score._values else 0

            result['prometheus'] = {
                'attacks_total': attacks_total,
                'attacks_success': attacks_success,
                'queries_total': queries_total,
                'active_tasks': active_tasks,
                'fitness_score': fitness_score,
            }
    except (ImportError, AttributeError):
        pass

    return jsonify(result)
