# -*- coding: utf-8 -*-
"""
FORGEDAN 适应度评估模块 (增强版)
对应论文 Section IV-D: 语义适应度测量

核心思想: 使用语义嵌入相似度而非关键词匹配来评估响应质量
公式: fitness = cosine_similarity(embed(response), embed(target_output))

增强功能:
- GPU加速: 自动检测并使用CUDA/MPS
- 批量处理: 支持动态批大小和分块处理
- 嵌入缓存: 避免重复计算
- 异步支持: async/await接口
- 多模型支持: 模型热切换和集成
"""

import os
import hashlib
import asyncio
import time
import threading
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import numpy as np

# 设置 HuggingFace 离线模式（如果本地有缓存则优先使用）
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

try:
    from sentence_transformers import SentenceTransformer

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    import torch

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@dataclass
class FitnessResult:
    """适应度计算结果"""

    score: float
    similarity: float
    cached: bool = False
    latency_ms: float = 0.0
    model_name: str = ""
    device: str = "cpu"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "similarity": self.similarity,
            "cached": self.cached,
            "latency_ms": self.latency_ms,
            "model_name": self.model_name,
            "device": self.device,
        }


@dataclass
class FitnessStats:
    """适应度计算统计"""

    total_calculations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_latency_ms: float = 0.0
    batch_count: int = 0
    total_items: int = 0

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return (
            self.total_latency_ms / self.total_calculations
            if self.total_calculations > 0
            else 0.0
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_calculations": self.total_calculations,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hit_rate,
            "total_latency_ms": self.total_latency_ms,
            "avg_latency_ms": self.avg_latency_ms,
            "batch_count": self.batch_count,
            "total_items": self.total_items,
        }


class EmbeddingCache:
    """嵌入向量缓存"""

    def __init__(self, maxsize: int = 5000, ttl_seconds: float = 7200):
        """
        初始化缓存

        Args:
            maxsize: 最大缓存条目数
            ttl_seconds: 缓存TTL (秒)
        """
        self.maxsize = maxsize
        self.ttl = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _compute_key(self, text: str, model_name: str) -> str:
        """计算缓存键"""
        content = f"{model_name}|||{text}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def get(self, text: str, model_name: str) -> Optional[np.ndarray]:
        """获取缓存的嵌入"""
        key = self._compute_key(text, model_name)
        with self._lock:
            if key not in self._cache:
                return None

            # 检查TTL
            if time.time() - self._timestamps[key] > self.ttl:
                del self._cache[key]
                del self._timestamps[key]
                return None

            self._cache.move_to_end(key)
            return self._cache[key]

    def get_batch(
        self, texts: List[str], model_name: str
    ) -> Tuple[List[Optional[np.ndarray]], List[int]]:
        """
        批量获取缓存

        Returns:
            (embeddings, miss_indices) - 嵌入列表和未命中的索引
        """
        embeddings = []
        miss_indices = []

        for i, text in enumerate(texts):
            emb = self.get(text, model_name)
            embeddings.append(emb)
            if emb is None:
                miss_indices.append(i)

        return embeddings, miss_indices

    def set(self, text: str, model_name: str, embedding: np.ndarray) -> None:
        """设置缓存"""
        key = self._compute_key(text, model_name)
        with self._lock:
            while len(self._cache) >= self.maxsize:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                del self._timestamps[oldest_key]

            self._cache[key] = embedding.copy()  # 存储副本
            self._timestamps[key] = time.time()

    def set_batch(
        self, texts: List[str], model_name: str, embeddings: List[np.ndarray]
    ) -> None:
        """批量设置缓存"""
        for text, emb in zip(texts, embeddings):
            self.set(text, model_name, emb)

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


def get_best_device() -> str:
    """自动检测最佳计算设备"""
    if not HAS_TORCH:
        return "cpu"

    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


class SemanticFitness:
    """
    语义适应度评估器 (增强版)

    使用 sentence-transformers 计算模型响应与目标输出之间的语义相似度。

    增强功能:
    - GPU加速: 自动检测CUDA/MPS
    - 嵌入缓存: 避免重复计算
    - 批量处理: 高效的批量编码
    - 目标预计算: 对固定目标预计算嵌入
    - 异步支持: async/await接口
    """

    # 推荐模型列表
    RECOMMENDED_MODELS = {
        "fast": "all-MiniLM-L6-v2",  # 快速，适合大规模测试
        "balanced": "all-mpnet-base-v2",  # 平衡速度和精度
        "accurate": "all-roberta-large-v1",  # 最准确，但较慢
        "multilingual": "paraphrase-multilingual-MiniLM-L12-v2",  # 多语言
    }

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "auto",
        cache_maxsize: int = 5000,
        cache_ttl: float = 7200,
        batch_size: int = 32,
    ):
        """
        初始化适应度评估器

        Args:
            model_name: sentence-transformers 模型名称
            device: 计算设备 ('auto', 'cuda', 'mps', 'cpu')
            cache_maxsize: 嵌入缓存最大大小
            cache_ttl: 缓存TTL (秒)
            batch_size: 批量编码大小
        """
        self.model_name = model_name
        self.device = get_best_device() if device == "auto" else device
        self.batch_size = batch_size

        self._model: Optional[SentenceTransformer] = None
        self._load_failed = False
        self._cache = EmbeddingCache(maxsize=cache_maxsize, ttl_seconds=cache_ttl)
        self._target_cache: Dict[str, np.ndarray] = {}  # 预计算的目标嵌入
        self._stats = FitnessStats()
        self._stats_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=2)

    @property
    def model(self) -> "SentenceTransformer":
        """延迟加载模型"""
        if self._model is None and not self._load_failed:
            if not HAS_SENTENCE_TRANSFORMERS:
                raise ImportError(
                    "需要安装 sentence-transformers: pip install sentence-transformers"
                )
            try:
                # 优先尝试离线加载
                self._model = SentenceTransformer(
                    self.model_name, local_files_only=True
                )
            except Exception:
                try:
                    os.environ["HF_HUB_OFFLINE"] = "0"
                    self._model = SentenceTransformer(self.model_name)
                except Exception as e:
                    self._load_failed = True
                    raise RuntimeError(f"无法加载模型 {self.model_name}: {e}")

            # 移动到指定设备
            if self.device != "cpu" and HAS_TORCH:
                try:
                    self._model = self._model.to(self.device)
                except Exception:
                    self.device = "cpu"  # 回退到CPU

        if self._model is None:
            raise RuntimeError(f"模型 {self.model_name} 加载失败")
        return self._model

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))

    def _cosine_similarity_batch(
        self, vectors: np.ndarray, target_vec: np.ndarray
    ) -> np.ndarray:
        """批量计算余弦相似度"""
        # vectors: (N, D), target_vec: (D,)
        dot_products = np.dot(vectors, target_vec)
        norms = np.linalg.norm(vectors, axis=1)
        target_norm = np.linalg.norm(target_vec)

        if target_norm == 0:
            return np.zeros(len(vectors))

        # 避免除零
        norms = np.where(norms == 0, 1e-10, norms)
        return dot_products / (norms * target_norm)

    def _encode_with_cache(self, texts: List[str]) -> np.ndarray:
        """带缓存的编码"""
        # 检查缓存
        cached_embeddings, miss_indices = self._cache.get_batch(texts, self.model_name)

        with self._stats_lock:
            self._stats.cache_hits += len(texts) - len(miss_indices)
            self._stats.cache_misses += len(miss_indices)

        if not miss_indices:
            # 全部命中缓存
            return np.array(cached_embeddings)

        # 编码未命中的文本
        texts_to_encode = [texts[i] for i in miss_indices]
        new_embeddings = self.model.encode(
            texts_to_encode,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        # 存入缓存
        self._cache.set_batch(texts_to_encode, self.model_name, list(new_embeddings))

        # 合并结果
        result = []
        new_idx = 0
        for i, cached in enumerate(cached_embeddings):
            if cached is not None:
                result.append(cached)
            else:
                result.append(new_embeddings[new_idx])
                new_idx += 1

        return np.array(result)

    def precompute_target(self, target_output: str, target_id: str = None) -> str:
        """
        预计算目标嵌入

        Args:
            target_output: 目标输出文本
            target_id: 目标标识符 (可选，默认使用hash)

        Returns:
            目标ID
        """
        if target_id is None:
            target_id = hashlib.sha256(target_output.encode()).hexdigest()[:16]

        if target_id not in self._target_cache:
            embedding = self.model.encode(
                [target_output],
                batch_size=1,
                show_progress_bar=False,
                convert_to_numpy=True,
            )[0]
            self._target_cache[target_id] = embedding

        return target_id

    def calculate(
        self, response: str, target_output: str, use_cache: bool = True
    ) -> FitnessResult:
        """
        计算适应度分数

        Args:
            response: 模型的实际响应
            target_output: 期望的目标输出
            use_cache: 是否使用缓存

        Returns:
            FitnessResult 对象
        """
        start_time = time.time()

        if not response or not target_output:
            return FitnessResult(
                score=0.0,
                similarity=0.0,
                model_name=self.model_name,
                device=self.device,
            )

        with self._stats_lock:
            self._stats.total_calculations += 1
            self._stats.total_items += 1

        # 获取嵌入
        if use_cache:
            # 检查响应缓存
            response_emb = self._cache.get(response, self.model_name)

            # 检查目标缓存
            target_hash = hashlib.sha256(target_output.encode()).hexdigest()[:16]
            target_emb = self._target_cache.get(target_hash)

            if response_emb is None or target_emb is None:
                texts_to_encode = []
                if response_emb is None:
                    texts_to_encode.append(response)
                if target_emb is None:
                    texts_to_encode.append(target_output)

                embeddings = self.model.encode(
                    texts_to_encode,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )

                idx = 0
                if response_emb is None:
                    response_emb = embeddings[idx]
                    self._cache.set(response, self.model_name, response_emb)
                    idx += 1
                    with self._stats_lock:
                        self._stats.cache_misses += 1
                else:
                    with self._stats_lock:
                        self._stats.cache_hits += 1

                if target_emb is None:
                    target_emb = embeddings[idx]
                    self._target_cache[target_hash] = target_emb
        else:
            embeddings = self.model.encode(
                [response, target_output],
                batch_size=2,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            response_emb = embeddings[0]
            target_emb = embeddings[1]

        # 计算相似度
        similarity = self._cosine_similarity(response_emb, target_emb)
        score = max(0.0, min(1.0, (similarity + 1) / 2))

        latency = (time.time() - start_time) * 1000
        with self._stats_lock:
            self._stats.total_latency_ms += latency

        return FitnessResult(
            score=score,
            similarity=similarity,
            cached=use_cache,
            latency_ms=latency,
            model_name=self.model_name,
            device=self.device,
        )

    def batch_calculate(
        self, responses: List[str], target_output: str, use_cache: bool = True
    ) -> List[FitnessResult]:
        """
        批量计算适应度分数

        Args:
            responses: 响应列表
            target_output: 目标输出
            use_cache: 是否使用缓存

        Returns:
            FitnessResult 列表
        """
        start_time = time.time()

        if not responses:
            return []

        with self._stats_lock:
            self._stats.batch_count += 1
            self._stats.total_items += len(responses)
            self._stats.total_calculations += 1

        # 获取目标嵌入
        target_hash = hashlib.sha256(target_output.encode()).hexdigest()[:16]
        target_emb = self._target_cache.get(target_hash)

        if target_emb is None:
            target_emb = self.model.encode(
                [target_output],
                batch_size=1,
                show_progress_bar=False,
                convert_to_numpy=True,
            )[0]
            self._target_cache[target_hash] = target_emb

        # 批量获取响应嵌入
        if use_cache:
            response_embeddings = self._encode_with_cache(responses)
        else:
            # 分块处理大批量
            all_embeddings = []
            for i in range(0, len(responses), self.batch_size):
                batch = responses[i : i + self.batch_size]
                batch_emb = self.model.encode(
                    batch,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                all_embeddings.append(batch_emb)
            response_embeddings = np.vstack(all_embeddings)

        # 批量计算相似度
        similarities = self._cosine_similarity_batch(response_embeddings, target_emb)
        scores = np.clip((similarities + 1) / 2, 0.0, 1.0)

        latency = (time.time() - start_time) * 1000
        latency_per_item = latency / len(responses)

        with self._stats_lock:
            self._stats.total_latency_ms += latency

        results = []
        for i, (score, sim) in enumerate(zip(scores, similarities)):
            results.append(
                FitnessResult(
                    score=float(score),
                    similarity=float(sim),
                    cached=use_cache,
                    latency_ms=latency_per_item,
                    model_name=self.model_name,
                    device=self.device,
                )
            )

        return results

    def calculate_with_precomputed(
        self, response: str, target_id: str, use_cache: bool = True
    ) -> FitnessResult:
        """
        使用预计算的目标嵌入计算适应度

        Args:
            response: 模型响应
            target_id: 预计算的目标ID
            use_cache: 是否使用缓存

        Returns:
            FitnessResult 对象
        """
        start_time = time.time()

        if target_id not in self._target_cache:
            raise ValueError(f"目标ID {target_id} 未预计算")

        target_emb = self._target_cache[target_id]

        with self._stats_lock:
            self._stats.total_calculations += 1
            self._stats.total_items += 1

        # 获取响应嵌入
        if use_cache:
            response_emb = self._cache.get(response, self.model_name)
            if response_emb is None:
                response_emb = self.model.encode(
                    [response],
                    batch_size=1,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )[0]
                self._cache.set(response, self.model_name, response_emb)
                with self._stats_lock:
                    self._stats.cache_misses += 1
            else:
                with self._stats_lock:
                    self._stats.cache_hits += 1
        else:
            response_emb = self.model.encode(
                [response], batch_size=1, show_progress_bar=False, convert_to_numpy=True
            )[0]

        similarity = self._cosine_similarity(response_emb, target_emb)
        score = max(0.0, min(1.0, (similarity + 1) / 2))

        latency = (time.time() - start_time) * 1000
        with self._stats_lock:
            self._stats.total_latency_ms += latency

        return FitnessResult(
            score=score,
            similarity=similarity,
            cached=use_cache,
            latency_ms=latency,
            model_name=self.model_name,
            device=self.device,
        )

    async def calculate_async(
        self, response: str, target_output: str, use_cache: bool = True
    ) -> FitnessResult:
        """异步计算适应度"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, lambda: self.calculate(response, target_output, use_cache)
        )

    async def batch_calculate_async(
        self, responses: List[str], target_output: str, use_cache: bool = True
    ) -> List[FitnessResult]:
        """异步批量计算适应度"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.batch_calculate(responses, target_output, use_cache),
        )

    def switch_model(self, model_name: str) -> None:
        """
        切换模型

        Args:
            model_name: 新模型名称
        """
        if model_name != self.model_name:
            self.model_name = model_name
            self._model = None
            self._load_failed = False
            self._target_cache.clear()  # 清空目标缓存
            # 注意: 不清空嵌入缓存，因为可能有其他模型的缓存

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self._stats.to_dict()
        stats["cache_size"] = self._cache.size()
        stats["precomputed_targets"] = len(self._target_cache)
        stats["model_name"] = self.model_name
        stats["device"] = self.device
        return stats

    def reset_stats(self) -> None:
        """重置统计"""
        with self._stats_lock:
            self._stats = FitnessStats()

    def clear_cache(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._target_cache.clear()

    # ============= 兼容旧API =============

    def calculate_legacy(self, response: str, target_output: str) -> float:
        """旧版API兼容 - 直接返回分数"""
        result = self.calculate(response, target_output)
        return result.score

    def batch_calculate_legacy(
        self, responses: List[str], target_output: str
    ) -> List[float]:
        """旧版API兼容 - 直接返回分数列表"""
        results = self.batch_calculate(responses, target_output)
        return [r.score for r in results]


class SimpleFitness:
    """
    简化版适应度评估器 (不依赖外部模型) - 增强版

    当无法使用 sentence-transformers 时的备选方案。
    支持多种文本相似度算法。
    """

    def __init__(self, method: str = "ngram", n: int = 3):
        """
        初始化

        Args:
            method: 相似度算法 ('ngram', 'jaccard', 'cosine_bow')
            n: n-gram 的 n 值
        """
        self.method = method
        self.n = n
        self._stats = FitnessStats()

    def _get_ngrams(self, text: str) -> set:
        """提取 n-gram"""
        text = text.lower()
        if len(text) < self.n:
            return {text}
        return set(text[i : i + self.n] for i in range(len(text) - self.n + 1))

    def _get_words(self, text: str) -> List[str]:
        """分词"""
        import re

        return re.findall(r"\w+", text.lower())

    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Jaccard相似度"""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def _cosine_bow(self, text1: str, text2: str) -> float:
        """词袋模型余弦相似度"""
        words1 = self._get_words(text1)
        words2 = self._get_words(text2)

        if not words1 or not words2:
            return 0.0

        # 构建词汇表
        vocab = list(set(words1) | set(words2))

        # 构建词频向量
        from collections import Counter

        freq1 = Counter(words1)
        freq2 = Counter(words2)

        vec1 = np.array([freq1.get(w, 0) for w in vocab], dtype=float)
        vec2 = np.array([freq2.get(w, 0) for w in vocab], dtype=float)

        # 计算余弦相似度
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

    def calculate(self, response: str, target_output: str) -> FitnessResult:
        """
        计算适应度分数

        Args:
            response: 模型响应
            target_output: 目标输出

        Returns:
            FitnessResult 对象
        """
        start_time = time.time()
        self._stats.total_calculations += 1
        self._stats.total_items += 1

        if not response or not target_output:
            return FitnessResult(score=0.0, similarity=0.0)

        if self.method == "ngram":
            ngrams1 = self._get_ngrams(response)
            ngrams2 = self._get_ngrams(target_output)
            similarity = self._jaccard_similarity(ngrams1, ngrams2)
        elif self.method == "jaccard":
            words1 = set(self._get_words(response))
            words2 = set(self._get_words(target_output))
            similarity = self._jaccard_similarity(words1, words2)
        elif self.method == "cosine_bow":
            similarity = self._cosine_bow(response, target_output)
        else:
            similarity = 0.0

        score = similarity  # SimpleFitness 的相似度已经在 [0,1] 范围

        latency = (time.time() - start_time) * 1000
        self._stats.total_latency_ms += latency

        return FitnessResult(
            score=score,
            similarity=similarity,
            latency_ms=latency,
            model_name=f"simple_{self.method}",
            device="cpu",
        )

    def batch_calculate(
        self, responses: List[str], target_output: str
    ) -> List[FitnessResult]:
        """批量计算"""
        return [self.calculate(resp, target_output) for resp in responses]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return self._stats.to_dict()

    # 兼容旧API
    def calculate_legacy(self, response: str, target_output: str) -> float:
        """旧版API"""
        return self.calculate(response, target_output).score


class EnsembleFitness:
    """
    集成适应度评估器

    组合多个评估器的结果，提供更稳健的评估。
    """

    def __init__(
        self,
        evaluators: List[Union[SemanticFitness, SimpleFitness]] = None,
        weights: List[float] = None,
    ):
        """
        初始化

        Args:
            evaluators: 评估器列表
            weights: 权重列表 (默认等权重)
        """
        self.evaluators = evaluators or []
        if weights:
            self.weights = weights
        else:
            self.weights = [1.0] * len(self.evaluators) if self.evaluators else []

        # 归一化权重
        if self.weights:
            total = sum(self.weights)
            self.weights = [w / total for w in self.weights]

    def add_evaluator(
        self, evaluator: Union[SemanticFitness, SimpleFitness], weight: float = 1.0
    ) -> None:
        """添加评估器"""
        self.evaluators.append(evaluator)
        self.weights.append(weight)

        # 重新归一化
        total = sum(self.weights)
        self.weights = [w / total for w in self.weights]

    def calculate(self, response: str, target_output: str) -> FitnessResult:
        """
        集成计算适应度

        Returns:
            加权平均的 FitnessResult
        """
        if not self.evaluators:
            return FitnessResult(score=0.0, similarity=0.0)

        start_time = time.time()

        scores = []
        similarities = []

        for evaluator, weight in zip(self.evaluators, self.weights):
            result = evaluator.calculate(response, target_output)
            scores.append(result.score * weight)
            similarities.append(result.similarity * weight)

        avg_score = sum(scores)
        avg_similarity = sum(similarities)

        return FitnessResult(
            score=avg_score,
            similarity=avg_similarity,
            latency_ms=(time.time() - start_time) * 1000,
            model_name="ensemble",
            details={"evaluator_count": len(self.evaluators)},
        )


# ============= 便捷函数 =============


def quick_fitness(response: str, target_output: str) -> float:
    """快速计算适应度 (使用SimpleFitness)"""
    evaluator = SimpleFitness()
    return evaluator.calculate(response, target_output).score


def create_fitness_evaluator(
    use_gpu: bool = True, model_type: str = "fast"
) -> Union[SemanticFitness, SimpleFitness]:
    """
    创建适应度评估器的工厂函数

    Args:
        use_gpu: 是否使用GPU
        model_type: 模型类型 ('fast', 'balanced', 'accurate', 'simple')

    Returns:
        评估器实例
    """
    if model_type == "simple" or not HAS_SENTENCE_TRANSFORMERS:
        return SimpleFitness()

    model_name = SemanticFitness.RECOMMENDED_MODELS.get(model_type, model_type)
    device = "auto" if use_gpu else "cpu"

    return SemanticFitness(model_name=model_name, device=device)
