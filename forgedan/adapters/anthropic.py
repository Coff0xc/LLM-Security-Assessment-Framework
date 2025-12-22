"""
Anthropic Claude 模型适配器
"""

import time
from typing import Any, Dict, List, Optional

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import ModelAdapter, ModelConfig, ModelResponse


class AnthropicAdapter(ModelAdapter):
    """Anthropic Claude API 适配器"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic 包未安装，请运行: pip install anthropic")

        self._client = AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """生成单个响应"""
        start_time = time.time()

        params = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

        if system_prompt:
            params["system"] = system_prompt

        # 添加额外参数
        params.update(kwargs.get("extra_params", {}))

        response = await self._client.messages.create(**params)

        latency = time.time() - start_time

        return ModelResponse(
            content=response.content[0].text,
            model=response.model,
            provider="anthropic",
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            latency=latency,
            metadata={
                "stop_reason": response.stop_reason,
                "response_id": response.id,
            }
        )

    async def batch_generate(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[ModelResponse]:
        """批量生成响应"""
        import asyncio
        tasks = [
            self.generate(prompt, system_prompt, **kwargs)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "anthropic",
            "model": self.config.model,
            "base_url": self.config.base_url or "https://api.anthropic.com",
            "supports_streaming": True,
            "supports_function_calling": False,
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.generate("test", max_tokens=1)
            return True
        except Exception:
            return False

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.close()
