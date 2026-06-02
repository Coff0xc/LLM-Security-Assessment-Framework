#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FORGEDAN 分布式工作节点启动脚本

启动方式：
    python -m forgedan.distributed.start_worker
    python -m forgedan.distributed.start_worker --coordinator http://localhost:8765
    python -m forgedan.distributed.start_worker --workers 4  # 多进程模式
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
        description="FORGEDAN 分布式工作节点",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 启动单个 Worker
    python -m forgedan.distributed.start_worker

    # 指定协调器地址
    python -m forgedan.distributed.start_worker --coordinator http://10.0.0.1:8765

    # 启动多进程 Worker
    python -m forgedan.distributed.start_worker --workers 4

    # 使用自定义名称和标签
    python -m forgedan.distributed.start_worker --name gpu-worker-1 --tags gpu,fast
        """,
    )

    # 协调器配置
    parser.add_argument(
        "--coordinator",
        type=str,
        default="http://localhost:8765",
        help="协调器 URL (默认: http://localhost:8765)",
    )
    parser.add_argument("--token", type=str, default=None, help="认证令牌")

    # Worker 标识
    parser.add_argument("--name", type=str, default=None, help="Worker 名称")
    parser.add_argument(
        "--id", type=str, default=None, help="Worker ID (默认: 自动生成)"
    )
    parser.add_argument(
        "--tags", type=str, default="", help="Worker 标签，逗号分隔 (例: gpu,fast,prod)"
    )

    # 性能配置
    parser.add_argument(
        "--concurrent", type=int, default=4, help="最大并发任务数 (默认: 4)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="多进程模式的进程数 (0=单进程, >0=多进程)",
    )

    # 心跳配置
    parser.add_argument(
        "--heartbeat-interval", type=float, default=10.0, help="心跳间隔(秒) (默认: 10)"
    )

    # 优雅退出
    parser.add_argument(
        "--shutdown-timeout",
        type=float,
        default=60.0,
        help="优雅退出超时(秒) (默认: 60)",
    )

    # 模型配置
    parser.add_argument(
        "--model", type=str, default="mock:test", help="使用的模型 (默认: mock:test)"
    )
    parser.add_argument("--api-key", type=str, default=None, help="API 密钥")

    # 其他
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)",
    )

    return parser.parse_args()


def create_engine_factory(model: str, api_key: str = None):
    """
    创建引擎工厂函数

    Args:
        model: 模型标识 (如 openai:gpt-3.5-turbo)
        api_key: API 密钥

    Returns:
        引擎工厂函数
    """

    def factory():
        from forgedan import ForgeDAN_Engine, ForgeDanConfig
        from forgedan.adapters import ModelAdapterFactory

        config = ForgeDanConfig()
        engine = ForgeDAN_Engine(config=config, enable_logging=False)

        if model.startswith("mock:"):
            # Mock 模式
            import random

            def mock_llm(prompt: str) -> str:
                if random.random() < 0.7:
                    return "I cannot help with that request."
                return f"Sure, here is how to {prompt[:30]}..."

            engine.set_target_llm(mock_llm, model_name=model)
        else:
            # 真实 API
            if not api_key:
                raise ValueError("需要提供 API 密钥")

            adapter = ModelAdapterFactory.create_from_string(model, api_key=api_key)

            async def async_llm(prompt: str) -> str:
                async with adapter:
                    response = await adapter.generate(prompt)
                    return response.content

            def sync_llm(prompt: str) -> str:
                import asyncio

                return asyncio.run(async_llm(prompt))

            engine.set_target_llm(sync_llm, model_name=model)

        return engine

    return factory


def main():
    """主函数"""
    args = parse_args()

    # 配置日志
    import logging

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 创建配置
    from forgedan.distributed.config import WorkerConfig

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    worker_config = WorkerConfig(
        worker_id=args.id,
        worker_name=args.name,
        coordinator_url=args.coordinator,
        coordinator_token=args.token,
        max_concurrent_tasks=args.concurrent,
        heartbeat_interval=args.heartbeat_interval,
        graceful_shutdown_timeout=args.shutdown_timeout,
        worker_tags=tags,
    )

    # 打印启动信息
    print("=" * 60)
    print("FORGEDAN 分布式工作节点")
    print("=" * 60)
    print(f"协调器: {args.coordinator}")
    print(f"模式: {'多进程' if args.workers > 0 else '单进程'}")
    if args.workers > 0:
        print(f"进程数: {args.workers}")
    print(f"最大并发: {args.concurrent}")
    print(f"模型: {args.model}")
    if args.name:
        print(f"名称: {args.name}")
    if tags:
        print(f"标签: {', '.join(tags)}")
    print("=" * 60)
    print("按 Ctrl+C 停止 Worker")
    print()

    if args.workers > 0:
        # 多进程模式
        from forgedan.distributed.worker import MultiProcessWorker

        mp_worker = MultiProcessWorker(
            coordinator_url=args.coordinator,
            num_workers=args.workers,
            worker_config=worker_config,
        )

        try:
            mp_worker.start()

            # 保持运行
            import time

            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n收到中断信号，正在停止所有 Worker...")
            mp_worker.stop()

    else:
        # 单进程模式
        from forgedan.distributed.worker import run_worker

        try:
            asyncio.run(run_worker(config=worker_config))
        except KeyboardInterrupt:
            print("\n收到中断信号，正在退出...")


if __name__ == "__main__":
    main()
