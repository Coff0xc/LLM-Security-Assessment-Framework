"""
模型适配器基类 - 定义统一接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ModelProvider(str, Enum):
    """模型提供商枚举"""

    # 国际模型
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

    # 国产模型
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"
    BAICHUAN = "baichuan"
    QWEN = "qwen"
    MOONSHOT = "moonshot"
    YI = "yi"

    # 本地/自部署
    OLLAMA = "ollama"
    VLLM = "vllm"
    HUGGINGFACE = "huggingface"
    AZURE = "azure"
    CUSTOM = "custom"
    MOCK = "mock"


@dataclass
class ModelConfig:
    """模型配置"""

    provider: ModelProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.provider, str):
            self.provider = ModelProvider(self.provider)


@dataclass
class ModelResponse:
    """模型响应"""

    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelAdapter(ABC):
    """模型适配器基类 - 所有适配器必须实现此接口"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self._client = None

    @abstractmethod
    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> ModelResponse:
        """
        生成单个响应

        Args:
            prompt: 用户提示
            system_prompt: 系统提示（可选）
            **kwargs: 额外参数（覆盖配置）

        Returns:
            ModelResponse: 模型响应
        """
        pass

    @abstractmethod
    async def batch_generate(
        self, prompts: List[str], system_prompt: Optional[str] = None, **kwargs
    ) -> List[ModelResponse]:
        """
        批量生成响应

        Args:
            prompts: 提示列表
            system_prompt: 系统提示（可选）
            **kwargs: 额外参数

        Returns:
            List[ModelResponse]: 响应列表
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict: 模型元数据
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 是否可用
        """
        pass

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()

    async def close(self):
        """关闭连接（子类可选实现）"""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.config.provider}, model={self.config.model})"
