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

__all__ = [
    # 基类
    'BaseAttack',
    'AttackResult',
    'AttackConfig',
    # ForgeDAN
    'ForgeDanAttack',
    'ForgeDanConfig',
    # PAIR
    'PAIRAttack',
    'PAIRConfig',
    # GCG
    'GCGAttack',
    'GCGConfig',
    # AutoDAN
    'AutoDANAttack',
    'AutoDANConfig',
    # TAP
    'TAPAttack',
    'TAPConfig',
    # Crescendo
    'CrescendoAttack',
    'CrescendoConfig',
]


# 攻击方法注册表，便于动态选择
ATTACK_REGISTRY = {
    'forgedan': ForgeDanAttack,
    'pair': PAIRAttack,
    'gcg': GCGAttack,
    'autodan': AutoDANAttack,
    'tap': TAPAttack,
    'crescendo': CrescendoAttack,
}


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
    name_lower = name.lower()
    if name_lower not in ATTACK_REGISTRY:
        available = ', '.join(ATTACK_REGISTRY.keys())
        raise ValueError(f"未知的攻击方法: {name}. 可用的方法: {available}")
    return ATTACK_REGISTRY[name_lower]


def list_attacks() -> list:
    """
    列出所有可用的攻击方法

    Returns:
        攻击方法信息列表
    """
    attacks = []
    for name, cls in ATTACK_REGISTRY.items():
        attacks.append({
            'name': name,
            'class': cls.__name__,
            'description': cls.description if hasattr(cls, 'description') else ''
        })
    return attacks
