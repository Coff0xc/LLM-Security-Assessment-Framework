# -*- coding: utf-8 -*-
"""
FORGEDAN 包初始化
"""

from .config import ForgeDanConfig
from .engine import ForgeDAN_Engine, EvolutionResult, Candidate
from .mutator import Mutator, MutationStrategy
from .fitness import SemanticFitness, SimpleFitness
from .judge import DualJudge
from .attack_logger import AttackLogger, AttackRecord
from .visualizer import Visualizer

__version__ = "1.1.0"
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
]
