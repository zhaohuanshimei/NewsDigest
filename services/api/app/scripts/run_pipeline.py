"""CLI entrypoint to run the full ingest + digest + translation pipeline.

Usage:
    python -m app.scripts.run_pipeline                    # today
    python -m app.scripts.run_pipeline --date 2026-06-29  # specific date
    python -m app.scripts.run_pipeline --no-translate     # skip translation

Environment variables (see .env.example):
    DATABASE_URL                — PostgreSQL connection string
    TRANSLATION_API_BASE_URL    — OpenAI-compatible base URL (e.g. NewAPI)
    TRANSLATION_API_KEY         — API key
    TRANSLATION_MODEL           — model name (default: gpt-4o-mini)
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from app.core.pipeline_state import PipelineResult
from app.database import SessionLocal
from app.services.article_normalizer import ArticleNormalizer
from app.services.article_service import ArticleService
from app.services.cluster_service import ClusterService
from app.services.digest_generator import DigestGenerator
from app.services.pipeline_orchestrator import PipelineOrchestrator
from app.services.translation_provider_factory import build_translation_provider
from app.services.translation_service import (
    PipelineTranslatorAdapter,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full news digest pipeline")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Target digest date (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--no-translate",
        action="store_true",
        help="Skip the translation step.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    target_date = date.fromisoformat(args.date) if args.date else date.today()

    with SessionLocal() as session:
        fetcher = ArticleService(session)
        normalizer = ArticleNormalizer(session)
        clusterer = ClusterService(session)
        digest_gen = DigestGenerator(session)

        translator = None
        if not args.no_translate:
            provider = build_translation_provider()
            translator = PipelineTranslatorAdapter(session, provider=provider)
            print(f"Translation provider: {provider.name}")
        else:
            print("Translation: skipped (--no-translate)")

        orchestrator = PipelineOrchestrator(
            session=session,
            fetcher=fetcher,
            normalizer=normalizer,
            clusterer=clusterer,
            digest_generator=digest_gen,
            translator=translator,
        )

        result: PipelineResult = orchestrator.run_full_pipeline(target_date)

    # Report
    print(f"\nPipeline result for {target_date}")
    print(f"  duration: {result.duration_seconds:.2f}s")
    print(f"  success:  {result.success}")
    for step in result.steps:
        status_mark = "OK" if step.is_success else "FAIL"
        print(f"  [{status_mark}] {step.name:12s} count={step.count} "
              f"duration={step.duration_seconds:.2f}s"
              + (f" error={step.error}" if step.error else ""))

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
