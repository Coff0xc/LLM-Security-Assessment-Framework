# -*- coding: utf-8 -*-
"""
FORGEDAN 适应度评估模块
对应论文 Section IV-D: 语义适应度测量

核心思想: 使用语义嵌入相似度而非关键词匹配来评估响应质量
公式: fitness = cosine_similarity(embed(response), embed(target_output))
"""

import numpy as np
from typing import Optional

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class SemanticFitness:
    """
    语义适应度评估器 (对应论文 Section IV-D)

    使用 sentence-transformers 计算模型响应与目标输出之间的语义相似度。
    避免使用简单的关键词匹配，提高评估的鲁棒性。
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化适应度评估器

        Args:
            model_name: sentence-transformers 模型名称
                       推荐: all-MiniLM-L6-v2 (快速) 或 all-roberta-large-v1 (精确)
        """
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> "SentenceTransformer":
        """延迟加载模型"""
        if self._model is None:
            if not HAS_SENTENCE_TRANSFORMERS:
                raise ImportError(
                    "需要安装 sentence-transformers: pip install sentence-transformers"
                )
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))

    def calculate(self, response: str, target_output: str) -> float:
        """
        计算适应度分数 (对应论文公式)

        Args:
            response: 模型的实际响应
            target_output: 期望的目标输出 (e.g., "Sure, here is how to...")

        Returns:
            适应度分数 [0, 1]，越高表示响应越接近目标
        """
        if not response or not target_output:
            return 0.0

        # 编码文本为向量
        embeddings = self.model.encode([response, target_output])
        response_vec = embeddings[0]
        target_vec = embeddings[1]

        # 计算余弦相似度
        similarity = self._cosine_similarity(response_vec, target_vec)

        # 归一化到 [0, 1]
        return max(0.0, min(1.0, (similarity + 1) / 2))

    def batch_calculate(
        self, responses: list, target_output: str
    ) -> list:
        """
        批量计算适应度分数

        Args:
            responses: 响应列表
            target_output: 目标输出

        Returns:
            适应度分数列表
        """
        if not responses:
            return []

        # 批量编码
        all_texts = responses + [target_output]
        embeddings = self.model.encode(all_texts)

        target_vec = embeddings[-1]
        scores = []

        for i in range(len(responses)):
            similarity = self._cosine_similarity(embeddings[i], target_vec)
            score = max(0.0, min(1.0, (similarity + 1) / 2))
            scores.append(score)

        return scores


class SimpleFitness:
    """
    简化版适应度评估器 (不依赖外部模型)

    当无法使用 sentence-transformers 时的备选方案。
    使用 n-gram 重叠度作为相似度度量。
    """

    def __init__(self, n: int = 3):
        self.n = n

    def _get_ngrams(self, text: str) -> set:
        """提取 n-gram"""
        text = text.lower()
        return set(text[i:i+self.n] for i in range(len(text) - self.n + 1))

    def calculate(self, response: str, target_output: str) -> float:
        """计算 n-gram 重叠度"""
        if not response or not target_output:
            return 0.0

        ngrams1 = self._get_ngrams(response)
        ngrams2 = self._get_ngrams(target_output)

        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)

        return intersection / union if union > 0 else 0.0
