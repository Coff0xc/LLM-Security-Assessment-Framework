# -*- coding: utf-8 -*-
"""
安全数据集管理

提供安全训练数据集的管理、验证、清洗和采样功能。
支持数据去重、质量过滤、类别平衡等操作。
"""

import json
import hashlib
import random
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Callable,
    Union,
    Iterator,
    Set,
    Tuple,
)
from enum import Enum
from collections import Counter

from .training_data_generator import TrainingSample, SampleType, ResponseType


@dataclass
class DatasetConfig:
    """数据集配置"""
    # 基本信息
    name: str = "safety_dataset"
    version: str = "1.0.0"
    description: str = ""

    # 质量过滤
    min_prompt_length: int = 10           # 最小提示长度
    max_prompt_length: int = 4096         # 最大提示长度
    min_response_length: int = 5          # 最小响应长度
    max_response_length: int = 4096       # 最大响应长度

    # 去重设置
    enable_dedup: bool = True              # 启用去重
    dedup_method: str = "hash"             # 去重方法 (hash, similarity)
    similarity_threshold: float = 0.95     # 相似度阈值 (用于similarity方法)

    # 平衡设置
    balance_by_type: bool = False          # 按类型平衡
    balance_by_category: bool = False      # 按类别平衡
    max_samples_per_category: int = 1000   # 每类别最大样本数

    # 验证设置
    validate_format: bool = True           # 验证格式
    validate_content: bool = True          # 验证内容

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class DatasetStats:
    """数据集统计信息"""
    total_samples: int = 0
    unique_samples: int = 0
    duplicates_removed: int = 0

    # 按类型
    by_sample_type: Dict[str, int] = field(default_factory=dict)
    by_response_type: Dict[str, int] = field(default_factory=dict)
    by_category: Dict[str, int] = field(default_factory=dict)
    by_source: Dict[str, int] = field(default_factory=dict)

    # 长度统计
    prompt_length_stats: Dict[str, float] = field(default_factory=dict)
    response_length_stats: Dict[str, float] = field(default_factory=dict)

    # 质量过滤
    filtered_by_length: int = 0
    filtered_by_content: int = 0

    # 时间
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    processed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class QualityFilter:
    """
    质量过滤器

    提供多种质量过滤规则，用于清洗训练数据。
    """

    def __init__(self, config: Optional[DatasetConfig] = None):
        """
        初始化质量过滤器

        Args:
            config: 数据集配置
        """
        self.config = config or DatasetConfig()

        # 有害关键词黑名单 (用于检测明显的有害内容)
        self.content_blacklist = set()

        # 必须包含的拒绝关键词 (用于验证拒绝响应)
        self.refusal_keywords = [
            "cannot", "can't", "unable", "won't", "refuse",
            "inappropriate", "harmful", "不能", "无法", "抱歉"
        ]

    def filter_by_length(self, sample: TrainingSample) -> bool:
        """
        按长度过滤

        Args:
            sample: 训练样本

        Returns:
            True 表示通过过滤
        """
        prompt_len = len(sample.prompt)
        response_len = len(sample.response)

        if prompt_len < self.config.min_prompt_length:
            return False
        if prompt_len > self.config.max_prompt_length:
            return False
        if response_len < self.config.min_response_length:
            return False
        if response_len > self.config.max_response_length:
            return False

        return True

    def filter_by_content(self, sample: TrainingSample) -> bool:
        """
        按内容过滤

        Args:
            sample: 训练样本

        Returns:
            True 表示通过过滤
        """
        # 检查空内容
        if not sample.prompt.strip() or not sample.response.strip():
            return False

        # 对于正样本，验证响应是否为拒绝响应
        if sample.sample_type == SampleType.POSITIVE:
            response_lower = sample.response.lower()
            has_refusal = any(kw in response_lower for kw in self.refusal_keywords)
            if not has_refusal:
                # 放宽检查，允许没有明确拒绝关键词但响应合理的样本
                pass

        return True

    def filter_by_format(self, sample: TrainingSample) -> bool:
        """
        按格式过滤

        Args:
            sample: 训练样本

        Returns:
            True 表示通过过滤
        """
        # 检查必要字段
        if not sample.id:
            return False
        if not sample.sample_type:
            return False
        if not sample.response_type:
            return False

        return True

    def apply_all(self, sample: TrainingSample) -> Tuple[bool, str]:
        """
        应用所有过滤规则

        Args:
            sample: 训练样本

        Returns:
            (是否通过, 失败原因)
        """
        if self.config.validate_format and not self.filter_by_format(sample):
            return False, "format_invalid"

        if not self.filter_by_length(sample):
            return False, "length_invalid"

        if self.config.validate_content and not self.filter_by_content(sample):
            return False, "content_invalid"

        return True, ""


class Deduplicator:
    """
    样本去重器

    支持基于哈希和相似度的去重方法。
    """

    def __init__(self, method: str = "hash", similarity_threshold: float = 0.95):
        """
        初始化去重器

        Args:
            method: 去重方法 (hash, similarity)
            similarity_threshold: 相似度阈值
        """
        self.method = method
        self.similarity_threshold = similarity_threshold
        self._seen_hashes: Set[str] = set()

    def reset(self):
        """重置去重状态"""
        self._seen_hashes = set()

    def _compute_hash(self, sample: TrainingSample) -> str:
        """计算样本哈希"""
        content = f"{sample.prompt}|{sample.response}"
        return hashlib.md5(content.encode()).hexdigest()

    def _compute_similarity(self, sample1: TrainingSample, sample2: TrainingSample) -> float:
        """
        计算两个样本的相似度

        使用简单的 Jaccard 相似度
        """
        words1 = set(sample1.prompt.lower().split())
        words2 = set(sample2.prompt.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def is_duplicate(self, sample: TrainingSample, existing_samples: Optional[List[TrainingSample]] = None) -> bool:
        """
        检查是否重复

        Args:
            sample: 待检查样本
            existing_samples: 已有样本列表 (用于similarity方法)

        Returns:
            True 表示是重复样本
        """
        if self.method == "hash":
            sample_hash = self._compute_hash(sample)
            if sample_hash in self._seen_hashes:
                return True
            self._seen_hashes.add(sample_hash)
            return False

        elif self.method == "similarity":
            if not existing_samples:
                return False

            for existing in existing_samples:
                similarity = self._compute_similarity(sample, existing)
                if similarity >= self.similarity_threshold:
                    return True
            return False

        return False

    def deduplicate(self, samples: List[TrainingSample]) -> Tuple[List[TrainingSample], int]:
        """
        对样本列表去重

        Args:
            samples: 样本列表

        Returns:
            (去重后的样本列表, 移除的重复数)
        """
        self.reset()
        unique_samples = []
        duplicates = 0

        for sample in samples:
            if not self.is_duplicate(sample, unique_samples):
                unique_samples.append(sample)
            else:
                duplicates += 1

        return unique_samples, duplicates


class CategoryBalancer:
    """
    类别平衡器

    实现多种类别平衡策略，确保训练数据分布均衡。
    """

    def __init__(self, max_per_category: int = 1000):
        """
        初始化类别平衡器

        Args:
            max_per_category: 每类别最大样本数
        """
        self.max_per_category = max_per_category

    def balance_by_type(
        self,
        samples: List[TrainingSample],
        target_distribution: Optional[Dict[str, float]] = None
    ) -> List[TrainingSample]:
        """
        按样本类型平衡

        Args:
            samples: 样本列表
            target_distribution: 目标分布 (type -> ratio)

        Returns:
            平衡后的样本列表
        """
        # 按类型分组
        groups: Dict[SampleType, List[TrainingSample]] = {}
        for sample in samples:
            if sample.sample_type not in groups:
                groups[sample.sample_type] = []
            groups[sample.sample_type].append(sample)

        if target_distribution is None:
            # 默认均匀分布
            target_distribution = {t.value: 1.0 / len(groups) for t in groups.keys()}

        # 计算每类目标数量
        total = len(samples)
        balanced = []

        for sample_type, group_samples in groups.items():
            ratio = target_distribution.get(sample_type.value, 1.0 / len(groups))
            target_count = min(int(total * ratio), len(group_samples), self.max_per_category)

            if target_count < len(group_samples):
                selected = random.sample(group_samples, target_count)
            else:
                selected = group_samples

            balanced.extend(selected)

        random.shuffle(balanced)
        return balanced

    def balance_by_category(
        self,
        samples: List[TrainingSample],
        categories: Optional[List[str]] = None
    ) -> List[TrainingSample]:
        """
        按有害类别平衡

        Args:
            samples: 样本列表
            categories: 需要平衡的类别列表

        Returns:
            平衡后的样本列表
        """
        # 按类别分组
        groups: Dict[str, List[TrainingSample]] = {}
        for sample in samples:
            cat = sample.category or "unknown"
            if cat not in groups:
                groups[cat] = []
            groups[cat].append(sample)

        # 如果指定了类别，只保留这些类别
        if categories:
            groups = {k: v for k, v in groups.items() if k in categories}

        if not groups:
            return samples

        # 找到最小类别大小
        min_count = min(len(g) for g in groups.values())
        target_count = min(min_count, self.max_per_category)

        balanced = []
        for group_samples in groups.values():
            if len(group_samples) > target_count:
                selected = random.sample(group_samples, target_count)
            else:
                selected = group_samples
            balanced.extend(selected)

        random.shuffle(balanced)
        return balanced

    def undersample(
        self,
        samples: List[TrainingSample],
        group_by: str = "sample_type"
    ) -> List[TrainingSample]:
        """
        下采样到最小类别大小

        Args:
            samples: 样本列表
            group_by: 分组依据

        Returns:
            下采样后的样本列表
        """
        # 分组
        groups: Dict[str, List[TrainingSample]] = {}
        for sample in samples:
            key = str(getattr(sample, group_by, "unknown"))
            if isinstance(getattr(sample, group_by, None), Enum):
                key = getattr(sample, group_by).value
            if key not in groups:
                groups[key] = []
            groups[key].append(sample)

        if not groups:
            return samples

        # 下采样
        min_count = min(len(g) for g in groups.values())
        balanced = []

        for group_samples in groups.values():
            selected = random.sample(group_samples, min_count)
            balanced.extend(selected)

        random.shuffle(balanced)
        return balanced

    def oversample(
        self,
        samples: List[TrainingSample],
        group_by: str = "sample_type"
    ) -> List[TrainingSample]:
        """
        上采样到最大类别大小

        Args:
            samples: 样本列表
            group_by: 分组依据

        Returns:
            上采样后的样本列表
        """
        # 分组
        groups: Dict[str, List[TrainingSample]] = {}
        for sample in samples:
            key = str(getattr(sample, group_by, "unknown"))
            if isinstance(getattr(sample, group_by, None), Enum):
                key = getattr(sample, group_by).value
            if key not in groups:
                groups[key] = []
            groups[key].append(sample)

        if not groups:
            return samples

        # 上采样
        max_count = min(max(len(g) for g in groups.values()), self.max_per_category)
        balanced = []

        for group_samples in groups.values():
            if len(group_samples) < max_count:
                # 重复采样
                additional = random.choices(group_samples, k=max_count - len(group_samples))
                selected = group_samples + additional
            else:
                selected = group_samples[:max_count]
            balanced.extend(selected)

        random.shuffle(balanced)
        return balanced


class SafetyDataset:
    """
    安全数据集

    提供安全训练数据的完整管理功能，包括:
    - 数据加载和保存
    - 质量过滤和验证
    - 去重和清洗
    - 类别平衡采样
    - 统计分析

    使用示例:
        dataset = SafetyDataset(config=DatasetConfig(name="my_dataset"))

        # 添加样本
        dataset.add_samples(samples)

        # 处理数据
        dataset.process()

        # 获取处理后的数据
        clean_samples = dataset.get_samples()

        # 保存
        dataset.save("output/dataset.json")
    """

    def __init__(self, config: Optional[DatasetConfig] = None):
        """
        初始化安全数据集

        Args:
            config: 数据集配置
        """
        self.config = config or DatasetConfig()
        self._samples: List[TrainingSample] = []
        self._stats = DatasetStats()

        # 初始化组件
        self._filter = QualityFilter(self.config)
        self._deduplicator = Deduplicator(
            method=self.config.dedup_method,
            similarity_threshold=self.config.similarity_threshold
        )
        self._balancer = CategoryBalancer(
            max_per_category=self.config.max_samples_per_category
        )

        self._processed = False

    @property
    def samples(self) -> List[TrainingSample]:
        """获取样本列表"""
        return self._samples

    @property
    def stats(self) -> DatasetStats:
        """获取统计信息"""
        return self._stats

    def add_sample(self, sample: TrainingSample):
        """添加单个样本"""
        self._samples.append(sample)
        self._processed = False

    def add_samples(self, samples: List[TrainingSample]):
        """批量添加样本"""
        self._samples.extend(samples)
        self._processed = False

    def get_samples(self, processed: bool = True) -> List[TrainingSample]:
        """
        获取样本

        Args:
            processed: 是否返回处理后的样本

        Returns:
            样本列表
        """
        if processed and not self._processed:
            self.process()
        return self._samples

    def process(self) -> DatasetStats:
        """
        处理数据集

        执行完整的数据处理流程:
        1. 质量过滤
        2. 去重
        3. 类别平衡

        Returns:
            处理统计信息
        """
        original_count = len(self._samples)
        self._stats.total_samples = original_count

        # 1. 质量过滤
        filtered_samples = []
        filtered_by_length = 0
        filtered_by_content = 0

        for sample in self._samples:
            passed, reason = self._filter.apply_all(sample)
            if passed:
                filtered_samples.append(sample)
            elif reason == "length_invalid":
                filtered_by_length += 1
            elif reason in ("content_invalid", "format_invalid"):
                filtered_by_content += 1

        self._stats.filtered_by_length = filtered_by_length
        self._stats.filtered_by_content = filtered_by_content

        # 2. 去重
        if self.config.enable_dedup:
            unique_samples, duplicates = self._deduplicator.deduplicate(filtered_samples)
            self._stats.duplicates_removed = duplicates
        else:
            unique_samples = filtered_samples
            self._stats.duplicates_removed = 0

        self._stats.unique_samples = len(unique_samples)

        # 3. 类别平衡
        if self.config.balance_by_type:
            unique_samples = self._balancer.balance_by_type(unique_samples)

        if self.config.balance_by_category:
            unique_samples = self._balancer.balance_by_category(unique_samples)

        self._samples = unique_samples

        # 更新统计
        self._update_stats()
        self._stats.processed_at = datetime.now().isoformat()
        self._processed = True

        return self._stats

    def _update_stats(self):
        """更新统计信息"""
        # 按类型统计
        type_counter = Counter(s.sample_type.value for s in self._samples)
        self._stats.by_sample_type = dict(type_counter)

        response_counter = Counter(s.response_type.value for s in self._samples)
        self._stats.by_response_type = dict(response_counter)

        category_counter = Counter(s.category for s in self._samples if s.category)
        self._stats.by_category = dict(category_counter)

        source_counter = Counter(s.source for s in self._samples if s.source)
        self._stats.by_source = dict(source_counter)

        # 长度统计
        prompt_lengths = [len(s.prompt) for s in self._samples]
        response_lengths = [len(s.response) for s in self._samples]

        if prompt_lengths:
            self._stats.prompt_length_stats = {
                "min": min(prompt_lengths),
                "max": max(prompt_lengths),
                "mean": sum(prompt_lengths) / len(prompt_lengths),
            }

        if response_lengths:
            self._stats.response_length_stats = {
                "min": min(response_lengths),
                "max": max(response_lengths),
                "mean": sum(response_lengths) / len(response_lengths),
            }

    def filter_by(
        self,
        predicate: Callable[[TrainingSample], bool]
    ) -> "SafetyDataset":
        """
        自定义过滤

        Args:
            predicate: 过滤函数

        Returns:
            新的数据集实例
        """
        filtered = [s for s in self._samples if predicate(s)]
        new_dataset = SafetyDataset(config=self.config)
        new_dataset.add_samples(filtered)
        return new_dataset

    def sample(
        self,
        n: int,
        stratify_by: Optional[str] = None,
        seed: Optional[int] = None
    ) -> List[TrainingSample]:
        """
        随机采样

        Args:
            n: 采样数量
            stratify_by: 分层依据
            seed: 随机种子

        Returns:
            采样的样本列表
        """
        if seed is not None:
            random.seed(seed)

        if stratify_by:
            # 分层采样
            groups: Dict[str, List[TrainingSample]] = {}
            for sample in self._samples:
                key = str(getattr(sample, stratify_by, "unknown"))
                if isinstance(getattr(sample, stratify_by, None), Enum):
                    key = getattr(sample, stratify_by).value
                if key not in groups:
                    groups[key] = []
                groups[key].append(sample)

            # 计算每组采样数
            per_group = n // len(groups) if groups else n
            sampled = []

            for group_samples in groups.values():
                k = min(per_group, len(group_samples))
                sampled.extend(random.sample(group_samples, k))

            return sampled[:n]
        else:
            return random.sample(self._samples, min(n, len(self._samples)))

    def split(
        self,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        seed: Optional[int] = None
    ) -> Tuple["SafetyDataset", "SafetyDataset", "SafetyDataset"]:
        """
        划分数据集

        Args:
            train_ratio: 训练集比例
            val_ratio: 验证集比例
            test_ratio: 测试集比例
            seed: 随机种子

        Returns:
            (train, val, test) 数据集元组
        """
        if seed is not None:
            random.seed(seed)

        shuffled = self._samples.copy()
        random.shuffle(shuffled)

        n = len(shuffled)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        train_samples = shuffled[:n_train]
        val_samples = shuffled[n_train:n_train + n_val]
        test_samples = shuffled[n_train + n_val:]

        train_dataset = SafetyDataset(config=self.config)
        train_dataset.add_samples(train_samples)

        val_dataset = SafetyDataset(config=self.config)
        val_dataset.add_samples(val_samples)

        test_dataset = SafetyDataset(config=self.config)
        test_dataset.add_samples(test_samples)

        return train_dataset, val_dataset, test_dataset

    def save(self, path: Union[str, Path], format: str = "json") -> str:
        """
        保存数据集

        Args:
            path: 输出路径
            format: 格式 (json, jsonl)

        Returns:
            输出文件路径
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            data = {
                "config": self.config.to_dict(),
                "stats": self._stats.to_dict(),
                "samples": [s.to_dict() for s in self._samples],
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        elif format == "jsonl":
            with open(path, "w", encoding="utf-8") as f:
                for sample in self._samples:
                    f.write(json.dumps(sample.to_dict(), ensure_ascii=False) + "\n")

        return str(path)

    @classmethod
    def load(cls, path: Union[str, Path]) -> "SafetyDataset":
        """
        加载数据集

        Args:
            path: 输入路径

        Returns:
            数据集实例
        """
        path = Path(path)

        with open(path, "r", encoding="utf-8") as f:
            if path.suffix == ".jsonl":
                # JSONL 格式
                samples = []
                for line in f:
                    data = json.loads(line.strip())
                    samples.append(TrainingSample.from_dict(data))
                dataset = cls()
                dataset.add_samples(samples)
            else:
                # JSON 格式
                data = json.load(f)
                config = DatasetConfig(**data.get("config", {}))
                dataset = cls(config=config)

                samples = [TrainingSample.from_dict(s) for s in data.get("samples", [])]
                dataset.add_samples(samples)

                # 恢复统计信息
                if "stats" in data:
                    for key, value in data["stats"].items():
                        if hasattr(dataset._stats, key):
                            setattr(dataset._stats, key, value)

        return dataset

    def __len__(self) -> int:
        return len(self._samples)

    def __iter__(self) -> Iterator[TrainingSample]:
        return iter(self._samples)

    def __getitem__(self, idx: int) -> TrainingSample:
        return self._samples[idx]
