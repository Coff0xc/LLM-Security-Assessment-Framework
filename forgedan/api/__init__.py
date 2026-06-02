# -*- coding: utf-8 -*-
"""
FORGEDAN API Blueprint 模块

将 Web API 端点拆分为独立的 Blueprint 模块，实现模块化架构。
"""

from flask import Flask
from typing import Optional, Dict, Any


def create_api_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    API 应用工厂函数

    创建 Flask 应用并注册所有 API Blueprint。

    Args:
        config: 可选的配置字典

    Returns:
        配置完成的 Flask 应用实例
    """
    import os
    from pathlib import Path

    package_dir = Path(__file__).parent.parent.parent.absolute()

    app = Flask(__name__)

    # 默认配置
    default_log_dir = package_dir / "logs" / "attacks"
    default_report_dir = package_dir / "reports"

    # 安全生成 SECRET_KEY
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        import secrets

        secret_key = secrets.token_hex(32)

    app.config.update(
        SECRET_KEY=secret_key,
        LOG_DIR=os.environ.get("LOG_DIR", str(default_log_dir)),
        REPORT_DIR=os.environ.get("REPORT_DIR", str(default_report_dir)),
        PROJECT_ROOT=str(package_dir),
        FORGEDAN_API_KEY=os.environ.get("FORGEDAN_API_KEY", ""),
        CORS_ALLOWED_ORIGINS=os.environ.get(
            "CORS_ALLOWED_ORIGINS", "http://localhost:5173"
        ),
    )

    if config:
        app.config.update(config)

    # 确保目录存在
    try:
        Path(app.config["LOG_DIR"]).mkdir(parents=True, exist_ok=True)
        Path(app.config["REPORT_DIR"]).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        import tempfile

        temp_dir = Path(tempfile.gettempdir()) / "forgedan"
        app.config["LOG_DIR"] = str(temp_dir / "logs")
        app.config["REPORT_DIR"] = str(temp_dir / "reports")
        Path(app.config["LOG_DIR"]).mkdir(parents=True, exist_ok=True)
        Path(app.config["REPORT_DIR"]).mkdir(parents=True, exist_ok=True)

    # 初始化共享组件 (存储在 app.extensions 中供 Blueprint 使用)
    from forgedan.web.app import TaskManager, ResponseCache, PerformanceMonitor

    app.extensions["task_manager"] = TaskManager(
        max_tasks=100, cleanup_interval=300, task_ttl=3600
    )
    app.extensions["response_cache"] = ResponseCache(max_size=200, default_ttl=60)
    app.extensions["perf_monitor"] = PerformanceMonitor()

    # 注册 Blueprint
    from .attacks import attacks_bp
    from .models import models_bp
    from .reports import reports_bp
    from .datasets import datasets_bp
    from .webscan import webscan_bp
    from .monitoring import monitoring_bp

    app.register_blueprint(attacks_bp)
    app.register_blueprint(models_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(datasets_bp)
    app.register_blueprint(webscan_bp)
    app.register_blueprint(monitoring_bp)

    # 请求钩子
    import time
    from flask import g

    @app.before_request
    def before_request():
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            app.extensions["perf_monitor"].record_request(duration)
        return response

    return app
