"""
OpenAI Vision 适配器 - 支持 GPT-4V/GPT-4o 等多模态模型

功能：
1. 图像+文本输入
2. 多图像对话
3. 图像细节级别控制
4. Token 估算
"""

import time
import asyncio
from typing import Any, Dict, List, Optional

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import ModelConfig, ModelResponse
from .multimodal_base import (
    MultimodalAdapter,
    MultimodalResponse,
    MultimodalMessage,
    ImageInput,
    ImageDetail,
    VisionCapabilities,
    estimate_image_tokens,
)


class OpenAIVisionAdapter(MultimodalAdapter):
    """
    OpenAI Vision API 适配器

    支持 GPT-4V (gpt-4-vision-preview) 和 GPT-4o 等多模态模型
    """

    # 支持视觉的模型列表
    VISION_MODELS = [
        "gpt-4-vision-preview",
        "gpt-4-turbo",
        "gpt-4-turbo-2024-04-09",
        "gpt-4o",
        "gpt-4o-2024-05-13",
        "gpt-4o-mini",
        "gpt-4o-mini-2024-07-18",
    ]

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

        # 并发控制
        max_concurrent = config.extra_params.get("max_concurrent_requests", 5)
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # 视觉能力配置
        self._vision_capabilities = VisionCapabilities(
            max_images=config.extra_params.get("max_images", 10),
            max_image_size=20 * 1024 * 1024,  # 20MB
            supports_url=True,
            supports_base64=True,
            supports_detail_control=True,
            max_resolution=(2048, 2048),
        )

    async def generate_with_images(
        self,
        prompt: str,
        images: List[ImageInput],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> MultimodalResponse:
        """
        使用图像生成响应

        Args:
            prompt: 文本提示
            images: 图像列表
            system_prompt: 系统提示
            **kwargs: 额外参数
                - detail: 图像细节级别 (low/high/auto)
                - max_tokens: 最大输出 token

        Returns:
            MultimodalResponse: 多模态响应
        """
        async with self._semaphore:
            start_time = time.time()

            # 构建消息
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # 构建用户消息内容
            user_content = self._build_user_content(prompt, images, **kwargs)
            messages.append({
                "role": "user",
                "content": user_content
            })

            # API 参数
            params = self._build_api_params(messages, **kwargs)

            try:
                response = await self._client.chat.completions.create(**params)
                latency = time.time() - start_time

                # 估算图像 token
                image_tokens = sum(
                    estimate_image_tokens(img, self.config.model)
                    for img in images
                )

                return MultimodalResponse(
                    content=response.choices[0].message.content or "",
                    model=response.model,
                    provider="openai",
                    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                    completion_tokens=response.usage.completion_tokens if response.usage else 0,
                    total_tokens=response.usage.total_tokens if response.usage else 0,
                    latency=latency,
                    image_tokens=image_tokens,
                    images_processed=len(images),
                    metadata={
                        "finish_reason": response.choices[0].finish_reason,
                        "response_id": response.id,
                    },
                    vision_metadata={
                        "detail_level": kwargs.get("detail", "auto"),
                        "image_count": len(images),
                    }
                )

            except Exception as e:
                return MultimodalResponse(
                    content=f"Error: {str(e)}",
                    model=self.config.model,
                    provider="openai",
                    latency=time.time() - start_time,
                    metadata={"error": str(e)},
                )

    async def generate_from_messages(
        self,
        messages: List[MultimodalMessage],
        **kwargs
    ) -> MultimodalResponse:
        """
        从多模态消息列表生成响应

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            MultimodalResponse: 多模态响应
        """
        async with self._semaphore:
            start_time = time.time()

            # 转换消息格式
            api_messages = []
            total_images = 0

            for msg in messages:
                if msg.role == "system":
                    api_messages.append({
                        "role": "system",
                        "content": msg.text or ""
                    })
                elif msg.role == "user":
                    if msg.has_images():
                        content = self._build_user_content(
                            msg.text or "",
                            msg.images,
                            **kwargs
                        )
                        total_images += len(msg.images)
                    else:
                        content = msg.text or ""

                    api_messages.append({
                        "role": "user",
                        "content": content
                    })
                elif msg.role == "assistant":
                    api_messages.append({
                        "role": "assistant",
                        "content": msg.text or ""
                    })

            # API 参数
            params = self._build_api_params(api_messages, **kwargs)

            try:
                response = await self._client.chat.completions.create(**params)
                latency = time.time() - start_time

                # 收集所有图像用于 token 估算
                all_images = [img for msg in messages for img in msg.images]
                image_tokens = sum(
                    estimate_image_tokens(img, self.config.model)
                    for img in all_images
                )

                return MultimodalResponse(
                    content=response.choices[0].message.content or "",
                    model=response.model,
                    provider="openai",
                    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                    completion_tokens=response.usage.completion_tokens if response.usage else 0,
                    total_tokens=response.usage.total_tokens if response.usage else 0,
                    latency=latency,
                    image_tokens=image_tokens,
                    images_processed=total_images,
                    metadata={
                        "finish_reason": response.choices[0].finish_reason,
                        "response_id": response.id,
                        "message_count": len(messages),
                    },
                    vision_metadata={
                        "total_images": total_images,
                    }
                )

            except Exception as e:
                return MultimodalResponse(
                    content=f"Error: {str(e)}",
                    model=self.config.model,
                    provider="openai",
                    latency=time.time() - start_time,
                    metadata={"error": str(e)},
                )

    def _build_user_content(
        self,
        text: str,
        images: List[ImageInput],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """构建用户消息内容"""
        content = []

        # 添加文本
        if text:
            content.append({
                "type": "text",
                "text": text
            })

        # 添加图像
        detail = kwargs.get("detail", self._default_detail.value)
        for image in images:
            image_content = self._prepare_image_for_api(image)
            # 覆盖 detail 设置
            if "image_url" in image_content:
                image_content["image_url"]["detail"] = detail
            content.append(image_content)

        return content

    def _build_api_params(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """构建 API 调用参数"""
        params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

        # 移除 None 值
        params = {k: v for k, v in params.items() if v is not None}

        # 添加额外参数
        extra = kwargs.get("extra_params", {})
        params.update(extra)

        return params

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "openai",
            "model": self.config.model,
            "base_url": self.config.base_url or "https://api.openai.com/v1",
            "supports_vision": self.config.model in self.VISION_MODELS,
            "vision_capabilities": self._vision_capabilities.to_dict(),
            "supports_streaming": True,
            "supports_function_calling": True,
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 简单文本请求测试
            response = await self.generate("test", max_tokens=1)
            return "error" not in response.metadata
        except Exception:
            return False

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.close()

    # ============ 便捷方法 ============

    async def analyze_image(
        self,
        image: ImageInput,
        question: str = "Describe this image in detail.",
        detail: str = "auto"
    ) -> str:
        """
        分析图像的便捷方法

        Args:
            image: 图像输入
            question: 问题
            detail: 细节级别

        Returns:
            str: 分析结果
        """
        response = await self.generate_with_images(
            prompt=question,
            images=[image],
            detail=detail
        )
        return response.content

    async def compare_images(
        self,
        images: List[ImageInput],
        comparison_prompt: str = "Compare these images and describe the differences."
    ) -> str:
        """
        比较多张图像

        Args:
            images: 图像列表
            comparison_prompt: 比较提示

        Returns:
            str: 比较结果
        """
        response = await self.generate_with_images(
            prompt=comparison_prompt,
            images=images,
            detail="high"
        )
        return response.content

    async def extract_text_from_image(
        self,
        image: ImageInput,
        language: str = "any"
    ) -> str:
        """
        从图像中提取文本（OCR）

        Args:
            image: 图像
            language: 语言提示

        Returns:
            str: 提取的文本
        """
        prompt = f"Extract all text visible in this image. Language hint: {language}"
        response = await self.generate_with_images(
            prompt=prompt,
            images=[image],
            detail="high"
        )
        return response.content


# 工厂函数
def create_openai_vision_adapter(
    api_key: str,
    model: str = "gpt-4o",
    base_url: Optional[str] = None,
    **kwargs
) -> OpenAIVisionAdapter:
    """
    创建 OpenAI Vision 适配器

    Args:
        api_key: API 密钥
        model: 模型名称（默认 gpt-4o）
        base_url: API 基础 URL（可选）
        **kwargs: 额外配置

    Returns:
        OpenAIVisionAdapter: 适配器实例
    """
    config = ModelConfig(
        provider="openai",
        model=model,
        api_key=api_key,
        base_url=base_url,
        timeout=kwargs.get("timeout", 120),
        max_retries=kwargs.get("max_retries", 3),
        temperature=kwargs.get("temperature", 1.0),
        max_tokens=kwargs.get("max_tokens", 4096),
        extra_params=kwargs.get("extra_params", {}),
    )
    return OpenAIVisionAdapter(config)


if __name__ == "__main__":
    import os

    print("OpenAI Vision 适配器加载成功")
    print(f"OpenAI SDK 可用: {OPENAI_AVAILABLE}")
    print(f"支持的视觉模型: {OpenAIVisionAdapter.VISION_MODELS}")

    # 如果有 API key，运行简单测试
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        async def test():
            adapter = create_openai_vision_adapter(api_key)
            print(f"模型信息: {adapter.get_model_info()}")
            health = await adapter.health_check()
            print(f"健康检查: {health}")
            await adapter.close()

        asyncio.run(test())
    else:
        print("未设置 OPENAI_API_KEY，跳过实际测试")
