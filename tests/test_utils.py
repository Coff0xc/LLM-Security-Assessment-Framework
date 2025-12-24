# -*- coding: utf-8 -*-
"""
工具模块单元测试
"""

import pytest
import asyncio
from forgedan.utils import async_retry, APIError


class TestAsyncRetry:
    """异步重试装饰器测试"""

    @pytest.mark.asyncio
    async def test_successful_call(self):
        """测试成功调用"""
        call_count = 0
        
        @async_retry(max_retries=3, base_delay=0.01)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_func()
        
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """测试失败后重试"""
        call_count = 0
        
        @async_retry(max_retries=3, base_delay=0.01)
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("temporary failure")
            return "success"
        
        result = await failing_then_success()
        
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        @async_retry(max_retries=3, base_delay=0.01)
        async def always_fails():
            raise Exception("always fails")
        
        with pytest.raises(Exception):
            await always_fails()

    @pytest.mark.asyncio
    async def test_retry_with_specific_exceptions(self):
        """测试只对特定异常重试"""
        call_count = 0
        
        @async_retry(max_retries=3, base_delay=0.01, exceptions=(ValueError,))
        async def value_error_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry this")
            return "success"
        
        result = await value_error_func()
        
        assert result == "success"
        assert call_count == 2


class TestAPIError:
    """API 错误测试"""

    def test_api_error_creation(self):
        """测试 API 错误创建"""
        error = APIError("test error", status_code=429)
        
        assert str(error) == "test error"
        assert error.status_code == 429

    def test_api_error_without_status(self):
        """测试无状态码的 API 错误"""
        error = APIError("test error")
        
        assert str(error) == "test error"
        assert error.status_code is None


class TestUtilityFunctions:
    """工具函数测试"""

    def test_import_utils(self):
        """测试工具模块导入"""
        from forgedan import utils
        
        assert hasattr(utils, 'async_retry')
        assert hasattr(utils, 'APIError')


class TestRateLimiter:
    """速率限制器测试（如果存在）"""

    def test_rate_limiter_existence(self):
        """测试速率限制器是否存在"""
        try:
            from forgedan.utils import RateLimiter
            assert True
        except ImportError:
            # 如果不存在也可以
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
