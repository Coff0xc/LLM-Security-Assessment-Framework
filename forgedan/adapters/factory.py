"""
模型适配器工厂 - 统一创建不同类型的适配器

支持的提供商:
- 国际模型: openai, anthropic, gemini
- 国产模型: deepseek, zhipu, baichuan, qwen, moonshot, yi
- 本地/自部署: ollama, vllm, huggingface
- 多模态: openai_vision, gemini_vision

使用方式:
    # 方式1: 通过配置对象
    config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4", api_key="...")
    adapter = ModelAdapterFactory.create(config)

    # 方式2: 通过字符串
    adapter = ModelAdapterFactory.create_from_string("openai:gpt-4", api_key="...")
    adapter = ModelAdapterFactory.create_from_string("deepseek:deepseek-chat", api_key="...")
    adapter = ModelAdapterFactory.create_from_string("qwen:qwen-max", api_key="...")

    # 方式3: 创建多模态适配器
    vision_adapter = ModelAdapterFactory.create_vision_adapter("openai", "gpt-4o", api_key="...")
"""

from typing import Dict, Optional, TYPE_CHECKING, Type
from .base import ModelAdapter, ModelConfig, ModelProvider

if TYPE_CHECKING:
    from .multimodal_base import MultimodalAdapter

# 延迟导入，避免循环依赖和未安装依赖的问题
_adapter_cache: Dict[ModelProvider, Type[ModelAdapter]] = {}


def _get_adapter_class(provider: ModelProvider) -> Type[ModelAdapter]:
    """
    获取适配器类（延迟加载）

    Args:
        provider: 模型提供商

    Returns:
        适配器类
    """
    if provider in _adapter_cache:
        return _adapter_cache[provider]

    adapter_class = None

    try:
        if provider == ModelProvider.OPENAI:
            from .openai import OpenAIAdapter

            adapter_class = OpenAIAdapter

        elif provider == ModelProvider.ANTHROPIC:
            from .anthropic import AnthropicAdapter

            adapter_class = AnthropicAdapter

        elif provider == ModelProvider.GEMINI:
            from .gemini import GeminiAdapter

            adapter_class = GeminiAdapter

        elif provider == ModelProvider.DEEPSEEK:
            from .deepseek import DeepSeekAdapter

            adapter_class = DeepSeekAdapter

        elif provider == ModelProvider.ZHIPU:
            from .zhipu import ZhipuAdapter

            adapter_class = ZhipuAdapter

        elif provider == ModelProvider.BAICHUAN:
            from .baichuan import BaichuanAdapter

            adapter_class = BaichuanAdapter

        elif provider == ModelProvider.QWEN:
            from .qwen import QwenAdapter

            adapter_class = QwenAdapter

        elif provider == ModelProvider.MOONSHOT:
            from .moonshot import MoonshotAdapter

            adapter_class = MoonshotAdapter

        elif provider == ModelProvider.YI:
            from .yi import YiAdapter

            adapter_class = YiAdapter

        elif provider == ModelProvider.OLLAMA:
            from .ollama import OllamaAdapter

            adapter_class = OllamaAdapter

        elif provider == ModelProvider.VLLM:
            from .vllm import VLLMAdapter

            adapter_class = VLLMAdapter

        elif provider == ModelProvider.HUGGINGFACE:
            from .huggingface import HuggingFaceAdapter

            adapter_class = HuggingFaceAdapter

        elif provider == ModelProvider.MOCK:
            from .mock import MockAdapter

            adapter_class = MockAdapter

    except ImportError as e:
        raise ImportError(f"无法加载 {provider.value} 适配器，请检查依赖是否安装: {e}")

    if adapter_class:
        _adapter_cache[provider] = adapter_class

    return adapter_class


class ModelAdapterFactory:
    """模型适配器工厂"""

    # 模型名称到提供商的映射（用于自动推断）
    _model_provider_map = {
        # OpenAI 模型
        "gpt-4": ModelProvider.OPENAI,
        "gpt-4-turbo": ModelProvider.OPENAI,
        "gpt-4o": ModelProvider.OPENAI,
        "gpt-3.5-turbo": ModelProvider.OPENAI,
        "o1-preview": ModelProvider.OPENAI,
        "o1-mini": ModelProvider.OPENAI,
        # Anthropic 模型
        "claude-3-opus": ModelProvider.ANTHROPIC,
        "claude-3-sonnet": ModelProvider.ANTHROPIC,
        "claude-3-haiku": ModelProvider.ANTHROPIC,
        "claude-3.5-sonnet": ModelProvider.ANTHROPIC,
        # Gemini 模型
        "gemini-pro": ModelProvider.GEMINI,
        "gemini-1.5-pro": ModelProvider.GEMINI,
        "gemini-1.5-flash": ModelProvider.GEMINI,
        # DeepSeek 模型
        "deepseek-chat": ModelProvider.DEEPSEEK,
        "deepseek-coder": ModelProvider.DEEPSEEK,
        "deepseek-reasoner": ModelProvider.DEEPSEEK,
        # 智谱 GLM 模型
        "glm-4": ModelProvider.ZHIPU,
        "glm-4-plus": ModelProvider.ZHIPU,
        "glm-4-air": ModelProvider.ZHIPU,
        "glm-4-flash": ModelProvider.ZHIPU,
        "glm-3-turbo": ModelProvider.ZHIPU,
        # 百川模型
        "baichuan2-turbo": ModelProvider.BAICHUAN,
        "baichuan3-turbo": ModelProvider.BAICHUAN,
        "baichuan4": ModelProvider.BAICHUAN,
        # 通义千问模型
        "qwen-turbo": ModelProvider.QWEN,
        "qwen-plus": ModelProvider.QWEN,
        "qwen-max": ModelProvider.QWEN,
        "qwen-vl-max": ModelProvider.QWEN,
        "qwen-coder-turbo": ModelProvider.QWEN,
        # Moonshot 模型
        "moonshot-v1-8k": ModelProvider.MOONSHOT,
        "moonshot-v1-32k": ModelProvider.MOONSHOT,
        "moonshot-v1-128k": ModelProvider.MOONSHOT,
        # 零一万物模型
        "yi-large": ModelProvider.YI,
        "yi-medium": ModelProvider.YI,
        "yi-vision": ModelProvider.YI,
    }

    # 自定义注册的适配器
    _custom_adapters: Dict[ModelProvider, Type[ModelAdapter]] = {}

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
        # 先检查自定义注册
        if config.provider in cls._custom_adapters:
            return cls._custom_adapters[config.provider](config)

        # 使用延迟加载获取适配器类
        adapter_class = _get_adapter_class(config.provider)

        if adapter_class is None:
            supported = [p.value for p in ModelProvider]
            raise ValueError(
                f"不支持的模型提供商: {config.provider}. " f"支持的提供商: {supported}"
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
            >>> factory.create_from_string("openai:gpt-4", api_key="sk-xxx")
            >>> factory.create_from_string("deepseek:deepseek-chat", api_key="sk-xxx")
            >>> factory.create_from_string("qwen:qwen-max", api_key="sk-xxx")
            >>> factory.create_from_string("gpt-4", api_key="sk-xxx")  # 自动推断提供商
        """
        if ":" in model_string:
            provider_str, model = model_string.split(":", 1)
            try:
                provider = ModelProvider(provider_str.lower())
            except ValueError:
                raise ValueError(
                    f"未知的提供商: {provider_str}. "
                    f"支持: {[p.value for p in ModelProvider]}"
                )
        else:
            # 尝试自动推断提供商
            model = model_string
            provider = cls._infer_provider(model)

            if provider is None:
                # 默认使用 OpenAI
                provider = ModelProvider.OPENAI

        config = ModelConfig(provider=provider, model=model, **kwargs)

        return cls.create(config)

    @classmethod
    def _infer_provider(cls, model: str) -> Optional[ModelProvider]:
        """
        根据模型名称推断提供商

        Args:
            model: 模型名称

        Returns:
            推断的提供商，如果无法推断返回 None
        """
        model_lower = model.lower()

        # 精确匹配
        if model_lower in cls._model_provider_map:
            return cls._model_provider_map[model_lower]

        # 模糊匹配
        if model_lower.startswith("gpt-") or model_lower.startswith("o1-"):
            return ModelProvider.OPENAI
        if model_lower.startswith("claude"):
            return ModelProvider.ANTHROPIC
        if model_lower.startswith("gemini"):
            return ModelProvider.GEMINI
        if model_lower.startswith("deepseek"):
            return ModelProvider.DEEPSEEK
        if model_lower.startswith("glm"):
            return ModelProvider.ZHIPU
        if model_lower.startswith("baichuan"):
            return ModelProvider.BAICHUAN
        if model_lower.startswith("qwen"):
            return ModelProvider.QWEN
        if model_lower.startswith("moonshot"):
            return ModelProvider.MOONSHOT
        if model_lower.startswith("yi-"):
            return ModelProvider.YI
        if model_lower.startswith("llama") or model_lower.startswith("mistral"):
            return ModelProvider.OLLAMA

        return None

    @classmethod
    def register_adapter(
        cls, provider: ModelProvider, adapter_class: Type[ModelAdapter]
    ):
        """
        注册自定义适配器

        Args:
            provider: 提供商枚举
            adapter_class: 适配器类
        """
        cls._custom_adapters[provider] = adapter_class

    @classmethod
    def list_providers(cls) -> list:
        """列出所有支持的提供商"""
        return list(ModelProvider)

    @classmethod
    def get_provider_info(cls, provider: ModelProvider) -> Dict:
        """
        获取提供商信息

        Args:
            provider: 提供商枚举

        Returns:
            提供商信息字典
        """
        info = {
            ModelProvider.OPENAI: {
                "name": "OpenAI",
                "website": "https://platform.openai.com",
                "models": [
                    "gpt-4",
                    "gpt-4-turbo",
                    "gpt-4o",
                    "gpt-3.5-turbo",
                    "o1-preview",
                ],
                "features": ["streaming", "function_calling", "vision"],
            },
            ModelProvider.ANTHROPIC: {
                "name": "Anthropic",
                "website": "https://console.anthropic.com",
                "models": [
                    "claude-3-opus",
                    "claude-3-sonnet",
                    "claude-3-haiku",
                    "claude-3.5-sonnet",
                ],
                "features": ["streaming", "vision"],
            },
            ModelProvider.GEMINI: {
                "name": "Google Gemini",
                "website": "https://aistudio.google.com",
                "models": ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"],
                "features": ["streaming", "multimodal", "safety_settings"],
            },
            ModelProvider.DEEPSEEK: {
                "name": "DeepSeek",
                "website": "https://platform.deepseek.com",
                "models": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
                "features": ["streaming", "long_context", "code_generation"],
            },
            ModelProvider.ZHIPU: {
                "name": "智谱 AI",
                "website": "https://open.bigmodel.cn",
                "models": ["glm-4", "glm-4-plus", "glm-4-air", "glm-3-turbo"],
                "features": [
                    "streaming",
                    "web_search",
                    "code_interpreter",
                    "retrieval",
                ],
            },
            ModelProvider.BAICHUAN: {
                "name": "百川",
                "website": "https://platform.baichuan-ai.com",
                "models": ["Baichuan2-Turbo", "Baichuan3-Turbo", "Baichuan4"],
                "features": ["streaming", "search_enhance"],
            },
            ModelProvider.QWEN: {
                "name": "通义千问",
                "website": "https://dashscope.console.aliyun.com",
                "models": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-vl-max"],
                "features": [
                    "streaming",
                    "multimodal",
                    "long_context",
                    "code_generation",
                ],
            },
            ModelProvider.MOONSHOT: {
                "name": "Moonshot (Kimi)",
                "website": "https://platform.moonshot.cn",
                "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                "features": ["streaming", "ultra_long_context", "file_upload"],
            },
            ModelProvider.YI: {
                "name": "零一万物",
                "website": "https://platform.lingyiwanwu.com",
                "models": ["yi-large", "yi-medium", "yi-vision", "yi-large-rag"],
                "features": ["streaming", "multimodal", "rag"],
            },
            ModelProvider.OLLAMA: {
                "name": "Ollama (本地)",
                "website": "https://ollama.ai",
                "models": ["llama2", "mistral", "codellama", "phi"],
                "features": ["streaming", "local_deployment"],
            },
            ModelProvider.VLLM: {
                "name": "vLLM (本地)",
                "website": "https://vllm.ai",
                "models": ["any compatible model"],
                "features": ["streaming", "high_throughput", "local_deployment"],
            },
        }

        return info.get(
            provider, {"name": provider.value, "models": [], "features": []}
        )

    @classmethod
    def create_vision_adapter(
        cls, provider: str, model: str, api_key: str, **kwargs
    ) -> "MultimodalAdapter":
        """
        创建多模态（视觉）适配器

        Args:
            provider: 提供商名称 (openai, gemini)
            model: 模型名称
            api_key: API 密钥
            **kwargs: 额外配置

        Returns:
            MultimodalAdapter: 多模态适配器实例

        Examples:
            >>> adapter = ModelAdapterFactory.create_vision_adapter(
            ...     "openai", "gpt-4o", api_key="sk-xxx"
            ... )
            >>> adapter = ModelAdapterFactory.create_vision_adapter(
            ...     "gemini", "gemini-1.5-pro", api_key="xxx"
            ... )
        """
        provider_lower = provider.lower()

        if provider_lower == "openai":
            from .openai_vision import OpenAIVisionAdapter

            config = ModelConfig(
                provider=ModelProvider.OPENAI, model=model, api_key=api_key, **kwargs
            )
            return OpenAIVisionAdapter(config)

        elif provider_lower == "gemini" or provider_lower == "google":
            from .gemini_vision import GeminiVisionAdapter

            config = ModelConfig(
                provider=ModelProvider.GEMINI, model=model, api_key=api_key, **kwargs
            )
            return GeminiVisionAdapter(config)

        else:
            raise ValueError(
                f"不支持的视觉模型提供商: {provider}. " f"支持: openai, gemini"
            )

    @classmethod
    def list_vision_models(cls) -> Dict[str, list]:
        """
        列出支持视觉的模型

        Returns:
            Dict: 提供商 -> 模型列表
        """
        return {
            "openai": [
                "gpt-4-vision-preview",
                "gpt-4-turbo",
                "gpt-4o",
                "gpt-4o-mini",
            ],
            "gemini": [
                "gemini-pro-vision",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
            ],
        }
