from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models.article import Article
from app.services.dedup_service import DedupService, _jaccard_similarity, normalize_title

# Each test article gets a completely disjoint body to prevent Layer 3
# (content similarity) from false-matching articles in different test
# scenarios.
_COUNTER = 100000
_TOPICS = [
    "astronomy galaxies nebula telescope orbit stellar cosmic",
    "cuisine recipe ingredients culinary gastronomy fermentation",
    "architecture blueprint foundation structural facade geometry",
    "botany photosynthesis germination pollination horticulture",
    "oceanography current tide coral reef bathymetric pelagic",
    "linguistics syntax phonology semantics morphology etymology",
    "mythology folklore legend deity ritual pantheon oracle",
    "medicine diagnosis prognosis therapy rehabilitation clinic",
    "meteorology precipitation barometer isobar cyclone anvil",
    "geology tectonic sediment erosion fossil strata mineral",
    "archaeology excavation artifact antiquity burial stratigraphy",
    "philosophy epistemology ontology ethics metaphysics dialectic",
    "sociology anthropology demography migration stratification",
    "astronomy redshift nebula quasar pulsar cosmology exoplanet",
    "economics macro fiscal monetary austerity stimulus gdp",
]


def _unique_body() -> str:
    """Return a body with completely disjoint word sets compared to any
    other call.  This ensures Layer 3 never false-matches unrelated articles."""
    global _COUNTER
    topic = _TOPICS[_COUNTER % len(_TOPICS)]
    _COUNTER += 1
    return (
        f"{topic} {' '.join(topic.split()[::-1])} "
        f"article_{_COUNTER} section_{_COUNTER % 100} identifier_{_COUNTER}"
    )


def _article(
    title: str = "Test Title",
    url: str = "https://example.com/article",
    summary: str | None = None,
    body: str | None = None,
    source_id: int = 1,
    normalized_url: str | None = None,
    updated_at=None,
) -> Article:
    now = datetime.now(timezone.utc)
    if body is None:
        body = _unique_body()
    a = Article(
        source_id=source_id,
        url=url,
        title=title,
        summary=summary,
        body=body,
        normalized_url=normalized_url or url,
        created_at=now,
        updated_at=updated_at or now,
    )
    a.id = _COUNTER
    return a


class TestNormalizeTitle:
    def test_lowercase(self) -> None:
        assert normalize_title("BREAKING NEWS") == "breaking news"

    def test_strip_media_prefix(self) -> None:
        assert normalize_title("BBC: World at War").startswith("world at war")

    def test_strip_punctuation(self) -> None:
        result = normalize_title("Hello, World! How are you?")
        assert "," not in result
        assert "!" not in result
        assert "?" not in result

    def test_multiple_spaces_collapsed(self) -> None:
        result = normalize_title("Hello    World")
        assert result == "hello world"

    def test_different_media_prefixes(self) -> None:
        nyt = normalize_title("NYT: Breaking News")
        cnn = normalize_title("CNN Breaking News")
        assert nyt == cnn

    def test_empty_string(self) -> None:
        assert normalize_title("") == ""

    def test_only_punctuation(self) -> None:
        r = normalize_title("!!! ???")
        assert r == ""


class TestJaccardSimilarity:
    def test_identical(self) -> None:
        assert _jaccard_similarity("hello world", "hello world") == 1.0

    def test_partial_overlap(self) -> None:
        s = _jaccard_similarity("hello world foo", "hello world bar")
        assert s == 0.5  # {hello,world,foo} ∩ {hello,world,bar} = 2, ∪ = 4

    def test_no_overlap(self) -> None:
        assert _jaccard_similarity("hello world", "foo bar baz") == 0.0

    def test_both_empty(self) -> None:
        assert _jaccard_similarity("", "") == 1.0

    def test_one_empty(self) -> None:
        assert _jaccard_similarity("hello", "") == 0.0


class TestDedupServiceUrlLayer:
    """Layer 1: URL exact match."""

    def test_url_match_dedup(self) -> None:
        articles = [
            _article(url="https://example.com/news", title="News A", source_id=1),
            _article(url="https://example.com/news", title="News A (dup)", source_id=2),
        ]
        service = DedupService()
        result = service.deduplicate(articles)
        assert len(result) == 1

    def test_url_no_match(self) -> None:
        articles = [
            _article(url="https://example.com/a", title="Article A", source_id=1),
            _article(url="https://example.com/b", title="Article B", source_id=2),
        ]
        service = DedupService()
        result = service.deduplicate(articles)
        assert len(result) == 2


class TestDedupServiceTitleLayer:
    """Layer 2: Title similarity."""

    def test_title_duplicate_detected(self) -> None:
        articles = [
            _article(
                url="https://example.com/a",
                title="Breaking: Major Event Happens Today",
                source_id=1,
            ),
            _article(
                url="https://example.com/b",
                title="Breaking: Major Event Happens Today",
                source_id=2,
            ),
        ]
        service = DedupService()
        result = service.deduplicate(articles)
        assert len(result) == 1

    def test_title_similar_but_different(self) -> None:
        """Titles with Jaccard below threshold should remain separate."""
        articles = [
            _article(
                url="https://example.com/a",
                title="Completely Different Topic One Two Three Four",
                source_id=1,
            ),
            _article(
                url="https://example.com/b",
                title="Some Other Unrelated News Story Here Today",
                source_id=2,
            ),
        ]
        service = DedupService()
        result = service.deduplicate(articles)
        assert len(result) == 2

    def test_media_prefix_stripped_before_comparison(self) -> None:
        articles = [
            _article(
                url="https://bbc.com/a",
                title="BBC: Climate Summit Reaches Agreement",
                source_id=1,
            ),
            _article(
                url="https://cnn.com/b",
                title="CNN: Climate Summit Reaches Agreement",
                source_id=2,
            ),
        ]
        service = DedupService()
        result = service.deduplicate(articles)
        assert len(result) == 1


class TestDedupServiceContentLayer:
    """Layer 3: Content similarity (TF-IDF cosine)."""

    def test_content_duplicate_detected(self) -> None:
        body = (
            "The president signed the new bill into law today at a ceremony "
            "attended by lawmakers from both parties. The legislation will "
            "provide funding for infrastructure projects across the country."
        )
        articles = [
            _article(
                url="https://example.com/a",
                title="Different Title A",
                body=body,
                source_id=1,
            ),
            _article(
                url="https://example.com/b",
                title="Different Title B",
                body=body,
                source_id=2,
            ),
        ]
        service = DedupService()
        result = service.deduplicate(articles)
        assert len(result) == 1

    def test_content_no_duplicate(self) -> None:
        articles = [
            _article(
                url="https://example.com/a",
                title="Title One",
                body="The quick brown fox jumps over the lazy dog. This is "
                     "completely unique content about nature and animals.",
                source_id=1,
            ),
            _article(
                url="https://example.com/b",
                title="Title Two",
                body="Stock markets rallied today as the Federal Reserve "
                     "announced a new interest rate policy. Investors were "
                     "optimistic about the economic outlook.",
                source_id=2,
            ),
        ]
        service = DedupService()
        result = service.deduplicate(articles)
        assert len(result) == 2


class TestDedupServiceAllLayersMiss:
    """All three layers miss — every article should be kept."""

    def test_all_unique(self) -> None:
        articles = [
            _article(
                url="https://example.com/a",
                title="Politics News Today",
                body="Government passes new law.",
                source_id=1,
            ),
            _article(
                url="https://example.com/b",
                title="Tech Breakthrough",
                body="Scientists discover new quantum computing method.",
                source_id=2,
            ),
            _article(
                url="https://example.com/c",
                title="Sports Update",
                body="Team wins championship in thrilling final game.",
                source_id=3,
            ),
        ]
        service = DedupService()
        result = service.deduplicate(articles)
        assert len(result) == 3


class TestDedupServicePickBest:
    """Quality_score-based retention rule."""

    def test_higher_quality_wins(self) -> None:
        articles = [
            _article(
                url="https://example.com/a",
                title="Same Title Shared By All",
                source_id=1,
            ),
            _article(
                url="https://example.com/b",
                title="Same Title Shared By All",
                source_id=2,
            ),
        ]
        quality_map = {1: 0.9, 2: 0.5}
        service = DedupService()
        result = service.deduplicate(articles, quality_map=quality_map)
        assert len(result) == 1
        assert result[0].source_id == 1

    def test_tie_breaker_newer_wins(self) -> None:
        now = datetime.now(timezone.utc)
        a1 = _article(
            url="https://example.com/a",
            title="Same Title Shared By All",
            source_id=1,
            updated_at=now,
        )
        a2 = _article(
            url="https://example.com/b",
            title="Same Title Shared By All",
            source_id=2,
            updated_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        quality_map = {1: 0.7, 2: 0.7}
        service = DedupService()
        result = service.deduplicate([a1, a2], quality_map=quality_map)
        assert len(result) == 1
        assert result[0].source_id == 1


class TestDedupServiceEdgeCases:
    def test_empty_list(self) -> None:
        service = DedupService()
        assert service.deduplicate([]) == []

    def test_single_article(self) -> None:
        a = _article(title="Only One", url="https://example.com/one")
        service = DedupService()
        result = service.deduplicate([a])
        assert len(result) == 1
        assert result[0].title == "Only One"

    def test_no_url_no_title(self) -> None:
        """Articles with missing URL or title should not crash the service."""
        a1 = _article(url="https://example.com/a", title="Has Title", source_id=1)
        a2 = _article(url="https://example.com/b", title="", source_id=2)
        a2.url = ""
        a2.normalized_url = ""
        service = DedupService()
        result = service.deduplicate([a1, a2])
        assert len(result) == 2
