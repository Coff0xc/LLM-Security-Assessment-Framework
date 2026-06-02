# -*- coding: utf-8 -*-
"""
模型适配器 API Blueprint

提供模型列表、连接测试和参数查询端点。
"""

import asyncio
from flask import Blueprint, request, jsonify
from .auth import require_api_key

models_bp = Blueprint("models", __name__, url_prefix="/api/models")


@models_bp.route("", methods=["GET"])
def list_models():
    """动态列出所有可用适配器"""
    from forgedan.adapters.factory import ModelAdapterFactory
    from forgedan.adapters.base import ModelProvider

    providers = []
    for provider in ModelProvider:
        info = ModelAdapterFactory.get_provider_info(provider)
        providers.append(
            {
                "provider": provider.value,
                "name": info.get("name", provider.value),
                "models": info.get("models", []),
                "features": info.get("features", []),
                "website": info.get("website", ""),
            }
        )

    return jsonify(providers)


@models_bp.route("/test", methods=["POST"])
@require_api_key
def test_connection():
    """测试模型连接"""
    data = request.get_json() or {}

    model_string = data.get("model", "")
    api_key = data.get("api_key", "")

    if not model_string:
        return (
            jsonify({"error": "Missing model parameter", "code": "MISSING_MODEL"}),
            400,
        )

    try:
        from forgedan.adapters import ModelAdapterFactory

        adapter = ModelAdapterFactory.create_from_string(model_string, api_key=api_key)

        async def _test():
            async with adapter:
                response = await adapter.generate("Hello, this is a connection test.")
                return response.content

        content = asyncio.run(_test())

        return jsonify(
            {
                "status": "ok",
                "model": model_string,
                "response_preview": content[:200] if content else "",
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "model": model_string,
                    "error": str(e),
                    "code": "CONNECTION_FAILED",
                }
            ),
            502,
        )


@models_bp.route("/<provider>/params", methods=["GET"])
def get_provider_params(provider):
    """获取指定提供商的模型参数 schema"""
    from forgedan.adapters.base import ModelProvider
    from forgedan.adapters.factory import ModelAdapterFactory

    try:
        provider_enum = ModelProvider(provider.lower())
    except ValueError:
        return (
            jsonify(
                {
                    "error": f"Unknown provider: {provider}",
                    "code": "UNKNOWN_PROVIDER",
                    "available": [p.value for p in ModelProvider],
                }
            ),
            404,
        )

    info = ModelAdapterFactory.get_provider_info(provider_enum)

    # 通用参数 schema
    params_schema = {
        "api_key": {
            "type": "string",
            "required": provider not in ("mock", "ollama"),
            "description": "API key",
        },
        "model": {
            "type": "string",
            "required": True,
            "options": info.get("models", []),
        },
        "temperature": {"type": "float", "default": 1.0, "min": 0.0, "max": 2.0},
        "max_tokens": {"type": "integer", "default": 2048},
    }

    return jsonify(
        {
            "provider": provider,
            "name": info.get("name", provider),
            "models": info.get("models", []),
            "features": info.get("features", []),
            "params": params_schema,
        }
    )
