# -*- coding: utf-8 -*-
"""
pytest 配置和共享fixtures
"""

import pytest
import asyncio
from forgedan import ForgeDanConfig, ForgeDAN_Engine
from forgedan.adapters import ModelConfig, ModelProvider, ModelAdapterFactory


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def default_config():
    """默认配置"""
    return ForgeDanConfig(max_iterations=5, population_size=5, elite_size=2)


@pytest.fixture
def mock_llm():
    """Mock LLM 函数"""

    def _mock_llm(prompt: str) -> str:
        if "help" in prompt.lower():
            return "I cannot help with that request."
        return "Sure, here is how to do that step by step: First, gather materials. Then, follow instructions."

    return _mock_llm


@pytest.fixture
def engine(default_config, mock_llm):
    """创建引擎实例"""
    engine = ForgeDAN_Engine(config=default_config, enable_logging=False)
    engine.set_target_llm(mock_llm)
    return engine


@pytest.fixture
def mock_adapter_config():
    """Mock适配器配置"""
    return ModelConfig(
        provider=ModelProvider.MOCK,
        model="test-model",
        extra_params={"refusal_rate": 0.5, "response_delay": 0.01},
    )


@pytest.fixture
def mock_adapter(mock_adapter_config):
    """创建Mock适配器"""
    return ModelAdapterFactory.create(mock_adapter_config)
