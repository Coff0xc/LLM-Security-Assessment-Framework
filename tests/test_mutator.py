# -*- coding: utf-8 -*-
"""
变异器模块单元测试
"""

import pytest
from forgedan.mutator import (
    Mutator,
    HomoglyphSubstitution,
    NeighborSwap,
    InsertChar,
    DeleteChar,
    SynonymReplacement,
    MorphologicalChange,
    Restructuring,
    Reordering,
)


class TestHomoglyphSubstitution:
    """同形字替换测试"""

    def test_basic_substitution(self):
        """测试基本替换"""
        strategy = HomoglyphSubstitution()
        text = "hello world"
        result = strategy.mutate(text)
        # 结果可能相同或不同（随机性）
        assert isinstance(result, str)
        assert len(result) == len(text)

    def test_empty_string(self):
        """测试空字符串"""
        strategy = HomoglyphSubstitution()
        assert strategy.mutate("") == ""

    def test_name_property(self):
        """测试策略名称"""
        strategy = HomoglyphSubstitution()
        assert strategy.name == "homoglyph_substitution"


class TestNeighborSwap:
    """邻位交换测试"""

    def test_basic_swap(self):
        """测试基本交换"""
        strategy = NeighborSwap()
        text = "abcd"
        result = strategy.mutate(text)
        assert len(result) == len(text)
        # 验证只有一对相邻字符交换
        diff_count = sum(1 for a, b in zip(text, result) if a != b)
        assert diff_count <= 2

    def test_short_string(self):
        """测试短字符串"""
        strategy = NeighborSwap()
        assert strategy.mutate("a") == "a"
        assert strategy.mutate("") == ""

    def test_name_property(self):
        """测试策略名称"""
        strategy = NeighborSwap()
        assert strategy.name == "neighbor_swap"


class TestInsertChar:
    """插入字符测试"""

    def test_basic_insert(self):
        """测试基本插入"""
        strategy = InsertChar()
        text = "hello"
        result = strategy.mutate(text)
        assert len(result) == len(text) + 1

    def test_empty_string(self):
        """测试空字符串"""
        strategy = InsertChar()
        assert strategy.mutate("") == ""

    def test_name_property(self):
        """测试策略名称"""
        strategy = InsertChar()
        assert strategy.name == "insert_char"


class TestDeleteChar:
    """删除字符测试"""

    def test_basic_delete(self):
        """测试基本删除"""
        strategy = DeleteChar()
        text = "hello"
        result = strategy.mutate(text)
        assert len(result) == len(text) - 1

    def test_short_string(self):
        """测试短字符串"""
        strategy = DeleteChar()
        assert strategy.mutate("a") == "a"
        assert strategy.mutate("") == ""

    def test_name_property(self):
        """测试策略名称"""
        strategy = DeleteChar()
        assert strategy.name == "delete_char"


class TestSynonymReplacement:
    """同义词替换测试"""

    def test_basic_replacement(self):
        """测试基本替换"""
        strategy = SynonymReplacement()
        text = "create a document"
        result = strategy.mutate(text)
        assert isinstance(result, str)

    def test_no_synonyms(self):
        """测试无同义词情况"""
        strategy = SynonymReplacement()
        text = "xyz abc"
        result = strategy.mutate(text)
        assert isinstance(result, str)

    def test_name_property(self):
        """测试策略名称"""
        strategy = SynonymReplacement()
        assert strategy.name == "synonym_replacement"


class TestMorphologicalChange:
    """形态变化测试"""

    def test_basic_change(self):
        """测试基本变化"""
        strategy = MorphologicalChange()
        text = "running fast"
        result = strategy.mutate(text)
        assert isinstance(result, str)

    def test_name_property(self):
        """测试策略名称"""
        strategy = MorphologicalChange()
        assert strategy.name == "morphological_change"


class TestRestructuring:
    """句式重构测试"""

    def test_how_to_pattern(self):
        """测试 How to 模式"""
        strategy = Restructuring()
        text = "How to make a cake"
        result = strategy.mutate(text)
        assert result.startswith("The process of")

    def test_can_you_pattern(self):
        """测试 Can you 模式"""
        strategy = Restructuring()
        text = "Can you help me"
        result = strategy.mutate(text)
        assert result.startswith("I need you to")

    def test_no_match(self):
        """测试无匹配模式"""
        strategy = Restructuring()
        text = "Random text here"
        result = strategy.mutate(text)
        assert result == text

    def test_name_property(self):
        """测试策略名称"""
        strategy = Restructuring()
        assert strategy.name == "restructuring"


class TestReordering:
    """语序调整测试"""

    def test_basic_reorder(self):
        """测试基本重排"""
        strategy = Reordering()
        text = "first part, second part, third part"
        result = strategy.mutate(text)
        assert isinstance(result, str)
        # 包含相同的部分
        assert "part" in result

    def test_no_comma(self):
        """测试无逗号情况"""
        strategy = Reordering()
        text = "no comma here"
        result = strategy.mutate(text)
        assert result == text

    def test_name_property(self):
        """测试策略名称"""
        strategy = Reordering()
        assert strategy.name == "reordering"


class TestMutator:
    """变异器主类测试"""

    def test_initialization(self):
        """测试初始化"""
        mutator = Mutator()
        assert len(mutator.strategies) == 8

    def test_mutate_single(self):
        """测试单次变异"""
        mutator = Mutator()
        text = "hello world"
        result = mutator.mutate(text, num_mutations=1)
        assert isinstance(result, str)

    def test_mutate_multiple(self):
        """测试多次变异"""
        mutator = Mutator()
        text = "hello world"
        result = mutator.mutate(text, num_mutations=3)
        assert isinstance(result, str)

    def test_get_strategy_names(self):
        """测试获取策略名称"""
        mutator = Mutator()
        names = mutator.get_strategy_names()
        assert len(names) == 8
        assert "homoglyph_substitution" in names
        assert "synonym_replacement" in names

    def test_mutate_with_strategy(self):
        """测试指定策略变异"""
        mutator = Mutator()
        text = "How to do something"
        result = mutator.mutate_with_strategy(text, "restructuring")
        assert result.startswith("The process of")

    def test_mutate_with_unknown_strategy(self):
        """测试未知策略"""
        mutator = Mutator()
        with pytest.raises(ValueError):
            mutator.mutate_with_strategy("text", "unknown_strategy")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
