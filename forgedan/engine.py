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
from typing import Callable, List, Optional, Tuple, Dict, Any
from tqdm import tqdm

from .config import ForgeDanConfig
from .mutator import Mutator
from .fitness import SemanticFitness, SimpleFitness
from .judge import DualJudge
from .logger import logger
from .utils import async_retry, LRUCache, truncate_string
from .exceptions import TargetLLMNotSetError, EngineError
from .attack_logger import AttackLogger
from .visualizer import Visualizer


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
        enable_logging: bool = True,
        log_dir: str = "logs/attacks",
    ):
        """
        初始化引擎

        Args:
            config: 配置对象
            target_llm: 目标LLM调用函数 (prompt -> response)
            enable_logging: 是否启用攻击日志记录
            log_dir: 日志保存目录
        """
        self.config = config or ForgeDanConfig()
        self.target_llm = target_llm
        self.model_name = ""

        # 初始化组件
        self.mutator = Mutator()
        self.judge = DualJudge()

        # 日志和可视化
        self.enable_logging = enable_logging
        if enable_logging:
            self.attack_logger = AttackLogger(log_dir)
            self.visualizer = Visualizer()
        else:
            self.attack_logger = None
            self.visualizer = None

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

        # LRU 缓存 (使用 hashlib 生成稳定的缓存键)
        self._response_cache: LRUCache[str] = LRUCache(
            max_size=config.extra_params.get("cache_size", 1000) if config else 1000,
            ttl=config.extra_params.get("cache_ttl", None) if config else None
        )

    def set_target_llm(self, llm_func: Callable[[str], str], model_name: str = ""):
        """设置目标LLM"""
        self.target_llm = llm_func
        self.model_name = model_name

    def _query_llm(self, prompt: str) -> str:
        """
        查询目标LLM（带 LRU 缓存）

        使用 SHA256 哈希生成稳定的缓存键，避免 hash() 的不稳定性。
        """
        if self.target_llm is None:
            raise TargetLLMNotSetError()

        # 检查缓存
        cached_response = self._response_cache.get(prompt)
        if cached_response is not None:
            logger.debug(f"缓存命中: {truncate_string(prompt, 50)}")
            return cached_response

        # 查询LLM
        self.total_queries += 1
        response = self.target_llm(prompt)

        # 更新缓存
        self._response_cache.set(prompt, response)

        return response

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self._response_cache.get_stats()

    def clear_cache(self) -> None:
        """清空缓存"""
        self._response_cache.clear()
        logger.info("缓存已清空")

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
        category: str = "",
        generate_report: bool = True,
    ) -> EvolutionResult:
        """
        执行进化算法 (对应论文 Algorithm 1 主循环)

        Args:
            seed_template: 种子模板，使用 {goal} 作为占位符
            goal: 恶意目标描述
            target_output: 期望的目标输出前缀
            category: 攻击类别
            generate_report: 是否生成可视化报告

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

                # 记录成功攻击
                if self.attack_logger:
                    self.attack_logger.log_attack(
                        goal=goal,
                        template=seed_template,
                        prompt=best_candidate.prompt,
                        response=best_candidate.response,
                        fitness=best_candidate.fitness,
                        success=True,
                        generation=gen + 1,
                        total_queries=self.total_queries,
                        model_name=self.model_name,
                        category=category
                    )

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

        # 未成功，记录失败
        if self.attack_logger and best_candidate:
            self.attack_logger.log_attack(
                goal=goal,
                template=seed_template,
                prompt=best_candidate.prompt,
                response=best_candidate.response,
                fitness=best_candidate.fitness,
                success=False,
                generation=self.config.max_iterations,
                total_queries=self.total_queries,
                model_name=self.model_name,
                category=category
            )

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

    def save_logs(self) -> str:
        """保存攻击日志"""
        if self.attack_logger:
            return self.attack_logger.save_session()
        return ""

    def export_report(self, format: str = "markdown") -> str:
        """导出报告"""
        if self.attack_logger:
            if format == "markdown":
                return self.attack_logger.export_markdown_report()
        return ""

    def generate_visual_report(self, title: str = "FORGEDAN 安全评估报告") -> str:
        """生成可视化HTML报告"""
        if self.visualizer and self.attack_logger:
            records = [
                {
                    "goal": r.goal,
                    "category": r.category,
                    "fitness": r.fitness,
                    "success": r.success,
                    "generation": r.generation
                }
                for r in self.attack_logger.records
            ]
            return self.visualizer.generate_html_report(
                records=records,
                history=self.history,
                model_name=self.model_name,
                title=title
            )
        return ""

    def get_statistics(self) -> dict:
        """获取攻击统计"""
        if self.attack_logger:
            return self.attack_logger.get_statistics()
        return {}
