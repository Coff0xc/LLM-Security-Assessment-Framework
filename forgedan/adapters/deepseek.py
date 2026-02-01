"""
DeepSeek 模型适配器
兼容 OpenAI 格式 API，支持 deepseek-chat, deepseek-coder 等模型
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


class DeepSeekAdapter(ModelAdapter):
    """
    DeepSeek API 适配器

    特性:
    - 兼容 OpenAI API 格式
    - 支持 deepseek-chat, deepseek-coder 模型
    - 支持超长上下文（64K+）
    - 自动重试机制
    - 并发控制
    """

    # DeepSeek 默认 API 端点
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"

    # 支持的模型列表
    SUPPORTED_MODELS = [
        "deepseek-chat",
        "deepseek-coder",
        "deepseek-reasoner",
    ]

    def __init__(self, config: ModelConfig):
        """
        初始化 DeepSeek 适配器

        Args:
            config: 模型配置，需包含 api_key
        """
        super().__init__(config)
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai 包未安装，请运行: pip install openai"
            )

        # 设置默认 base_url
        base_url = config.base_url or self.DEFAULT_BASE_URL

        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
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
                - temperature: 温度参数
                - max_tokens: 最大生成 token 数
                - top_p: 核采样参数
                - stop: 停止序列
                - stream: 是否流式输出

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

                # 判断是否需要重试
                if "rate limit" in error_msg or "timeout" in error_msg:
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(self._retry_delay * (attempt + 1))
                        continue

                # 不可重试的错误直接抛出
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

        # 构建请求参数
        params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "frequency_penalty": kwargs.get("frequency_penalty", self.config.frequency_penalty),
            "presence_penalty": kwargs.get("presence_penalty", self.config.presence_penalty),
        }

        # 处理 max_tokens
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        if max_tokens:
            params["max_tokens"] = max_tokens

        # 处理停止序列
        if "stop" in kwargs:
            params["stop"] = kwargs["stop"]

        # 移除 None 值
        params = {k: v for k, v in params.items() if v is not None}

        # 检查流式输出
        if kwargs.get("stream", False):
            return await self._stream_generate(params, start_time)

        # 发送请求
        response = await self._client.chat.completions.create(**params)

        latency = time.time() - start_time

        # 处理响应
        content = response.choices[0].message.content or ""

        return ModelResponse(
            content=content,
            model=response.model,
            provider="deepseek",
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
            latency=latency,
            metadata={
                "finish_reason": response.choices[0].finish_reason,
                "response_id": response.id,
            }
        )

    async def _stream_generate(
        self,
        params: Dict[str, Any],
        start_time: float
    ) -> ModelResponse:
        """
        流式生成响应

        Args:
            params: 请求参数
            start_time: 开始时间

        Returns:
            ModelResponse: 完整的响应（收集所有流式块后）
        """
        params["stream"] = True

        collected_content = []

        async with self._client.chat.completions.create(**params) as response:
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    collected_content.append(chunk.choices[0].delta.content)

        latency = time.time() - start_time
        full_content = "".join(collected_content)

        return ModelResponse(
            content=full_content,
            model=self.config.model,
            provider="deepseek",
            prompt_tokens=0,  # 流式模式下可能无法获取
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
            "provider": "deepseek",
            "model": self.config.model,
            "base_url": self._client.base_url,
            "supports_streaming": True,
            "supports_function_calling": True,
            "is_coder_model": "coder" in model,
            "max_context_length": self._get_context_length(model),
        }

    def _get_context_length(self, model: str) -> int:
        """获取模型的最大上下文长度"""
        context_lengths = {
            "deepseek-chat": 64000,
            "deepseek-coder": 64000,
            "deepseek-reasoner": 64000,
        }
        return context_lengths.get(model, 32000)

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.generate("test", max_tokens=5)
            return True
        except Exception:
            return False

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.close()

    async def code_completion(
        self,
        code: str,
        language: str = "python",
        instruction: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        代码补全/生成（针对 deepseek-coder 优化）

        Args:
            code: 代码上下文
            language: 编程语言
            instruction: 指令（如 "完成这个函数"）
            **kwargs: 额外参数

        Returns:
            ModelResponse: 生成的代码
        """
        system_prompt = f"""You are an expert {language} programmer.
Follow best practices, write clean and efficient code.
Only output code without explanation unless asked."""

        prompt = code
        if instruction:
            prompt = f"{instruction}\n\n```{language}\n{code}\n```"

        # 使用 coder 模型（如果可用）
        original_model = self.config.model
        if "coder" not in original_model.lower():
            self.config.model = "deepseek-coder"

        try:
            response = await self.generate(prompt, system_prompt, **kwargs)
            return response
        finally:
            self.config.model = original_model
