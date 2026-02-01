# -*- coding: utf-8 -*-
"""
FORGEDAN 指标导出器

提供 HTTP 服务暴露 /metrics 端点，支持 Prometheus 抓取。
同时支持 Push Gateway 模式，适用于短期任务。

主要功能:
- HTTP 服务器暴露 /metrics 端点
- Push Gateway 客户端
- 自定义标签注入
- 多线程安全

使用示例:
    # 启动 HTTP 服务
    exporter = MetricsExporter(port=8000)
    exporter.start()

    # 推送到 Push Gateway
    push_client = PushGatewayClient(
        gateway_url="http://localhost:9091",
        job="forgedan"
    )
    push_client.push()
"""

import json
import time
import threading
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Optional, Any, Callable, List
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass, field
import logging

# HTTP 客户端
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .metrics import ForgeDanMetrics, metrics as global_metrics

logger = logging.getLogger(__name__)


@dataclass
class ExporterConfig:
    """导出器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    path: str = "/metrics"
    enable_json: bool = True  # 是否启用 /metrics/json 端点
    enable_health: bool = True  # 是否启用 /health 端点
    basic_auth: Optional[tuple] = None  # (username, password)
    extra_labels: Dict[str, str] = field(default_factory=dict)


class MetricsHTTPHandler(BaseHTTPRequestHandler):
    """Prometheus 指标 HTTP 处理器"""

    # 类变量，由 MetricsExporter 设置
    metrics_instance: ForgeDanMetrics = None
    extra_labels: Dict[str, str] = {}
    enable_json: bool = True
    enable_health: bool = True
    basic_auth: Optional[tuple] = None

    def log_message(self, format, *args):
        """覆盖日志方法，使用 logging"""
        logger.debug(f"{self.address_string()} - {format % args}")

    def _check_auth(self) -> bool:
        """检查基础认证"""
        if not self.basic_auth:
            return True

        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return False

        import base64
        try:
            credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = credentials.split(":", 1)
            return (username, password) == self.basic_auth
        except Exception:
            return False

    def _send_response(self, status: int, content: str, content_type: str = "text/plain"):
        """发送 HTTP 响应"""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # 健康检查端点 (无需认证)
        if path == "/health" and self.enable_health:
            self._handle_health()
            return

        # 认证检查
        if not self._check_auth():
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="Prometheus Metrics"')
            self.end_headers()
            return

        # Prometheus 文本格式端点
        if path == "/metrics":
            self._handle_metrics_text()
        # JSON 格式端点
        elif path == "/metrics/json" and self.enable_json:
            self._handle_metrics_json()
        # 摘要端点
        elif path == "/metrics/summary":
            self._handle_metrics_summary()
        else:
            self._send_response(404, "Not Found")

    def _handle_health(self):
        """处理健康检查"""
        health_data = {
            "status": "ok",
            "timestamp": time.time(),
            "service": "forgedan-metrics-exporter"
        }
        self._send_response(200, json.dumps(health_data), "application/json")

    def _handle_metrics_text(self):
        """处理 Prometheus 文本格式请求"""
        if self.metrics_instance is None:
            self._send_response(500, "Metrics not initialized")
            return

        try:
            content = self.metrics_instance.to_prometheus_format()

            # 添加额外标签的元数据
            if self.extra_labels:
                meta_lines = [
                    f"# LABELS {json.dumps(self.extra_labels)}"
                ]
                content = "\n".join(meta_lines) + "\n" + content

            self._send_response(
                200, content,
                "text/plain; version=0.0.4; charset=utf-8"
            )
        except Exception as e:
            logger.error(f"生成指标失败: {e}")
            self._send_response(500, f"Error: {str(e)}")

    def _handle_metrics_json(self):
        """处理 JSON 格式请求"""
        if self.metrics_instance is None:
            self._send_response(500, "Metrics not initialized")
            return

        try:
            data = self.metrics_instance.collect_all()

            # 添加额外标签
            if self.extra_labels:
                for item in data:
                    item["labels"] = {**self.extra_labels, **item.get("labels", {})}

            response = {
                "status": "ok",
                "timestamp": time.time(),
                "metrics": data
            }
            self._send_response(200, json.dumps(response, indent=2), "application/json")
        except Exception as e:
            logger.error(f"生成 JSON 指标失败: {e}")
            self._send_response(500, json.dumps({"error": str(e)}), "application/json")

    def _handle_metrics_summary(self):
        """处理摘要请求"""
        if self.metrics_instance is None:
            self._send_response(500, "Metrics not initialized")
            return

        try:
            summary = self.metrics_instance.get_summary()
            response = {
                "status": "ok",
                "timestamp": time.time(),
                "summary": summary,
                "labels": self.extra_labels
            }
            self._send_response(200, json.dumps(response, indent=2), "application/json")
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            self._send_response(500, json.dumps({"error": str(e)}), "application/json")


class MetricsExporter:
    """
    Prometheus 指标导出器

    启动 HTTP 服务器，暴露指标端点供 Prometheus 抓取。

    使用示例:
        exporter = MetricsExporter(port=8000)
        exporter.start()

        # 程序退出时
        exporter.stop()
    """

    def __init__(
        self,
        metrics_instance: ForgeDanMetrics = None,
        config: ExporterConfig = None,
        host: str = "0.0.0.0",
        port: int = 8000,
        extra_labels: Dict[str, str] = None,
        basic_auth: tuple = None
    ):
        """
        初始化导出器

        Args:
            metrics_instance: 指标实例 (默认使用全局实例)
            config: 配置对象 (优先级高于单独参数)
            host: 监听地址
            port: 监听端口
            extra_labels: 额外标签
            basic_auth: 基础认证 (username, password)
        """
        self.metrics = metrics_instance or global_metrics

        if config:
            self.config = config
        else:
            self.config = ExporterConfig(
                host=host,
                port=port,
                extra_labels=extra_labels or {},
                basic_auth=basic_auth
            )

        self.server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self, background: bool = True) -> None:
        """
        启动 HTTP 服务器

        Args:
            background: 是否在后台线程运行
        """
        if self._running:
            logger.warning("导出器已在运行")
            return

        # 配置处理器
        MetricsHTTPHandler.metrics_instance = self.metrics
        MetricsHTTPHandler.extra_labels = self.config.extra_labels
        MetricsHTTPHandler.enable_json = self.config.enable_json
        MetricsHTTPHandler.enable_health = self.config.enable_health
        MetricsHTTPHandler.basic_auth = self.config.basic_auth

        try:
            self.server = HTTPServer(
                (self.config.host, self.config.port),
                MetricsHTTPHandler
            )
            self._running = True

            logger.info(
                f"Prometheus 指标导出器启动: "
                f"http://{self.config.host}:{self.config.port}/metrics"
            )

            if background:
                self._thread = threading.Thread(
                    target=self.server.serve_forever,
                    daemon=True
                )
                self._thread.start()
            else:
                self.server.serve_forever()

        except Exception as e:
            logger.error(f"启动导出器失败: {e}")
            raise

    def stop(self) -> None:
        """停止 HTTP 服务器"""
        if not self._running:
            return

        self._running = False
        if self.server:
            self.server.shutdown()
            self.server = None
        logger.info("指标导出器已停止")

    def is_running(self) -> bool:
        """检查是否运行中"""
        return self._running

    def get_url(self) -> str:
        """获取指标端点 URL"""
        return f"http://{self.config.host}:{self.config.port}/metrics"


class PushGatewayClient:
    """
    Prometheus Push Gateway 客户端

    用于将指标推送到 Push Gateway，适用于批处理任务和短期运行的作业。

    使用示例:
        client = PushGatewayClient(
            gateway_url="http://localhost:9091",
            job="forgedan-batch"
        )
        client.push()  # 推送指标
        client.delete()  # 删除指标
    """

    def __init__(
        self,
        gateway_url: str,
        job: str,
        metrics_instance: ForgeDanMetrics = None,
        instance: str = None,
        grouping_key: Dict[str, str] = None,
        timeout: float = 10.0
    ):
        """
        初始化 Push Gateway 客户端

        Args:
            gateway_url: Push Gateway 地址
            job: 作业名称
            metrics_instance: 指标实例
            instance: 实例标识 (可选，默认使用主机名)
            grouping_key: 分组键
            timeout: 请求超时时间
        """
        if not HAS_REQUESTS:
            raise ImportError("需要安装 requests 库: pip install requests")

        self.gateway_url = gateway_url.rstrip("/")
        self.job = job
        self.metrics = metrics_instance or global_metrics
        self.instance = instance or socket.gethostname()
        self.grouping_key = grouping_key or {}
        self.timeout = timeout

    def _build_url(self) -> str:
        """构建推送 URL"""
        url = f"{self.gateway_url}/metrics/job/{self.job}"

        # 添加实例
        if self.instance:
            url += f"/instance/{self.instance}"

        # 添加分组键
        for key, value in self.grouping_key.items():
            url += f"/{key}/{value}"

        return url

    def push(self) -> bool:
        """
        推送指标到 Push Gateway

        Returns:
            是否成功
        """
        url = self._build_url()

        try:
            content = self.metrics.to_prometheus_format()
            response = requests.post(
                url,
                data=content.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                timeout=self.timeout
            )

            if response.status_code in (200, 202):
                logger.debug(f"指标推送成功: {url}")
                return True
            else:
                logger.error(
                    f"指标推送失败: {response.status_code} - {response.text}"
                )
                return False

        except requests.RequestException as e:
            logger.error(f"指标推送异常: {e}")
            return False

    def push_add(self) -> bool:
        """
        追加模式推送 (不覆盖现有指标)

        Returns:
            是否成功
        """
        url = self._build_url()

        try:
            content = self.metrics.to_prometheus_format()
            response = requests.put(
                url,
                data=content.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                timeout=self.timeout
            )

            if response.status_code in (200, 202):
                logger.debug(f"指标追加成功: {url}")
                return True
            else:
                logger.error(
                    f"指标追加失败: {response.status_code} - {response.text}"
                )
                return False

        except requests.RequestException as e:
            logger.error(f"指标追加异常: {e}")
            return False

    def delete(self) -> bool:
        """
        删除 Push Gateway 上的指标

        Returns:
            是否成功
        """
        url = self._build_url()

        try:
            response = requests.delete(url, timeout=self.timeout)

            if response.status_code in (200, 202, 204):
                logger.debug(f"指标删除成功: {url}")
                return True
            else:
                logger.error(
                    f"指标删除失败: {response.status_code} - {response.text}"
                )
                return False

        except requests.RequestException as e:
            logger.error(f"指标删除异常: {e}")
            return False


class PeriodicPusher:
    """
    定期推送器

    定期将指标推送到 Push Gateway。

    使用示例:
        pusher = PeriodicPusher(
            client=push_client,
            interval=15  # 每15秒推送一次
        )
        pusher.start()
    """

    def __init__(
        self,
        client: PushGatewayClient,
        interval: float = 15.0
    ):
        """
        初始化定期推送器

        Args:
            client: Push Gateway 客户端
            interval: 推送间隔 (秒)
        """
        self.client = client
        self.interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """启动定期推送"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._push_loop, daemon=True)
        self._thread.start()
        logger.info(f"定期推送器启动，间隔: {self.interval}秒")

    def stop(self) -> None:
        """停止定期推送"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.interval + 1)
        logger.info("定期推送器已停止")

    def _push_loop(self) -> None:
        """推送循环"""
        while self._running:
            try:
                self.client.push()
            except Exception as e:
                logger.error(f"定期推送失败: {e}")

            # 分段睡眠，以便快速响应停止请求
            for _ in range(int(self.interval * 10)):
                if not self._running:
                    break
                time.sleep(0.1)


def create_exporter(
    port: int = 8000,
    push_gateway: str = None,
    job: str = "forgedan",
    extra_labels: Dict[str, str] = None
) -> tuple:
    """
    创建导出器的便捷函数

    Args:
        port: HTTP 服务端口
        push_gateway: Push Gateway 地址 (可选)
        job: 作业名称
        extra_labels: 额外标签

    Returns:
        (exporter, push_client) 元组
    """
    exporter = MetricsExporter(
        port=port,
        extra_labels=extra_labels or {}
    )

    push_client = None
    if push_gateway:
        push_client = PushGatewayClient(
            gateway_url=push_gateway,
            job=job
        )

    return exporter, push_client
