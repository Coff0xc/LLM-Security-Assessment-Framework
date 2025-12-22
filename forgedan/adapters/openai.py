"""
OpenAI 模型适配器
"""

import time
import asyncio
from typing import Any, Dict, List, Optional

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import ModelAdapter, ModelConfig, ModelResponse


class OpenAIAdapter(ModelAdapter):
    """OpenAI API 适配器（带并发限制）"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if not OPENAI_AVAILABLE:
            raise ImportError("openai 包未安装，请运行: pip install openai")

        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

        # 并发限制
        max_concurrent = config.extra_params.get("max_concurrent_requests", 10)
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """生成单个响应（带并发控制）"""
        async with self._semaphore:
            start_time = time.time()

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # 合并配置和运行时参数
            params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "frequency_penalty": kwargs.get("frequency_penalty", self.config.frequency_penalty),
                "presence_penalty": kwargs.get("presence_penalty", self.config.presence_penalty),
            }

            # 移除 None 值
            params = {k: v for k, v in params.items() if v is not None}

            # 添加额外参数
            params.update(kwargs.get("extra_params", {}))

            response = await self._client.chat.completions.create(**params)

            latency = time.time() - start_time

            return ModelResponse(
                content=response.choices[0].message.content,
                model=response.model,
                provider="openai",
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                latency=latency,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id,
                }
            )

    async def batch_generate(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[ModelResponse]:
        """批量生成响应（并发执行）"""
        import asyncio
        tasks = [
            self.generate(prompt, system_prompt, **kwargs)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "openai",
            "model": self.config.model,
            "base_url": self.config.base_url or "https://api.openai.com/v1",
            "supports_streaming": True,
            "supports_function_calling": "gpt" in self.config.model.lower(),
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
