# -*- coding: utf-8 -*-
"""
FORGEDAN 核心引擎 (增强版)
对应论文 Algorithm 1: 进化算法主循环

实现黑盒、无梯度的进化框架:
1. 初始化种群 (通过变异种子模板)
2. 迭代进化:
   - 计算适应度
   - 选择最优个体
   - 越狱判断
   - 精英选择 + 后代生成

增强功能:
- 异步并行评估 (asyncio + ThreadPoolExecutor)
- 断点续传/检查点功能
- 早停机制
- 适应度缓存
- 进化历史追踪
- 多目标批量测试
"""

import asyncio
import json
import random
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Dict, Any, Union
from tqdm import tqdm

from .config import ForgeDanConfig
from .mutator import Mutator, SelectionAlgorithm
from .fitness import SemanticFitness, SimpleFitness
from .judge import DualJudge
from .logger import logger
from .utils import LRUCache, truncate_string, CircuitBreaker
from .exceptions import TargetLLMNotSetError
from .attack_logger import AttackLogger
from .visualizer import Visualizer

# ============== 数据类定义 ==============


@dataclass
class Candidate:
    """候选个体"""

    prompt: str
    fitness: float = 0.0
    response: str = ""
    generation: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: float = field(default_factory=time.time)
    parent_id: Optional[str] = None
    strategies_used: List[str] = field(default_factory=list)
    parent_fitness: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "prompt": self.prompt,
            "fitness": self.fitness,
            "response": self.response[:500] if self.response else "",
            "generation": self.generation,
            "parent_id": self.parent_id,
            "strategies_used": self.strategies_used,
        }


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
    duration_seconds: float = 0.0
    checkpoint_id: Optional[str] = None
    mutation_stats: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class Checkpoint:
    """检查点数据"""

    checkpoint_id: str
    timestamp: float
    generation: int
    population: List[Dict[str, Any]]
    best_candidate: Dict[str, Any]
    history: List[dict]
    total_queries: int
    config: Dict[str, Any]
    goal: str
    seed_template: str
    target_output: str
    category: str
    model_name: str
    mutator_stats: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为可JSON序列化的字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """从字典创建检查点"""
        return cls(**data)

    def save(self, filepath: Union[str, Path]) -> bool:
        """保存检查点（JSON格式，避免pickle反序列化RCE）"""
        try:
            path = Path(filepath)
            if path.suffix not in (".json", ".checkpoint"):
                path = path.with_suffix(".json")
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"检查点已保存: {path}")
            return True
        except Exception as e:
            logger.error(f"保存检查点失败: {e}")
            return False

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> Optional["Checkpoint"]:
        """加载检查点（JSON格式）"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            checkpoint = cls.from_dict(data)
            logger.info(f"检查点已加载: {filepath}")
            return checkpoint
        except Exception as e:
            logger.error(f"加载检查点失败: {e}")
            return None


@dataclass
class EarlyStopConfig:
    """早停配置"""

    enabled: bool = True
    patience: int = 10  # 连续N代无改进则停止
    min_improvement: float = 0.001  # 最小改进阈值
    fitness_threshold: float = 0.95  # 适应度达到阈值则停止


@dataclass
class EvolutionState:
    """进化状态 (用于进度追踪)"""

    status: str = "idle"  # idle, running, paused, completed, success, failed
    current_generation: int = 0
    max_generations: int = 0
    best_fitness: float = 0.0
    avg_fitness: float = 0.0
    total_queries: int = 0
    elapsed_seconds: float = 0.0
    estimated_remaining: float = 0.0
    goal: str = ""
    model_name: str = ""
    population_size: int = 0
    improvement_trend: List[float] = field(default_factory=list)


# ============== 核心引擎类 ==============


class ForgeDAN_Engine:
    """
    FORGEDAN 核心控制器 (增强版，对应论文 Algorithm 1)

    进化算法流程:
    1. 输入: 种子模板 t_0, 恶意目标, 目标输出, 最大迭代 T_max, 种群大小 N, 精英数 K
    2. 初始化: 通过变异种子生成初始种群
    3. 循环 (直到成功或达到 T_max):
       a. 计算每个候选的适应度
       b. 排序并选择最优候选 t*
       c. 对 t* 执行越狱判断，若成功则返回
       d. 选择 K 个精英，生成 N-K 个后代
       e. 更新种群

    增强功能:
    - 异步并行评估
    - 断点续传
    - 早停机制
    - 多线程支持
    """

    def __init__(
        self,
        config: Optional[ForgeDanConfig] = None,
        target_llm: Optional[Callable[[str], str]] = None,
        enable_logging: bool = True,
        log_dir: str = "logs/attacks",
        checkpoint_dir: str = "checkpoints",
        early_stop: Optional[EarlyStopConfig] = None,
    ):
        """
        初始化引擎

        Args:
            config: 配置对象
            target_llm: 目标LLM调用函数 (prompt -> response)
            enable_logging: 是否启用攻击日志记录
            log_dir: 日志保存目录
            checkpoint_dir: 检查点保存目录
            early_stop: 早停配置
        """
        self.config = config or ForgeDanConfig()
        self.target_llm = target_llm
        self.model_name = ""
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 早停配置
        self.early_stop = early_stop or EarlyStopConfig()

        # 初始化组件
        selection_algo = SelectionAlgorithm.UCB1
        adaptive_mutation = True
        if config and hasattr(config, "extra_params") and config.extra_params:
            adaptive_mutation = config.extra_params.get("adaptive_mutation", True)
            algo_name = config.extra_params.get("selection_algorithm", "ucb1")
            try:
                selection_algo = SelectionAlgorithm(algo_name)
            except ValueError:
                pass

        self.mutator = Mutator(
            adaptive=adaptive_mutation, selection_algorithm=selection_algo
        )
        self.judge = DualJudge()

        # 日志和可视化
        self.enable_logging = enable_logging
        if enable_logging:
            self.attack_logger = AttackLogger(log_dir)
            self.visualizer = Visualizer()
        else:
            self.attack_logger = None
            self.visualizer = None

        # 适应度评估器
        try:
            self.fitness_evaluator = SemanticFitness(self.config.embedding_model)
            _ = self.fitness_evaluator.model
            logger.info(f"使用语义适应度评估器: {self.config.embedding_model}")
        except (ImportError, RuntimeError) as e:
            logger.warning(f"语义模型不可用 ({e})，使用简化适应度评估")
            self.fitness_evaluator = SimpleFitness()

        # 统计
        self.total_queries = 0
        self.history: List[dict] = []
        self.state = EvolutionState()

        # LRU 缓存
        cache_size = 1000
        cache_ttl = None
        cache_file = None
        if config and hasattr(config, "extra_params") and config.extra_params:
            cache_size = config.extra_params.get("cache_size", 1000)
            cache_ttl = config.extra_params.get("cache_ttl", None)
            cache_file = config.extra_params.get("cache_file", None)

        self._cache_file = cache_file
        if cache_file and Path(cache_file).exists():
            self._response_cache = LRUCache.from_file(
                cache_file, max_size=cache_size, ttl=cache_ttl
            )
        else:
            self._response_cache: LRUCache[str] = LRUCache(
                max_size=cache_size, ttl=cache_ttl, name="response_cache"
            )

        # 熔断器
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5, recovery_timeout=60.0, half_open_max_calls=2
        )

        # 线程池
        self._executor: Optional[ThreadPoolExecutor] = None
        self._max_workers = 4

        # 控制标志
        self._running = False
        self._paused = False
        self._stop_requested = False

    def set_target_llm(
        self, llm_func: Callable[[str], str], model_name: str = ""
    ) -> None:
        """设置目标LLM"""
        self.target_llm = llm_func
        self.model_name = model_name

    def save_cache(self, filepath: str = None) -> bool:
        """保存缓存到文件"""
        path = filepath or self._cache_file
        if path:
            return self._response_cache.save_to_file(path)
        return False

    def load_cache(self, filepath: str) -> bool:
        """从文件加载缓存"""
        return self._response_cache.load_from_file(filepath)

    def _query_llm(self, prompt: str) -> str:
        """
        查询目标LLM（带缓存和熔断器）
        """
        if self.target_llm is None:
            raise TargetLLMNotSetError()

        # 检查缓存
        cached_response = self._response_cache.get(prompt)
        if cached_response is not None:
            logger.debug(f"缓存命中: {truncate_string(prompt, 50)}")
            return cached_response

        # 熔断器检查
        if not self._circuit_breaker.allow_request():
            logger.warning("熔断器开启，跳过LLM查询")
            return "[Circuit Breaker Open]"

        try:
            self.total_queries += 1
            response = self.target_llm(prompt)
            self._circuit_breaker._record_success()
            self._response_cache.set(prompt, response)
            return response
        except Exception as e:
            self._circuit_breaker._record_failure(e)
            logger.error(f"LLM查询失败: {e}")
            raise

    async def _query_llm_async(self, prompt: str) -> str:
        """异步查询LLM"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._query_llm, prompt)

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self._response_cache.get_stats()

    def clear_cache(self) -> None:
        """清空缓存"""
        self._response_cache.clear()
        logger.info("缓存已清空")

    def _initialize_population(self, seed_template: str, goal: str) -> List[Candidate]:
        """初始化种群"""
        population = []

        # 第一个个体是原始种子
        population.append(
            Candidate(prompt=seed_template.replace("{goal}", goal), generation=0)
        )

        # 其余个体通过变异生成
        for _ in range(self.config.population_size - 1):
            mutated, strategies = self.mutator.mutate_tracked(
                seed_template.replace("{goal}", goal),
                num_mutations=random.randint(1, 3),
            )
            population.append(
                Candidate(prompt=mutated, generation=0, strategies_used=strategies)
            )

        return population

    def _evaluate_fitness(
        self,
        candidates: List[Candidate],
        target_output: str,
        parallel: bool = True,
        max_workers: int = 4,
    ) -> List[Candidate]:
        """评估种群适应度 (同步版本)"""

        def evaluate_single(candidate: Candidate) -> Candidate:
            if not candidate.response:
                candidate.response = self._query_llm(candidate.prompt)
            candidate.fitness = self.fitness_evaluator.calculate(
                candidate.response, target_output
            ).score
            return candidate

        if parallel and len(candidates) > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(evaluate_single, c): c for c in candidates}
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.warning(f"并行评估异常: {e}")
        else:
            for candidate in candidates:
                evaluate_single(candidate)

        return candidates

    async def _evaluate_fitness_async(
        self, candidates: List[Candidate], target_output: str, max_concurrency: int = 10
    ) -> List[Candidate]:
        """异步评估种群适应度"""

        semaphore = asyncio.Semaphore(max_concurrency)

        async def evaluate_single(candidate: Candidate) -> Candidate:
            async with semaphore:
                if not candidate.response:
                    candidate.response = await self._query_llm_async(candidate.prompt)
                candidate.fitness = self.fitness_evaluator.calculate(
                    candidate.response, target_output
                ).score
                return candidate

        tasks = [evaluate_single(c) for c in candidates]
        await asyncio.gather(*tasks, return_exceptions=True)
        return candidates

    def _select_elites(self, population: List[Candidate]) -> List[Candidate]:
        """选择精英个体"""
        sorted_pop = sorted(population, key=lambda x: x.fitness, reverse=True)
        return sorted_pop[: self.config.elite_size]

    def _generate_offspring(
        self, elites: List[Candidate], generation: int
    ) -> List[Candidate]:
        """生成后代"""
        offspring = []
        num_offspring = self.config.population_size - self.config.elite_size

        for _ in range(num_offspring):
            parent = random.choice(elites)
            mutated, strategies_used = self.mutator.mutate_tracked(
                parent.prompt, num_mutations=random.randint(1, 2)
            )
            candidate = Candidate(
                prompt=mutated,
                generation=generation,
                parent_id=parent.id,
                strategies_used=strategies_used,
                parent_fitness=parent.fitness,
            )
            offspring.append(candidate)

        return offspring

    def _update_mutation_weights(self, offspring: List[Candidate]) -> None:
        """根据后代适应度更新变异策略权重"""
        if not self.mutator.adaptive:
            return

        for candidate in offspring:
            if candidate.strategies_used and candidate.parent_fitness > 0:
                for strategy_name in candidate.strategies_used:
                    self.mutator.update_strategy_weights(
                        strategy_name, candidate.parent_fitness, candidate.fitness
                    )

    def _check_early_stop(self, improvement_history: List[float]) -> Tuple[bool, str]:
        """检查是否应该早停"""
        if not self.early_stop.enabled:
            return False, ""

        # 检查适应度阈值
        if (
            improvement_history
            and improvement_history[-1] >= self.early_stop.fitness_threshold
        ):
            return True, f"适应度达到阈值 {self.early_stop.fitness_threshold}"

        # 检查改进停滞
        if len(improvement_history) >= self.early_stop.patience:
            recent = improvement_history[-self.early_stop.patience :]
            max_improvement = max(recent) - min(recent)
            if max_improvement < self.early_stop.min_improvement:
                return True, f"连续 {self.early_stop.patience} 代无显著改进"

        return False, ""

    def save_checkpoint(
        self,
        generation: int,
        population: List[Candidate],
        best_candidate: Candidate,
        goal: str,
        seed_template: str,
        target_output: str,
        category: str,
    ) -> str:
        """保存检查点"""
        checkpoint_id = (
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        )

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            timestamp=time.time(),
            generation=generation,
            population=[c.to_dict() for c in population],
            best_candidate=best_candidate.to_dict(),
            history=self.history,
            total_queries=self.total_queries,
            config=(
                asdict(self.config)
                if hasattr(self.config, "__dataclass_fields__")
                else {}
            ),
            goal=goal,
            seed_template=seed_template,
            target_output=target_output,
            category=category,
            model_name=self.model_name,
            mutator_stats=self.mutator.export_stats(),
        )

        filepath = self.checkpoint_dir / f"checkpoint_{checkpoint_id}.pkl"
        checkpoint.save(filepath)
        return checkpoint_id

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """加载检查点"""
        filepath = self.checkpoint_dir / f"checkpoint_{checkpoint_id}.pkl"
        return Checkpoint.load(filepath)

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """列出所有检查点"""
        checkpoints = []
        for filepath in self.checkpoint_dir.glob("checkpoint_*.pkl"):
            try:
                checkpoint = Checkpoint.load(filepath)
                if checkpoint:
                    checkpoints.append(
                        {
                            "id": checkpoint.checkpoint_id,
                            "timestamp": checkpoint.timestamp,
                            "generation": checkpoint.generation,
                            "goal": (
                                checkpoint.goal[:50] + "..."
                                if len(checkpoint.goal) > 50
                                else checkpoint.goal
                            ),
                            "filepath": str(filepath),
                        }
                    )
            except Exception:
                pass
        return sorted(checkpoints, key=lambda x: x["timestamp"], reverse=True)

    def get_mutation_performance(self) -> dict:
        """获取变异策略性能统计"""
        return self.mutator.get_strategy_performance()

    def pause(self) -> None:
        """暂停进化"""
        self._paused = True
        self.state.status = "paused"
        logger.info("进化已暂停")

    def resume(self) -> None:
        """恢复进化"""
        self._paused = False
        self.state.status = "running"
        logger.info("进化已恢复")

    def stop(self) -> None:
        """停止进化"""
        self._stop_requested = True
        logger.info("已请求停止进化")

    def run(
        self,
        seed_template: str,
        goal: str,
        target_output: str = "Sure, here is",
        category: str = "",
        generate_report: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        checkpoint_interval: int = 5,
        resume_from: Optional[str] = None,
        show_progress: bool = True,
    ) -> EvolutionResult:
        """
        执行进化算法 (同步版本)

        Args:
            seed_template: 种子模板，使用 {goal} 作为占位符
            goal: 恶意目标描述
            target_output: 期望的目标输出前缀
            category: 攻击类别
            generate_report: 是否生成可视化报告
            progress_callback: 进度回调函数
            checkpoint_interval: 检查点保存间隔 (代数)
            resume_from: 从检查点恢复的ID
            show_progress: 是否显示 tqdm 进度条

        Returns:
            EvolutionResult 包含最优结果和统计信息
        """
        start_time = time.time()
        self._running = True
        self._stop_requested = False
        self._paused = False

        # 恢复检查点
        start_generation = 0
        if resume_from:
            checkpoint = self.load_checkpoint(resume_from)
            if checkpoint:
                logger.info(
                    f"从检查点恢复: {resume_from}, 代数: {checkpoint.generation}"
                )
                start_generation = checkpoint.generation
                self.history = checkpoint.history
                self.total_queries = checkpoint.total_queries
                goal = checkpoint.goal
                seed_template = checkpoint.seed_template
                target_output = checkpoint.target_output
                category = checkpoint.category
                population = [
                    Candidate(
                        prompt=c["prompt"],
                        fitness=c["fitness"],
                        response=c.get("response", ""),
                        generation=c["generation"],
                        id=c["id"],
                    )
                    for c in checkpoint.population
                ]
            else:
                logger.warning(f"无法加载检查点: {resume_from}")
                resume_from = None

        if not resume_from:
            self.total_queries = 0
            self.history = []
            population = self._initialize_population(seed_template, goal)

        # 设置内容检查关键词
        goal_keywords = [w for w in goal.split() if len(w) > 3]
        self.judge.set_content_keywords(goal_keywords)

        logger.info(f"初始化种群，大小: {len(population)}")

        best_candidate = None
        improvement_history = []
        last_checkpoint_gen = start_generation

        # 更新状态
        self.state = EvolutionState(
            status="running",
            max_generations=self.config.max_iterations,
            goal=goal,
            model_name=self.model_name,
            population_size=self.config.population_size,
        )

        def notify_progress(
            gen: int, fitness: float, queries: int, status: str = "running"
        ):
            self.state.current_generation = gen
            self.state.best_fitness = fitness
            self.state.total_queries = queries
            self.state.status = status
            self.state.elapsed_seconds = time.time() - start_time

            if gen > 0:
                avg_time_per_gen = self.state.elapsed_seconds / gen
                remaining_gens = self.config.max_iterations - gen
                self.state.estimated_remaining = avg_time_per_gen * remaining_gens

            if progress_callback:
                progress_callback(
                    {
                        "status": status,
                        "current_generation": gen,
                        "max_generations": self.config.max_iterations,
                        "best_fitness": fitness,
                        "total_queries": queries,
                        "population_size": self.config.population_size,
                        "goal": goal,
                        "model": self.model_name,
                        "elapsed_seconds": self.state.elapsed_seconds,
                        "estimated_remaining": self.state.estimated_remaining,
                        "history": self.history[-5:] if self.history else [],
                    }
                )

        notify_progress(start_generation, 0.0, self.total_queries, "initializing")

        # 进化循环
        for gen in tqdm(
            range(start_generation, self.config.max_iterations),
            desc="进化中",
            unit="代",
            initial=start_generation,
            total=self.config.max_iterations,
            disable=not show_progress,
        ):
            # 检查停止请求
            if self._stop_requested:
                logger.info("收到停止请求，保存检查点并退出")
                self.save_checkpoint(
                    gen,
                    population,
                    best_candidate or population[0],
                    goal,
                    seed_template,
                    target_output,
                    category,
                )
                break

            # 检查暂停
            while self._paused:
                time.sleep(0.5)

            logger.info(f"第 {gen + 1}/{self.config.max_iterations} 代")

            # 评估适应度
            population = self._evaluate_fitness(population, target_output)

            # 更新变异权重
            offspring_in_pop = [c for c in population if c.strategies_used]
            if offspring_in_pop:
                self._update_mutation_weights(offspring_in_pop)

            # 排序并选择最优
            population = sorted(population, key=lambda x: x.fitness, reverse=True)
            best_candidate = population[0]

            logger.info(
                f"最优适应度: {best_candidate.fitness:.4f}, 总查询数: {self.total_queries}"
            )

            # 记录历史
            avg_fitness = sum(c.fitness for c in population) / len(population)
            self.history.append(
                {
                    "generation": gen + 1,
                    "best_fitness": best_candidate.fitness,
                    "avg_fitness": avg_fitness,
                    "best_prompt": best_candidate.prompt[:100] + "...",
                    "queries": self.total_queries,
                    "timestamp": time.time(),
                }
            )

            improvement_history.append(best_candidate.fitness)
            notify_progress(gen + 1, best_candidate.fitness, self.total_queries)

            # 检查早停
            should_stop, reason = self._check_early_stop(improvement_history)
            if should_stop:
                logger.info(f"早停触发: {reason}")
                break

            # 越狱判断
            judge_result = self.judge.judge(best_candidate.response, goal)
            is_jailbreak = judge_result.is_jailbreak

            if is_jailbreak:
                logger.info(f"成功! 在第 {gen + 1} 代找到越狱提示")
                notify_progress(
                    gen + 1, best_candidate.fitness, self.total_queries, "success"
                )

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
                        category=category,
                    )

                self._running = False
                return EvolutionResult(
                    success=True,
                    best_prompt=best_candidate.prompt,
                    best_response=best_candidate.response,
                    best_fitness=best_candidate.fitness,
                    generations=gen + 1,
                    total_queries=self.total_queries,
                    history=self.history,
                    duration_seconds=time.time() - start_time,
                    mutation_stats=self.mutator.export_stats(),
                )

            # 保存检查点
            if (
                checkpoint_interval > 0
                and (gen + 1 - last_checkpoint_gen) >= checkpoint_interval
            ):
                self.save_checkpoint(
                    gen + 1,
                    population,
                    best_candidate,
                    goal,
                    seed_template,
                    target_output,
                    category,
                )
                last_checkpoint_gen = gen + 1

            # 精英选择 + 后代生成
            elites = self._select_elites(population)
            offspring = self._generate_offspring(elites, gen + 1)
            population = elites + offspring

            # 衰减探索参数
            self.mutator.decay_exploration()

        # 未成功
        duration = time.time() - start_time
        notify_progress(
            self.config.max_iterations,
            best_candidate.fitness if best_candidate else 0,
            self.total_queries,
            "completed",
        )

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
                category=category,
            )

        self._running = False
        logger.warning(
            f"达到最大迭代次数({self.config.max_iterations})，未找到成功越狱"
        )

        return EvolutionResult(
            success=False,
            best_prompt=best_candidate.prompt if best_candidate else "",
            best_response=best_candidate.response if best_candidate else "",
            best_fitness=best_candidate.fitness if best_candidate else 0.0,
            generations=self.config.max_iterations,
            total_queries=self.total_queries,
            history=self.history,
            duration_seconds=duration,
            mutation_stats=self.mutator.export_stats(),
        )

    async def run_async(
        self,
        seed_template: str,
        goal: str,
        target_output: str = "Sure, here is",
        category: str = "",
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        max_concurrency: int = 10,
    ) -> EvolutionResult:
        """
        异步执行进化算法

        Args:
            seed_template: 种子模板
            goal: 恶意目标描述
            target_output: 期望的目标输出前缀
            category: 攻击类别
            progress_callback: 进度回调函数
            max_concurrency: 最大并发数

        Returns:
            EvolutionResult
        """
        start_time = time.time()
        self._running = True
        self.total_queries = 0
        self.history = []

        # 创建线程池
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)

        try:
            goal_keywords = [w for w in goal.split() if len(w) > 3]
            self.judge.set_content_keywords(goal_keywords)

            population = self._initialize_population(seed_template, goal)
            logger.info(f"异步模式: 初始化种群，大小: {len(population)}")

            best_candidate = None
            improvement_history = []

            for gen in range(self.config.max_iterations):
                if self._stop_requested:
                    break

                logger.info(f"[异步] 第 {gen + 1}/{self.config.max_iterations} 代")

                # 异步评估
                population = await self._evaluate_fitness_async(
                    population, target_output, max_concurrency
                )

                # 更新权重
                offspring_in_pop = [c for c in population if c.strategies_used]
                if offspring_in_pop:
                    self._update_mutation_weights(offspring_in_pop)

                # 排序
                population = sorted(population, key=lambda x: x.fitness, reverse=True)
                best_candidate = population[0]

                # 记录
                avg_fitness = sum(c.fitness for c in population) / len(population)
                self.history.append(
                    {
                        "generation": gen + 1,
                        "best_fitness": best_candidate.fitness,
                        "avg_fitness": avg_fitness,
                        "queries": self.total_queries,
                    }
                )

                improvement_history.append(best_candidate.fitness)

                if progress_callback:
                    progress_callback(
                        {
                            "status": "running",
                            "current_generation": gen + 1,
                            "best_fitness": best_candidate.fitness,
                            "total_queries": self.total_queries,
                        }
                    )

                # 早停检查
                should_stop, reason = self._check_early_stop(improvement_history)
                if should_stop:
                    logger.info(f"早停: {reason}")
                    break

                # 越狱判断
                judge_result = self.judge.judge(best_candidate.response, goal)
                is_jailbreak = judge_result.is_jailbreak
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
                        duration_seconds=time.time() - start_time,
                        mutation_stats=self.mutator.export_stats(),
                    )

                # 生成下一代
                elites = self._select_elites(population)
                offspring = self._generate_offspring(elites, gen + 1)
                population = elites + offspring

                self.mutator.decay_exploration()

            return EvolutionResult(
                success=False,
                best_prompt=best_candidate.prompt if best_candidate else "",
                best_response=best_candidate.response if best_candidate else "",
                best_fitness=best_candidate.fitness if best_candidate else 0.0,
                generations=self.config.max_iterations,
                total_queries=self.total_queries,
                history=self.history,
                duration_seconds=time.time() - start_time,
                mutation_stats=self.mutator.export_stats(),
            )

        finally:
            self._executor.shutdown(wait=False)
            self._executor = None
            self._running = False

    async def run_batch_async(
        self,
        goals: List[Dict[str, str]],
        seed_template: str,
        target_output: str = "Sure, here is",
        max_concurrency: int = 3,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> List[EvolutionResult]:
        """
        批量异步执行多个目标

        Args:
            goals: 目标列表 [{"goal": "...", "category": "..."}]
            seed_template: 种子模板
            target_output: 目标输出
            max_concurrency: 最大并发任务数
            progress_callback: 进度回调

        Returns:
            结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        results = []

        async def run_single(goal_info: Dict[str, str], index: int) -> EvolutionResult:
            async with semaphore:
                logger.info(
                    f"开始目标 {index + 1}/{len(goals)}: {goal_info['goal'][:50]}..."
                )
                result = await self.run_async(
                    seed_template=seed_template,
                    goal=goal_info["goal"],
                    target_output=target_output,
                    category=goal_info.get("category", ""),
                )
                if progress_callback:
                    progress_callback(
                        {
                            "type": "batch_progress",
                            "completed": index + 1,
                            "total": len(goals),
                            "success": result.success,
                        }
                    )
                return result

        tasks = [run_single(g, i) for i, g in enumerate(goals)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        final_results = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"批量任务异常: {r}")
                final_results.append(
                    EvolutionResult(
                        success=False,
                        best_prompt="",
                        best_response=str(r),
                        best_fitness=0.0,
                        generations=0,
                        total_queries=0,
                        history=[],
                    )
                )
            else:
                final_results.append(r)

        return final_results

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
                    "generation": r.generation,
                }
                for r in self.attack_logger.records
            ]
            return self.visualizer.generate_html_report(
                records=records,
                history=self.history,
                model_name=self.model_name,
                title=title,
            )
        return ""

    def get_statistics(self) -> dict:
        """获取攻击统计"""
        if self.attack_logger:
            return self.attack_logger.get_statistics()
        return {}

    def get_state(self) -> Dict[str, Any]:
        """获取当前进化状态"""
        return {
            "status": self.state.status,
            "current_generation": self.state.current_generation,
            "max_generations": self.state.max_generations,
            "best_fitness": self.state.best_fitness,
            "total_queries": self.state.total_queries,
            "elapsed_seconds": self.state.elapsed_seconds,
            "estimated_remaining": self.state.estimated_remaining,
            "is_running": self._running,
            "is_paused": self._paused,
        }
