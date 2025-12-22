"""
模型适配器工厂 - 统一创建不同类型的适配器
"""

from typing import Dict, Type
from .base import ModelAdapter, ModelConfig, ModelProvider
from .openai import OpenAIAdapter
from .anthropic import AnthropicAdapter
from .ollama import OllamaAdapter
from .vllm import VLLMAdapter
from .huggingface import HuggingFaceAdapter
from .mock import MockAdapter


class ModelAdapterFactory:
    """模型适配器工厂"""

    _adapters: Dict[ModelProvider, Type[ModelAdapter]] = {
        ModelProvider.OPENAI: OpenAIAdapter,
        ModelProvider.ANTHROPIC: AnthropicAdapter,
        ModelProvider.OLLAMA: OllamaAdapter,
        ModelProvider.VLLM: VLLMAdapter,
        ModelProvider.HUGGINGFACE: HuggingFaceAdapter,
        ModelProvider.MOCK: MockAdapter,
    }

    @classmethod
    def create(cls, config: ModelConfig) -> ModelAdapter:
        """
        创建模型适配器

        Args:
            config: 模型配置

        Returns:
            ModelAdapter: 对应的适配器实例

        Raises:
            ValueError: 不支持的提供商
        """
        adapter_class = cls._adapters.get(config.provider)
        if adapter_class is None:
            raise ValueError(
                f"不支持的模型提供商: {config.provider}. "
                f"支持的提供商: {list(cls._adapters.keys())}"
            )

        return adapter_class(config)

    @classmethod
    def create_from_string(cls, model_string: str, **kwargs) -> ModelAdapter:
        """
        从字符串创建适配器

        Args:
            model_string: 格式为 "provider:model" 或 "model"
            **kwargs: 额外配置参数

        Returns:
            ModelAdapter: 适配器实例

        Examples:
            >>> factory.create_from_string("openai:gpt-3.5-turbo", api_key="sk-xxx")
            >>> factory.create_from_string("anthropic:claude-3-opus", api_key="sk-ant-xxx")
            >>> factory.create_from_string("ollama:llama2")
        """
        if ":" in model_string:
            provider_str, model = model_string.split(":", 1)
            provider = ModelProvider(provider_str.lower())
        else:
            # 默认使用 OpenAI
            provider = ModelProvider.OPENAI
            model = model_string

        config = ModelConfig(
            provider=provider,
            model=model,
            **kwargs
        )

        return cls.create(config)

    @classmethod
    def register_adapter(
        cls,
        provider: ModelProvider,
        adapter_class: Type[ModelAdapter]
    ):
        """
        注册自定义适配器

        Args:
            provider: 提供商枚举
            adapter_class: 适配器类
        """
        cls._adapters[provider] = adapter_class

    @classmethod
    def list_providers(cls) -> list:
        """列出所有支持的提供商"""
        return list(cls._adapters.keys())
