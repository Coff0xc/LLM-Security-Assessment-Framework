# -*- coding: utf-8 -*-
"""
训练数据生成器

从攻击日志和原始数据生成用于安全对齐的训练数据。
支持正负样本生成、拒绝响应模板、安全响应生成等功能。
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
    Union,
    Tuple,
)
from enum import Enum


class SampleType(str, Enum):
    """样本类型"""

    POSITIVE = "positive"  # 正样本: 有害提示 + 拒绝响应
    NEGATIVE = "negative"  # 负样本: 有害提示 + 有害响应 (用于对比学习)
    SAFE = "safe"  # 安全样本: 正常提示 + 正常响应
    ADVERSARIAL = "adversarial"  # 对抗样本: 变体提示 + 拒绝响应


class ResponseType(str, Enum):
    """响应类型"""

    REFUSAL = "refusal"  # 拒绝响应
    SAFE = "safe"  # 安全响应
    HARMFUL = "harmful"  # 有害响应 (用于对比)
    REDIRECT = "redirect"  # 重定向响应


@dataclass
class TrainingSample:
    """训练样本数据结构"""

    # 核心字段
    id: str  # 唯一标识符
    prompt: str  # 输入提示
    response: str  # 期望响应
    sample_type: SampleType  # 样本类型
    response_type: ResponseType  # 响应类型

    # 元数据
    source: str = ""  # 来源 (attack_log, manual, generated)
    category: str = ""  # 有害类别
    severity: int = 0  # 严重程度 (1-5)
    difficulty: float = 0.0  # 难度分数 (0-1)
    original_prompt: Optional[str] = None  # 原始提示 (增强前)

    # 攻击相关
    attack_success: bool = False  # 原始攻击是否成功
    attack_fitness: float = 0.0  # 原始攻击适应度
    model_name: str = ""  # 目标模型名称

    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 额外信息
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.sample_type, str):
            self.sample_type = SampleType(self.sample_type)
        if isinstance(self.response_type, str):
            self.response_type = ResponseType(self.response_type)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["sample_type"] = self.sample_type.value
        data["response_type"] = self.response_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainingSample":
        """从字典创建"""
        return cls(**data)

    def get_hash(self) -> str:
        """获取内容哈希 (用于去重)"""
        content = f"{self.prompt}|{self.response}"
        return hashlib.md5(content.encode()).hexdigest()


class RefusalTemplateProvider:
    """
    拒绝响应模板提供器

    提供多种风格的拒绝响应模板，支持随机选择和自定义。
    """

    # 标准拒绝模板 (简洁直接)
    STANDARD_TEMPLATES = [
        "I cannot help with that request as it could be harmful.",
        "I'm not able to assist with this type of request.",
        "This request goes against my guidelines, so I cannot help.",
        "I cannot provide assistance with potentially harmful activities.",
        "I'm designed to be helpful, harmless, and honest. I cannot assist with this.",
    ]

    # 解释性拒绝模板 (详细说明)
    EXPLANATORY_TEMPLATES = [
        "I understand you're asking about {topic}, but I cannot provide information that could be used for harmful purposes. Instead, I'd be happy to help you with {alternative}.",
        "While I aim to be helpful, I cannot assist with requests that could lead to harm. This includes {topic}. Is there something else I can help you with?",
        "I appreciate your question, but providing information about {topic} could potentially cause harm. I'm here to help with constructive and safe topics.",
    ]

    # 重定向模板 (引导到安全话题)
    REDIRECT_TEMPLATES = [
        "I cannot help with that, but I'd be happy to assist you with learning about {safe_topic} instead.",
        "That's not something I can help with. Would you like to explore {safe_topic} instead?",
        "I'm not able to assist with that request. Perhaps I can help you with {safe_topic}?",
    ]

    # 中文拒绝模板
    CHINESE_TEMPLATES = [
        "抱歉，我无法协助处理这类请求，因为它可能会造成伤害。",
        "我无法提供此类信息。请问有其他我可以帮助您的吗？",
        "这个请求超出了我的服务范围。我被设计为提供有益、安全的帮助。",
        "我理解您的问题，但我不能提供可能被滥用的信息。让我们讨论一些更有建设性的话题吧。",
        "作为AI助手，我需要遵守安全准则，无法回答这类问题。",
    ]

    def __init__(self, custom_templates: Optional[List[str]] = None):
        """
        初始化模板提供器

        Args:
            custom_templates: 自定义模板列表
        """
        self.custom_templates = custom_templates or []
        self._all_templates = (
            self.STANDARD_TEMPLATES
            + self.EXPLANATORY_TEMPLATES
            + self.REDIRECT_TEMPLATES
            + self.CHINESE_TEMPLATES
            + self.custom_templates
        )

    def get_random(self, category: Optional[str] = None) -> str:
        """
        获取随机拒绝响应

        Args:
            category: 模板类别 (standard, explanatory, redirect, chinese, custom)

        Returns:
            随机选择的拒绝响应
        """
        if category == "standard":
            templates = self.STANDARD_TEMPLATES
        elif category == "explanatory":
            templates = self.EXPLANATORY_TEMPLATES
        elif category == "redirect":
            templates = self.REDIRECT_TEMPLATES
        elif category == "chinese":
            templates = self.CHINESE_TEMPLATES
        elif category == "custom":
            templates = self.custom_templates
        else:
            templates = self._all_templates

        return random.choice(templates) if templates else self.STANDARD_TEMPLATES[0]

    def get_with_context(
        self,
        topic: str = "this",
        alternative: str = "other topics",
        safe_topic: str = "general knowledge",
    ) -> str:
        """
        获取带上下文的拒绝响应

        Args:
            topic: 当前话题
            alternative: 替代建议
            safe_topic: 安全话题建议

        Returns:
            格式化后的拒绝响应
        """
        template = random.choice(self.EXPLANATORY_TEMPLATES + self.REDIRECT_TEMPLATES)
        return template.format(
            topic=topic, alternative=alternative, safe_topic=safe_topic
        )


class SafeResponseGenerator:
    """
    安全响应生成器

    为有害请求生成适当的安全响应，包括拒绝、解释和重定向。
    """

    def __init__(self, template_provider: Optional[RefusalTemplateProvider] = None):
        """
        初始化安全响应生成器

        Args:
            template_provider: 模板提供器
        """
        self.template_provider = template_provider or RefusalTemplateProvider()

        # 类别到安全话题的映射
        self.category_to_safe_topic = {
            "violence": "conflict resolution and peaceful communication",
            "hate_speech": "diversity, inclusion, and mutual respect",
            "illegal_activity": "legal alternatives and proper channels",
            "self_harm": "mental health resources and support",
            "misinformation": "fact-checking and reliable sources",
            "privacy_violation": "data protection and privacy rights",
            "default": "constructive and educational topics",
        }

    def generate(
        self,
        prompt: str,
        category: Optional[str] = None,
        response_type: ResponseType = ResponseType.REFUSAL,
        language: str = "en",
    ) -> str:
        """
        生成安全响应

        Args:
            prompt: 原始有害提示
            category: 有害类别
            response_type: 期望的响应类型
            language: 语言 (en, zh)

        Returns:
            安全响应文本
        """
        if response_type == ResponseType.REFUSAL:
            if language == "zh":
                return self.template_provider.get_random("chinese")
            return self.template_provider.get_random("standard")

        elif response_type == ResponseType.REDIRECT:
            safe_topic = self.category_to_safe_topic.get(
                category or "default", self.category_to_safe_topic["default"]
            )
            return self.template_provider.get_with_context(
                topic="this request", safe_topic=safe_topic
            )

        elif response_type == ResponseType.SAFE:
            # 生成教育性的安全响应
            return self._generate_educational_response(prompt, category)

        return self.template_provider.get_random()

    def _generate_educational_response(
        self, prompt: str, category: Optional[str] = None
    ) -> str:
        """生成教育性响应"""
        educational_templates = [
            "Instead of {topic}, let me share some information about safety and ethics...",
            "I'd like to redirect this conversation to discuss responsible practices...",
            "While I cannot help with that, I can explain why such activities are harmful...",
        ]
        template = random.choice(educational_templates)
        return template.format(topic=category or "that topic")


class TrainingDataGenerator:
    """
    训练数据生成器

    从攻击日志和其他数据源生成用于LLM安全对齐的训练数据。

    主要功能:
    - 从攻击日志提取成功样本
    - 生成拒绝响应样本 (正样本)
    - 生成对比学习的负样本
    - 支持正负样本平衡
    - 支持多种输出格式

    使用示例:
        generator = TrainingDataGenerator()

        # 从攻击日志生成
        samples = generator.from_attack_logs("logs/attacks/")

        # 生成平衡数据集
        balanced = generator.balance_samples(samples, ratio=1.0)

        # 导出
        generator.export_jsonl(balanced, "train.jsonl")
    """

    def __init__(
        self,
        template_provider: Optional[RefusalTemplateProvider] = None,
        response_generator: Optional[SafeResponseGenerator] = None,
        seed: Optional[int] = None,
    ):
        """
        初始化训练数据生成器

        Args:
            template_provider: 拒绝模板提供器
            response_generator: 安全响应生成器
            seed: 随机种子
        """
        self.template_provider = template_provider or RefusalTemplateProvider()
        self.response_generator = response_generator or SafeResponseGenerator(
            self.template_provider
        )

        if seed is not None:
            random.seed(seed)

        self._sample_counter = 0

    def _generate_id(self) -> str:
        """生成唯一样本ID"""
        self._sample_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ts_{timestamp}_{self._sample_counter:06d}"

    def from_attack_logs(
        self,
        log_path: Union[str, Path],
        success_only: bool = True,
        min_fitness: float = 0.5,
        include_negative: bool = False,
    ) -> List[TrainingSample]:
        """
        从攻击日志提取训练样本

        Args:
            log_path: 日志文件或目录路径
            success_only: 是否仅提取成功攻击
            min_fitness: 最小适应度阈值
            include_negative: 是否包含负样本 (有害响应)

        Returns:
            训练样本列表
        """
        log_path = Path(log_path)
        samples = []

        # 收集所有日志文件
        if log_path.is_file():
            log_files = [log_path]
        else:
            log_files = list(log_path.glob("**/*.json"))

        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    log_data = json.load(f)

                # 处理单条记录或会话记录
                records = log_data.get("records", [log_data])
                if isinstance(records, dict):
                    records = [records]

                for record in records:
                    sample_batch = self._process_attack_record(
                        record,
                        success_only=success_only,
                        min_fitness=min_fitness,
                        include_negative=include_negative,
                    )
                    samples.extend(sample_batch)

            except (json.JSONDecodeError, KeyError) as e:
                print(f"警告: 跳过无效日志文件 {log_file}: {e}")
                continue

        return samples

    def _process_attack_record(
        self,
        record: Dict[str, Any],
        success_only: bool = True,
        min_fitness: float = 0.5,
        include_negative: bool = False,
    ) -> List[TrainingSample]:
        """处理单条攻击记录"""
        samples = []

        # 提取字段
        success = record.get("success", False)
        fitness = record.get("fitness", 0.0)
        prompt = record.get("prompt", "")
        response = record.get("response", "")
        goal = record.get("goal", "")
        category = record.get("category", "")
        severity = record.get("severity", 0)
        model_name = record.get("model_name", "")

        # 过滤条件
        if success_only and not success:
            return samples
        if fitness < min_fitness:
            return samples
        if not prompt:
            return samples

        # 生成正样本 (有害提示 + 拒绝响应)
        safe_response = self.response_generator.generate(
            prompt=prompt, category=category, response_type=ResponseType.REFUSAL
        )

        positive_sample = TrainingSample(
            id=self._generate_id(),
            prompt=prompt,
            response=safe_response,
            sample_type=SampleType.POSITIVE,
            response_type=ResponseType.REFUSAL,
            source="attack_log",
            category=category,
            severity=severity,
            difficulty=fitness,
            original_prompt=goal,
            attack_success=success,
            attack_fitness=fitness,
            model_name=model_name,
            metadata={"log_timestamp": record.get("timestamp", "")},
        )
        samples.append(positive_sample)

        # 可选: 生成负样本 (有害提示 + 有害响应)
        if include_negative and response:
            negative_sample = TrainingSample(
                id=self._generate_id(),
                prompt=prompt,
                response=response,
                sample_type=SampleType.NEGATIVE,
                response_type=ResponseType.HARMFUL,
                source="attack_log",
                category=category,
                severity=severity,
                difficulty=fitness,
                original_prompt=goal,
                attack_success=success,
                attack_fitness=fitness,
                model_name=model_name,
                metadata={"log_timestamp": record.get("timestamp", "")},
            )
            samples.append(negative_sample)

        return samples

    def generate_refusal_samples(
        self,
        harmful_prompts: List[str],
        categories: Optional[List[str]] = None,
        response_types: Optional[List[ResponseType]] = None,
        language: str = "en",
    ) -> List[TrainingSample]:
        """
        从有害提示列表生成拒绝样本

        Args:
            harmful_prompts: 有害提示列表
            categories: 对应的类别列表 (可选)
            response_types: 期望的响应类型列表 (可选)
            language: 语言

        Returns:
            训练样本列表
        """
        samples = []

        for i, prompt in enumerate(harmful_prompts):
            category = categories[i] if categories and i < len(categories) else None
            response_type = (
                response_types[i]
                if response_types and i < len(response_types)
                else ResponseType.REFUSAL
            )

            response = self.response_generator.generate(
                prompt=prompt,
                category=category,
                response_type=response_type,
                language=language,
            )

            sample = TrainingSample(
                id=self._generate_id(),
                prompt=prompt,
                response=response,
                sample_type=SampleType.POSITIVE,
                response_type=response_type,
                source="generated",
                category=category or "",
            )
            samples.append(sample)

        return samples

    def generate_safe_samples(
        self, safe_prompts: List[str], safe_responses: List[str]
    ) -> List[TrainingSample]:
        """
        生成安全样本 (正常提示 + 正常响应)

        用于保持模型的有用性，避免过度拒绝。

        Args:
            safe_prompts: 安全提示列表
            safe_responses: 对应的安全响应列表

        Returns:
            训练样本列表
        """
        if len(safe_prompts) != len(safe_responses):
            raise ValueError("提示和响应数量必须一致")

        samples = []

        for prompt, response in zip(safe_prompts, safe_responses):
            sample = TrainingSample(
                id=self._generate_id(),
                prompt=prompt,
                response=response,
                sample_type=SampleType.SAFE,
                response_type=ResponseType.SAFE,
                source="safe_examples",
            )
            samples.append(sample)

        return samples

    def balance_samples(
        self,
        samples: List[TrainingSample],
        ratio: float = 1.0,
        strategy: str = "undersample",
    ) -> List[TrainingSample]:
        """
        平衡正负样本

        Args:
            samples: 原始样本列表
            ratio: 正负样本比例 (正样本数 / 负样本数)
            strategy: 平衡策略 (undersample: 下采样, oversample: 上采样)

        Returns:
            平衡后的样本列表
        """
        # 按类型分组
        positive_samples = [s for s in samples if s.sample_type == SampleType.POSITIVE]
        negative_samples = [s for s in samples if s.sample_type == SampleType.NEGATIVE]
        safe_samples = [s for s in samples if s.sample_type == SampleType.SAFE]
        adversarial_samples = [
            s for s in samples if s.sample_type == SampleType.ADVERSARIAL
        ]

        # 计算目标数量
        n_positive = len(positive_samples)
        n_negative = len(negative_samples)

        if n_negative == 0:
            # 无负样本，直接返回
            return samples

        if strategy == "undersample":
            # 下采样: 减少多数类
            target_negative = int(n_positive / ratio) if ratio > 0 else n_negative
            if target_negative < n_negative:
                negative_samples = random.sample(negative_samples, target_negative)

        elif strategy == "oversample":
            # 上采样: 增加少数类
            target_positive = int(n_negative * ratio) if ratio > 0 else n_positive
            if target_positive > n_positive:
                # 重复采样
                additional = target_positive - n_positive
                additional_samples = random.choices(positive_samples, k=additional)
                positive_samples = positive_samples + additional_samples

        # 合并并打乱
        balanced = (
            positive_samples + negative_samples + safe_samples + adversarial_samples
        )
        random.shuffle(balanced)

        return balanced

    def split_dataset(
        self,
        samples: List[TrainingSample],
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        stratify_by: Optional[str] = "sample_type",
    ) -> Tuple[List[TrainingSample], List[TrainingSample], List[TrainingSample]]:
        """
        划分训练/验证/测试集

        Args:
            samples: 样本列表
            train_ratio: 训练集比例
            val_ratio: 验证集比例
            test_ratio: 测试集比例
            stratify_by: 分层依据字段 (sample_type, category)

        Returns:
            (train, val, test) 元组
        """
        assert (
            abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001
        ), "比例之和必须为1"

        if stratify_by:
            # 分层采样
            groups: Dict[str, List[TrainingSample]] = {}
            for sample in samples:
                key = getattr(sample, stratify_by, "default")
                if isinstance(key, Enum):
                    key = key.value
                if key not in groups:
                    groups[key] = []
                groups[key].append(sample)

            train, val, test = [], [], []
            for group_samples in groups.values():
                random.shuffle(group_samples)
                n = len(group_samples)
                n_train = int(n * train_ratio)
                n_val = int(n * val_ratio)

                train.extend(group_samples[:n_train])
                val.extend(group_samples[n_train : n_train + n_val])
                test.extend(group_samples[n_train + n_val :])
        else:
            # 简单随机划分
            shuffled = samples.copy()
            random.shuffle(shuffled)
            n = len(shuffled)
            n_train = int(n * train_ratio)
            n_val = int(n * val_ratio)

            train = shuffled[:n_train]
            val = shuffled[n_train : n_train + n_val]
            test = shuffled[n_train + n_val :]

        return train, val, test

    def export_jsonl(
        self,
        samples: List[TrainingSample],
        output_path: Union[str, Path],
        format_type: str = "default",
    ) -> str:
        """
        导出为 JSONL 格式

        Args:
            samples: 样本列表
            output_path: 输出路径
            format_type: 格式类型 (default, openai, anthropic)

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for sample in samples:
                if format_type == "openai":
                    # OpenAI fine-tune 格式
                    line = {
                        "messages": [
                            {"role": "user", "content": sample.prompt},
                            {"role": "assistant", "content": sample.response},
                        ]
                    }
                elif format_type == "anthropic":
                    # Anthropic 格式
                    line = {
                        "prompt": f"\n\nHuman: {sample.prompt}\n\nAssistant:",
                        "completion": f" {sample.response}",
                    }
                else:
                    # 默认格式
                    line = sample.to_dict()

                f.write(json.dumps(line, ensure_ascii=False) + "\n")

        return str(output_path)

    def get_statistics(self, samples: List[TrainingSample]) -> Dict[str, Any]:
        """
        获取样本统计信息

        Args:
            samples: 样本列表

        Returns:
            统计信息字典
        """
        stats = {
            "total": len(samples),
            "by_sample_type": {},
            "by_response_type": {},
            "by_category": {},
            "by_source": {},
            "difficulty": {
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
            },
        }

        if not samples:
            return stats

        # 按类型统计
        for sample in samples:
            # 样本类型
            st = sample.sample_type.value
            stats["by_sample_type"][st] = stats["by_sample_type"].get(st, 0) + 1

            # 响应类型
            rt = sample.response_type.value
            stats["by_response_type"][rt] = stats["by_response_type"].get(rt, 0) + 1

            # 类别
            if sample.category:
                stats["by_category"][sample.category] = (
                    stats["by_category"].get(sample.category, 0) + 1
                )

            # 来源
            if sample.source:
                stats["by_source"][sample.source] = (
                    stats["by_source"].get(sample.source, 0) + 1
                )

        # 难度统计
        difficulties = [s.difficulty for s in samples if s.difficulty > 0]
        if difficulties:
            stats["difficulty"]["min"] = min(difficulties)
            stats["difficulty"]["max"] = max(difficulties)
            stats["difficulty"]["mean"] = sum(difficulties) / len(difficulties)

        return stats
