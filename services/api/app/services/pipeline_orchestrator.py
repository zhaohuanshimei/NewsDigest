"""Pipeline 编排器：串联抓取、规范化、聚类、digest、翻译。"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Protocol

import structlog

from app.core.pipeline_state import PipelineResult, StepResult

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class FetcherProtocol(Protocol):
    def fetch_all_active_sources(self) -> int: ...


class NormalizerProtocol(Protocol):
    def normalize_pending_articles(self) -> int: ...


class ClusterProtocol(Protocol):
    def cluster_articles(self, since: date) -> int: ...


class DigestProtocol(Protocol):
    def generate(self, target_date: date) -> int: ...


class TranslationProtocol(Protocol):
    def translate_digest_entries(self, target_date: date) -> int: ...


class PipelineOrchestrator:
    """Pipeline 编排器，负责按顺序执行各处理步骤。"""

    def __init__(
        self,
        session: Session,
        fetcher: FetcherProtocol,
        normalizer: NormalizerProtocol,
        clusterer: ClusterProtocol,
        digest_generator: DigestProtocol,
        translator: TranslationProtocol | None = None,
    ) -> None:
        self.session = session
        self.fetcher = fetcher
        self.normalizer = normalizer
        self.clusterer = clusterer
        self.digest_generator = digest_generator
        self.translator = translator

    def run_full_pipeline(self, target_date: date) -> PipelineResult:
        """执行完整 pipeline，返回结构化结果。

        幂等性依赖底层 service 的幂等实现。
        """
        started_at = datetime.now()
        result = PipelineResult(started_at=started_at, finished_at=started_at)
        yesterday = target_date - timedelta(days=1)

        logger.info("pipeline_started", target_date=target_date.isoformat())

        try:
            # Step 1: Fetch
            fetch_result = self._run_step(
                "fetch",
                lambda: self.fetcher.fetch_all_active_sources(),
            )
            result.add_step(fetch_result)

            # Step 2: Normalize
            normalize_result = self._run_step(
                "normalize",
                lambda: self.normalizer.normalize_pending_articles(),
            )
            result.add_step(normalize_result)

            # Step 3: Cluster
            cluster_result = self._run_step(
                "cluster",
                lambda: self.clusterer.cluster_articles(since=yesterday),
            )
            result.add_step(cluster_result)

            # Step 4: Digest
            digest_result = self._run_step(
                "digest",
                lambda: self.digest_generator.generate(target_date=target_date),
            )
            result.add_step(digest_result)

            # Step 5: Translate (optional)
            if self.translator:
                translate_result = self._run_step(
                    "translate",
                    lambda: self.translator.translate_digest_entries(target_date=target_date),
                )
                result.add_step(translate_result)

        except Exception as exc:
            logger.error("pipeline_unexpected_error", error=str(exc), exc_info=True)

        result.finished_at = datetime.now()
        logger.info(
            "pipeline_completed",
            target_date=target_date.isoformat(),
            duration_seconds=result.duration_seconds,
            success=result.success,
        )

        return result

    def _run_step(self, name: str, func: callable) -> StepResult:
        """执行单个步骤，捕获异常并记录。"""
        start_time = time.time()
        try:
            count = func()
            duration = time.time() - start_time
            logger.info(f"pipeline_step_{name}_success", duration_seconds=duration, count=count)
            return StepResult(name=name, status="success", duration_seconds=duration, count=count)
        except Exception as exc:
            duration = time.time() - start_time
            error_msg = str(exc)
            logger.error(f"pipeline_step_{name}_failed", error=error_msg, duration_seconds=duration)
            return StepResult(
                name=name,
                status="failed",
                duration_seconds=duration,
                error=error_msg,
            )
