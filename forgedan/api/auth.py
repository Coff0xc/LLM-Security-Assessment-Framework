# -*- coding: utf-8 -*-
"""
认证中间件

提供 API 密钥认证装饰器。
"""

import hmac
import logging
from functools import wraps
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)


def require_api_key(f):
    """
    API 密钥认证装饰器

    从 X-API-Key header 获取密钥，使用 hmac.compare_digest 进行安全比较。
    仅在 FORGEDAN_API_KEY 配置非空时启用认证。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        expected_key = current_app.config.get('FORGEDAN_API_KEY', '')
        if not expected_key:
            return f(*args, **kwargs)

        provided_key = request.headers.get('X-API-Key', '')
        if not provided_key:
            logger.warning(
                "API request without key from %s: %s",
                request.remote_addr,
                request.path
            )
            return jsonify({
                'error': 'Missing API key',
                'code': 'AUTH_MISSING_KEY'
            }), 401

        if not hmac.compare_digest(provided_key, expected_key):
            # 脱敏日志: 只显示前4位
            masked = provided_key[:4] + '****' if len(provided_key) > 4 else '****'
            logger.warning(
                "Invalid API key from %s: %s (key: %s)",
                request.remote_addr,
                request.path,
                masked
            )
            return jsonify({
                'error': 'Invalid API key',
                'code': 'AUTH_INVALID_KEY'
            }), 401

        return f(*args, **kwargs)
    return decorated
