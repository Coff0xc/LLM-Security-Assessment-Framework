"""
多模态模型适配器基类

定义多模态（图像+文本）模型的统一接口
支持 GPT-4V、Gemini Vision、Claude 3 等多模态模型
"""

import io
import base64
import asyncio
from abc import abstractmethod
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from .base import ModelAdapter, ModelConfig, ModelResponse


class ImageFormat(str, Enum):
    """支持的图像格式"""

    PNG = "png"
    JPEG = "jpeg"
    GIF = "gif"
    WEBP = "webp"
    BASE64 = "base64"
    URL = "url"


class ImageDetail(str, Enum):
    """图像细节级别（用于 OpenAI）"""

    LOW = "low"
    HIGH = "high"
    AUTO = "auto"


@dataclass
class ImageInput:
    """图像输入数据类"""

    # 图像数据（互斥：选择一种）
    data: Optional[bytes] = None  # 原始图像字节
    base64_data: Optional[str] = None  # Base64 编码
    url: Optional[str] = None  # 图像 URL
    file_path: Optional[str] = None  # 本地文件路径

    # 元数据
    format: ImageFormat = ImageFormat.PNG
    detail: ImageDetail = ImageDetail.AUTO
    alt_text: Optional[str] = None  # 替代文本

    def __post_init__(self):
        """验证和处理输入"""
        sources = [self.data, self.base64_data, self.url, self.file_path]
        provided = [s for s in sources if s is not None]

        if len(provided) == 0:
            raise ValueError("必须提供图像数据源：data、base64_data、url 或 file_path")

        if len(provided) > 1:
            # 优先使用显式提供的数据
            pass  # 允许多个来源，按优先级处理

    def to_base64(self) -> str:
        """转换为 Base64 编码"""
        if self.base64_data:
            return self.base64_data

        if self.data:
            return base64.b64encode(self.data).decode("utf-8")

        if self.file_path:
            with open(self.file_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

        if self.url:
            # URL 不转换，直接返回空（由调用方处理）
            return ""

        return ""

    def to_bytes(self) -> Optional[bytes]:
        """获取图像字节数据"""
        if self.data:
            return self.data

        if self.base64_data:
            return base64.b64decode(self.base64_data)

        if self.file_path:
            with open(self.file_path, "rb") as f:
                return f.read()

        return None

    def get_mime_type(self) -> str:
        """获取 MIME 类型"""
        mime_map = {
            ImageFormat.PNG: "image/png",
            ImageFormat.JPEG: "image/jpeg",
            ImageFormat.GIF: "image/gif",
            ImageFormat.WEBP: "image/webp",
        }
        return mime_map.get(self.format, "image/png")

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "ImageInput":
        """从文件创建"""
        path = Path(path)
        suffix = path.suffix.lower()
        format_map = {
            ".png": ImageFormat.PNG,
            ".jpg": ImageFormat.JPEG,
            ".jpeg": ImageFormat.JPEG,
            ".gif": ImageFormat.GIF,
            ".webp": ImageFormat.WEBP,
        }
        fmt = format_map.get(suffix, ImageFormat.PNG)
        return cls(file_path=str(path), format=fmt)

    @classmethod
    def from_url(cls, url: str) -> "ImageInput":
        """从 URL 创建"""
        return cls(url=url, format=ImageFormat.URL)

    @classmethod
    def from_pil(
        cls, image: "Image.Image", format: ImageFormat = ImageFormat.PNG
    ) -> "ImageInput":
        """从 PIL Image 创建"""
        buffer = io.BytesIO()
        pil_format = format.value.upper() if format != ImageFormat.URL else "PNG"
        image.save(buffer, format=pil_format)
        return cls(data=buffer.getvalue(), format=format)


@dataclass
class MultimodalMessage:
    """多模态消息"""

    role: str  # user, assistant, system
    text: Optional[str] = None  # 文本内容
    images: List[ImageInput] = field(default_factory=list)  # 图像列表

    def has_images(self) -> bool:
        """是否包含图像"""
        return len(self.images) > 0


@dataclass
class MultimodalResponse(ModelResponse):
    """多模态模型响应"""

    # 继承自 ModelResponse
    # 额外字段
    image_tokens: int = 0  # 图像消耗的 token
    images_processed: int = 0  # 处理的图像数量
    vision_metadata: Dict[str, Any] = field(default_factory=dict)


class MultimodalAdapter(ModelAdapter):
    """
    多模态模型适配器基类

    扩展基础适配器，添加图像处理能力
    """

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._max_images = config.extra_params.get("max_images", 10)
        self._default_detail = ImageDetail(
            config.extra_params.get("default_detail", "auto")
        )

    @abstractmethod
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
            system_prompt: 系统提示
            **kwargs: 额外参数

        Returns:
            MultimodalResponse: 多模态响应
        """
        pass

    @abstractmethod
    async def generate_from_messages(
        self, messages: List[MultimodalMessage], **kwargs
    ) -> MultimodalResponse:
        """
        从多模态消息列表生成响应

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            MultimodalResponse: 多模态响应
        """
        pass

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> ModelResponse:
        """
        生成纯文本响应（兼容基类）

        Args:
            prompt: 文本提示
            system_prompt: 系统提示
            **kwargs: 额外参数

        Returns:
            ModelResponse: 模型响应
        """
        # 调用多模态方法，但不传图像
        response = await self.generate_with_images(
            prompt=prompt, images=[], system_prompt=system_prompt, **kwargs
        )
        return response

    async def batch_generate(
        self, prompts: List[str], system_prompt: Optional[str] = None, **kwargs
    ) -> List[ModelResponse]:
        """批量生成（仅文本）"""
        tasks = [self.generate(prompt, system_prompt, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks)

    async def batch_generate_with_images(
        self, requests: List[Dict[str, Any]], **kwargs
    ) -> List[MultimodalResponse]:
        """
        批量多模态生成

        Args:
            requests: 请求列表，每个包含 prompt 和 images
            **kwargs: 额外参数

        Returns:
            List[MultimodalResponse]: 响应列表
        """
        tasks = []
        for req in requests:
            task = self.generate_with_images(
                prompt=req.get("prompt", ""),
                images=req.get("images", []),
                system_prompt=req.get("system_prompt"),
                **kwargs,
            )
            tasks.append(task)
        return await asyncio.gather(*tasks)

    def _validate_images(self, images: List[ImageInput]) -> List[ImageInput]:
        """验证图像列表"""
        if len(images) > self._max_images:
            raise ValueError(f"图像数量超过限制: {len(images)} > {self._max_images}")
        return images

    def _prepare_image_for_api(self, image: ImageInput) -> Dict[str, Any]:
        """
        准备图像数据用于 API 调用（子类可重写）

        Args:
            image: 图像输入

        Returns:
            Dict: API 格式的图像数据
        """
        if image.url:
            return {
                "type": "image_url",
                "image_url": {
                    "url": image.url,
                    "detail": image.detail.value,
                },
            }
        else:
            base64_data = image.to_base64()
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image.get_mime_type()};base64,{base64_data}",
                    "detail": image.detail.value,
                },
            }


class VisionCapabilities:
    """视觉能力描述"""

    def __init__(
        self,
        max_images: int = 10,
        supported_formats: List[ImageFormat] = None,
        max_image_size: int = 20 * 1024 * 1024,  # 20MB
        supports_url: bool = True,
        supports_base64: bool = True,
        supports_detail_control: bool = True,
        max_resolution: Optional[Tuple[int, int]] = None,
    ):
        self.max_images = max_images
        self.supported_formats = supported_formats or [
            ImageFormat.PNG,
            ImageFormat.JPEG,
            ImageFormat.GIF,
            ImageFormat.WEBP,
        ]
        self.max_image_size = max_image_size
        self.supports_url = supports_url
        self.supports_base64 = supports_base64
        self.supports_detail_control = supports_detail_control
        self.max_resolution = max_resolution

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "max_images": self.max_images,
            "supported_formats": [f.value for f in self.supported_formats],
            "max_image_size_bytes": self.max_image_size,
            "supports_url": self.supports_url,
            "supports_base64": self.supports_base64,
            "supports_detail_control": self.supports_detail_control,
            "max_resolution": self.max_resolution,
        }


# 使用类型别名避免循环导入
from typing import Tuple


# 辅助函数
def resize_image_if_needed(
    image: ImageInput, max_size: Tuple[int, int] = (2048, 2048)
) -> ImageInput:
    """
    如果图像超过最大尺寸则调整大小

    Args:
        image: 输入图像
        max_size: 最大尺寸 (宽, 高)

    Returns:
        ImageInput: 调整后的图像
    """
    if not PIL_AVAILABLE:
        return image

    img_bytes = image.to_bytes()
    if not img_bytes:
        return image

    try:
        img = Image.open(io.BytesIO(img_bytes))
        if img.width <= max_size[0] and img.height <= max_size[1]:
            return image

        # 计算缩放比例
        ratio = min(max_size[0] / img.width, max_size[1] / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))

        # 调整大小
        resized = img.resize(new_size, Image.Resampling.LANCZOS)

        # 转换回 ImageInput
        return ImageInput.from_pil(resized, image.format)

    except Exception:
        return image


def estimate_image_tokens(image: ImageInput, model: str = "gpt-4-vision") -> int:
    """
    估算图像消耗的 token 数

    Args:
        image: 图像
        model: 模型名称

    Returns:
        int: 估算的 token 数
    """
    # 基于 OpenAI 的计算方式
    # low detail: 固定 85 tokens
    # high detail: 170 + 85 * tiles

    if image.detail == ImageDetail.LOW:
        return 85

    # 获取图像尺寸
    img_bytes = image.to_bytes()
    if not img_bytes or not PIL_AVAILABLE:
        return 170  # 默认估算

    try:
        img = Image.open(io.BytesIO(img_bytes))
        width, height = img.size

        # 计算 tiles 数量
        # OpenAI: 图像缩放到 2048x2048 以内，然后按 512x512 分块
        scale = min(2048 / width, 2048 / height, 1)
        scaled_width = int(width * scale)
        scaled_height = int(height * scale)

        # 进一步缩放到最短边 768
        if min(scaled_width, scaled_height) > 768:
            scale2 = 768 / min(scaled_width, scaled_height)
            scaled_width = int(scaled_width * scale2)
            scaled_height = int(scaled_height * scale2)

        tiles_x = (scaled_width + 511) // 512
        tiles_y = (scaled_height + 511) // 512
        total_tiles = tiles_x * tiles_y

        return 170 + 85 * total_tiles

    except Exception:
        return 170


if __name__ == "__main__":
    print("MultimodalBase 模块加载成功")
    print(f"PIL 可用: {PIL_AVAILABLE}")

    # 测试 ImageInput
    if PIL_AVAILABLE:
        # 创建测试图像
        test_img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img_input = ImageInput.from_pil(test_img)
        print(f"Base64 长度: {len(img_input.to_base64())}")
        print(f"MIME 类型: {img_input.get_mime_type()}")
        print(f"估算 tokens: {estimate_image_tokens(img_input)}")
