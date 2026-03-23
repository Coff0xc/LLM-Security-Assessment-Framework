# -*- coding: utf-8 -*-
"""
适应度评估模块单元测试
"""

import pytest
from forgedan.fitness import SimpleFitness


class TestSimpleFitness:
    """简化版适应度评估器测试"""

    def setup_method(self):
        """每个测试前初始化"""
        self.fitness = SimpleFitness(n=3)

    def test_initialization(self):
        """测试初始化"""
        fitness = SimpleFitness(n=2)
        assert fitness.n == 2

    def test_calculate_identical(self):
        """测试相同文本"""
        result = self.fitness.calculate("hello world", "hello world")
        assert result.score == 1.0

    def test_calculate_different(self):
        """测试完全不同文本"""
        result = self.fitness.calculate("abcdefg", "xyz123")
        assert 0.0 <= result.score <= 1.0

    def test_calculate_partial_overlap(self):
        """测试部分重叠"""
        result = self.fitness.calculate("hello world", "hello there")
        assert 0.0 < result.score < 1.0

    def test_calculate_empty_response(self):
        """测试空响应"""
        result = self.fitness.calculate("", "target")
        assert result.score == 0.0

    def test_calculate_empty_target(self):
        """测试空目标"""
        result = self.fitness.calculate("response", "")
        assert result.score == 0.0

    def test_calculate_both_empty(self):
        """测试都为空"""
        result = self.fitness.calculate("", "")
        assert result.score == 0.0

    def test_calculate_short_text(self):
        """测试短文本"""
        fitness = SimpleFitness(n=3)
        result = fitness.calculate("ab", "xy")
        assert result.score == 0.0  # 不同的短文本无重叠

    def test_get_ngrams(self):
        """测试n-gram提取"""
        ngrams = self.fitness._get_ngrams("hello")
        assert "hel" in ngrams
        assert "ell" in ngrams
        assert "llo" in ngrams

    def test_calculate_case_insensitive(self):
        """测试大小写不敏感"""
        result1 = self.fitness.calculate("HELLO", "hello")
        result2 = self.fitness.calculate("hello", "hello")
        assert result1.score == result2.score


# 仅在安装了 sentence-transformers 时运行
try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False


@pytest.mark.skipif(not HAS_ST, reason="sentence-transformers not installed")
class TestSemanticFitness:
    """语义适应度评估器测试（需要 sentence-transformers）"""

    def test_initialization(self):
        """测试初始化"""
        from forgedan.fitness import SemanticFitness
        fitness = SemanticFitness()
        assert fitness.model_name == "all-MiniLM-L6-v2"

    def test_calculate_similar(self):
        """测试相似文本"""
        from forgedan.fitness import SemanticFitness
        fitness = SemanticFitness()
        result = fitness.calculate("I love programming", "I enjoy coding")
        assert result.score > 0.5

    def test_calculate_different(self):
        """测试不同文本"""
        from forgedan.fitness import SemanticFitness
        fitness = SemanticFitness()
        result = fitness.calculate("Hello world", "The weather is nice today")
        assert 0.0 <= result.score <= 1.0

    def test_batch_calculate(self):
        """测试批量计算"""
        from forgedan.fitness import SemanticFitness
        fitness = SemanticFitness()
        responses = ["I love coding", "Programming is fun", "Random text"]
        target = "I enjoy programming"
        scores = fitness.batch_calculate(responses, target)
        assert len(scores) == 3
        assert all(0.0 <= s <= 1.0 for s in scores)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
