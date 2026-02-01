#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FORGEDAN 分布式协调器启动脚本

启动方式：
    python -m forgedan.distributed.start_coordinator
    python -m forgedan.distributed.start_coordinator --port 8765
    python -m forgedan.distributed.start_coordinator --redis redis://localhost:6379
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="FORGEDAN 分布式协调器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 使用默认配置启动
    python -m forgedan.distributed.start_coordinator

    # 指定端口
    python -m forgedan.distributed.start_coordinator --port 8765

    # 使用 Redis 队列
    python -m forgedan.distributed.start_coordinator --redis redis://localhost:6379

    # 启用认证
    python -m forgedan.distributed.start_coordinator --token my-secret-token
        """
    )

    # 服务器配置
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="监听地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="监听端口 (默认: 8765)"
    )

    # 队列配置
    parser.add_argument(
        "--redis",
        type=str,
        default=None,
        help="Redis URL (例: redis://localhost:6379/0)"
    )
    parser.add_argument(
        "--queue-size",
        type=int,
        default=10000,
        help="最大队列容量 (默认: 10000)"
    )

    # 认证配置
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="认证令牌"
    )
    parser.add_argument(
        "--enable-auth",
        action="store_true",
        help="启用认证"
    )

    # 负载均衡
    parser.add_argument(
        "--lb-strategy",
        type=str,
        choices=["round_robin", "least_loaded", "random", "weighted"],
        default="least_loaded",
        help="负载均衡策略 (默认: least_loaded)"
    )

    # Worker 管理
    parser.add_argument(
        "--max-workers",
        type=int,
        default=100,
        help="最大 Worker 数量 (默认: 100)"
    )
    parser.add_argument(
        "--worker-timeout",
        type=float,
        default=60.0,
        help="Worker 超时时间(秒) (默认: 60)"
    )

    # 检查点
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default="checkpoints/distributed",
        help="检查点保存目录"
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=float,
        default=60.0,
        help="检查点保存间隔(秒) (默认: 60)"
    )

    # 其他
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 配置日志
    import logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 创建配置
    from forgedan.distributed.config import (
        CoordinatorConfig,
        QueueConfig,
        QueueBackend,
        LoadBalanceStrategy,
    )

    # 队列配置
    queue_config = QueueConfig(
        backend=QueueBackend.REDIS if args.redis else QueueBackend.MEMORY,
        max_queue_size=args.queue_size,
    )

    if args.redis:
        # 解析 Redis URL
        from urllib.parse import urlparse
        parsed = urlparse(args.redis)
        queue_config.redis_host = parsed.hostname or "localhost"
        queue_config.redis_port = parsed.port or 6379
        queue_config.redis_password = parsed.password
        queue_config.redis_db = int(parsed.path.lstrip("/") or 0)

    # 协调器配置
    coordinator_config = CoordinatorConfig(
        host=args.host,
        port=args.port,
        enable_auth=args.enable_auth or bool(args.token),
        auth_token=args.token,
        load_balance_strategy=LoadBalanceStrategy(args.lb_strategy),
        max_workers=args.max_workers,
        worker_timeout=args.worker_timeout,
        checkpoint_dir=args.checkpoint_dir,
        checkpoint_interval=args.checkpoint_interval,
    )

    # 打印启动信息
    print("=" * 60)
    print("FORGEDAN 分布式协调器")
    print("=" * 60)
    print(f"监听地址: {args.host}:{args.port}")
    print(f"队列后端: {'Redis' if args.redis else 'Memory'}")
    if args.redis:
        print(f"Redis URL: {args.redis}")
    print(f"负载均衡: {args.lb_strategy}")
    print(f"最大 Worker: {args.max_workers}")
    print(f"认证: {'启用' if coordinator_config.enable_auth else '禁用'}")
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    print()

    # 启动协调器
    from forgedan.distributed.coordinator import run_coordinator

    try:
        asyncio.run(run_coordinator(coordinator_config, queue_config))
    except KeyboardInterrupt:
        print("\n收到中断信号，正在退出...")


if __name__ == "__main__":
    main()
