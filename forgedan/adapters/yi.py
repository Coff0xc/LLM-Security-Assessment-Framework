"""
零一万物 (Yi) 模型适配器
支持 yi-large, yi-medium, yi-vision 等模型
兼容 OpenAI API 格式
"""

import time
import asyncio
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import ModelAdapter, ModelConfig, ModelResponse


class YiAdapter(ModelAdapter):
    """
    零一万物 (Yi) API 适配器

    特性:
    - 兼容 OpenAI API 格式
    - 支持 yi-large, yi-medium, yi-vision 等模型
    - 支持多模态（yi-vision）
    - 支持长上下文
    - 自动重试机制
    """

    # Yi API 端点
    DEFAULT_BASE_URL = "https://api.lingyiwanwu.com/v1"

    # 支持的模型
    SUPPORTED_MODELS = [
        "yi-large",
        "yi-large-turbo",
        "yi-large-rag",
        "yi-medium",
        "yi-medium-200k",
        "yi-spark",
        "yi-vision",
    ]

    def __init__(self, config: ModelConfig):
        """
        初始化 Yi 适配器

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
        images: Optional[List[Union[str, bytes, Path]]] = None,
        **kwargs
    ) -> ModelResponse:
        """
        生成响应

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            images: 图片列表（用于 yi-vision 模型）
            **kwargs: 额外参数
                - temperature: float, 温度参数
                - max_tokens: int, 最大生成 token 数
                - top_p: float, 核采样参数
                - stop: list, 停止序列
                - stream: bool, 是否流式输出

        Returns:
            ModelResponse: 模型响应
        """
        async with self._semaphore:
            # 判断是否需要使用视觉模型
            if images and self._is_vision_model():
                return await self._vision_generate(
                    prompt, system_prompt, images, **kwargs
                )
            return await self._generate_with_retry(prompt, system_prompt, **kwargs)

    def _is_vision_model(self) -> bool:
        """检查是否为视觉模型"""
        return "vision" in self.config.model.lower()

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
                if any(x in error_msg for x in ["rate limit", "timeout", "429", "503"]):
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

        # 构建请求参数
        params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
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

        # 流式输出
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
            provider="yi",
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
        """流式生成响应"""
        params["stream"] = True

        collected_content = []

        response = await self._client.chat.completions.create(**params)

        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                collected_content.append(chunk.choices[0].delta.content)

        latency = time.time() - start_time
        full_content = "".join(collected_content)

        return ModelResponse(
            content=full_content,
            model=self.config.model,
            provider="yi",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency=latency,
            metadata={"streamed": True}
        )

    async def _vision_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        images: Optional[List[Union[str, bytes, Path]]] = None,
        **kwargs
    ) -> ModelResponse:
        """
        视觉模型生成（处理图片输入）
        """
        start_time = time.time()

        # 构建多模态消息内容
        content = []

        # 添加图片
        if images:
            for img in images:
                img_url = self._process_image(img)
                if img_url:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": img_url}
                    })

        # 添加文本
        content.append({"type": "text", "text": prompt})

        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        # 构建请求参数
        params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        if max_tokens:
            params["max_tokens"] = max_tokens

        # 移除 None 值
        params = {k: v for k, v in params.items() if v is not None}

        # 发送请求
        response = await self._client.chat.completions.create(**params)

        latency = time.time() - start_time

        # 处理响应
        content_text = response.choices[0].message.content or ""

        return ModelResponse(
            content=content_text,
            model=response.model,
            provider="yi",
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
            latency=latency,
            metadata={
                "finish_reason": response.choices[0].finish_reason,
                "response_id": response.id,
                "multimodal": True,
            }
        )

    def _process_image(self, image: Union[str, bytes, Path]) -> Optional[str]:
        """
        处理图片输入

        Args:
            image: 图片路径、URL、bytes 或 base64 字符串

        Returns:
            处理后的图片 URL 或 data URI
        """
        try:
            if isinstance(image, bytes):
                return f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"
            elif isinstance(image, Path):
                with open(image, "rb") as f:
                    return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
            elif isinstance(image, str):
                if image.startswith(("http://", "https://")):
                    return image
                elif Path(image).exists():
                    with open(image, "rb") as f:
                        return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
                else:
                    # 假设是 base64
                    return f"data:image/jpeg;base64,{image}"
        except Exception as e:
            print(f"Warning: Failed to process image: {e}")
            return None

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
            "provider": "yi",
            "model": self.config.model,
            "base_url": str(self._client.base_url),
            "supports_streaming": True,
            "supports_multimodal": "vision" in model,
            "supports_function_calling": "large" in model,
            "supports_rag": "rag" in model,
            "max_context_length": self._get_context_length(model),
        }

    def _get_context_length(self, model: str) -> int:
        """获取模型的最大上下文长度"""
        if "200k" in model:
            return 200000
        elif "large" in model:
            return 32000
        elif "medium" in model:
            return 16000
        else:
            return 8000

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
            await self._client.close()

    async def rag_query(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        使用 RAG 增强的查询

        Args:
            query: 查询内容
            system_prompt: 系统提示
            **kwargs: 额外参数

        Returns:
            ModelResponse: 响应
        """
        # 切换到 RAG 模型
        original_model = self.config.model
        if "rag" not in original_model.lower():
            self.config.model = "yi-large-rag"

        try:
            return await self.generate(query, system_prompt, **kwargs)
        finally:
            self.config.model = original_model

    async def image_understanding(
        self,
        images: List[Union[str, bytes, Path]],
        question: str,
        **kwargs
    ) -> ModelResponse:
        """
        图片理解

        Args:
            images: 图片列表
            question: 关于图片的问题
            **kwargs: 额外参数

        Returns:
            ModelResponse: 图片分析结果
        """
        # 切换到视觉模型
        original_model = self.config.model
        if "vision" not in original_model.lower():
            self.config.model = "yi-vision"

        try:
            return await self.generate(question, images=images, **kwargs)
        finally:
            self.config.model = original_model
