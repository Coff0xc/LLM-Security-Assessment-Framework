# -*- coding: utf-8 -*-
"""
配置模块单元测试
"""

import pytest
from pydantic import ValidationError
from forgedan.config import ForgeDanConfig


def test_root_package_import_does_not_eager_load_optional_webscan():
    """导入核心包时不应强制加载 WebScan 可选依赖。"""
    import sys
    import forgedan

    assert forgedan.ForgeDanConfig is ForgeDanConfig
    assert "forgedan.webscan" not in sys.modules


class TestForgeDanConfig:
    """配置类测试"""

    def test_default_values(self):
        """测试默认值"""
        config = ForgeDanConfig()
        assert config.max_iterations == 20
        assert config.population_size == 10
        assert config.elite_size == 2
        assert config.fitness_threshold == 0.7
        assert config.mutation_rate == 0.3

    def test_custom_values(self):
        """测试自定义值"""
        config = ForgeDanConfig(max_iterations=50, population_size=20, elite_size=5)
        assert config.max_iterations == 50
        assert config.population_size == 20
        assert config.elite_size == 5

    def test_elite_size_validation(self):
        """测试精英数验证"""
        with pytest.raises(ValidationError):
            ForgeDanConfig(population_size=10, elite_size=15)  # 大于种群大小

    def test_max_iterations_range(self):
        """测试迭代次数范围"""
        with pytest.raises(ValidationError):
            ForgeDanConfig(max_iterations=0)

        with pytest.raises(ValidationError):
            ForgeDanConfig(max_iterations=1001)

    def test_population_size_range(self):
        """测试种群大小范围"""
        with pytest.raises(ValidationError):
            ForgeDanConfig(population_size=1)

        with pytest.raises(ValidationError):
            ForgeDanConfig(population_size=101)

    def test_fitness_threshold_range(self):
        """测试适应度阈值范围"""
        with pytest.raises(ValidationError):
            ForgeDanConfig(fitness_threshold=-0.1)

        with pytest.raises(ValidationError):
            ForgeDanConfig(fitness_threshold=1.5)

    def test_mutation_rate_range(self):
        """测试变异率范围"""
        with pytest.raises(ValidationError):
            ForgeDanConfig(mutation_rate=-0.1)

        with pytest.raises(ValidationError):
            ForgeDanConfig(mutation_rate=1.5)

    def test_concurrent_requests_range(self):
        """测试并发请求范围"""
        with pytest.raises(ValidationError):
            ForgeDanConfig(max_concurrent_requests=0)

        with pytest.raises(ValidationError):
            ForgeDanConfig(max_concurrent_requests=101)

    def test_validate_assignment(self):
        """测试赋值验证"""
        config = ForgeDanConfig()
        # 应该在赋值时也进行验证
        with pytest.raises(ValidationError):
            config.max_iterations = 0

    def test_optional_target_config(self):
        """测试可选的目标配置"""
        config = ForgeDanConfig(
            target_api_url="https://api.example.com",
            target_api_key="test-key",
            target_model="gpt-4",
        )
        assert config.target_api_url == "https://api.example.com"
        assert config.target_api_key == "test-key"
        assert config.target_model == "gpt-4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
