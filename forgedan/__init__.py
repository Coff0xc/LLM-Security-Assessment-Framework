# -*- coding: utf-8 -*-
"""
FORGEDAN 包初始化

ForgeDAN - LLM 安全评估框架
包含文本攻击、多模态攻击、防御训练等模块
"""

from .config import ForgeDanConfig
from .engine import ForgeDAN_Engine, EvolutionResult, Candidate
from .mutator import Mutator, MutationStrategy
from .fitness import SemanticFitness, SimpleFitness
from .judge import DualJudge
from .attack_logger import AttackLogger, AttackRecord
from .visualizer import Visualizer

# Defense 模块 (对抗训练数据生成)
from . import defense

# Multimodal 模块 (多模态攻击)
from . import multimodal

# WebScan 模块 (网站安全测试)
from . import webscan

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
