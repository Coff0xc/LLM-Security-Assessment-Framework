# -*- coding: utf-8 -*-
"""
攻击方法模块

提供多种 LLM 越狱攻击算法实现。
"""

from .base import BaseAttack, AttackResult
from .forgedan import ForgeDanAttack
from .pair import PAIRAttack
from .gcg import GCGAttack

__all__ = [
    'BaseAttack',
    'AttackResult',
    'ForgeDanAttack',
    'PAIRAttack',
    'GCGAttack',
]
