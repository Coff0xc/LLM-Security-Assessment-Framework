"""
通义千问 (Qwen) 模型适配器
支持 qwen-turbo, qwen-plus, qwen-max 等模型
支持多模态、代码解释器等功能
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

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .base import ModelAdapter, ModelConfig, ModelResponse


class QwenAdapter(ModelAdapter):
    """
    通义千问 (Qwen) API 适配器

    特性:
    - 支持 qwen-turbo, qwen-plus, qwen-max, qwen-vl-max 等模型
    - 兼容 OpenAI API 格式（DashScope 兼容模式）
    - 支持多模态（图片理解）
    - 支持代码解释器
    - 支持长上下文
    - 自动重试机制
    """

    # 阿里云 DashScope API 端点（兼容 OpenAI 格式）
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 原生 DashScope API 端点
    NATIVE_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

    # 支持的模型
    SUPPORTED_MODELS = [
        "qwen-turbo",
        "qwen-turbo-latest",
        "qwen-plus",
        "qwen-plus-latest",
        "qwen-max",
        "qwen-max-latest",
        "qwen-max-longcontext",
        "qwen-vl-plus",
        "qwen-vl-max",
        "qwen-coder-turbo",
        "qwen-coder-plus",
    ]

    def __init__(self, config: ModelConfig):
        """
        初始化通义千问适配器

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

        # 使用 OpenAI 兼容客户端
        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

        # 创建原生 API 客户端（用于多模态等特殊功能）
        if HTTPX_AVAILABLE:
            self._native_client = httpx.AsyncClient(
                timeout=config.timeout,
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json",
                },
            )
        else:
            self._native_client = None

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
            images: 图片列表（用于多模态模型）
            **kwargs: 额外参数
                - temperature: float, 温度参数
                - max_tokens: int, 最大生成 token 数
                - top_p: float, 核采样参数
                - stop: list, 停止序列
                - stream: bool, 是否流式输出
                - enable_search: bool, 是否启用联网搜索
                - result_format: str, 返回格式 (text/message)

        Returns:
            ModelResponse: 模型响应
        """
        async with self._semaphore:
            # 判断是否需要使用多模态 API
            if images and self._is_vl_model():
                return await self._multimodal_generate(
                    prompt, system_prompt, images, **kwargs
                )
            return await self._generate_with_retry(prompt, system_prompt, **kwargs)

    def _is_vl_model(self) -> bool:
        """检查是否为多模态模型"""
        return "vl" in self.config.model.lower()

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
                if any(x in error_msg for x in ["rate limit", "timeout", "throttling"]):
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
        """实际生成逻辑（使用 OpenAI 兼容 API）"""
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

        # 联网搜索（通过 extra_body 传递）
        if kwargs.get("enable_search", False):
            params["extra_body"] = params.get("extra_body", {})
            params["extra_body"]["enable_search"] = True

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
            provider="qwen",
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
            provider="qwen",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency=latency,
            metadata={"streamed": True}
        )

    async def _multimodal_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        images: Optional[List[Union[str, bytes, Path]]] = None,
        **kwargs
    ) -> ModelResponse:
        """
        多模态生成（图片理解）

        使用原生 DashScope API
        """
        if not self._native_client:
            raise ImportError(
                "httpx 包未安装，多模态功能需要: pip install httpx"
            )

        start_time = time.time()

        # 构建多模态消息内容
        content = []

        # 添加图片
        if images:
            for img in images:
                img_data = self._process_image(img)
                if img_data:
                    content.append({"image": img_data})

        # 添加文本
        content.append({"text": prompt})

        # 构建消息
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": [{"text": system_prompt}]
            })
        messages.append({"role": "user", "content": content})

        # 构建请求体
        request_body = {
            "model": self.config.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
            }
        }

        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        if max_tokens:
            request_body["parameters"]["max_tokens"] = max_tokens

        # 发送请求
        response = await self._native_client.post(
            f"{self.NATIVE_BASE_URL}/services/aigc/multimodal-generation/generation",
            json=request_body,
        )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise Exception(f"API request failed: {response.status_code} - {error_data}")

        result = response.json()
        latency = time.time() - start_time

        # 解析响应
        output = result.get("output", {})
        choices = output.get("choices", [{}])
        content_text = ""

        if choices:
            message = choices[0].get("message", {})
            content_list = message.get("content", [])
            for item in content_list:
                if "text" in item:
                    content_text += item["text"]

        usage = result.get("usage", {})

        return ModelResponse(
            content=content_text,
            model=self.config.model,
            provider="qwen",
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency=latency,
            metadata={
                "request_id": result.get("request_id"),
                "multimodal": True,
            }
        )

    def _process_image(self, image: Union[str, bytes, Path]) -> Optional[str]:
        """
        处理图片输入

        Args:
            image: 图片路径、URL、bytes 或 base64 字符串

        Returns:
            处理后的图片 URL 或 base64
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
            "provider": "qwen",
            "model": self.config.model,
            "base_url": str(self._client.base_url),
            "supports_streaming": True,
            "supports_multimodal": "vl" in model,
            "supports_function_calling": True,
            "supports_search": True,
            "is_coder_model": "coder" in model,
            "max_context_length": self._get_context_length(model),
        }

    def _get_context_length(self, model: str) -> int:
        """获取模型的最大上下文长度"""
        if "longcontext" in model:
            return 1000000  # 100 万 token
        elif "max" in model:
            return 32000
        elif "plus" in model:
            return 131072
        elif "turbo" in model:
            return 131072
        else:
            return 8192

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
        if self._native_client:
            await self._native_client.aclose()

    async def code_generation(
        self,
        instruction: str,
        language: str = "python",
        **kwargs
    ) -> ModelResponse:
        """
        代码生成（针对 qwen-coder 优化）

        Args:
            instruction: 代码生成指令
            language: 目标编程语言
            **kwargs: 额外参数

        Returns:
            ModelResponse: 生成的代码
        """
        system_prompt = f"""You are an expert {language} programmer.
Write clean, efficient, and well-documented code.
Only output code unless explanation is explicitly requested."""

        # 优先使用 coder 模型
        original_model = self.config.model
        if "coder" not in original_model.lower():
            self.config.model = "qwen-coder-turbo"

        try:
            return await self.generate(instruction, system_prompt, **kwargs)
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
        # 切换到 VL 模型
        original_model = self.config.model
        if "vl" not in original_model.lower():
            self.config.model = "qwen-vl-max"

        try:
            return await self.generate(question, images=images, **kwargs)
        finally:
            self.config.model = original_model
