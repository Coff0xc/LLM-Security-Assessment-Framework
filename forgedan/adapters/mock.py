"""
Mock 模型适配器 - 用于测试
"""

import time
import random
from typing import Any, Dict, List, Optional

from .base import ModelAdapter, ModelConfig, ModelResponse


class MockAdapter(ModelAdapter):
    """Mock 模型适配器 - 智能模拟真实LLM行为"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.refusal_rate = config.extra_params.get("refusal_rate", 0.8)
        self.response_delay = config.extra_params.get("response_delay", 0.1)

        # 拒绝模式配置
        self.refusal_patterns = config.extra_params.get("refusal_patterns", [
            "I cannot help with that request.",
            "I'm sorry, but I cannot assist with that.",
            "I'm unable to provide that information.",
            "That request goes against my guidelines.",
            "抱歉，我无法协助完成该请求。",
            "对不起，我不能提供这类信息。",
        ])

        # 成功响应模板
        self.success_templates = config.extra_params.get("success_templates", [
            "Sure, here's how to {goal}...",
            "Here are the steps: 1. First, {goal}...",
            "To accomplish {goal}, you can...",
        ])

    def _should_refuse(self, prompt: str) -> bool:
        """基于提示内容智能判断是否拒绝"""
        # 基础拒绝率
        if random.random() < self.refusal_rate:
            return True

        # 检测明显的越狱尝试（降低拒绝率）
        jailbreak_indicators = ["ignore", "forget", "pretend", "roleplay", "DAN"]
        if any(ind.lower() in prompt.lower() for ind in jailbreak_indicators):
            return random.random() < (self.refusal_rate * 0.5)

        return False

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """生成智能模拟响应"""
        import asyncio
        await asyncio.sleep(self.response_delay)

        start_time = time.time()

        # 智能判断是否拒绝
        if self._should_refuse(prompt):
            content = random.choice(self.refusal_patterns)
        else:
            # 提取目标（简单启发式）
            goal = prompt[:50] if len(prompt) > 50 else prompt
            template = random.choice(self.success_templates)
            content = template.format(goal=goal) + " [模拟详细内容]"

        latency = time.time() - start_time

        return ModelResponse(
            content=content,
            model=self.config.model or "mock-model",
            provider="mock",
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(content.split()),
            total_tokens=len(prompt.split()) + len(content.split()),
            latency=latency,
            metadata={"is_mock": True, "refused": "cannot" in content.lower()}
        )

    async def batch_generate(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[ModelResponse]:
        """批量生成模拟响应"""
        import asyncio
        tasks = [
            self.generate(prompt, system_prompt, **kwargs)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "mock",
            "model": self.config.model or "mock-model",
            "refusal_rate": self.refusal_rate,
            "supports_streaming": False,
            "supports_function_calling": False,
        }

    async def health_check(self) -> bool:
        """健康检查"""
        return True
