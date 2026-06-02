"""
自定义数据集加载器
"""

import json
import csv
from pathlib import Path
from typing import List

from .base import Dataset, DatasetSample, DatasetMetadata


class CustomDataset(Dataset):
    """自定义数据集加载器 - 支持 JSON 和 CSV 格式"""

    def __init__(
        self,
        path: str,
        name: str = "custom",
        description: str = "自定义数据集",
        format: str = "auto",  # auto, json, csv
    ):
        super().__init__(path)
        self.name = name
        self.description = description
        self.format = format

    def load(self) -> List[DatasetSample]:
        """加载自定义数据集"""
        path = Path(self.path)
        if not path.exists():
            raise FileNotFoundError(f"数据集文件不存在: {self.path}")

        # 自动检测格式
        if self.format == "auto":
            if path.suffix == ".json":
                return self._load_json(path)
            elif path.suffix == ".csv":
                return self._load_csv(path)
            else:
                raise ValueError(f"无法识别的文件格式: {path.suffix}")
        elif self.format == "json":
            return self._load_json(path)
        elif self.format == "csv":
            return self._load_csv(path)
        else:
            raise ValueError(f"不支持的格式: {self.format}")

    def _load_json(self, path: Path) -> List[DatasetSample]:
        """加载 JSON 格式"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("JSON 文件必须包含一个列表")

        samples = []
        for item in data:
            if isinstance(item, str):
                # 简单格式：只有 goal
                sample = DatasetSample(goal=item)
            elif isinstance(item, dict):
                # 完整格式
                sample = DatasetSample(
                    goal=item.get("goal", item.get("prompt", item.get("text", ""))),
                    target=item.get("target"),
                    category=item.get("category"),
                    severity=item.get("severity"),
                    metadata=item.get("metadata", {}),
                )
            else:
                raise ValueError(f"无效的数据项类型: {type(item)}")

            samples.append(sample)

        return samples

    def _load_csv(self, path: Path) -> List[DatasetSample]:
        """加载 CSV 格式"""
        samples = []

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                sample = DatasetSample(
                    goal=row.get("goal", row.get("prompt", row.get("text", ""))),
                    target=row.get("target"),
                    category=row.get("category"),
                    severity=int(row["severity"]) if row.get("severity") else None,
                    metadata={
                        k: v
                        for k, v in row.items()
                        if k not in ["goal", "target", "category", "severity"]
                    },
                )
                samples.append(sample)

        return samples

    def get_metadata(self) -> DatasetMetadata:
        """获取元数据"""
        samples = self.get_samples()
        categories = list(set(s.category for s in samples if s.category))

        return DatasetMetadata(
            name=self.name,
            version="1.0",
            description=self.description,
            size=len(samples),
            categories=categories,
            source=str(self.path),
        )
