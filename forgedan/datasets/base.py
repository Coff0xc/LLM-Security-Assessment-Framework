"""
数据集基类和数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class HarmCategory(str, Enum):
    """有害内容类别"""

    VIOLENCE = "violence"  # 暴力
    HATE_SPEECH = "hate_speech"  # 仇恨言论
    ILLEGAL_ACTIVITY = "illegal_activity"  # 非法活动
    SELF_HARM = "self_harm"  # 自我伤害
    SEXUAL_CONTENT = "sexual_content"  # 性内容
    MISINFORMATION = "misinformation"  # 虚假信息
    PRIVACY_VIOLATION = "privacy_violation"  # 隐私侵犯
    PROFANITY = "profanity"  # 脏话
    MALWARE = "malware"  # 恶意软件
    OTHER = "other"  # 其他


@dataclass
class DatasetSample:
    """数据集样本"""

    goal: str  # 恶意目标/请求
    target: Optional[str] = None  # 期望的有害响应（可选）
    category: Optional[HarmCategory] = None  # 类别
    severity: Optional[int] = None  # 严重程度 (1-5)
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据

    def __post_init__(self):
        if isinstance(self.category, str):
            self.category = HarmCategory(self.category)

    def to_dict(self) -> dict:
        """转为字典"""
        result = {"goal": self.goal}
        if self.target is not None:
            result["target"] = self.target
        if self.category is not None:
            result["category"] = (
                self.category.value
                if isinstance(self.category, HarmCategory)
                else self.category
            )
        if self.severity is not None:
            result["severity"] = self.severity
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class DatasetMetadata:
    """数据集元数据"""

    name: str
    version: str
    description: str
    size: int
    categories: List[HarmCategory]
    source: str
    license: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


class Dataset(ABC):
    """数据集基类"""

    def __init__(self, path: Optional[str] = None):
        self.path = path
        self._samples: List[DatasetSample] = []
        self._metadata: Optional[DatasetMetadata] = None
        self._name: Optional[str] = None

    @property
    def name(self) -> str:
        """数据集名称"""
        if self._name is not None:
            return self._name
        if self._metadata:
            return self._metadata.name
        return ""

    @name.setter
    def name(self, value: str):
        self._name = value

    @abstractmethod
    def load(self) -> List[DatasetSample]:
        """
        加载数据集

        Returns:
            List[DatasetSample]: 样本列表
        """
        pass

    def get_samples(self) -> List[DatasetSample]:
        """获取所有样本"""
        if not self._samples:
            self._samples = self.load()
        return self._samples

    def get_metadata(self) -> DatasetMetadata:
        """获取元数据"""
        if self._metadata is None:
            raise NotImplementedError("子类必须实现 get_metadata 方法")
        return self._metadata

    def filter_by_category(self, category: HarmCategory) -> List[DatasetSample]:
        """按类别过滤"""
        return [s for s in self.get_samples() if s.category == category]

    def filter_by_severity(
        self, min_severity: int, max_severity: int = 5
    ) -> List[DatasetSample]:
        """按严重程度过滤"""
        return [
            s
            for s in self.get_samples()
            if s.severity and min_severity <= s.severity <= max_severity
        ]

    def sample(self, n: int, seed: Optional[int] = None) -> List[DatasetSample]:
        """随机采样"""
        import random

        if seed is not None:
            random.seed(seed)
        samples = self.get_samples()
        return random.sample(samples, min(n, len(samples)))

    def __len__(self) -> int:
        return len(self.get_samples())

    def __getitem__(self, idx: int) -> DatasetSample:
        return self.get_samples()[idx]

    def __iter__(self):
        return iter(self.get_samples())


class SafetyDataset(Dataset):
    """便利数据集类 - 直接从样本列表创建"""

    def __init__(self, name: str = "", samples: list = None, path: str = None):
        super().__init__(path)
        self._name = name
        self._samples = samples or []

    @property
    def name(self) -> str:
        return self._name

    def load(self) -> List[DatasetSample]:
        return self._samples
