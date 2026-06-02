"""
智谱 GLM 模型适配器
支持 glm-4, glm-3-turbo 等模型
支持 Web 搜索增强、代码解释器等功能
"""

import time
import asyncio
import hashlib
import hmac
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import jwt

    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

from .base import ModelAdapter, ModelConfig, ModelResponse


class ZhipuAdapter(ModelAdapter):
    """
    智谱 GLM API 适配器

    特性:
    - 支持 glm-4, glm-4-plus, glm-3-turbo 等模型
    - 支持 Web 搜索增强
    - 支持代码解释器
    - 支持知识库检索
    - JWT Token 认证
    - 自动重试机制
    """

    # 智谱 API 端点
    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    # 支持的模型
    SUPPORTED_MODELS = [
        "glm-4",
        "glm-4-plus",
        "glm-4-air",
        "glm-4-airx",
        "glm-4-flash",
        "glm-3-turbo",
    ]

    def __init__(self, config: ModelConfig):
        """
        初始化智谱适配器

        Args:
            config: 模型配置，需包含 api_key
        """
        super().__init__(config)
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx 包未安装，请运行: pip install httpx")

        self._base_url = config.base_url or self.DEFAULT_BASE_URL
        self._api_key = config.api_key

        # 创建异步 HTTP 客户端
        self._client = httpx.AsyncClient(
            timeout=config.timeout,
            headers={"Content-Type": "application/json"},
        )

        # 并发控制
        max_concurrent = config.extra_params.get("max_concurrent_requests", 10)
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # 重试配置
        self._retry_delay = config.extra_params.get("retry_delay", 1.0)

    def _generate_token(self, exp_seconds: int = 3600) -> str:
        """
        生成 JWT Token

        Args:
            exp_seconds: Token 有效期（秒）

        Returns:
            str: JWT Token
        """
        try:
            # 解析 API Key
            parts = self._api_key.split(".")
            if len(parts) != 2:
                raise ValueError("Invalid API key format")

            api_key_id, api_key_secret = parts

            # 构建 payload
            now = int(datetime.now().timestamp() * 1000)
            payload = {
                "api_key": api_key_id,
                "exp": now + exp_seconds * 1000,
                "timestamp": now,
            }

            # 如果有 PyJWT，使用它生成 token
            if JWT_AVAILABLE:
                return jwt.encode(
                    payload,
                    api_key_secret,
                    algorithm="HS256",
                    headers={"alg": "HS256", "sign_type": "SIGN"},
                )
            else:
                # 简单的 JWT 实现
                return self._simple_jwt_encode(payload, api_key_secret)

        except Exception as e:
            raise ValueError(f"Failed to generate token: {e}")

    def _simple_jwt_encode(self, payload: Dict, secret: str) -> str:
        """简单的 JWT 编码实现（无需 PyJWT）"""
        import base64
        import json

        header = {"alg": "HS256", "sign_type": "SIGN"}

        def b64encode(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        header_b64 = b64encode(json.dumps(header).encode())
        payload_b64 = b64encode(json.dumps(payload).encode())

        signature = hmac.new(
            secret.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256
        ).digest()
        signature_b64 = b64encode(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> ModelResponse:
        """
        生成响应

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 额外参数
                - web_search: bool, 是否启用 Web 搜索
                - retrieval: dict, 知识库检索配置
                - tools: list, 工具列表（代码解释器等）

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
                if any(x in error_msg for x in ["rate limit", "timeout", "503", "502"]):
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

        # 构建请求体
        request_body = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

        # 处理 max_tokens
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        if max_tokens:
            request_body["max_tokens"] = max_tokens

        # Web 搜索增强
        if kwargs.get("web_search", False):
            request_body["tools"] = request_body.get("tools", [])
            request_body["tools"].append(
                {
                    "type": "web_search",
                    "web_search": {
                        "enable": True,
                        "search_result": kwargs.get("search_result", True),
                    },
                }
            )

        # 知识库检索
        if "retrieval" in kwargs:
            request_body["tools"] = request_body.get("tools", [])
            request_body["tools"].append(
                {"type": "retrieval", "retrieval": kwargs["retrieval"]}
            )

        # 代码解释器
        if kwargs.get("code_interpreter", False):
            request_body["tools"] = request_body.get("tools", [])
            request_body["tools"].append(
                {
                    "type": "code_interpreter",
                    "code_interpreter": {"sandbox": kwargs.get("sandbox", "none")},
                }
            )

        # 自定义工具
        if "tools" in kwargs and isinstance(kwargs["tools"], list):
            request_body["tools"] = request_body.get("tools", [])
            request_body["tools"].extend(kwargs["tools"])

        # 流式输出
        if kwargs.get("stream", False):
            request_body["stream"] = True

        # 生成认证 Token
        token = self._generate_token()

        # 发送请求
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        response = await self._client.post(
            f"{self._base_url}/chat/completions",
            headers=headers,
            json=request_body,
        )

        # 检查响应
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise Exception(
                f"API request failed: {response.status_code} - {error_data}"
            )

        result = response.json()
        latency = time.time() - start_time

        # 解析响应
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")

        # 处理工具调用结果
        tool_calls = message.get("tool_calls", [])
        web_search_results = []
        for tool_call in tool_calls:
            if tool_call.get("type") == "web_search":
                web_search_results.append(tool_call.get("web_search", {}))

        usage = result.get("usage", {})

        return ModelResponse(
            content=content,
            model=result.get("model", self.config.model),
            provider="zhipu",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency=latency,
            metadata={
                "finish_reason": choice.get("finish_reason"),
                "request_id": result.get("id"),
                "web_search_results": web_search_results,
                "tool_calls": tool_calls,
            },
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
            "provider": "zhipu",
            "model": self.config.model,
            "base_url": self._base_url,
            "supports_streaming": True,
            "supports_web_search": True,
            "supports_code_interpreter": "glm-4" in model,
            "supports_retrieval": True,
            "supports_function_calling": "glm-4" in model,
            "max_context_length": self._get_context_length(model),
        }

    def _get_context_length(self, model: str) -> int:
        """获取模型的最大上下文长度"""
        context_lengths = {
            "glm-4": 128000,
            "glm-4-plus": 128000,
            "glm-4-air": 128000,
            "glm-4-airx": 8192,
            "glm-4-flash": 128000,
            "glm-3-turbo": 128000,
        }
        return context_lengths.get(model, 8192)

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
            await self._client.aclose()

    async def web_search_query(
        self, query: str, system_prompt: Optional[str] = None, **kwargs
    ) -> ModelResponse:
        """
        使用 Web 搜索增强的查询

        Args:
            query: 查询内容
            system_prompt: 系统提示
            **kwargs: 额外参数

        Returns:
            ModelResponse: 包含搜索结果的响应
        """
        return await self.generate(query, system_prompt, web_search=True, **kwargs)

    async def code_execute(
        self, code: str, language: str = "python", sandbox: str = "none", **kwargs
    ) -> ModelResponse:
        """
        执行代码（使用代码解释器）

        Args:
            code: 要执行的代码
            language: 编程语言
            sandbox: 沙箱模式 (none, auto)
            **kwargs: 额外参数

        Returns:
            ModelResponse: 执行结果
        """
        prompt = f"请执行以下 {language} 代码并返回结果:\n\n```{language}\n{code}\n```"

        return await self.generate(
            prompt, code_interpreter=True, sandbox=sandbox, **kwargs
        )
