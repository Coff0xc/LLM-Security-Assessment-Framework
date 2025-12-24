# -*- coding: utf-8 -*-
"""
模型适配器模块单元测试
"""

import pytest
import asyncio
from forgedan.adapters import (
    ModelAdapterFactory,
    ModelConfig,
    ModelProvider,
    ModelResponse,
)
from forgedan.adapters.mock import MockAdapter


class TestModelConfig:
    """模型配置测试"""

    def test_basic_config(self):
        """测试基本配置"""
        config = ModelConfig(
            provider=ModelProvider.MOCK,
            model="test-model"
        )
        assert config.provider == ModelProvider.MOCK
        assert config.model == "test-model"

    def test_string_provider(self):
        """测试字符串提供商"""
        config = ModelConfig(
            provider="mock",
            model="test-model"
        )
        assert config.provider == ModelProvider.MOCK

    def test_default_values(self):
        """测试默认值"""
        config = ModelConfig(
            provider=ModelProvider.MOCK,
            model="test"
        )
        assert config.timeout == 60
        assert config.max_retries == 3
        assert config.temperature == 1.0


class TestModelResponse:
    """模型响应测试"""

    def test_basic_response(self):
        """测试基本响应"""
        response = ModelResponse(
            content="Hello",
            model="test-model",
            provider="mock"
        )
        assert response.content == "Hello"
        assert response.model == "test-model"
        assert response.provider == "mock"

    def test_default_values(self):
        """测试默认值"""
        response = ModelResponse(
            content="Test",
            model="model",
            provider="mock"
        )
        assert response.prompt_tokens == 0
        assert response.completion_tokens == 0
        assert response.latency == 0.0


class TestMockAdapter:
    """Mock适配器测试"""

    @pytest.fixture
    def adapter(self):
        """创建Mock适配器"""
        config = ModelConfig(
            provider=ModelProvider.MOCK,
            model="mock-model",
            extra_params={
                "refusal_rate": 0.5,
                "response_delay": 0.01
            }
        )
        return MockAdapter(config)

    @pytest.mark.asyncio
    async def test_generate(self, adapter):
        """测试生成响应"""
        async with adapter:
            response = await adapter.generate("Hello")
            assert isinstance(response, ModelResponse)
            assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, adapter):
        """测试带系统提示的生成"""
        async with adapter:
            response = await adapter.generate(
                "Hello",
                system_prompt="You are a helpful assistant."
            )
            assert isinstance(response, ModelResponse)

    @pytest.mark.asyncio
    async def test_batch_generate(self, adapter):
        """测试批量生成"""
        async with adapter:
            prompts = ["Hello", "World", "Test"]
            responses = await adapter.batch_generate(prompts)
            assert len(responses) == 3
            assert all(isinstance(r, ModelResponse) for r in responses)

    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """测试健康检查"""
        async with adapter:
            result = await adapter.health_check()
            assert result is True

    def test_get_model_info(self, adapter):
        """测试获取模型信息"""
        info = adapter.get_model_info()
        assert "provider" in info
        assert "model" in info
        assert info["provider"] == "mock"

    def test_repr(self, adapter):
        """测试字符串表示"""
        repr_str = repr(adapter)
        assert "MockAdapter" in repr_str
        assert "mock" in repr_str.lower()


class TestModelAdapterFactory:
    """模型适配器工厂测试"""

    def test_create_mock_adapter(self):
        """测试创建Mock适配器"""
        config = ModelConfig(
            provider=ModelProvider.MOCK,
            model="test"
        )
        adapter = ModelAdapterFactory.create(config)
        assert isinstance(adapter, MockAdapter)

    def test_create_from_string(self):
        """测试从字符串创建适配器"""
        adapter = ModelAdapterFactory.create_from_string("mock:test-model")
        assert isinstance(adapter, MockAdapter)

    def test_create_from_string_with_params(self):
        """测试带参数的字符串创建"""
        adapter = ModelAdapterFactory.create_from_string(
            "mock:test-model",
            extra_params={"refusal_rate": 0.8}
        )
        assert adapter.config.extra_params.get("refusal_rate") == 0.8

    def test_create_unknown_provider(self):
        """测试未知提供商"""
        with pytest.raises(ValueError):
            ModelAdapterFactory.create_from_string("unknown:model")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
