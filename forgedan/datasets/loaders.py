"""
数据集加载器 - 统一接口
"""

from typing import Dict, Type, Optional
from .base import Dataset
from .advbench import AdvBenchDataset
from .custom import CustomDataset


class DatasetLoader:
    """数据集加载器 - 统一管理所有数据集"""

    _datasets: Dict[str, Type[Dataset]] = {
        "advbench": AdvBenchDataset,
        "custom": CustomDataset,
    }

    @classmethod
    def load(cls, name: str, path: Optional[str] = None, **kwargs) -> Dataset:
        """
        加载数据集

        Args:
            name: 数据集名称 (advbench, wildguard, custom)
            path: 数据集路径（可选）
            **kwargs: 额外参数

        Returns:
            Dataset: 数据集实例

        Examples:
            >>> loader.load("advbench")  # 使用内置样本
            >>> loader.load("advbench", path="./data/advbench.json")
            >>> loader.load("custom", path="./data/my_dataset.json")
        """
        dataset_class = cls._datasets.get(name.lower())
        if dataset_class is None:
            raise ValueError(
                f"不支持的数据集: {name}. "
                f"支持的数据集: {list(cls._datasets.keys())}"
            )

        if path:
            return dataset_class(path=path, **kwargs)
        else:
            return dataset_class(**kwargs)

    @classmethod
    def register_dataset(cls, name: str, dataset_class: Type[Dataset]):
        """
        注册自定义数据集

        Args:
            name: 数据集名称
            dataset_class: 数据集类
        """
        cls._datasets[name.lower()] = dataset_class

    @classmethod
    def list_datasets(cls) -> list:
        """列出所有支持的数据集"""
        return list(cls._datasets.keys())
