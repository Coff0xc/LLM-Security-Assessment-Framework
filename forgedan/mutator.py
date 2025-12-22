# -*- coding: utf-8 -*-
"""
FORGEDAN 变异模块
对应论文 Section IV-C 和 Table I: 多策略层次化变异

实现三个层次的变异策略:
- Character-Level: 同形字替换、邻位交换、插入/删除字符
- Word-Level: 同义词替换、形态变化
- Sentence-Level: 句式重构、语序调整
"""

import random
import string
from abc import ABC, abstractmethod
from typing import List

from .config import HOMOGLYPH_MAP, SYNONYM_DICT


class MutationStrategy(ABC):
    """变异策略基类 (插件化架构)"""

    @abstractmethod
    def mutate(self, text: str) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


# ============== Character-Level Mutations ==============

class HomoglyphSubstitution(MutationStrategy):
    """同形字替换: 用视觉相似字符替换 (e.g., 'o'->'0')"""

    @property
    def name(self) -> str:
        return "homoglyph_substitution"

    def mutate(self, text: str) -> str:
        chars = list(text)
        for i, c in enumerate(chars):
            if c.lower() in HOMOGLYPH_MAP and random.random() < 0.2:
                chars[i] = random.choice(HOMOGLYPH_MAP[c.lower()])
        return ''.join(chars)


class NeighborSwap(MutationStrategy):
    """邻位交换: 交换相邻字符位置"""

    @property
    def name(self) -> str:
        return "neighbor_swap"

    def mutate(self, text: str) -> str:
        if len(text) < 2:
            return text
        chars = list(text)
        idx = random.randint(0, len(chars) - 2)
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
        return ''.join(chars)


class InsertChar(MutationStrategy):
    """插入字符: 随机位置插入字符"""

    @property
    def name(self) -> str:
        return "insert_char"

    def mutate(self, text: str) -> str:
        if not text:
            return text
        idx = random.randint(0, len(text))
        char = random.choice(string.ascii_lowercase + ' ')
        return text[:idx] + char + text[idx:]


class DeleteChar(MutationStrategy):
    """删除字符: 随机删除一个字符"""

    @property
    def name(self) -> str:
        return "delete_char"

    def mutate(self, text: str) -> str:
        if len(text) <= 1:
            return text
        idx = random.randint(0, len(text) - 1)
        return text[:idx] + text[idx + 1:]


# ============== Word-Level Mutations ==============

class SynonymReplacement(MutationStrategy):
    """同义词替换: 用同义词替换关键词"""

    @property
    def name(self) -> str:
        return "synonym_replacement"

    def mutate(self, text: str) -> str:
        words = text.split()
        for i, word in enumerate(words):
            word_lower = word.lower().strip('.,!?')
            if word_lower in SYNONYM_DICT and random.random() < 0.3:
                replacement = random.choice(SYNONYM_DICT[word_lower])
                # 保持原始大小写
                if word[0].isupper():
                    replacement = replacement.capitalize()
                words[i] = replacement
        return ' '.join(words)


class MorphologicalChange(MutationStrategy):
    """形态变化: 改变词的形态 (时态、单复数等)"""

    @property
    def name(self) -> str:
        return "morphological_change"

    def mutate(self, text: str) -> str:
        # 简单的形态变化规则
        replacements = [
            ("ing ", "tion "), ("tion ", "ing "),
            ("ed ", "ing "), ("s ", " "),
            ("ly ", " "), (" is ", " was "),
        ]
        for old, new in replacements:
            if old in text.lower() and random.random() < 0.2:
                text = text.replace(old, new, 1)
                break
        return text


# ============== Sentence-Level Mutations ==============

class Restructuring(MutationStrategy):
    """句式重构: 改变句子结构 (e.g., "How to X" -> "The process of X is...")"""

    @property
    def name(self) -> str:
        return "restructuring"

    def mutate(self, text: str) -> str:
        patterns = [
            ("How to ", "The process of "),
            ("How do I ", "The method for "),
            ("Can you ", "I need you to "),
            ("Tell me ", "Explain "),
            ("What is ", "Describe "),
            ("Write ", "Compose "),
        ]
        for old, new in patterns:
            if text.lower().startswith(old.lower()):
                return new + text[len(old):]
        return text


class Reordering(MutationStrategy):
    """语序调整: 调整句子中子句的顺序"""

    @property
    def name(self) -> str:
        return "reordering"

    def mutate(self, text: str) -> str:
        # 按逗号或句号分割，然后重排
        if ',' in text:
            parts = text.split(',')
            if len(parts) >= 2:
                random.shuffle(parts)
                return ','.join(parts)
        return text


class Mutator:
    """
    变异器主类 (对应论文 Section IV-C)

    采用插件化架构，支持扩展新的变异策略。
    mutate() 函数随机选择一种策略应用于输入文本。
    """

    def __init__(self):
        # 注册所有变异策略
        self.strategies: List[MutationStrategy] = [
            # Character-Level
            HomoglyphSubstitution(),
            NeighborSwap(),
            InsertChar(),
            DeleteChar(),
            # Word-Level
            SynonymReplacement(),
            MorphologicalChange(),
            # Sentence-Level
            Restructuring(),
            Reordering(),
        ]

    def mutate(self, text: str, num_mutations: int = 1) -> str:
        """
        对输入文本应用随机变异

        Args:
            text: 输入文本
            num_mutations: 应用的变异次数

        Returns:
            变异后的文本
        """
        result = text
        for _ in range(num_mutations):
            strategy = random.choice(self.strategies)
            result = strategy.mutate(result)
        return result

    def mutate_with_strategy(self, text: str, strategy_name: str) -> str:
        """使用指定策略进行变异"""
        for strategy in self.strategies:
            if strategy.name == strategy_name:
                return strategy.mutate(text)
        raise ValueError(f"未知策略: {strategy_name}")

    def get_strategy_names(self) -> List[str]:
        """获取所有可用策略名称"""
        return [s.name for s in self.strategies]
