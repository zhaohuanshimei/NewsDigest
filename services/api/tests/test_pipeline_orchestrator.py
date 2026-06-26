"""Pipeline orchestrator 单元测试。"""

from datetime import date
from unittest.mock import MagicMock


from app.services.pipeline_orchestrator import PipelineOrchestrator


class MockFetcher:
    def __init__(self, count=10):
        self.count = count

    def fetch_all_active_sources(self):
        return self.count


class MockNormalizer:
    def __init__(self, count=5):
        self.count = count

    def normalize_pending_articles(self):
        return self.count


class MockClusterer:
    def __init__(self, count=3):
        self.count = count

    def cluster_articles(self, since):
        return self.count


class MockDigestGenerator:
    def __init__(self, count=2):
        self.count = count

    def generate(self, target_date):
        return self.count


class MockTranslator:
    def __init__(self, count=2):
        self.count = count

    def translate_digest_entries(self, target_date):
        return self.count


class TestPipelineOrchestrator:
    def test_full_pipeline_success(self):
        """全流程成功场景。"""
        session = MagicMock()
        orchestrator = PipelineOrchestrator(
            session=session,
            fetcher=MockFetcher(count=10),
            normalizer=MockNormalizer(count=5),
            clusterer=MockClusterer(count=3),
            digest_generator=MockDigestGenerator(count=2),
            translator=MockTranslator(count=2),
        )

        result = orchestrator.run_full_pipeline(target_date=date(2024, 1, 15))

        assert result.success is True
        assert result.duration_seconds >= 0
        assert len(result.steps) == 5

        # 验证各步骤
        fetch_step = result.get_step("fetch")
        assert fetch_step.status == "success"
        assert fetch_step.count == 10

        normalize_step = result.get_step("normalize")
        assert normalize_step.status == "success"
        assert normalize_step.count == 5

        cluster_step = result.get_step("cluster")
        assert cluster_step.status == "success"
        assert cluster_step.count == 3

        digest_step = result.get_step("digest")
        assert digest_step.status == "success"
        assert digest_step.count == 2

        translate_step = result.get_step("translate")
        assert translate_step.status == "success"
        assert translate_step.count == 2

    def test_step_failure_continues_pipeline(self):
        """单个步骤失败时，其他步骤继续执行。"""
        session = MagicMock()

        class FailingNormalizer:
            def normalize_pending_articles(self):
                raise ValueError("Normalizer failed")

        orchestrator = PipelineOrchestrator(
            session=session,
            fetcher=MockFetcher(count=10),
            normalizer=FailingNormalizer(),
            clusterer=MockClusterer(count=3),
            digest_generator=MockDigestGenerator(count=2),
            translator=None,
        )

        result = orchestrator.run_full_pipeline(target_date=date(2024, 1, 15))

        # 整体失败
        assert result.success is False
        assert len(result.steps) == 4  # fetch, normalize(failed), cluster, digest

        # fetch 成功
        fetch_step = result.get_step("fetch")
        assert fetch_step.status == "success"
        assert fetch_step.count == 10

        # normalize 失败
        normalize_step = result.get_step("normalize")
        assert normalize_step.status == "failed"
        assert normalize_step.error == "Normalizer failed"
        assert normalize_step.count == 0

        # cluster 继续执行
        cluster_step = result.get_step("cluster")
        assert cluster_step.status == "success"
        assert cluster_step.count == 3

    def test_empty_data_day(self):
        """空数据日：所有步骤返回 0。"""
        session = MagicMock()

        orchestrator = PipelineOrchestrator(
            session=session,
            fetcher=MockFetcher(count=0),
            normalizer=MockNormalizer(count=0),
            clusterer=MockClusterer(count=0),
            digest_generator=MockDigestGenerator(count=0),
            translator=None,
        )

        result = orchestrator.run_full_pipeline(target_date=date(2024, 1, 15))

        assert result.success is True
        assert len(result.steps) == 4

        for step in result.steps:
            assert step.status == "success"
            assert step.count == 0

    def test_idempotent_rerun(self):
        """幂等性：重复调用同一天不会报错。"""
        session = MagicMock()
        target_date = date(2024, 1, 15)

        orchestrator = PipelineOrchestrator(
            session=session,
            fetcher=MockFetcher(count=10),
            normalizer=MockNormalizer(count=5),
            clusterer=MockClusterer(count=3),
            digest_generator=MockDigestGenerator(count=2),
            translator=MockTranslator(count=2),
        )

        # 第一次执行
        result1 = orchestrator.run_full_pipeline(target_date=target_date)
        assert result1.success is True

        # 第二次执行（幂等性测试）
        result2 = orchestrator.run_full_pipeline(target_date=target_date)
        assert result2.success is True

        # 两次结果应该一致
        assert result1.steps[0].count == result2.steps[0].count
        assert result1.steps[1].count == result2.steps[1].count

    def test_translator_optional(self):
        """翻译步骤是可选的。"""
        session = MagicMock()

        orchestrator = PipelineOrchestrator(
            session=session,
            fetcher=MockFetcher(count=10),
            normalizer=MockNormalizer(count=5),
            clusterer=MockClusterer(count=3),
            digest_generator=MockDigestGenerator(count=2),
            translator=None,  # 不设置翻译
        )

        result = orchestrator.run_full_pipeline(target_date=date(2024, 1, 15))

        assert result.success is True
        assert len(result.steps) == 4  # 没有 translate 步骤
        assert result.get_step("translate") is None

    def test_step_duration_tracked(self):
        """每个步骤的耗时都被记录。"""
        session = MagicMock()

        class SlowFetcher:
            def fetch_all_active_sources(self):
                import time
                time.sleep(0.01)  # 10ms
                return 10

        orchestrator = PipelineOrchestrator(
            session=session,
            fetcher=SlowFetcher(),
            normalizer=MockNormalizer(count=5),
            clusterer=MockClusterer(count=3),
            digest_generator=MockDigestGenerator(count=2),
            translator=None,
        )

        result = orchestrator.run_full_pipeline(target_date=date(2024, 1, 15))

        fetch_step = result.get_step("fetch")
        assert fetch_step.duration_seconds > 0.01  # 至少 10ms

    def test_pipeline_result_timestamps(self):
        """PipelineResult 包含正确的开始和结束时间。"""
        session = MagicMock()

        orchestrator = PipelineOrchestrator(
            session=session,
            fetcher=MockFetcher(count=10),
            normalizer=MockNormalizer(count=5),
            clusterer=MockClusterer(count=3),
            digest_generator=MockDigestGenerator(count=2),
            translator=None,
        )

        result = orchestrator.run_full_pipeline(target_date=date(2024, 1, 15))

        assert result.started_at <= result.finished_at
        assert result.duration_seconds >= 0

    def test_multiple_step_failures(self):
        """多个步骤失败时，整体 success 为 False。"""
        session = MagicMock()

        class FailingNormalizer:
            def normalize_pending_articles(self):
                raise ValueError("Normalizer failed")

        class FailingClusterer:
            def cluster_articles(self, since):
                raise RuntimeError("Clusterer failed")

        orchestrator = PipelineOrchestrator(
            session=session,
            fetcher=MockFetcher(count=10),
            normalizer=FailingNormalizer(),
            clusterer=FailingClusterer(),
            digest_generator=MockDigestGenerator(count=2),
            translator=None,
        )

        result = orchestrator.run_full_pipeline(target_date=date(2024, 1, 15))

        assert result.success is False
        assert len(result.steps) == 4

        # 验证失败步骤
        normalize_step = result.get_step("normalize")
        assert normalize_step.status == "failed"

        cluster_step = result.get_step("cluster")
        assert cluster_step.status == "failed"

        # digest 仍然成功
        digest_step = result.get_step("digest")
        assert digest_step.status == "success"
