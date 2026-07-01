from __future__ import annotations

from collections import Counter
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.cluster_member import ClusterMember
from app.repositories.cluster_repository import ClusterRepository


DEFAULT_SIMILARITY_THRESHOLD = 0.6
SCORE_ARTICLE_WEIGHT = 0.4
SCORE_SOURCE_WEIGHT = 0.6
SINGLE_SOURCE_PENALTY = 0.5


class ClusterService:
    """事件聚类服务。

    将多家媒体对同一事件的报道聚成 Cluster，计算代表文章与排序分值。

    算法：TF-IDF + cosine similarity，全量扫描 since 之后的文章并贪心分组。
    同一篇文章只会出现在一个 cluster 中；已聚类的文章自动跳过。
    """

    def __init__(
        self,
        db: Session,
        threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ):
        self.db = db
        self.threshold = threshold
        self.repo = ClusterRepository(db)

    # ------------------------------------------------------------------
    # 公共入口
    # ------------------------------------------------------------------

    def cluster_articles(self, since: datetime) -> int:
        """对 since 之后（含）创建的文章执行聚类，返回新建 cluster 数量。"""
        articles = self._load_articles_since(since)
        if not articles:
            return 0

        already_clustered = self.repo.get_clustered_article_ids()
        pending = [a for a in articles if a.id not in already_clustered]
        if not pending:
            return 0

        groups = self._group_by_similarity(pending)

        created = 0
        for group in groups:
            if len(group) < 2:
                # 单篇文章不单独成 cluster
                continue
            self._create_cluster_for_group(group)
            created += 1

        self.db.commit()
        return created

    # ------------------------------------------------------------------
    # 数据加载
    # ------------------------------------------------------------------

    def _load_articles_since(self, since: datetime) -> list[Article]:
        """加载 since 之后创建的文章，并预取其 source 以避免 N+1 查询。"""
        rows = (
            self.db.query(Article)
            .filter(Article.created_at >= since)
            .order_by(Article.created_at.asc())
            .all()
        )
        for article in rows:
            _ = article.source  # 触发懒加载
        return rows

    # ------------------------------------------------------------------
    # 聚类
    # ------------------------------------------------------------------

    def _group_by_similarity(self, articles: list[Article]) -> list[list[Article]]:
        """TF-IDF + cosine 相似度贪心分组。

        优化：先按 topic 预分组，只在同 topic 内算相似度，减少 O(n²) 比较量。
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        # Pre-group by topic to reduce comparisons
        topic_groups: dict[str, list[Article]] = {}
        for a in articles:
            t = a.topic or "general"
            topic_groups.setdefault(t, []).append(a)

        all_groups: list[list[Article]] = []
        for topic, topic_articles in topic_groups.items():
            if len(topic_articles) < 2:
                all_groups.append(topic_articles)
                continue

            corpus = [self._article_text(a) for a in topic_articles]
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(corpus)

            groups: list[list[int]] = []
            for idx in range(len(topic_articles)):
                vec = tfidf_matrix[idx]
                placed = False
                for member_indices in groups:
                    rep_vec = tfidf_matrix[member_indices[0]]
                    sim = float(cosine_similarity(vec, rep_vec)[0, 0])
                    if sim >= self.threshold:
                        member_indices.append(idx)
                        placed = True
                        break
                if not placed:
                    groups.append([idx])

            all_groups.extend([[topic_articles[i] for i in g] for g in groups])

        return all_groups

    @staticmethod
    def _article_text(article: Article) -> str:
        summary = article.summary or ""
        return f"{article.title} {summary}".strip()

    # ------------------------------------------------------------------
    # 代表文章与分值
    # ------------------------------------------------------------------

    def _select_representative(self, group: list[Article]) -> Article:
        """选取 cluster 内 source 最丰富的文章。

        解读为：该文章所属 source 在本组中出现的次数最多（来自报道量最大
        的来源），平局时取组内第一篇。
        """
        if len(group) == 1:
            return group[0]

        source_counts: dict[int, int] = {}
        for a in group:
            source_counts[a.source_id] = source_counts.get(a.source_id, 0) + 1

        best = group[0]
        best_count = source_counts[best.source_id]
        for a in group[1:]:
            count = source_counts[a.source_id]
            if count > best_count:
                best = a
                best_count = count
        return best

    def _compute_score(self, group: list[Article]) -> float:
        article_count = len(group)
        distinct_sources = len({a.source_id for a in group})
        score = (
            article_count * SCORE_ARTICLE_WEIGHT
            + distinct_sources * SCORE_SOURCE_WEIGHT
        )
        if distinct_sources <= 1:
            score *= SINGLE_SOURCE_PENALTY
        return round(score, 4)

    @staticmethod
    def _pick_topic(group: list[Article]) -> str:
        """Pick cluster topic by majority vote from member articles.

        Falls back to ``general`` if no articles have a topic set.
        """
        topics = [a.topic for a in group if a.topic]
        if not topics:
            return "general"
        return Counter(topics).most_common(1)[0][0]

    def _create_cluster_for_group(self, group: list[Article]) -> None:
        representative = self._select_representative(group)
        score = self._compute_score(group)
        topic = self._pick_topic(group)

        cluster = self.repo.create_cluster(
            representative_article_id=representative.id,
            size=len(group),
            score=score,
            topic=topic,
        )
        # 代表文章 rank=0，其余按 created_at 升序顺延
        rest = sorted(
            (a for a in group if a.id != representative.id),
            key=lambda a: a.created_at,
        )
        ordered = [representative] + rest
        for rank, article in enumerate(ordered):
            self.repo.add_member(cluster.id, article.id, rank)

    # ------------------------------------------------------------------
    # 查询辅助（供 digest 生成等服务复用）
    # ------------------------------------------------------------------

    def get_cluster_members(self, cluster_id: int) -> list[Article]:
        """返回某 cluster 的全部成员文章（按 rank 升序）。"""
        rows = (
            self.db.query(Article)
            .join(ClusterMember, ClusterMember.article_id == Article.id)
            .filter(ClusterMember.cluster_id == cluster_id)
            .order_by(ClusterMember.rank.asc())
            .all()
        )
        return rows
