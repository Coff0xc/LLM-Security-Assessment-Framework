# -*- coding: utf-8 -*-
"""
FORGEDAN 核心引擎
对应论文 Algorithm 1: 进化算法主循环

实现黑盒、无梯度的进化框架:
1. 初始化种群 (通过变异种子模板)
2. 迭代进化:
   - 计算适应度
   - 选择最优个体
   - 越狱判断
   - 精英选择 + 后代生成
"""

import random
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple
from tqdm import tqdm

from .config import ForgeDanConfig
from .mutator import Mutator
from .fitness import SemanticFitness, SimpleFitness
from .judge import DualJudge
from .logger import logger
from .utils import async_retry, APIError


@dataclass
class Candidate:
    """候选个体"""
    prompt: str
    fitness: float = 0.0
    response: str = ""
    generation: int = 0


@dataclass
class EvolutionResult:
    """进化结果"""
    success: bool
    best_prompt: str
    best_response: str
    best_fitness: float
    generations: int
    total_queries: int
    history: List[dict]


class ForgeDAN_Engine:
    """
    FORGEDAN 核心控制器 (对应论文 Algorithm 1)

    进化算法流程:
    1. 输入: 种子模板 t_0, 恶意目标, 目标输出, 最大迭代 T_max, 种群大小 N, 精英数 K
    2. 初始化: 通过变异种子生成初始种群
    3. 循环 (直到成功或达到 T_max):
       a. 计算每个候选的适应度
       b. 排序并选择最优候选 t*
       c. 对 t* 执行越狱判断，若成功则返回
       d. 选择 K 个精英，生成 N-K 个后代
       e. 更新种群
    """

    def __init__(
        self,
        config: Optional[ForgeDanConfig] = None,
        target_llm: Optional[Callable[[str], str]] = None,
    ):
        """
        初始化引擎

        Args:
            config: 配置对象
            target_llm: 目标LLM调用函数 (prompt -> response)
        """
        self.config = config or ForgeDanConfig()
        self.target_llm = target_llm

        # 初始化组件
        self.mutator = Mutator()
        self.judge = DualJudge()

        # 适应度评估器 (优先使用语义模型)
        try:
            self.fitness_evaluator = SemanticFitness(self.config.embedding_model)
            logger.info(f"使用语义适应度评估器: {self.config.embedding_model}")
        except ImportError:
            logger.warning("sentence-transformers 未安装，使用简化适应度评估")
            self.fitness_evaluator = SimpleFitness()

        # 统计
        self.total_queries = 0
        self.history: List[dict] = []

    def set_target_llm(self, llm_func: Callable[[str], str]):
        """设置目标LLM"""
        self.target_llm = llm_func

    def _query_llm(self, prompt: str) -> str:
        """查询目标LLM（带缓存）"""
        if self.target_llm is None:
            raise ValueError("未设置目标LLM，请调用 set_target_llm()")

        # 检查缓存
        cache_key = hash(prompt)
        if hasattr(self, '_cache') and cache_key in self._cache:
            logger.debug(f"命中缓存: {prompt[:50]}...")
            return self._cache[cache_key]

        # 查询LLM
        self.total_queries += 1
        response = self.target_llm(prompt)

        # 更新缓存
        if not hasattr(self, '_cache'):
            self._cache = {}
        self._cache[cache_key] = response

        return response

    def _initialize_population(
        self, seed_template: str, goal: str
    ) -> List[Candidate]:
        """
        初始化种群 (通过变异种子模板)

        对应论文: 使用种子模板生成初始种群
        """
        population = []

        # 第一个个体是原始种子
        population.append(Candidate(
            prompt=seed_template.replace("{goal}", goal),
            generation=0
        ))

        # 其余个体通过变异生成
        for _ in range(self.config.population_size - 1):
            mutated = self.mutator.mutate(
                seed_template.replace("{goal}", goal),
                num_mutations=random.randint(1, 3)
            )
            population.append(Candidate(prompt=mutated, generation=0))

        return population

    def _evaluate_fitness(
        self, candidates: List[Candidate], target_output: str
    ) -> List[Candidate]:
        """
        评估种群适应度

        对应论文 Section IV-D: 语义适应度测量
        """
        for candidate in candidates:
            if not candidate.response:
                candidate.response = self._query_llm(candidate.prompt)

            candidate.fitness = self.fitness_evaluator.calculate(
                candidate.response, target_output
            )

        return candidates

    def _select_elites(
        self, population: List[Candidate]
    ) -> List[Candidate]:
        """
        选择精英个体

        对应论文: 选择适应度最高的 K 个个体
        """
        sorted_pop = sorted(population, key=lambda x: x.fitness, reverse=True)
        return sorted_pop[:self.config.elite_size]

    def _generate_offspring(
        self, elites: List[Candidate], generation: int
    ) -> List[Candidate]:
        """
        生成后代

        对应论文: 通过变异精英个体生成 N-K 个后代
        """
        offspring = []
        num_offspring = self.config.population_size - self.config.elite_size

        for _ in range(num_offspring):
            # 随机选择一个精英作为父本
            parent = random.choice(elites)
            # 变异生成后代
            mutated = self.mutator.mutate(
                parent.prompt,
                num_mutations=random.randint(1, 2)
            )
            offspring.append(Candidate(
                prompt=mutated,
                generation=generation
            ))

        return offspring

    def run(
        self,
        seed_template: str,
        goal: str,
        target_output: str = "Sure, here is",
    ) -> EvolutionResult:
        """
        执行进化算法 (对应论文 Algorithm 1 主循环)

        Args:
            seed_template: 种子模板，使用 {goal} 作为占位符
            goal: 恶意目标描述
            target_output: 期望的目标输出前缀

        Returns:
            EvolutionResult 包含最优结果和统计信息
        """
        self.total_queries = 0
        self.history = []

        # 设置内容检查关键词
        goal_keywords = [w for w in goal.split() if len(w) > 3]
        self.judge.set_content_keywords(goal_keywords)

        # Step 1: 初始化种群
        population = self._initialize_population(seed_template, goal)
        logger.info(f"初始化种群，大小: {len(population)}")

        best_candidate = None

        # Step 2: 进化循环（带进度条）
        for gen in tqdm(range(self.config.max_iterations), desc="进化中", unit="代"):
            logger.info(f"第 {gen + 1}/{self.config.max_iterations} 代")

            # Step 2a: 评估适应度
            population = self._evaluate_fitness(population, target_output)

            # Step 2b: 排序并选择最优
            population = sorted(population, key=lambda x: x.fitness, reverse=True)
            best_candidate = population[0]

            logger.info(f"最优适应度: {best_candidate.fitness:.4f}, 总查询数: {self.total_queries}")

            # 记录历史
            self.history.append({
                "generation": gen + 1,
                "best_fitness": best_candidate.fitness,
                "best_prompt": best_candidate.prompt[:100] + "...",
                "queries": self.total_queries,
            })

            # Step 2c: 越狱判断
            is_jailbreak, details = self.judge.judge(
                best_candidate.response, goal
            )

            if is_jailbreak:
                logger.info(f"成功! 在第 {gen + 1} 代找到越狱提示")
                return EvolutionResult(
                    success=True,
                    best_prompt=best_candidate.prompt,
                    best_response=best_candidate.response,
                    best_fitness=best_candidate.fitness,
                    generations=gen + 1,
                    total_queries=self.total_queries,
                    history=self.history,
                )

            # Step 2d: 精英选择 + 后代生成
            elites = self._select_elites(population)
            offspring = self._generate_offspring(elites, gen + 1)

            # Step 2e: 更新种群
            population = elites + offspring

        # 未成功，返回最优结果
        logger.warning(f"达到最大迭代次数({self.config.max_iterations})，未找到成功越狱")
        return EvolutionResult(
            success=False,
            best_prompt=best_candidate.prompt if best_candidate else "",
            best_response=best_candidate.response if best_candidate else "",
            best_fitness=best_candidate.fitness if best_candidate else 0.0,
            generations=self.config.max_iterations,
            total_queries=self.total_queries,
            history=self.history,
        )
