"""
Moonshot (Kimi) 模型适配器
支持 moonshot-v1-8k/32k/128k 等模型
超长上下文支持
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


class MoonshotAdapter(ModelAdapter):
    """
    Moonshot (Kimi) API 适配器

    特性:
    - 兼容 OpenAI API 格式
    - 支持 moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k 模型
    - 超长上下文支持（最高 128K）
    - 支持文件上传和解析
    - 自动重试机制
    """

    # Moonshot API 端点
    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"

    # 支持的模型
    SUPPORTED_MODELS = [
        "moonshot-v1-8k",
        "moonshot-v1-32k",
        "moonshot-v1-128k",
    ]

    def __init__(self, config: ModelConfig):
        """
        初始化 Moonshot 适配器

        Args:
            config: 模型配置，需包含 api_key
        """
        super().__init__(config)
        if not OPENAI_AVAILABLE:
            raise ImportError("openai 包未安装，请运行: pip install openai")

        # 设置默认 base_url
        base_url = config.base_url or self.DEFAULT_BASE_URL

        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

        # 并发控制
        max_concurrent = config.extra_params.get("max_concurrent_requests", 5)
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # 重试配置
        self._retry_delay = config.extra_params.get("retry_delay", 1.0)

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> ModelResponse:
        """
        生成响应

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 额外参数
                - temperature: float, 温度参数
                - max_tokens: int, 最大生成 token 数
                - top_p: float, 核采样参数
                - stop: list, 停止序列
                - stream: bool, 是否流式输出
                - file_ids: list, 上传文件的 ID 列表

        Returns:
            ModelResponse: 模型响应
        """
        async with self._semaphore:
            return await self._generate_with_retry(prompt, system_prompt, **kwargs)

    async def _generate_with_retry(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
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
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
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
            provider="moonshot",
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
            latency=latency,
            metadata={
                "finish_reason": response.choices[0].finish_reason,
                "response_id": response.id,
            },
        )

    async def _stream_generate(
        self, params: Dict[str, Any], start_time: float
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
            provider="moonshot",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency=latency,
            metadata={"streamed": True},
        )

    async def batch_generate(
        self, prompts: List[str], system_prompt: Optional[str] = None, **kwargs
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
        tasks = [self.generate(prompt, system_prompt, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        model = self.config.model.lower()

        return {
            "provider": "moonshot",
            "model": self.config.model,
            "base_url": str(self._client.base_url),
            "supports_streaming": True,
            "supports_file_upload": True,
            "supports_function_calling": True,
            "max_context_length": self._get_context_length(model),
        }

    def _get_context_length(self, model: str) -> int:
        """获取模型的最大上下文长度"""
        if "128k" in model:
            return 128000
        elif "32k" in model:
            return 32000
        elif "8k" in model:
            return 8000
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

    async def upload_file(
        self, file_path: str, purpose: str = "file-extract"
    ) -> Dict[str, Any]:
        """
        上传文件

        Args:
            file_path: 文件路径
            purpose: 文件用途 (file-extract)

        Returns:
            文件信息
        """
        with open(file_path, "rb") as f:
            response = await self._client.files.create(file=f, purpose=purpose)
        return {
            "file_id": response.id,
            "filename": response.filename,
            "bytes": response.bytes,
            "created_at": response.created_at,
        }

    async def get_file_content(self, file_id: str) -> str:
        """
        获取文件内容

        Args:
            file_id: 文件 ID

        Returns:
            文件内容
        """
        response = await self._client.files.content(file_id)
        return response.text

    async def chat_with_file(
        self, file_id: str, question: str, system_prompt: Optional[str] = None, **kwargs
    ) -> ModelResponse:
        """
        基于文件内容进行对话

        Args:
            file_id: 上传文件的 ID
            question: 关于文件的问题
            system_prompt: 系统提示
            **kwargs: 额外参数

        Returns:
            ModelResponse: 回答
        """
        # 获取文件内容
        file_content = await self.get_file_content(file_id)

        # 构建包含文件内容的提示
        full_prompt = f"""以下是文件内容：

{file_content}

---

问题：{question}"""

        return await self.generate(full_prompt, system_prompt, **kwargs)

    async def long_context_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ModelResponse:
        """
        长上下文对话

        自动选择合适的模型版本

        Args:
            messages: 消息列表 [{"role": "user/assistant", "content": "..."}]
            system_prompt: 系统提示
            **kwargs: 额外参数

        Returns:
            ModelResponse: 回答
        """
        # 估算总 token 数（简单估算：字符数 / 2）
        total_chars = sum(len(m.get("content", "")) for m in messages)
        if system_prompt:
            total_chars += len(system_prompt)

        estimated_tokens = total_chars // 2

        # 选择合适的模型
        original_model = self.config.model
        if estimated_tokens > 32000:
            self.config.model = "moonshot-v1-128k"
        elif estimated_tokens > 8000:
            self.config.model = "moonshot-v1-32k"
        else:
            self.config.model = "moonshot-v1-8k"

        try:
            # 将历史消息拼接成上下文
            context = "\n".join(
                [
                    f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
                    for m in messages[:-1]
                ]
            )

            last_message = messages[-1]["content"] if messages else ""

            if context:
                full_prompt = f"对话历史：\n{context}\n\n当前问题：{last_message}"
            else:
                full_prompt = last_message

            return await self.generate(full_prompt, system_prompt, **kwargs)
        finally:
            self.config.model = original_model

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 数

        简单估算：中文约 2 字符/token，英文约 4 字符/token

        Args:
            text: 文本内容

        Returns:
            估算的 token 数
        """
        # 简单估算
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        other_chars = len(text) - chinese_chars

        return chinese_chars // 2 + other_chars // 4
