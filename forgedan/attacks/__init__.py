# -*- coding: utf-8 -*-
"""
攻击方法模块

提供多种 LLM 越狱攻击算法实现。

已实现的攻击方法：
- ForgeDanAttack: 基于遗传算法的进化攻击
- PAIRAttack: 对话式自动迭代攻击
- GCGAttack: 梯度引导的对抗攻击
- AutoDANAttack: 层级遗传算法的隐蔽攻击
- TAPAttack: 树状搜索的自动化攻击
- CrescendoAttack: 多轮对话渐进式攻击
"""

from .base import BaseAttack, AttackResult, AttackConfig
from .forgedan import ForgeDanAttack, ForgeDanConfig
from .pair import PAIRAttack, PAIRConfig
from .gcg import GCGAttack, GCGConfig
from .autodan import AutoDANAttack, AutoDANConfig
from .tap import TAPAttack, TAPConfig
from .crescendo import CrescendoAttack, CrescendoConfig
from .registry import ATTACK_REGISTRY, register_attack, get_attack, list_attacks

# 注册所有攻击方法
register_attack("forgedan", ForgeDanAttack)
register_attack("autodan", AutoDANAttack)
register_attack("pair", PAIRAttack)
register_attack("gcg", GCGAttack)
register_attack("crescendo", CrescendoAttack)
register_attack("tap", TAPAttack)

__all__ = [
    # 基类
    "BaseAttack",
    "AttackResult",
    "AttackConfig",
    # ForgeDAN
    "ForgeDanAttack",
    "ForgeDanConfig",
    # PAIR
    "PAIRAttack",
    "PAIRConfig",
    # GCG
    "GCGAttack",
    "GCGConfig",
    # AutoDAN
    "AutoDANAttack",
    "AutoDANConfig",
    # TAP
    "TAPAttack",
    "TAPConfig",
    # Crescendo
    "CrescendoAttack",
    "CrescendoConfig",
    # 注册表
    "ATTACK_REGISTRY",
    "register_attack",
    "get_attack",
    "list_attacks",
]


def get_attack_class(name: str) -> type:
    """
    根据名称获取攻击类

    Args:
        name: 攻击方法名称（不区分大小写）

    Returns:
        对应的攻击类

    Raises:
        ValueError: 如果名称未知
    """
    cls = get_attack(name)
    if cls is None:
        available = ", ".join(ATTACK_REGISTRY.keys())
        raise ValueError(f"未知的攻击方法: {name}. 可用的方法: {available}")
    return cls
