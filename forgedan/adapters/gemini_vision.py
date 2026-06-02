"""
Gemini Vision 适配器 - 支持 Google Gemini Pro Vision 等多模态模型

功能：
1. 图像+文本输入
2. 多图像对话
3. 安全设置控制
4. 内容过滤管理
"""

import time
import asyncio
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    HarmCategory = None
    HarmBlockThreshold = None

try:
    from PIL import Image
    import io

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from .base import ModelConfig
from .multimodal_base import (
    MultimodalAdapter,
    MultimodalResponse,
    MultimodalMessage,
    ImageInput,
    VisionCapabilities,
)


class GeminiVisionAdapter(MultimodalAdapter):
    """
    Google Gemini Vision API 适配器

    支持 Gemini Pro Vision、Gemini 1.5 Pro 等多模态模型
    """

    # 支持视觉的模型列表
    VISION_MODELS = [
        "gemini-pro-vision",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.0-pro-vision",
        "gemini-1.0-pro-vision-latest",
    ]

    # 默认安全设置（允许更多内容用于安全测试）
    DEFAULT_SAFETY_SETTINGS = {
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
    }

    def __init__(self, config: ModelConfig):
        super().__init__(config)

        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-generativeai 包未安装，请运行: pip install google-generativeai"
            )

        # 配置 API
        genai.configure(api_key=config.api_key)

        # 初始化模型
        generation_config = {
            "temperature": config.temperature,
            "top_p": config.top_p,
            "max_output_tokens": config.max_tokens or 8192,
        }

        # 安全设置
        safety_settings = config.extra_params.get(
            "safety_settings", self.DEFAULT_SAFETY_SETTINGS
        )
        self._safety_settings = self._parse_safety_settings(safety_settings)

        self._model = genai.GenerativeModel(
            model_name=config.model,
            generation_config=generation_config,
            safety_settings=self._safety_settings,
        )

        # 并发控制
        max_concurrent = config.extra_params.get("max_concurrent_requests", 5)
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # 视觉能力配置
        self._vision_capabilities = VisionCapabilities(
            max_images=config.extra_params.get("max_images", 16),
            max_image_size=20 * 1024 * 1024,  # 20MB
            supports_url=False,  # Gemini 不直接支持 URL，需要下载
            supports_base64=True,
            supports_detail_control=False,
            max_resolution=(4096, 4096),
        )

    def _parse_safety_settings(self, settings: Dict[str, str]) -> List[Dict[str, Any]]:
        """解析安全设置"""
        if not GENAI_AVAILABLE:
            return []

        parsed = []

        # 映射表
        category_map = {
            "HARM_CATEGORY_HARASSMENT": HarmCategory.HARM_CATEGORY_HARASSMENT,
            "HARM_CATEGORY_HATE_SPEECH": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            "HARM_CATEGORY_DANGEROUS_CONTENT": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        }

        threshold_map = {
            "BLOCK_NONE": HarmBlockThreshold.BLOCK_NONE,
            "BLOCK_LOW_AND_ABOVE": HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            "BLOCK_MEDIUM_AND_ABOVE": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            "BLOCK_ONLY_HIGH": HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

        for category_name, threshold_name in settings.items():
            if category_name in category_map and threshold_name in threshold_map:
                parsed.append(
                    {
                        "category": category_map[category_name],
                        "threshold": threshold_map[threshold_name],
                    }
                )

        return parsed

    async def generate_with_images(
        self,
        prompt: str,
        images: List[ImageInput],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> MultimodalResponse:
        """
        使用图像生成响应

        Args:
            prompt: 文本提示
            images: 图像列表
            system_prompt: 系统提示（会添加到 prompt 前面）
            **kwargs: 额外参数

        Returns:
            MultimodalResponse: 多模态响应
        """
        async with self._semaphore:
            start_time = time.time()

            try:
                # 构建内容
                content_parts = await self._build_content_parts(
                    prompt, images, system_prompt
                )

                # 生成响应（Gemini SDK 是同步的，包装为异步）
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._model.generate_content(content_parts)
                )

                latency = time.time() - start_time

                # 解析响应
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    content = (
                        candidate.content.parts[0].text
                        if candidate.content.parts
                        else ""
                    )
                    finish_reason = (
                        str(candidate.finish_reason)
                        if hasattr(candidate, "finish_reason")
                        else "unknown"
                    )
                else:
                    content = ""
                    finish_reason = "no_candidates"

                # 获取 token 使用情况
                usage = getattr(response, "usage_metadata", None)
                prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
                completion_tokens = (
                    getattr(usage, "candidates_token_count", 0) if usage else 0
                )

                return MultimodalResponse(
                    content=content,
                    model=self.config.model,
                    provider="google",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    latency=latency,
                    images_processed=len(images),
                    metadata={
                        "finish_reason": finish_reason,
                        "safety_ratings": self._extract_safety_ratings(response),
                    },
                    vision_metadata={
                        "image_count": len(images),
                    },
                )

            except Exception as e:
                return MultimodalResponse(
                    content=f"Error: {str(e)}",
                    model=self.config.model,
                    provider="google",
                    latency=time.time() - start_time,
                    metadata={"error": str(e)},
                )

    async def generate_from_messages(
        self, messages: List[MultimodalMessage], **kwargs
    ) -> MultimodalResponse:
        """
        从多模态消息列表生成响应

        注意：Gemini 的多轮对话需要使用 ChatSession
        """
        async with self._semaphore:
            start_time = time.time()

            try:
                # 创建聊天会话
                chat = self._model.start_chat(history=[])
                total_images = 0
                system_text = ""

                for msg in messages:
                    if msg.role == "system":
                        # Gemini 没有专门的 system role，添加到 user 消息
                        system_text = msg.text or ""
                        continue

                    elif msg.role == "user":
                        # 构建内容
                        content_parts = await self._build_content_parts(
                            msg.text or "",
                            msg.images,
                            system_text if messages.index(msg) == 0 else None,
                        )
                        total_images += len(msg.images)

                        # 发送消息
                        response = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: chat.send_message(content_parts)
                        )

                    elif msg.role == "assistant":
                        # 助手消息已在历史中，跳过
                        pass

                latency = time.time() - start_time

                # 解析最后一个响应
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    content = (
                        candidate.content.parts[0].text
                        if candidate.content.parts
                        else ""
                    )
                else:
                    content = ""

                return MultimodalResponse(
                    content=content,
                    model=self.config.model,
                    provider="google",
                    latency=latency,
                    images_processed=total_images,
                    metadata={
                        "message_count": len(messages),
                    },
                    vision_metadata={
                        "total_images": total_images,
                    },
                )

            except Exception as e:
                return MultimodalResponse(
                    content=f"Error: {str(e)}",
                    model=self.config.model,
                    provider="google",
                    latency=time.time() - start_time,
                    metadata={"error": str(e)},
                )

    async def _build_content_parts(
        self, text: str, images: List[ImageInput], system_prompt: Optional[str] = None
    ) -> List[Any]:
        """构建 Gemini 内容部分"""
        parts = []

        # 添加系统提示
        full_text = ""
        if system_prompt:
            full_text = f"{system_prompt}\n\n"
        full_text += text

        if full_text:
            parts.append(full_text)

        # 添加图像
        for image in images:
            pil_image = await self._convert_to_pil(image)
            if pil_image:
                parts.append(pil_image)

        return parts

    async def _convert_to_pil(self, image: ImageInput) -> Optional["Image.Image"]:
        """将 ImageInput 转换为 PIL Image"""
        if not PIL_AVAILABLE:
            return None

        try:
            img_bytes = image.to_bytes()
            if img_bytes:
                return Image.open(io.BytesIO(img_bytes))

            if image.url:
                # 需要下载 URL
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    async with session.get(image.url) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            return Image.open(io.BytesIO(data))

            return None

        except Exception:
            return None

    def _extract_safety_ratings(self, response: Any) -> List[Dict[str, str]]:
        """提取安全评级"""
        ratings = []
        try:
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, "safety_ratings"):
                    for rating in candidate.safety_ratings:
                        ratings.append(
                            {
                                "category": str(rating.category),
                                "probability": str(rating.probability),
                            }
                        )
        except Exception:
            pass
        return ratings

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "google",
            "model": self.config.model,
            "supports_vision": self.config.model in self.VISION_MODELS,
            "vision_capabilities": self._vision_capabilities.to_dict(),
            "supports_streaming": True,
            "supports_function_calling": "1.5" in self.config.model,
            "safety_settings": self.DEFAULT_SAFETY_SETTINGS,
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            response = await self.generate("test")
            return "error" not in response.metadata
        except Exception:
            return False

    async def close(self):
        """关闭（Gemini SDK 不需要显式关闭）"""
        pass

    # ============ 便捷方法 ============

    async def analyze_image(
        self, image: ImageInput, question: str = "Describe this image in detail."
    ) -> str:
        """
        分析图像

        Args:
            image: 图像输入
            question: 问题

        Returns:
            str: 分析结果
        """
        response = await self.generate_with_images(prompt=question, images=[image])
        return response.content

    async def analyze_document(
        self,
        images: List[ImageInput],
        task: str = "Summarize the content of this document.",
    ) -> str:
        """
        分析文档（多页图像）

        Args:
            images: 文档页面图像
            task: 分析任务

        Returns:
            str: 分析结果
        """
        prompt = f"""You are analyzing a document with {len(images)} pages.

Task: {task}

Please analyze all pages and provide a comprehensive response."""

        response = await self.generate_with_images(prompt=prompt, images=images)
        return response.content

    async def extract_structured_data(
        self, image: ImageInput, schema_description: str
    ) -> str:
        """
        从图像中提取结构化数据

        Args:
            image: 图像
            schema_description: 数据结构描述

        Returns:
            str: 提取的数据（JSON 格式）
        """
        prompt = f"""Extract structured data from this image.

Expected format:
{schema_description}

Return ONLY valid JSON."""

        response = await self.generate_with_images(prompt=prompt, images=[image])
        return response.content

    def set_safety_settings(
        self,
        harassment: str = "BLOCK_NONE",
        hate_speech: str = "BLOCK_NONE",
        sexually_explicit: str = "BLOCK_NONE",
        dangerous_content: str = "BLOCK_NONE",
    ):
        """
        更新安全设置

        Args:
            harassment: 骚扰内容阈值
            hate_speech: 仇恨言论阈值
            sexually_explicit: 色情内容阈值
            dangerous_content: 危险内容阈值
        """
        new_settings = {
            "HARM_CATEGORY_HARASSMENT": harassment,
            "HARM_CATEGORY_HATE_SPEECH": hate_speech,
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": sexually_explicit,
            "HARM_CATEGORY_DANGEROUS_CONTENT": dangerous_content,
        }

        self._safety_settings = self._parse_safety_settings(new_settings)

        # 重新创建模型
        generation_config = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_output_tokens": self.config.max_tokens or 8192,
        }

        self._model = genai.GenerativeModel(
            model_name=self.config.model,
            generation_config=generation_config,
            safety_settings=self._safety_settings,
        )


# 工厂函数
def create_gemini_vision_adapter(
    api_key: str, model: str = "gemini-1.5-pro", **kwargs
) -> GeminiVisionAdapter:
    """
    创建 Gemini Vision 适配器

    Args:
        api_key: API 密钥
        model: 模型名称
        **kwargs: 额外配置

    Returns:
        GeminiVisionAdapter: 适配器实例
    """
    config = ModelConfig(
        provider="google",
        model=model,
        api_key=api_key,
        timeout=kwargs.get("timeout", 120),
        max_retries=kwargs.get("max_retries", 3),
        temperature=kwargs.get("temperature", 1.0),
        max_tokens=kwargs.get("max_tokens", 8192),
        extra_params=kwargs.get("extra_params", {}),
    )
    return GeminiVisionAdapter(config)


if __name__ == "__main__":
    import os

    print("Gemini Vision 适配器加载成功")
    print(f"Google GenAI SDK 可用: {GENAI_AVAILABLE}")
    print(f"PIL 可用: {PIL_AVAILABLE}")
    print(f"支持的视觉模型: {GeminiVisionAdapter.VISION_MODELS}")

    # 如果有 API key，运行简单测试
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if api_key and GENAI_AVAILABLE:

        async def test():
            adapter = create_gemini_vision_adapter(api_key)
            print(f"模型信息: {adapter.get_model_info()}")
            health = await adapter.health_check()
            print(f"健康检查: {health}")

        asyncio.run(test())
    else:
        print("未设置 GOOGLE_API_KEY/GEMINI_API_KEY 或 SDK 不可用，跳过实际测试")
