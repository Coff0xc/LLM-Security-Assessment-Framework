"""
百川 (Baichuan) 模型适配器
支持 Baichuan2-Turbo 等模型
支持搜索增强功能
"""

import time
import asyncio
import hashlib
import json
from typing import Any, Dict, List, Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .base import ModelAdapter, ModelConfig, ModelResponse


class BaichuanAdapter(ModelAdapter):
    """
    百川 AI API 适配器

    特性:
    - 支持 Baichuan2-Turbo, Baichuan2-Turbo-192k 等模型
    - 支持搜索增强
    - 支持流式输出
    - 自动重试机制
    """

    # 百川 API 端点
    DEFAULT_BASE_URL = "https://api.baichuan-ai.com/v1"

    # 支持的模型
    SUPPORTED_MODELS = [
        "Baichuan2-Turbo",
        "Baichuan2-Turbo-192k",
        "Baichuan3-Turbo",
        "Baichuan3-Turbo-128k",
        "Baichuan4",
    ]

    def __init__(self, config: ModelConfig):
        """
        初始化百川适配器

        Args:
            config: 模型配置，需包含 api_key
        """
        super().__init__(config)
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx 包未安装，请运行: pip install httpx"
            )

        self._base_url = config.base_url or self.DEFAULT_BASE_URL
        self._api_key = config.api_key

        # 创建异步 HTTP 客户端
        self._client = httpx.AsyncClient(
            timeout=config.timeout,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
        )

        # 并发控制
        max_concurrent = config.extra_params.get("max_concurrent_requests", 10)
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # 重试配置
        self._retry_delay = config.extra_params.get("retry_delay", 1.0)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        生成响应

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 额外参数
                - with_search_enhance: bool, 是否启用搜索增强
                - stream: bool, 是否流式输出
                - temperature: float, 温度参数
                - top_p: float, 核采样参数
                - top_k: int, Top-K 采样

        Returns:
            ModelResponse: 模型响应
        """
        async with self._semaphore:
            return await self._generate_with_retry(prompt, system_prompt, **kwargs)

    async def _generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """带重试的生成逻辑"""
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                return await self._do_generate(prompt, system_prompt, **kwargs)
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()

                # 可重试的错误
                if any(x in error_msg for x in ["rate limit", "timeout", "503", "502", "500"]):
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(self._retry_delay * (attempt + 1))
                        continue
                raise

        raise last_exception

    async def _do_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """实际生成逻辑"""
        start_time = time.time()

        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 构建请求体
        request_body = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

        # 处理 max_tokens
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        if max_tokens:
            request_body["max_tokens"] = max_tokens

        # Top-K 采样
        if "top_k" in kwargs:
            request_body["top_k"] = kwargs["top_k"]

        # 搜索增强
        if kwargs.get("with_search_enhance", False):
            request_body["with_search_enhance"] = True

        # 流式输出
        if kwargs.get("stream", False):
            request_body["stream"] = True
            return await self._stream_generate(request_body, start_time)

        # 发送请求
        response = await self._client.post(
            f"{self._base_url}/chat/completions",
            json=request_body,
        )

        # 检查响应
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise Exception(
                f"API request failed: {response.status_code} - {error_data}"
            )

        result = response.json()
        latency = time.time() - start_time

        # 解析响应
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")

        usage = result.get("usage", {})

        # 搜索结果（如果有）
        search_results = result.get("search_results", [])

        return ModelResponse(
            content=content,
            model=result.get("model", self.config.model),
            provider="baichuan",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency=latency,
            metadata={
                "finish_reason": choice.get("finish_reason"),
                "request_id": result.get("id"),
                "search_results": search_results,
            }
        )

    async def _stream_generate(
        self,
        request_body: Dict[str, Any],
        start_time: float
    ) -> ModelResponse:
        """
        流式生成响应

        Args:
            request_body: 请求体
            start_time: 开始时间

        Returns:
            ModelResponse: 完整响应
        """
        collected_content = []

        async with self._client.stream(
            "POST",
            f"{self._base_url}/chat/completions",
            json=request_body,
        ) as response:
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue

                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    choice = data.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        collected_content.append(content)
                except json.JSONDecodeError:
                    continue

        latency = time.time() - start_time
        full_content = "".join(collected_content)

        return ModelResponse(
            content=full_content,
            model=self.config.model,
            provider="baichuan",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency=latency,
            metadata={"streamed": True}
        )

    async def batch_generate(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[ModelResponse]:
        """
        批量生成响应（并发执行）

        Args:
            prompts: 提示列表
            system_prompt: 系统提示
            **kwargs: 额外参数

        Returns:
            响应列表
        """
        tasks = [
            self.generate(prompt, system_prompt, **kwargs)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        model = self.config.model.lower()

        return {
            "provider": "baichuan",
            "model": self.config.model,
            "base_url": self._base_url,
            "supports_streaming": True,
            "supports_search_enhance": True,
            "supports_function_calling": "baichuan4" in model or "baichuan3" in model,
            "max_context_length": self._get_context_length(model),
        }

    def _get_context_length(self, model: str) -> int:
        """获取模型的最大上下文长度"""
        if "192k" in model:
            return 192000
        elif "128k" in model:
            return 128000
        else:
            return 32000

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.generate("你好", max_tokens=5)
            return True
        except Exception:
            return False

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()

    async def search_enhanced_query(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        使用搜索增强的查询

        Args:
            query: 查询内容
            system_prompt: 系统提示
            **kwargs: 额外参数

        Returns:
            ModelResponse: 包含搜索结果的响应
        """
        return await self.generate(
            query,
            system_prompt,
            with_search_enhance=True,
            **kwargs
        )
