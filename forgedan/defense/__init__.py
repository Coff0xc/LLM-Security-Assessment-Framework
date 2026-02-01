# -*- coding: utf-8 -*-
"""
FORGEDAN Defense 模块 - 对抗训练数据生成

此模块提供从攻击日志生成对抗训练数据的完整工具链，用于增强 LLM 的安全防护能力。

主要功能:
- 从攻击日志提取成功样本
- 生成拒绝/安全响应样本
- 数据增强 (回译、同义词替换、对抗样本)
- 多格式导出 (JSONL, Parquet, HuggingFace, OpenAI, Anthropic)

使用示例:
    from forgedan.defense import TrainingDataGenerator, SafetyDataset

    # 从攻击日志生成训练数据
    generator = TrainingDataGenerator()
    dataset = generator.from_attack_logs("logs/attacks/")

    # 导出为 OpenAI fine-tune 格式
    from forgedan.defense.export import DataExporter
    exporter = DataExporter(dataset)
    exporter.to_openai_finetune("output/train.jsonl")
"""

from .training_data_generator import (
    TrainingDataGenerator,
    TrainingSample,
    SampleType,
    ResponseType,
)
from .safety_dataset import (
    SafetyDataset,
    DatasetConfig,
    DatasetStats,
)
from .augmentation import (
    DataAugmentor,
    AugmentationConfig,
    AugmentationType,
)
from .export import (
    DataExporter,
    ExportFormat,
    ExportConfig,
)

__version__ = "1.0.0"
__all__ = [
    # 训练数据生成
    "TrainingDataGenerator",
    "TrainingSample",
    "SampleType",
    "ResponseType",
    # 安全数据集
    "SafetyDataset",
    "DatasetConfig",
    "DatasetStats",
    # 数据增强
    "DataAugmentor",
    "AugmentationConfig",
    "AugmentationType",
    # 导出
    "DataExporter",
    "ExportFormat",
    "ExportConfig",
]
