from __future__ import annotations

import re
import string
from collections import defaultdict
from typing import Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.article import Article
from app.repositories.article_repository import ArticleRepository

# Known media name prefixes to strip during title normalization
MEDIA_PREFIXES: frozenset[str] = frozenset({
    "BBC", "CNN", "NYT", "NPR", "ABC News", "NBC News", "CBS News",
    "Sky News", "Reuters", "AP", "The Associated Press",
    "The Guardian", "Guardian", "WashPost", "Washington Post",
    "The Washington Post", "Al Jazeera", "DW", "France 24",
    "USA Today", "The Independent", "Politico", "The Hill",
    "Ars Technica", "The Verge", "WIRED", "TechCrunch",
    "CNBC", "MarketWatch", "New Scientist", "Scientific American",
    "Bloomberg", "WSJ", "The Wall Street Journal",
    "Financial Times", "The Economist",
})

# Title Jaccard similarity threshold (Layer 2)
TITLE_SIMILARITY_THRESHOLD = 0.85

# Content TF-IDF cosine similarity threshold (Layer 3)
CONTENT_SIMILARITY_THRESHOLD = 0.88


def normalize_title(title: str) -> str:
    """Normalize a title for similarity comparison.

    Steps: lowercase → strip media prefixes → remove punctuation → trim.
    """
    normalized = title.lower().strip()

    # Strip known media name prefixes
    for prefix in sorted(MEDIA_PREFIXES, key=len, reverse=True):
        prefix_lower = prefix.lower()
        if normalized.startswith(prefix_lower):
            # Remove the prefix and any following colon/dash/space
            normalized = normalized[len(prefix_lower) :].lstrip(": -–—|/\\")
            break

    # Remove punctuation characters
    translator = str.maketrans("", "", string.punctuation)
    normalized = normalized.translate(translator)

    # Collapse whitespace and trim
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def _jaccard_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity between two strings."""
    set_a = set(a.split())
    set_b = set(b.split())
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _get_content_text(article: Article) -> str:
    """Get the best available content text for an article."""
    parts = []
    if article.summary:
        parts.append(article.summary)
    if article.body:
        parts.append(article.body)
    return " ".join(parts)


class DedupService:
    """Multi-layer deduplication service for articles.

    Three-layer funnel:
      Layer 1: URL exact match (via repository)
      Layer 2: Title similarity (Jaccard > 0.85)
      Layer 3: Content similarity (TF-IDF cosine > 0.88, only for Layer-2 misses)
    """

    def __init__(
        self,
        repository: ArticleRepository | None = None,
    ) -> None:
        self.repository = repository

    def deduplicate(
        self,
        articles: list[Article],
        quality_map: dict[int, float] | None = None,
    ) -> list[Article]:
        """Deduplicate a list of articles using the three-layer funnel.

        When a group of articles refers to the same event, only the one with
        the highest source quality_score is kept.  Ties are broken by
        updated_at (newer wins) and then by id (lower wins, i.e. seen first).

        Args:
            articles: List of articles to deduplicate.
            quality_map: Mapping of source_id → quality_score.  Articles
                from sources not in the map get a default score of 0.5.

        Returns:
            Deduplicated list of articles.
        """
        if len(articles) <= 1:
            return list(articles)

        quality_map = quality_map or {}
        n = len(articles)

        # ── Layer 1: URL exact match ──────────────────────────────
        url_groups: dict[str, list[int]] = defaultdict(list)
        url_articles: list[Article] = []
        url_key: dict[int, str] = {}

        for i, a in enumerate(articles):
            url = (a.normalized_url or a.url or "").strip().lower()
            if url:
                url_groups[url].append(i)
                url_key[i] = url
            else:
                url_articles.append(a)

        # Dedup within each URL group
        seen_urls: set[str] = set()
        for i, a in enumerate(articles):
            key = url_key.get(i)
            if key is None:
                continue
            if key in seen_urls:
                continue
            seen_urls.add(key)
            group = [articles[idx] for idx in url_groups[key]]
            best = self._pick_best(group, quality_map)
            url_articles.append(best)

        # ── Layer 2: Title similarity ────────────────────────────
        title_groups: list[list[Article]] = []
        title_remaining: list[Article] = []

        for a in url_articles:
            normalized = normalize_title(a.title)
            placed = False
            for group in title_groups:
                rep_norm = normalize_title(group[0].title)
                if _jaccard_similarity(normalized, rep_norm) > TITLE_SIMILARITY_THRESHOLD:
                    group.append(a)
                    placed = True
                    break
            if not placed:
                title_groups.append([a])

        for group in title_groups:
            if len(group) == 1:
                title_remaining.append(group[0])
            else:
                # These articles share the same title → same event.
                # Further check via content similarity if needed.
                best = self._pick_best(group, quality_map)
                title_remaining.append(best)

        # ── Layer 3: Content similarity (only for Layer-2 misses) ─
        # Build a corpus from articles that passed Layer 2
        if len(title_remaining) <= 1:
            return title_remaining

        texts = [_get_content_text(a) for a in title_remaining]
        # Filter out articles with no content text
        valid_indices = [i for i, t in enumerate(texts) if t.strip()]
        if len(valid_indices) <= 1:
            return title_remaining

        valid_articles = [title_remaining[i] for i in valid_indices]
        valid_texts = [texts[i] for i in valid_indices]

        try:
            vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words="english",
                lowercase=True,
            )
            tfidf_matrix = vectorizer.fit_transform(valid_texts)
            sim_matrix = cosine_similarity(tfidf_matrix)

            # Build content-based groups
            assigned = [False] * len(valid_articles)
            content_groups: list[list[Article]] = []

            for i in range(len(valid_articles)):
                if assigned[i]:
                    continue
                group = [valid_articles[i]]
                assigned[i] = True
                for j in range(i + 1, len(valid_articles)):
                    if assigned[j]:
                        continue
                    if sim_matrix[i, j] > CONTENT_SIMILARITY_THRESHOLD:
                        group.append(valid_articles[j])
                        assigned[j] = True
                content_groups.append(group)

            # Pick best per content group
            content_result: list[Article] = []
            for group in content_groups:
                if len(group) == 1:
                    content_result.append(group[0])
                else:
                    content_result.append(self._pick_best(group, quality_map))

            # Re-insert articles that had empty text
            for i in range(len(title_remaining)):
                if i not in valid_indices:
                    content_result.append(title_remaining[i])

            return content_result

        except ValueError:
            # TF-IDF may fail on very short/corpus
            return title_remaining

    def _pick_best(
        self,
        candidates: list[Article],
        quality_map: dict[int, float],
    ) -> Article:
        """Pick the best article from a group of duplicates.

        Preference order:
          1. Highest source quality_score
          2. Newest updated_at
          3. Lowest id (seen first)
        """
        return max(
            candidates,
            key=lambda a: (
                quality_map.get(a.source_id, 0.5),
                a.updated_at or a.created_at,
                -a.id,
            ),
        )
