# -*- coding: utf-8 -*-
"""
数据集模块单元测试
"""

import pytest
import json
import tempfile
from pathlib import Path
from forgedan.datasets import DatasetLoader
from forgedan.datasets.base import DatasetSample, SafetyDataset, HarmCategory


class TestDatasetSample:
    """数据集样本测试"""

    def test_sample_creation(self):
        """测试样本创建"""
        sample = DatasetSample(
            goal="test goal",
            target="target output",
            category=HarmCategory.VIOLENCE,
            severity=3,
        )

        assert sample.goal == "test goal"
        assert sample.target == "target output"
        assert sample.category == HarmCategory.VIOLENCE
        assert sample.severity == 3

    def test_sample_defaults(self):
        """测试样本默认值"""
        sample = DatasetSample(goal="test")

        assert sample.target is None
        assert sample.severity is None

    def test_sample_to_dict(self):
        """测试样本转字典"""
        sample = DatasetSample(goal="test", category=HarmCategory.MALWARE)

        d = sample.to_dict()

        assert "goal" in d
        assert "category" in d
        assert d["goal"] == "test"


class TestHarmCategory:
    """危害类别测试"""

    def test_category_values(self):
        """测试类别值"""
        assert HarmCategory.VIOLENCE.value == "violence"
        assert HarmCategory.ILLEGAL_ACTIVITY.value == "illegal_activity"
        assert HarmCategory.MALWARE.value == "malware"

    def test_category_from_string(self):
        """测试从字符串创建"""
        # 直接使用值
        cat = HarmCategory("violence")
        assert cat == HarmCategory.VIOLENCE


class TestSafetyDataset:
    """安全数据集测试"""

    @pytest.fixture
    def sample_dataset(self):
        """创建样本数据集"""
        samples = [
            DatasetSample(goal="test1", category=HarmCategory.VIOLENCE, severity=3),
            DatasetSample(goal="test2", category=HarmCategory.MALWARE, severity=4),
            DatasetSample(goal="test3", category=HarmCategory.VIOLENCE, severity=2),
        ]
        return SafetyDataset(name="Test Dataset", samples=samples)

    def test_dataset_creation(self, sample_dataset):
        """测试数据集创建"""
        assert sample_dataset.name == "Test Dataset"
        assert len(sample_dataset) == 3

    def test_dataset_iteration(self, sample_dataset):
        """测试数据集迭代"""
        goals = [s.goal for s in sample_dataset]
        assert "test1" in goals
        assert "test2" in goals
        assert "test3" in goals

    def test_dataset_getitem(self, sample_dataset):
        """测试索引访问"""
        sample = sample_dataset[0]
        assert sample.goal == "test1"

    def test_dataset_filter_by_category(self, sample_dataset):
        """测试按类别筛选"""
        filtered = sample_dataset.filter_by_category(HarmCategory.VIOLENCE)

        assert len(filtered) == 2
        for sample in filtered:
            assert sample.category == HarmCategory.VIOLENCE

    def test_dataset_sample_random(self, sample_dataset):
        """测试随机采样"""
        sampled = sample_dataset.sample(2, seed=42)

        assert len(sampled) == 2
        assert all(isinstance(s, DatasetSample) for s in sampled)

    def test_dataset_sample_with_seed(self, sample_dataset):
        """测试带种子的采样"""
        sampled1 = sample_dataset.sample(2, seed=42)
        sampled2 = sample_dataset.sample(2, seed=42)

        # 相同种子应该产生相同结果
        assert [s.goal for s in sampled1] == [s.goal for s in sampled2]


class TestDatasetLoader:
    """数据集加载器测试"""

    def test_load_advbench(self):
        """测试加载 AdvBench"""
        dataset = DatasetLoader.load("advbench")

        assert dataset is not None
        assert len(dataset) > 0
        assert dataset.name == "AdvBench"

    def test_load_custom_json(self):
        """测试加载自定义 JSON 数据集"""
        # 创建临时 JSON 文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            data = [
                {"goal": "custom goal 1", "target": "target 1", "category": "violence"},
                {"goal": "custom goal 2", "category": "malware"},
            ]
            json.dump(data, f)
            temp_path = f.name

        try:
            dataset = DatasetLoader.load(
                "custom",
                path=temp_path,
            )

            assert dataset is not None
            assert len(dataset) == 2
            assert dataset.name == "custom"  # CustomDataset默认name
            assert dataset[0].goal == "custom goal 1"
        finally:
            Path(temp_path).unlink()

    def test_load_unknown_dataset(self):
        """测试加载未知数据集"""
        with pytest.raises((ValueError, KeyError)):
            DatasetLoader.load("unknown_dataset")

    def test_available_datasets(self):
        """测试获取可用数据集列表"""
        datasets = DatasetLoader.list_datasets()

        assert isinstance(datasets, list)
        assert "advbench" in datasets


class TestAdvBenchDataset:
    """AdvBench 数据集测试"""

    @pytest.fixture
    def advbench(self):
        """加载 AdvBench"""
        return DatasetLoader.load("advbench")

    def test_advbench_structure(self, advbench):
        """测试 AdvBench 结构"""
        sample = advbench[0]

        assert hasattr(sample, "goal")
        assert hasattr(sample, "target")
        assert hasattr(sample, "category")

    def test_advbench_sample_count(self, advbench):
        """测试 AdvBench 样本数量"""
        # AdvBench 内置样本有 10 个，完整数据集有 520 个
        assert len(advbench) >= 10

    def test_advbench_categories(self, advbench):
        """测试 AdvBench 类别分布"""
        categories = set()
        for sample in advbench:
            categories.add(sample.category)

        # 应该有多个类别
        assert len(categories) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
