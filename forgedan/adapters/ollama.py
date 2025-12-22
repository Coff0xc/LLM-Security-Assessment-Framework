"""
Ollama 本地模型适配器
"""

import time
from typing import Any, Dict, List, Optional

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from .base import ModelAdapter, ModelConfig, ModelResponse


class OllamaAdapter(ModelAdapter):
    """Ollama 本地模型适配器"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp 包未安装，请运行: pip install aiohttp")

        self.base_url = config.base_url or "http://localhost:11434"
        self._session = None

    async def _get_session(self):
        """获取或创建 aiohttp session"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
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

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        if self.config.max_tokens:
            payload["options"]["num_predict"] = self.config.max_tokens

        url = f"{self.base_url}/api/generate"

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama API 错误 ({response.status}): {error_text}")

            data = await response.json()

        latency = time.time() - start_time

        return ModelResponse(
            content=data.get("response", ""),
            model=self.config.model,
            provider="ollama",
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            latency=latency,
            metadata={
                "context": data.get("context"),
                "done": data.get("done"),
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
            "provider": "ollama",
            "model": self.config.model,
            "base_url": self.base_url,
            "supports_streaming": True,
            "supports_function_calling": False,
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/tags"
            async with session.get(url) as response:
                return response.status == 200
        except Exception:
            return False

    async def close(self):
        """关闭 session"""
        if self._session:
            await self._session.close()
            self._session = None
