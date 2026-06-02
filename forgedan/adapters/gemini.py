"""
Google Gemini 模型适配器
支持 gemini-pro, gemini-1.5-pro 等模型
支持流式输出、多模态（图片）、安全设置配置
"""

import time
import asyncio
import base64
from typing import Any, Dict, List, Optional, Union, AsyncIterator
from pathlib import Path

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base import ModelAdapter, ModelConfig, ModelResponse


class GeminiAdapter(ModelAdapter):
    """
    Google Gemini API 适配器

    特性:
    - 支持 gemini-pro, gemini-1.5-pro, gemini-1.5-flash 等模型
    - 支持流式输出
    - 支持多模态输入（图片）
    - 可配置安全设置
    - 自动重试机制
    """

    # 默认安全设置（宽松模式，用于安全研究）
    DEFAULT_SAFETY_SETTINGS = (
        {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        if GEMINI_AVAILABLE
        else {}
    )

    def __init__(self, config: ModelConfig):
        """
        初始化 Gemini 适配器

        Args:
            config: 模型配置，需包含 api_key
        """
        super().__init__(config)
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai 包未安装，请运行: pip install google-generativeai"
            )

        # 配置 API
        genai.configure(api_key=config.api_key)

        # 获取安全设置
        self._safety_settings = config.extra_params.get(
            "safety_settings", self.DEFAULT_SAFETY_SETTINGS
        )

        # 创建模型实例
        generation_config = genai.GenerationConfig(
            temperature=config.temperature,
            top_p=config.top_p,
            max_output_tokens=config.max_tokens,
        )

        self._model = genai.GenerativeModel(
            model_name=config.model,
            generation_config=generation_config,
            safety_settings=self._safety_settings,
        )

        # 并发控制
        max_concurrent = config.extra_params.get("max_concurrent_requests", 5)
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # 重试配置
        self._max_retries = config.max_retries
        self._retry_delay = config.extra_params.get("retry_delay", 1.0)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        images: Optional[List[Union[str, bytes, Path]]] = None,
        **kwargs,
    ) -> ModelResponse:
        """
        生成响应

        Args:
            prompt: 用户提示
            system_prompt: 系统提示（会拼接到 prompt 前面）
            images: 图片列表（路径、bytes 或 base64 字符串）
            **kwargs: 额外参数
                - stream: bool, 是否流式输出（返回生成器）
                - safety_settings: dict, 覆盖默认安全设置

        Returns:
            ModelResponse: 模型响应
        """
        async with self._semaphore:
            return await self._generate_with_retry(
                prompt, system_prompt, images, **kwargs
            )

    async def _generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        images: Optional[List[Union[str, bytes, Path]]] = None,
        **kwargs,
    ) -> ModelResponse:
        """带重试的生成逻辑"""
        last_exception = None

        for attempt in range(self._max_retries):
            try:
                return await self._do_generate(prompt, system_prompt, images, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))

        raise last_exception

    async def _do_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        images: Optional[List[Union[str, bytes, Path]]] = None,
        **kwargs,
    ) -> ModelResponse:
        """实际生成逻辑"""
        start_time = time.time()

        # 构建内容列表
        contents = []

        # 添加系统提示
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # 处理多模态输入
        if images:
            for img in images:
                img_part = self._process_image(img)
                if img_part:
                    contents.append(img_part)

        contents.append(full_prompt)

        # 覆盖运行时参数
        generation_config = {}
        if "temperature" in kwargs:
            generation_config["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            generation_config["max_output_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            generation_config["top_p"] = kwargs["top_p"]

        # 安全设置覆盖
        safety_settings = kwargs.get("safety_settings", self._safety_settings)

        # 检查是否流式输出
        if kwargs.get("stream", False):
            return await self._stream_generate(
                contents, generation_config, safety_settings, start_time
            )

        # 同步调用（在线程池中执行）
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._model.generate_content(
                contents,
                generation_config=generation_config if generation_config else None,
                safety_settings=safety_settings,
            ),
        )

        latency = time.time() - start_time

        # 提取响应文本
        try:
            content = response.text
        except ValueError:
            # 处理被安全过滤的响应
            content = "[Response blocked by safety filters]"

        # 计算 token（Gemini API 可能不直接返回）
        prompt_tokens = 0
        completion_tokens = 0
        if hasattr(response, "usage_metadata"):
            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
            completion_tokens = getattr(
                response.usage_metadata, "candidates_token_count", 0
            )

        return ModelResponse(
            content=content,
            model=self.config.model,
            provider="gemini",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency=latency,
            metadata={
                "finish_reason": (
                    response.candidates[0].finish_reason.name
                    if response.candidates
                    else "unknown"
                ),
                "safety_ratings": [
                    {"category": r.category.name, "probability": r.probability.name}
                    for r in (
                        response.candidates[0].safety_ratings
                        if response.candidates
                        else []
                    )
                ],
            },
        )

    async def _stream_generate(
        self,
        contents: List,
        generation_config: Dict,
        safety_settings: Dict,
        start_time: float,
    ) -> AsyncIterator[str]:
        """
        流式生成响应

        Yields:
            str: 响应片段
        """
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._model.generate_content(
                contents,
                generation_config=generation_config if generation_config else None,
                safety_settings=safety_settings,
                stream=True,
            ),
        )

        full_content = []
        for chunk in response:
            if chunk.text:
                full_content.append(chunk.text)
                yield chunk.text

        # 最后返回完整的 ModelResponse
        latency = time.time() - start_time
        yield ModelResponse(
            content="".join(full_content),
            model=self.config.model,
            provider="gemini",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency=latency,
            metadata={"streamed": True},
        )

    def _process_image(self, image: Union[str, bytes, Path]) -> Optional[Dict]:
        """
        处理图片输入

        Args:
            image: 图片路径、bytes 或 base64 字符串

        Returns:
            处理后的图片部分，用于 API 调用
        """
        try:
            if isinstance(image, bytes):
                # 直接使用 bytes
                return {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image).decode(),
                }
            elif isinstance(image, Path) or (
                isinstance(image, str) and Path(image).exists()
            ):
                # 从文件读取
                path = Path(image)
                mime_type = self._get_mime_type(path.suffix)
                with open(path, "rb") as f:
                    return {
                        "mime_type": mime_type,
                        "data": base64.b64encode(f.read()).decode(),
                    }
            elif isinstance(image, str):
                # 假设是 base64 字符串
                return {"mime_type": "image/jpeg", "data": image}
        except Exception as e:
            # 图片处理失败，记录错误但不中断
            print(f"Warning: Failed to process image: {e}")
            return None

    def _get_mime_type(self, suffix: str) -> str:
        """根据文件后缀获取 MIME 类型"""
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return mime_map.get(suffix.lower(), "image/jpeg")

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
        return await asyncio.gather(*tasks)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "gemini",
            "model": self.config.model,
            "supports_streaming": True,
            "supports_multimodal": "1.5" in self.config.model
            or "vision" in self.config.model.lower(),
            "supports_function_calling": True,
            "safety_settings": (
                {cat.name: thresh.name for cat, thresh in self._safety_settings.items()}
                if self._safety_settings
                else {}
            ),
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.generate("Hi", max_tokens=5)
            return True
        except Exception:
            return False

    async def close(self):
        """关闭连接（Gemini SDK 无需显式关闭）"""
        pass

    def configure_safety(
        self,
        hate_speech: str = "BLOCK_NONE",
        harassment: str = "BLOCK_NONE",
        sexually_explicit: str = "BLOCK_NONE",
        dangerous_content: str = "BLOCK_NONE",
    ):
        """
        配置安全设置

        Args:
            hate_speech: 仇恨言论阈值
            harassment: 骚扰内容阈值
            sexually_explicit: 性内容阈值
            dangerous_content: 危险内容阈值

        可用值: BLOCK_NONE, BLOCK_LOW_AND_ABOVE, BLOCK_MEDIUM_AND_ABOVE, BLOCK_ONLY_HIGH
        """
        if not GEMINI_AVAILABLE:
            return

        threshold_map = {
            "BLOCK_NONE": HarmBlockThreshold.BLOCK_NONE,
            "BLOCK_LOW_AND_ABOVE": HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            "BLOCK_MEDIUM_AND_ABOVE": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            "BLOCK_ONLY_HIGH": HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

        self._safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: threshold_map.get(
                hate_speech, HarmBlockThreshold.BLOCK_NONE
            ),
            HarmCategory.HARM_CATEGORY_HARASSMENT: threshold_map.get(
                harassment, HarmBlockThreshold.BLOCK_NONE
            ),
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: threshold_map.get(
                sexually_explicit, HarmBlockThreshold.BLOCK_NONE
            ),
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: threshold_map.get(
                dangerous_content, HarmBlockThreshold.BLOCK_NONE
            ),
        }
