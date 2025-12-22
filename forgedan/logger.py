# -*- coding: utf-8 -*-
"""
统一日志系统
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "forgedan",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """配置日志记录器"""

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    # 默认格式
    if format_string is None:
        format_string = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"

    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 全局日志实例
logger = setup_logger()
