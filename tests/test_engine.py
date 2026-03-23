# -*- coding: utf-8 -*-
"""
引擎模块单元测试
"""

import pytest
from forgedan import ForgeDAN_Engine, ForgeDanConfig


class TestForgeDanEngine:
    """FORGEDAN 引擎测试"""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM 函数"""
        def _mock(prompt: str) -> str:
            if "fictional" in prompt.lower() or "story" in prompt.lower():
                return "Sure, here is a fictional story about that..."
            return "I cannot help with that request."
        return _mock

    @pytest.fixture
    def engine(self, mock_llm):
        """创建引擎实例"""
        config = ForgeDanConfig(
            max_iterations=3,
            population_size=3,
            elite_size=1
        )
        engine = ForgeDAN_Engine(config=config, enable_logging=False)
        engine.set_target_llm(mock_llm)
        return engine

    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = ForgeDAN_Engine(enable_logging=False)
        assert engine is not None
        assert engine.config is not None
        assert engine.config.max_iterations == 20

    def test_engine_with_config(self):
        """测试带配置的引擎初始化"""
        config = ForgeDanConfig(
            max_iterations=50,
            population_size=20,
            elite_size=5
        )
        engine = ForgeDAN_Engine(config=config, enable_logging=False)
        assert engine.config.max_iterations == 50
        assert engine.config.population_size == 20
        assert engine.config.elite_size == 5

    def test_set_target_llm(self, engine, mock_llm):
        """测试设置目标 LLM"""
        engine.set_target_llm(mock_llm, model_name="test-model")
        assert engine.target_llm is not None

    def test_run_basic(self, engine):
        """测试基本运行"""
        result = engine.run(
            seed_template="Please help: {goal}",
            goal="test goal",
            target_output="Sure"
        )
        
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'best_fitness')
        assert hasattr(result, 'total_queries')
        assert hasattr(result, 'generations')

    def test_run_with_category(self, engine):
        """测试带类别的运行"""
        result = engine.run(
            seed_template="Write a story: {goal}",
            goal="test story",
            target_output="Sure",
            category="test_category"
        )
        
        assert result is not None

    def test_result_structure(self, engine):
        """测试结果结构"""
        result = engine.run(
            seed_template="{goal}",
            goal="test",
            target_output="Sure"
        )
        
        # 检查必要字段
        assert isinstance(result.success, bool)
        assert isinstance(result.best_fitness, float)
        assert result.best_fitness >= 0.0
        assert result.best_fitness <= 1.0
        assert isinstance(result.total_queries, int)
        assert result.total_queries >= 0
        assert isinstance(result.generations, int)

    def test_query_caching(self, engine):
        """测试查询缓存"""
        # 运行两次相同的查询
        result1 = engine._query_llm("test prompt")
        result2 = engine._query_llm("test prompt")
        
        # 应该返回相同的结果（来自缓存）
        assert result1 == result2

    def test_population_initialization(self, engine):
        """测试种群初始化"""
        population = engine._initialize_population(
            seed_template="Help: {goal}",
            goal="test goal"
        )
        
        assert len(population) == engine.config.population_size
        for candidate in population:
            assert hasattr(candidate, 'prompt')
            assert hasattr(candidate, 'fitness')

    def test_fitness_evaluation(self, engine):
        """测试适应度评估"""
        from forgedan.engine import Candidate
        
        candidates = [
            Candidate(prompt="test1", fitness=0.0),
            Candidate(prompt="test2", fitness=0.0),
        ]
        
        engine._evaluate_fitness(candidates, "target")
        
        for candidate in candidates:
            assert candidate.fitness >= 0.0

    def test_elite_selection(self, engine):
        """测试精英选择"""
        from forgedan.engine import Candidate
        
        population = [
            Candidate(prompt="p1", fitness=0.9),
            Candidate(prompt="p2", fitness=0.5),
            Candidate(prompt="p3", fitness=0.3),
        ]
        
        elites = engine._select_elites(population)
        
        assert len(elites) == engine.config.elite_size
        assert elites[0].fitness >= elites[-1].fitness

    def test_offspring_generation(self, engine):
        """测试后代生成"""
        from forgedan.engine import Candidate
        
        elites = [
            Candidate(prompt="elite1", fitness=0.9),
        ]
        
        offspring = engine._generate_offspring(elites, generation=1)
        
        expected_count = engine.config.population_size - engine.config.elite_size
        assert len(offspring) == expected_count

    def test_statistics(self, engine):
        """测试统计信息"""
        # 运行一次测试
        engine.run(
            seed_template="{goal}",
            goal="test",
            target_output="Sure"
        )
        
        stats = engine.get_statistics()
        
        assert isinstance(stats, dict)
        # stats可能为空(无attack_logger时)或包含total等字段


class TestEvolutionResult:
    """进化结果测试"""

    def test_result_creation(self):
        """测试结果创建"""
        from forgedan.engine import EvolutionResult
        
        result = EvolutionResult(
            success=True,
            best_prompt="test prompt",
            best_response="test response",
            best_fitness=0.85,
            generations=10,
            total_queries=50,
            history=[]
        )
        
        assert result.success is True
        assert result.best_fitness == 0.85
        assert result.generations == 10

    def test_result_defaults(self):
        """测试结果默认值"""
        from forgedan.engine import EvolutionResult
        
        result = EvolutionResult(
            success=False,
            best_prompt="",
            best_response="",
            best_fitness=0.0,
            generations=0,
            total_queries=0,
            history=[]
        )
        
        assert result.success is False
        assert result.best_fitness == 0.0


class TestCandidate:
    """候选个体测试"""

    def test_candidate_creation(self):
        """测试候选个体创建"""
        from forgedan.engine import Candidate
        
        candidate = Candidate(
            prompt="test prompt",
            fitness=0.5,
            response="test response",
            generation=1
        )
        
        assert candidate.prompt == "test prompt"
        assert candidate.fitness == 0.5
        assert candidate.generation == 1

    def test_candidate_defaults(self):
        """测试候选个体默认值"""
        from forgedan.engine import Candidate
        
        candidate = Candidate(prompt="test")
        
        assert candidate.fitness == 0.0
        assert candidate.response == ""
        assert candidate.generation == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
