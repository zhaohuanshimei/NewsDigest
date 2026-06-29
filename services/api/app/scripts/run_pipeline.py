"""CLI entrypoint to run the full ingest + digest + translation pipeline.

Usage:
    python -m app.scripts.run_pipeline                    # today
    python -m app.scripts.run_pipeline --date 2026-06-29  # specific date
    python -m app.scripts.run_pipeline --no-translate     # skip translation
    python -m app.scripts.run_pipeline --seed             # seed default sources first
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date, datetime, timedelta

import structlog

from app.database import SessionLocal
from app.repositories.article_repository import ArticleRepository
from app.repositories.source_repository import SourceRepository
from app.services.article_normalizer import ArticleNormalizer
from app.services.article_service import ArticleService
from app.services.cluster_service import ClusterService
from app.services.digest_generator import DigestGenerator
from app.services.fetchers.rss_fetcher import RssFetcher
from app.services.source_service import SourceService
from app.services.translation_provider_factory import build_translation_provider
from app.services.translation_service import PipelineTranslatorAdapter

logger = structlog.get_logger()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full news digest pipeline")
    parser.add_argument("--date", type=str, default=None, help="Target date YYYY-MM-DD")
    parser.add_argument("--no-translate", action="store_true", help="Skip translation")
    parser.add_argument("--seed", action="store_true", help="Seed default sources first")
    return parser.parse_args()


def _step(name: str, func: callable) -> tuple[str, str, int, str | None]:
    """Run a step, return (name, status, count, error)."""
    start = time.time()
    try:
        result = func()
        duration = time.time() - start
        count = result if isinstance(result, int) else 0
        logger.info("pipeline_step_done", name=name, count=count, duration=duration)
        return (name, "OK", count, None)
    except Exception as exc:
        duration = time.time() - start
        logger.error("pipeline_step_failed", name=name, error=str(exc), duration=duration)
        return (name, "FAIL", 0, str(exc))


def main() -> int:
    args = _parse_args()
    target_date = date.fromisoformat(args.date) if args.date else date.today()

    with SessionLocal() as session:
        # Step 0: Seed sources if requested or if none exist
        source_repo = SourceRepository(session)
        if args.seed or not source_repo.list_all():
            print(">>> Seeding default sources...")
            source_service = SourceService(source_repo)
            sources = source_service.seed_default_sources(session)
            print(f"    Seeded {len(sources)} sources")

        # Step 1: Fetch RSS from all active sources
        print(f"\nPipeline for {target_date}")
        print("=" * 50)

        fetcher = RssFetcher()
        article_repo = ArticleRepository(session)
        article_service = ArticleService(article_repo, source_repo, fetcher)

        results = _step("fetch", lambda: article_service.fetch_all_active_sources(session))
        name, status, count, error = results
        fetch_result = article_service.fetch_all_active_sources(session) if status == "OK" else {}
        total_new = sum(v[0] for v in fetch_result.values()) if fetch_result else 0
        total_dup = sum(v[1] for v in fetch_result.values()) if fetch_result else 0
        print(f"  [{status}] {name:12s} new={total_new} dup={total_dup}"
              + (f" error={error}" if error else ""))

        # Step 2: Normalize pending articles
        normalizer = ArticleNormalizer(session)
        # ArticleNormalizer doesn't have normalize_pending_articles — it works
        # per-article during fetch_and_persist. So we skip this step.
        # The fetcher's normalize() is called inside ArticleService.fetch_and_persist.
        print(f"  [SKIP] normalize      (handled during fetch)")

        # Step 3: Cluster articles from yesterday and today
        since = datetime.combine(target_date - timedelta(days=1), datetime.min.time())
        clusterer = ClusterService(session)
        name, status, count, error = _step("cluster", lambda: clusterer.cluster_articles(since=since))
        print(f"  [{status}] {name:12s} clusters={count}"
              + (f" error={error}" if error else ""))

        # Step 4: Generate digest
        digest_gen = DigestGenerator(session)
        name, status, count, error = _step("digest", lambda: digest_gen.generate(target_date=target_date))
        print(f"  [{status}] {name:12s} digest={'created' if status == 'OK' else 'failed'}"
              + (f" error={error}" if error else ""))

        # Step 5: Translate (if configured)
        if not args.no_translate:
            provider = build_translation_provider()
            print(f"\n  Translation provider: {provider.name}")
            if provider.name != "null":
                adapter = PipelineTranslatorAdapter(session, provider=provider)
                name, status, count, error = _step("translate", lambda: adapter.translate_digest_entries(target_date=target_date))
                print(f"  [{status}] {name:12s} entries={count}"
                      + (f" error={error}" if error else ""))
            else:
                print(f"  [SKIP] translate      (no TRANSLATION_* env vars)")
        else:
            print(f"\n  [SKIP] translate      (--no-translate)")

    print("\n" + "=" * 50)
    print("Pipeline complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
