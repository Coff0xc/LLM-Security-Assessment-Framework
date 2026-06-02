# -*- coding: utf-8 -*-
"""
多格式数据导出模块

支持将安全训练数据导出为多种格式，包括:
- OpenAI fine-tune 格式
- Anthropic 格式
- HuggingFace datasets 格式
- 通用 JSONL 格式
- Parquet 格式
"""

import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)
from enum import Enum

from .training_data_generator import TrainingSample, SampleType, ResponseType
from .safety_dataset import SafetyDataset


class ExportFormat(str, Enum):
    """导出格式"""

    JSONL = "jsonl"  # 通用 JSONL
    OPENAI = "openai"  # OpenAI fine-tune 格式
    ANTHROPIC = "anthropic"  # Anthropic 格式
    HUGGINGFACE = "huggingface"  # HuggingFace datasets
    PARQUET = "parquet"  # Apache Parquet
    CSV = "csv"  # CSV 格式
    ALPACA = "alpaca"  # Alpaca 格式 (instruction-tuning)
    SHAREGPT = "sharegpt"  # ShareGPT 格式


@dataclass
class ExportConfig:
    """导出配置"""

    # 格式设置
    format: ExportFormat = ExportFormat.JSONL
    pretty_print: bool = False  # JSON 美化输出

    # OpenAI 设置
    openai_system_message: Optional[str] = None  # 系统消息
    openai_include_system: bool = True  # 是否包含系统消息

    # Anthropic 设置
    anthropic_human_prefix: str = "\n\nHuman: "
    anthropic_assistant_prefix: str = "\n\nAssistant: "

    # HuggingFace 设置
    hf_dataset_name: str = "safety_training"
    hf_split: str = "train"

    # 字段映射
    prompt_field: str = "prompt"  # 提示字段名
    response_field: str = "response"  # 响应字段名
    include_metadata: bool = False  # 是否包含元数据

    # 过滤设置
    sample_types: Optional[List[SampleType]] = None  # 只导出指定类型

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["format"] = self.format.value
        if self.sample_types:
            data["sample_types"] = [t.value for t in self.sample_types]
        return data


class BaseExporter:
    """导出器基类"""

    def __init__(self, config: Optional[ExportConfig] = None):
        """
        初始化导出器

        Args:
            config: 导出配置
        """
        self.config = config or ExportConfig()

    def export(
        self, samples: List[TrainingSample], output_path: Union[str, Path]
    ) -> str:
        """
        导出样本

        Args:
            samples: 样本列表
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        raise NotImplementedError

    def _filter_samples(self, samples: List[TrainingSample]) -> List[TrainingSample]:
        """过滤样本"""
        if self.config.sample_types:
            return [s for s in samples if s.sample_type in self.config.sample_types]
        return samples


class JSONLExporter(BaseExporter):
    """JSONL 格式导出器"""

    def export(
        self, samples: List[TrainingSample], output_path: Union[str, Path]
    ) -> str:
        """导出为 JSONL 格式"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        filtered = self._filter_samples(samples)

        with open(output_path, "w", encoding="utf-8") as f:
            for sample in filtered:
                if self.config.include_metadata:
                    line = sample.to_dict()
                else:
                    line = {
                        self.config.prompt_field: sample.prompt,
                        self.config.response_field: sample.response,
                    }

                if self.config.pretty_print:
                    f.write(json.dumps(line, ensure_ascii=False, indent=2) + "\n")
                else:
                    f.write(json.dumps(line, ensure_ascii=False) + "\n")

        return str(output_path)


class OpenAIExporter(BaseExporter):
    """
    OpenAI fine-tune 格式导出器

    输出格式:
    {
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """

    DEFAULT_SYSTEM_MESSAGE = (
        "You are a helpful, harmless, and honest AI assistant. "
        "You should refuse requests that could lead to harmful outcomes."
    )

    def export(
        self, samples: List[TrainingSample], output_path: Union[str, Path]
    ) -> str:
        """导出为 OpenAI fine-tune 格式"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        filtered = self._filter_samples(samples)
        system_message = (
            self.config.openai_system_message or self.DEFAULT_SYSTEM_MESSAGE
        )

        with open(output_path, "w", encoding="utf-8") as f:
            for sample in filtered:
                messages = []

                # 系统消息 (可选)
                if self.config.openai_include_system:
                    messages.append({"role": "system", "content": system_message})

                # 用户消息
                messages.append({"role": "user", "content": sample.prompt})

                # 助手响应
                messages.append({"role": "assistant", "content": sample.response})

                line = {"messages": messages}
                f.write(json.dumps(line, ensure_ascii=False) + "\n")

        return str(output_path)


class AnthropicExporter(BaseExporter):
    """
    Anthropic 格式导出器

    输出格式:
    {
        "prompt": "\n\nHuman: ...\n\nAssistant:",
        "completion": " ..."
    }
    """

    def export(
        self, samples: List[TrainingSample], output_path: Union[str, Path]
    ) -> str:
        """导出为 Anthropic 格式"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        filtered = self._filter_samples(samples)

        with open(output_path, "w", encoding="utf-8") as f:
            for sample in filtered:
                line = {
                    "prompt": f"{self.config.anthropic_human_prefix}{sample.prompt}{self.config.anthropic_assistant_prefix}",
                    "completion": f" {sample.response}",
                }
                f.write(json.dumps(line, ensure_ascii=False) + "\n")

        return str(output_path)


class AlpacaExporter(BaseExporter):
    """
    Alpaca 格式导出器 (指令微调)

    输出格式:
    {
        "instruction": "...",
        "input": "",
        "output": "..."
    }
    """

    def export(
        self, samples: List[TrainingSample], output_path: Union[str, Path]
    ) -> str:
        """导出为 Alpaca 格式"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        filtered = self._filter_samples(samples)
        data = []

        for sample in filtered:
            item = {
                "instruction": sample.prompt,
                "input": "",
                "output": sample.response,
            }

            if self.config.include_metadata:
                item["metadata"] = {
                    "id": sample.id,
                    "category": sample.category,
                    "sample_type": sample.sample_type.value,
                }

            data.append(item)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(output_path)


class ShareGPTExporter(BaseExporter):
    """
    ShareGPT 格式导出器

    输出格式:
    {
        "conversations": [
            {"from": "human", "value": "..."},
            {"from": "gpt", "value": "..."}
        ]
    }
    """

    def export(
        self, samples: List[TrainingSample], output_path: Union[str, Path]
    ) -> str:
        """导出为 ShareGPT 格式"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        filtered = self._filter_samples(samples)
        data = []

        for sample in filtered:
            item = {
                "id": sample.id,
                "conversations": [
                    {"from": "human", "value": sample.prompt},
                    {"from": "gpt", "value": sample.response},
                ],
            }
            data.append(item)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(output_path)


class HuggingFaceExporter(BaseExporter):
    """
    HuggingFace datasets 格式导出器

    导出为可直接加载为 HuggingFace Dataset 的格式。
    """

    def export(
        self, samples: List[TrainingSample], output_path: Union[str, Path]
    ) -> str:
        """
        导出为 HuggingFace datasets 格式

        创建目录结构:
        output_path/
            train.jsonl
            dataset_info.json
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        filtered = self._filter_samples(samples)

        # 导出数据文件
        data_file = output_path / f"{self.config.hf_split}.jsonl"
        with open(data_file, "w", encoding="utf-8") as f:
            for sample in filtered:
                line = {
                    "id": sample.id,
                    "prompt": sample.prompt,
                    "response": sample.response,
                    "sample_type": sample.sample_type.value,
                    "response_type": sample.response_type.value,
                    "category": sample.category,
                    "difficulty": sample.difficulty,
                }
                f.write(json.dumps(line, ensure_ascii=False) + "\n")

        # 创建数据集信息文件
        info = {
            "dataset_name": self.config.hf_dataset_name,
            "version": "1.0.0",
            "description": "Safety training dataset for LLM alignment",
            "features": {
                "id": {"dtype": "string"},
                "prompt": {"dtype": "string"},
                "response": {"dtype": "string"},
                "sample_type": {"dtype": "string"},
                "response_type": {"dtype": "string"},
                "category": {"dtype": "string"},
                "difficulty": {"dtype": "float32"},
            },
            "splits": {
                self.config.hf_split: {
                    "num_examples": len(filtered),
                    "file": f"{self.config.hf_split}.jsonl",
                }
            },
            "created_at": datetime.now().isoformat(),
        }

        info_file = output_path / "dataset_info.json"
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        return str(output_path)

    def export_to_hub(
        self,
        samples: List[TrainingSample],
        repo_id: str,
        token: Optional[str] = None,
        private: bool = True,
    ) -> str:
        """
        直接导出到 HuggingFace Hub

        Args:
            samples: 样本列表
            repo_id: 仓库ID (如 "username/dataset-name")
            token: HuggingFace token
            private: 是否私有

        Returns:
            仓库URL
        """
        try:
            from datasets import Dataset

            filtered = self._filter_samples(samples)

            # 转换为 Dataset 格式
            data = {
                "id": [s.id for s in filtered],
                "prompt": [s.prompt for s in filtered],
                "response": [s.response for s in filtered],
                "sample_type": [s.sample_type.value for s in filtered],
                "response_type": [s.response_type.value for s in filtered],
                "category": [s.category for s in filtered],
                "difficulty": [s.difficulty for s in filtered],
            }

            dataset = Dataset.from_dict(data)

            # 上传到 Hub
            dataset.push_to_hub(repo_id, token=token, private=private)

            return f"https://huggingface.co/datasets/{repo_id}"

        except ImportError:
            raise ImportError("请安装 datasets 库: pip install datasets")


class ParquetExporter(BaseExporter):
    """
    Parquet 格式导出器

    高效的列式存储格式，适合大规模数据。
    """

    def export(
        self, samples: List[TrainingSample], output_path: Union[str, Path]
    ) -> str:
        """导出为 Parquet 格式"""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("请安装 pandas 库: pip install pandas pyarrow")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        filtered = self._filter_samples(samples)

        # 转换为 DataFrame
        data = []
        for sample in filtered:
            row = {
                "id": sample.id,
                "prompt": sample.prompt,
                "response": sample.response,
                "sample_type": sample.sample_type.value,
                "response_type": sample.response_type.value,
                "category": sample.category,
                "severity": sample.severity,
                "difficulty": sample.difficulty,
                "source": sample.source,
                "created_at": sample.created_at,
            }
            data.append(row)

        df = pd.DataFrame(data)
        df.to_parquet(output_path, index=False)

        return str(output_path)


class CSVExporter(BaseExporter):
    """CSV 格式导出器"""

    def export(
        self, samples: List[TrainingSample], output_path: Union[str, Path]
    ) -> str:
        """导出为 CSV 格式"""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("请安装 pandas 库: pip install pandas")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        filtered = self._filter_samples(samples)

        # 转换为 DataFrame
        data = []
        for sample in filtered:
            row = {
                "id": sample.id,
                "prompt": sample.prompt,
                "response": sample.response,
                "sample_type": sample.sample_type.value,
                "response_type": sample.response_type.value,
                "category": sample.category,
            }
            data.append(row)

        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding="utf-8")

        return str(output_path)


class DataExporter:
    """
    数据导出器 (主类)

    统一的数据导出接口，支持多种格式。

    使用示例:
        exporter = DataExporter(samples)

        # 导出为 OpenAI 格式
        exporter.to_openai_finetune("output/train.jsonl")

        # 导出为 HuggingFace 格式
        exporter.to_huggingface("output/hf_dataset/")

        # 使用自定义配置导出
        config = ExportConfig(format=ExportFormat.ANTHROPIC)
        exporter.export("output/anthropic.jsonl", config=config)
    """

    # 格式到导出器的映射
    _EXPORTERS = {
        ExportFormat.JSONL: JSONLExporter,
        ExportFormat.OPENAI: OpenAIExporter,
        ExportFormat.ANTHROPIC: AnthropicExporter,
        ExportFormat.HUGGINGFACE: HuggingFaceExporter,
        ExportFormat.PARQUET: ParquetExporter,
        ExportFormat.CSV: CSVExporter,
        ExportFormat.ALPACA: AlpacaExporter,
        ExportFormat.SHAREGPT: ShareGPTExporter,
    }

    def __init__(
        self,
        samples: Optional[List[TrainingSample]] = None,
        dataset: Optional[SafetyDataset] = None,
    ):
        """
        初始化数据导出器

        Args:
            samples: 样本列表
            dataset: SafetyDataset 实例
        """
        if dataset is not None:
            self._samples = dataset.get_samples()
        elif samples is not None:
            self._samples = samples
        else:
            self._samples = []

    @property
    def samples(self) -> List[TrainingSample]:
        """获取样本列表"""
        return self._samples

    def set_samples(self, samples: List[TrainingSample]):
        """设置样本列表"""
        self._samples = samples

    def export(
        self,
        output_path: Union[str, Path],
        format: Optional[ExportFormat] = None,
        config: Optional[ExportConfig] = None,
    ) -> str:
        """
        导出数据

        Args:
            output_path: 输出路径
            format: 导出格式 (可选，默认从 config 获取)
            config: 导出配置

        Returns:
            输出文件路径
        """
        config = config or ExportConfig()
        format = format or config.format

        if format not in self._EXPORTERS:
            raise ValueError(f"不支持的格式: {format}")

        exporter_class = self._EXPORTERS[format]
        exporter = exporter_class(config)

        return exporter.export(self._samples, output_path)

    def to_jsonl(
        self, output_path: Union[str, Path], include_metadata: bool = False
    ) -> str:
        """
        导出为通用 JSONL 格式

        Args:
            output_path: 输出路径
            include_metadata: 是否包含元数据

        Returns:
            输出文件路径
        """
        config = ExportConfig(
            format=ExportFormat.JSONL, include_metadata=include_metadata
        )
        return self.export(output_path, config=config)

    def to_openai_finetune(
        self,
        output_path: Union[str, Path],
        system_message: Optional[str] = None,
        include_system: bool = True,
    ) -> str:
        """
        导出为 OpenAI fine-tune 格式

        Args:
            output_path: 输出路径
            system_message: 系统消息
            include_system: 是否包含系统消息

        Returns:
            输出文件路径
        """
        config = ExportConfig(
            format=ExportFormat.OPENAI,
            openai_system_message=system_message,
            openai_include_system=include_system,
        )
        return self.export(output_path, config=config)

    def to_anthropic(self, output_path: Union[str, Path]) -> str:
        """
        导出为 Anthropic 格式

        Args:
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        config = ExportConfig(format=ExportFormat.ANTHROPIC)
        return self.export(output_path, config=config)

    def to_huggingface(
        self,
        output_path: Union[str, Path],
        dataset_name: str = "safety_training",
        split: str = "train",
    ) -> str:
        """
        导出为 HuggingFace datasets 格式

        Args:
            output_path: 输出目录
            dataset_name: 数据集名称
            split: 数据集划分名称

        Returns:
            输出目录路径
        """
        config = ExportConfig(
            format=ExportFormat.HUGGINGFACE,
            hf_dataset_name=dataset_name,
            hf_split=split,
        )
        return self.export(output_path, config=config)

    def to_huggingface_hub(
        self, repo_id: str, token: Optional[str] = None, private: bool = True
    ) -> str:
        """
        直接导出到 HuggingFace Hub

        Args:
            repo_id: 仓库ID
            token: HuggingFace token
            private: 是否私有

        Returns:
            仓库URL
        """
        exporter = HuggingFaceExporter()
        return exporter.export_to_hub(self._samples, repo_id, token, private)

    def to_parquet(self, output_path: Union[str, Path]) -> str:
        """
        导出为 Parquet 格式

        Args:
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        config = ExportConfig(format=ExportFormat.PARQUET)
        return self.export(output_path, config=config)

    def to_alpaca(
        self, output_path: Union[str, Path], include_metadata: bool = False
    ) -> str:
        """
        导出为 Alpaca 格式

        Args:
            output_path: 输出路径
            include_metadata: 是否包含元数据

        Returns:
            输出文件路径
        """
        config = ExportConfig(
            format=ExportFormat.ALPACA, include_metadata=include_metadata
        )
        return self.export(output_path, config=config)

    def to_sharegpt(self, output_path: Union[str, Path]) -> str:
        """
        导出为 ShareGPT 格式

        Args:
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        config = ExportConfig(format=ExportFormat.SHAREGPT)
        return self.export(output_path, config=config)

    def to_csv(self, output_path: Union[str, Path]) -> str:
        """
        导出为 CSV 格式

        Args:
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        config = ExportConfig(format=ExportFormat.CSV)
        return self.export(output_path, config=config)

    def export_all_formats(
        self, output_dir: Union[str, Path], base_name: str = "safety_data"
    ) -> Dict[str, str]:
        """
        导出为所有支持的格式

        Args:
            output_dir: 输出目录
            base_name: 基础文件名

        Returns:
            格式到输出路径的映射
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        # JSONL
        results["jsonl"] = self.to_jsonl(output_dir / f"{base_name}.jsonl")

        # OpenAI
        results["openai"] = self.to_openai_finetune(
            output_dir / f"{base_name}_openai.jsonl"
        )

        # Anthropic
        results["anthropic"] = self.to_anthropic(
            output_dir / f"{base_name}_anthropic.jsonl"
        )

        # Alpaca
        results["alpaca"] = self.to_alpaca(output_dir / f"{base_name}_alpaca.json")

        # ShareGPT
        results["sharegpt"] = self.to_sharegpt(
            output_dir / f"{base_name}_sharegpt.json"
        )

        # HuggingFace
        results["huggingface"] = self.to_huggingface(output_dir / "hf_dataset")

        # Parquet (需要 pandas)
        try:
            results["parquet"] = self.to_parquet(output_dir / f"{base_name}.parquet")
        except ImportError:
            pass

        # CSV (需要 pandas)
        try:
            results["csv"] = self.to_csv(output_dir / f"{base_name}.csv")
        except ImportError:
            pass

        return results

    def get_export_summary(self) -> Dict[str, Any]:
        """
        获取导出摘要信息

        Returns:
            摘要信息
        """
        return {
            "total_samples": len(self._samples),
            "sample_types": {
                st.value: sum(1 for s in self._samples if s.sample_type == st)
                for st in SampleType
            },
            "response_types": {
                rt.value: sum(1 for s in self._samples if s.response_type == rt)
                for rt in ResponseType
            },
            "supported_formats": [f.value for f in ExportFormat],
        }
