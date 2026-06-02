"""
模型适配器模块 - 统一不同 LLM 提供商的接口

支持的提供商:
- 国际模型: openai, anthropic, gemini
- 国产模型: deepseek, zhipu, baichuan, qwen, moonshot, yi
- 本地/自部署: ollama, vllm, huggingface

使用示例:
    # 方式1: 通过工厂类创建
    from forgedan.adapters import ModelAdapterFactory

    adapter = ModelAdapterFactory.create_from_string(
        "openai:gpt-4",
        api_key="sk-xxx"
    )

    response = await adapter.generate("Hello, world!")
    print(response.content)

    # 方式2: 通过配置对象创建
    from forgedan.adapters import ModelConfig, ModelProvider, ModelAdapterFactory

    config = ModelConfig(
        provider=ModelProvider.QWEN,
        model="qwen-max",
        api_key="sk-xxx"
    )
    adapter = ModelAdapterFactory.create(config)

    # 方式3: 直接实例化适配器
    from forgedan.adapters.qwen import QwenAdapter
    from forgedan.adapters import ModelConfig, ModelProvider

    config = ModelConfig(
        provider=ModelProvider.QWEN,
        model="qwen-vl-max",
        api_key="sk-xxx"
    )
    adapter = QwenAdapter(config)

    # 多模态示例
    response = await adapter.generate(
        "描述这张图片",
        images=["path/to/image.jpg"]
    )
"""

from .base import ModelAdapter, ModelConfig, ModelResponse, ModelProvider
from .factory import ModelAdapterFactory

# 多模态支持
from .multimodal_base import (
    MultimodalAdapter,
    MultimodalResponse,
    MultimodalMessage,
    ImageInput,
    ImageFormat,
    ImageDetail,
    VisionCapabilities,
)

# 延迟导入具体适配器，避免未安装依赖时报错
__all__ = [
    # 基类
    "ModelAdapter",
    "ModelConfig",
    "ModelResponse",
    "ModelProvider",
    "ModelAdapterFactory",
    # 多模态基类
    "MultimodalAdapter",
    "MultimodalResponse",
    "MultimodalMessage",
    "ImageInput",
    "ImageFormat",
    "ImageDetail",
    "VisionCapabilities",
]


def __getattr__(name: str):
    """
    延迟导入具体适配器类

    这样可以避免在未安装某个适配器依赖时导入整个模块失败
    """
    adapter_map = {
        # 国际模型
        "OpenAIAdapter": ("openai", "OpenAIAdapter"),
        "AnthropicAdapter": ("anthropic", "AnthropicAdapter"),
        "GeminiAdapter": ("gemini", "GeminiAdapter"),
        # 多模态适配器
        "OpenAIVisionAdapter": ("openai_vision", "OpenAIVisionAdapter"),
        "GeminiVisionAdapter": ("gemini_vision", "GeminiVisionAdapter"),
        # 国产模型
        "DeepSeekAdapter": ("deepseek", "DeepSeekAdapter"),
        "ZhipuAdapter": ("zhipu", "ZhipuAdapter"),
        "BaichuanAdapter": ("baichuan", "BaichuanAdapter"),
        "QwenAdapter": ("qwen", "QwenAdapter"),
        "MoonshotAdapter": ("moonshot", "MoonshotAdapter"),
        "YiAdapter": ("yi", "YiAdapter"),
        # 本地/自部署
        "OllamaAdapter": ("ollama", "OllamaAdapter"),
        "VLLMAdapter": ("vllm", "VLLMAdapter"),
        "HuggingFaceAdapter": ("huggingface", "HuggingFaceAdapter"),
        "MockAdapter": ("mock", "MockAdapter"),
    }

    if name in adapter_map:
        module_name, class_name = adapter_map[name]
        import importlib

        module = importlib.import_module(f".{module_name}", __name__)
        return getattr(module, class_name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
