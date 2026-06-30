from __future__ import annotations

import re

from app.core.topic_rules import MIN_MATCHES, TOPIC_RULES
from app.models.article import Article


class TopicClassifier:
    """Rule-based topic classifier.

    Classifies articles into one of:
    ``politics / business / tech / science / world / health / general``

    This is a pure function — no database or external state required.
    """

    def classify(self, article: Article) -> str:
        """Return the topic label for the given article."""
        return classify_by_text(article.title, article.summary)


def classify_by_text(title: str, summary: str | None) -> str:
    """Classify by title and summary text.

    The topic with the most keyword matches wins.  If the winner has fewer
    than ``MIN_MATCHES`` the article is classified as ``general``.

    Args:
        title: Article title.
        summary: Article summary (may be None or empty).

    Returns:
        One of ``politics / business / tech / science / world / health / general``.
    """
    text = _prepare_text(title, summary)
    if not text:
        return "general"

    best_topic = "general"
    best_hits = 0

    for topic, keywords in TOPIC_RULES.items():
        hits = 0
        for kw in keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text):
                hits += 1

        if hits > best_hits:
            best_hits = hits
            best_topic = topic

    if best_hits < MIN_MATCHES:
        return "general"

    return best_topic


def _prepare_text(title: str, summary: str | None) -> str:
    """Combine title and summary into a single lowercased search string."""
    parts = [title]
    if summary:
        parts.append(summary)
    combined = " ".join(parts).lower()
    combined = combined.strip()
    return combined
