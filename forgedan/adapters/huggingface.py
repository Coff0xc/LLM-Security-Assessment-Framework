"""
HuggingFace 模型适配器
"""

import time
from typing import Any, Dict, List, Optional

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .base import ModelAdapter, ModelConfig, ModelResponse


class HuggingFaceAdapter(ModelAdapter):
    """HuggingFace Transformers 本地模型适配器"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers 包未安装，请运行: pip install transformers torch")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(config.model)
        self.model = AutoModelForCausalLM.from_pretrained(
            config.model,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
        )

        if self.device == "cpu":
            self.model = self.model.to(self.device)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """生成单个响应"""
        start_time = time.time()

        # 构建完整提示
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Tokenize
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.device)
        prompt_tokens = inputs.input_ids.shape[1]

        # 生成参数
        gen_kwargs = {
            "max_new_tokens": kwargs.get("max_tokens", self.config.max_tokens or 512),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "do_sample": True,
            "pad_token_id": self.tokenizer.eos_token_id,
        }

        # 生成
        with torch.no_grad():
            outputs = self.model.generate(**inputs, **gen_kwargs)

        # 解码
        generated_text = self.tokenizer.decode(
            outputs[0][prompt_tokens:],
            skip_special_tokens=True
        )

        completion_tokens = outputs.shape[1] - prompt_tokens
        latency = time.time() - start_time

        return ModelResponse(
            content=generated_text,
            model=self.config.model,
            provider="huggingface",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency=latency,
            metadata={
                "device": self.device,
            }
        )

    async def batch_generate(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[ModelResponse]:
        """批量生成响应"""
        # HuggingFace 可以真正批量处理
        start_time = time.time()

        # 构建完整提示
        full_prompts = []
        for prompt in prompts:
            if system_prompt:
                full_prompts.append(f"{system_prompt}\n\n{prompt}")
            else:
                full_prompts.append(prompt)

        # Tokenize
        inputs = self.tokenizer(
            full_prompts,
            return_tensors="pt",
            padding=True,
            truncation=True
        ).to(self.device)

        # 生成参数
        gen_kwargs = {
            "max_new_tokens": kwargs.get("max_tokens", self.config.max_tokens or 512),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "do_sample": True,
            "pad_token_id": self.tokenizer.eos_token_id,
        }

        # 生成
        with torch.no_grad():
            outputs = self.model.generate(**inputs, **gen_kwargs)

        # 解码
        responses = []
        for i, output in enumerate(outputs):
            prompt_length = inputs.input_ids[i].shape[0]
            generated_text = self.tokenizer.decode(
                output[prompt_length:],
                skip_special_tokens=True
            )

            completion_tokens = output.shape[0] - prompt_length
            responses.append(ModelResponse(
                content=generated_text,
                model=self.config.model,
                provider="huggingface",
                prompt_tokens=prompt_length,
                completion_tokens=completion_tokens,
                total_tokens=prompt_length + completion_tokens,
                latency=time.time() - start_time,
                metadata={"device": self.device}
            ))

        return responses

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "huggingface",
            "model": self.config.model,
            "device": self.device,
            "supports_streaming": False,
            "supports_function_calling": False,
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.generate("test", max_tokens=1)
            return True
        except Exception:
            return False

    async def close(self):
        """清理资源"""
        if hasattr(self, 'model'):
            del self.model
        if hasattr(self, 'tokenizer'):
            del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
