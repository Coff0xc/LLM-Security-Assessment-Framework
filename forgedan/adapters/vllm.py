"""
vLLM 模型适配器
"""

import time
from typing import Any, Dict, List, Optional

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from .base import ModelAdapter, ModelConfig, ModelResponse


class VLLMAdapter(ModelAdapter):
    """vLLM 服务器适配器（兼容 OpenAI API）"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp 包未安装，请运行: pip install aiohttp")

        self.base_url = config.base_url or "http://localhost:8000"
        self._session = None

    async def _get_session(self):
        """获取或创建 aiohttp session"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self._session

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """生成单个响应"""
        start_time = time.time()
        session = await self._get_session()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        # 移除 None 值
        payload = {k: v for k, v in payload.items() if v is not None}

        url = f"{self.base_url}/v1/chat/completions"

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"vLLM API 错误 ({response.status}): {error_text}")

            data = await response.json()

        latency = time.time() - start_time

        usage = data.get("usage", {})
        return ModelResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", self.config.model),
            provider="vllm",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency=latency,
            metadata={
                "finish_reason": data["choices"][0].get("finish_reason"),
                "response_id": data.get("id"),
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
            "provider": "vllm",
            "model": self.config.model,
            "base_url": self.base_url,
            "supports_streaming": True,
            "supports_function_calling": False,
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/health"
            async with session.get(url) as response:
                return response.status == 200
        except Exception:
            return False

    async def close(self):
        """关闭 session"""
        if self._session:
            await self._session.close()
            self._session = None
