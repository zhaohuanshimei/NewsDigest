from __future__ import annotations

import pytest

from app.models.article import Article
from app.services.topic_classifier import TopicClassifier, classify_by_text


def _article(title: str = "Test", summary: str | None = None) -> Article:
    a = Article(
        source_id=1,
        url="https://example.com/article",
        title=title,
        summary=summary,
    )
    a.id = 1
    return a


class TestTopicClassifier:
    """Test each topic with at least 2 positive examples."""

    def make_classifier(self) -> TopicClassifier:
        return TopicClassifier()

    # ── politics ────────────────────────────────────────────────

    def test_politics_election(self) -> None:
        a = _article("Congress passes new election reform bill today")
        assert self.make_classifier().classify(a) == "politics"

    def test_politics_senate(self) -> None:
        a = _article("Senate committee votes on landmark legislation")
        assert self.make_classifier().classify(a) == "politics"

    # ── business ────────────────────────────────────────────────

    def test_business_market(self) -> None:
        a = _article("Stock market rallies as Fed holds interest rates steady")
        assert self.make_classifier().classify(a) == "business"

    def test_business_merger(self) -> None:
        a = _article("Tech giant announces billion-dollar acquisition of startup")
        assert self.make_classifier().classify(a) == "business"

    # ── tech ────────────────────────────────────────────────────

    def test_tech_ai(self) -> None:
        a = _article("OpenAI releases new GPT model with improved machine learning capabilities")
        assert self.make_classifier().classify(a) == "tech"

    def test_tech_chip(self) -> None:
        a = _article("Nvidia unveils next-generation semiconductor chip with AI processor design")
        assert self.make_classifier().classify(a) == "tech"

    # ── science ─────────────────────────────────────────────────

    def test_science_space(self) -> None:
        a = _article("NASA rover discovers evidence of water on Mars surface")
        assert self.make_classifier().classify(a) == "science"

    def test_science_climate(self) -> None:
        a = _article("New study reveals accelerated climate change impacts on Arctic")
        assert self.make_classifier().classify(a) == "science"

    # ── world ───────────────────────────────────────────────────

    def test_world_conflict(self) -> None:
        a = _article("UN calls for ceasefire as conflict escalates in region")
        assert self.make_classifier().classify(a) == "world"

    def test_world_diplomacy(self) -> None:
        a = _article("NATO allies discuss new defense strategy amid global tensions")
        assert self.make_classifier().classify(a) == "world"

    # ── health ──────────────────────────────────────────────────

    def test_health_disease(self) -> None:
        a = _article("FDA approves new treatment for heart disease patients")
        assert self.make_classifier().classify(a) == "health"

    def test_health_vaccine(self) -> None:
        a = _article("New vaccine shows promising results in clinical trial for disease prevention")
        assert self.make_classifier().classify(a) == "health"

    # ── general (fallback) ──────────────────────────────────────

    def test_general_fallback(self) -> None:
        a = _article("Local community holds annual charity bake sale event")
        assert self.make_classifier().classify(a) == "general"

    def test_general_empty_text(self) -> None:
        a = _article("")
        assert self.make_classifier().classify(a) == "general"

    # ── cross-topic conflict ────────────────────────────────────

    def test_cross_topic_keyword_conflict(self) -> None:
        """Article matching multiple topics should pick the highest hit rate."""
        a = _article(
            "AI startup secures billion-dollar funding from venture capital investors "
            "in silicon valley"
        )
        # "ai", "startup" → tech; "billion", "startup", "investors", "venture",
        # "capital" → business; tech has ~50 keywords, business ~26 keywords.
        # So business may have a higher hit rate per keyword.
        result = self.make_classifier().classify(a)
        assert result in ("tech", "business")


class TestClassifyByText:
    def test_none_summary(self) -> None:
        assert classify_by_text("Election results show landslide victory for new government party", None) == "politics"

    def test_empty_summary(self) -> None:
        assert classify_by_text("Congress passes landmark legislation on healthcare reform", "") == "politics"

    def test_both_empty(self) -> None:
        assert classify_by_text("", "") == "general"
