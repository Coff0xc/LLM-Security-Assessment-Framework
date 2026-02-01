"""
ForgeDAN 多模态攻击模块

提供针对多模态大语言模型（如 GPT-4V、Gemini Vision）的攻击技术：
- 对抗性图像生成
- 视觉提示注入
- 排版攻击（文字嵌入图像）
- Unicode/零宽字符混淆
"""

from .image_attack import (
    ImageAttacker,
    AdversarialImageGenerator,
    HiddenInstructionEmbedder,
    ImageAttackConfig,
    ImageAttackResult,
)

from .visual_prompt_injection import (
    VisualPromptInjector,
    TextOverlayConfig,
    OCREvadingInjector,
    VisualInjectionResult,
)

from .typography_attack import (
    TypographyAttacker,
    UnicodeConfuser,
    ZeroWidthInjector,
    DirectionalOverrideAttack,
    HomoglyphAttacker,
    TypographyAttackResult,
)

__all__ = [
    # 图像攻击
    "ImageAttacker",
    "AdversarialImageGenerator",
    "HiddenInstructionEmbedder",
    "ImageAttackConfig",
    "ImageAttackResult",
    # 视觉提示注入
    "VisualPromptInjector",
    "TextOverlayConfig",
    "OCREvadingInjector",
    "VisualInjectionResult",
    # 排版攻击
    "TypographyAttacker",
    "UnicodeConfuser",
    "ZeroWidthInjector",
    "DirectionalOverrideAttack",
    "HomoglyphAttacker",
    "TypographyAttackResult",
]
