# -*- coding: utf-8 -*-
"""
FORGEDAN 包初始化

ForgeDAN - LLM 安全评估框架
包含文本攻击、多模态攻击、防御训练等模块
"""

from importlib import import_module

from .config import ForgeDanConfig
from .engine import ForgeDAN_Engine, EvolutionResult, Candidate
from .mutator import Mutator, MutationStrategy
from .fitness import SemanticFitness, SimpleFitness
from .judge import DualJudge
from .attack_logger import AttackLogger, AttackRecord
from .visualizer import Visualizer

_LAZY_SUBMODULES = {"defense", "multimodal", "webscan"}
_OPTIONAL_EXTRA_HINTS = {
    "webscan": "pip install 'forgedan[web]'",
}


def __getattr__(name: str):
    """按需加载扩展模块，避免核心导入被可选依赖阻塞。"""
    if name not in _LAZY_SUBMODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    try:
        module = import_module(f"{__name__}.{name}")
    except ModuleNotFoundError as exc:
        hint = _OPTIONAL_EXTRA_HINTS.get(name)
        if hint and exc.name and not exc.name.startswith(__name__):
            raise ModuleNotFoundError(
                f"Optional module 'forgedan.{name}' requires additional dependencies. "
                f"Install them with: {hint}"
            ) from exc
        raise

    globals()[name] = module
    return module


__version__ = "1.2.0"
__all__ = [
    # 配置
    "ForgeDanConfig",
    # 引擎
    "ForgeDAN_Engine",
    "EvolutionResult",
    "Candidate",
    # 变异
    "Mutator",
    "MutationStrategy",
    # 适应度
    "SemanticFitness",
    "SimpleFitness",
    # 判断器
    "DualJudge",
    # 日志
    "AttackLogger",
    "AttackRecord",
    # 可视化
    "Visualizer",
    # Defense
    "defense",
    # Multimodal
    "multimodal",
    # WebScan
    "webscan",
]
