# -*- coding: utf-8 -*-
"""
攻击方法注册表

提供攻击方法的注册、查询和列举功能。
"""

from typing import Dict, Type, List, Any, Optional

ATTACK_REGISTRY: Dict[str, Type] = {}


def register_attack(name: str, cls: Type) -> None:
    """
    注册攻击方法

    Args:
        name: 攻击方法名称（小写）
        cls: 攻击类
    """
    ATTACK_REGISTRY[name.lower()] = cls


def get_attack(name: str) -> Optional[Type]:
    """
    根据名称获取攻击类

    Args:
        name: 攻击方法名称（不区分大小写）

    Returns:
        对应的攻击类，未找到返回 None
    """
    return ATTACK_REGISTRY.get(name.lower())


def list_attacks() -> List[Dict[str, Any]]:
    """
    列出所有已注册的攻击方法

    Returns:
        攻击方法信息列表
    """
    result = []
    for name, cls in ATTACK_REGISTRY.items():
        info = (
            cls.get_info_static()
            if hasattr(cls, "get_info_static")
            else {
                "name": getattr(cls, "name", name),
                "description": getattr(cls, "description", ""),
            }
        )
        result.append(
            {
                "name": name,
                "info": info,
            }
        )
    return result
