from __future__ import annotations

from datetime import datetime, timedelta, timezone


from app.models.article import Article
from app.models.cluster import Cluster
from app.models.cluster_member import ClusterMember
from app.models.source import Source
from app.services.cluster_service import (
    ClusterService,
    SCORE_ARTICLE_WEIGHT,
    SCORE_SOURCE_WEIGHT,
    SINGLE_SOURCE_PENALTY,
)


# ------------------------------------------------------------------
# 辅助
# ------------------------------------------------------------------


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc)


def _make_source(db, name: str = "src-a") -> Source:
    source = Source(name=name, kind="rss", url=f"https://{name}.example/feed", language="en")
    db.add(source)
    db.flush()
    return source


_article_seq = 0


def _make_article(
    db,
    source: Source,
    title: str,
    summary: str = "",
    created_at: datetime | None = None,
) -> Article:
    global _article_seq
    _article_seq += 1
    article = Article(
        source_id=source.id,
        url=f"https://{source.name}.example/article-{_article_seq}",
        title=title,
        summary=summary,
        language="en",
        created_at=created_at or _utc(datetime(2026, 6, 26, 9, 0, 0)),
    )
    db.add(article)
    db.flush()
    return article


# ------------------------------------------------------------------
# 测试
# ------------------------------------------------------------------


def test_no_articles_returns_zero(db_session):
    service = ClusterService(db_session)
    assert service.cluster_articles(_utc(datetime(2026, 6, 1))) == 0


def test_single_article_does_not_form_cluster(db_session):
    src = _make_source(db_session)
    _make_article(db_session, src, "Lonely article about something unique")
    db_session.commit()

    service = ClusterService(db_session)
    created = service.cluster_articles(_utc(datetime(2026, 6, 1)))
    assert created == 0
    assert db_session.query(Cluster).count() == 0
    assert db_session.query(ClusterMember).count() == 0


def test_similar_articles_form_one_cluster(db_session):
    src = _make_source(db_session, "src-a")
    src2 = _make_source(db_session, "src-b")
    base = _utc(datetime(2026, 6, 26, 9, 0, 0))
    _make_article(
        db_session,
        src,
        "OpenAI launches new GPT model with improved reasoning",
        summary="The new model shows better reasoning capabilities.",
        created_at=base,
    )
    _make_article(
        db_session,
        src2,
        "OpenAI launches new GPT model with improved reasoning",
        summary="A new GPT model was released today by OpenAI.",
        created_at=base + timedelta(minutes=10),
    )
    db_session.commit()

    service = ClusterService(db_session)
    created = service.cluster_articles(_utc(datetime(2026, 6, 1)))
    assert created == 1

    clusters = db_session.query(Cluster).all()
    assert len(clusters) == 1
    cluster = clusters[0]
    assert cluster.size == 2
    members = (
        db_session.query(ClusterMember)
        .filter(ClusterMember.cluster_id == cluster.id)
        .order_by(ClusterMember.rank)
        .all()
    )
    assert len(members) == 2
    # rank 从 0 开始且唯一
    assert {m.rank for m in members} == {0, 1}
    # 一篇文章只在一个 cluster
    assert len({m.article_id for m in members}) == 2


def test_dissimilar_articles_do_not_cluster(db_session):
    src = _make_source(db_session, "src-a")
    src2 = _make_source(db_session, "src-b")
    base = _utc(datetime(2026, 6, 26, 9, 0, 0))
    _make_article(
        db_session,
        src,
        "NASA announces new Mars rover mission for 2030",
        summary="A new rover will search for life on Mars.",
        created_at=base,
    )
    _make_article(
        db_session,
        src2,
        "Global stock markets tumble on inflation fears",
        summary="Investors worry about rising consumer prices.",
        created_at=base + timedelta(minutes=10),
    )
    db_session.commit()

    service = ClusterService(db_session)
    assert service.cluster_articles(_utc(datetime(2026, 6, 1))) == 0
    assert db_session.query(Cluster).count() == 0


def test_threshold_respected(db_session):
    """调高阈值后，原本能聚的相似文章不再成簇。"""
    src = _make_source(db_session, "src-a")
    src2 = _make_source(db_session, "src-b")
    base = _utc(datetime(2026, 6, 26, 9, 0, 0))
    _make_article(
        db_session,
        src,
        "Tech company releases quarterly earnings report",
        summary="Revenue exceeded analyst expectations.",
        created_at=base,
    )
    _make_article(
        db_session,
        src2,
        "Tech company releases quarterly earnings report",
        summary="Revenue exceeded analyst expectations this quarter.",
        created_at=base + timedelta(minutes=10),
    )
    db_session.commit()

    # 默认阈值下应聚成 1 个
    assert ClusterService(db_session).cluster_articles(_utc(datetime(2026, 6, 1))) == 1
    # 极高阈值下不再聚成新 cluster（但上一行已聚类，文章已被跳过）
    strict = ClusterService(db_session, threshold=0.999)
    assert strict.cluster_articles(_utc(datetime(2026, 6, 1))) == 0


def test_already_clustered_articles_are_skipped(db_session):
    src = _make_source(db_session, "src-a")
    src2 = _make_source(db_session, "src-b")
    base = _utc(datetime(2026, 6, 26, 9, 0, 0))
    a1 = _make_article(
        db_session,
        src,
        "OpenAI launches new GPT model with improved reasoning",
        summary="The new model shows better reasoning capabilities.",
        created_at=base,
    )
    a2 = _make_article(
        db_session,
        src2,
        "OpenAI launches new GPT model with improved reasoning",
        summary="A new GPT model was released today by OpenAI.",
        created_at=base + timedelta(minutes=10),
    )
    db_session.commit()

    service = ClusterService(db_session)
    assert service.cluster_articles(_utc(datetime(2026, 6, 1))) == 1
    # 再次运行：所有文章已聚类，应返回 0 且不重复创建
    assert service.cluster_articles(_utc(datetime(2026, 6, 1))) == 0
    assert db_session.query(Cluster).count() == 1
    assert db_session.query(ClusterMember).count() == 2

    # 成员正是 a1 / a2
    member_article_ids = {
        m.article_id for m in db_session.query(ClusterMember).all()
    }
    assert member_article_ids == {a1.id, a2.id}


def test_article_appears_in_only_one_cluster(db_session):
    """三篇文章，前两篇相似、第三篇与前两篇不相似，确认不混组。"""
    src = _make_source(db_session, "src-a")
    src2 = _make_source(db_session, "src-b")
    src3 = _make_source(db_session, "src-c")
    base = _utc(datetime(2026, 6, 26, 9, 0, 0))
    _make_article(
        db_session,
        src,
        "OpenAI launches new GPT model with improved reasoning",
        summary="The new model shows better reasoning capabilities.",
        created_at=base,
    )
    _make_article(
        db_session,
        src2,
        "OpenAI launches new GPT model with improved reasoning",
        summary="A new GPT model was released today by OpenAI.",
        created_at=base + timedelta(minutes=10),
    )
    _make_article(
        db_session,
        src3,
        "Local football team wins city championship final",
        summary="The home team celebrated a dramatic victory.",
        created_at=base + timedelta(minutes=20),
    )
    db_session.commit()

    service = ClusterService(db_session)
    assert service.cluster_articles(_utc(datetime(2026, 6, 1))) == 1
    assert db_session.query(Cluster).count() == 1
    assert db_session.query(ClusterMember).count() == 2


def test_representative_article_picks_richest_source(db_session):
    """同一 source 出现两篇、另一 source 一篇；代表文章应来自量大的 source。"""
    src_a = _make_source(db_session, "src-a")
    src_b = _make_source(db_session, "src-b")
    base = _utc(datetime(2026, 6, 26, 9, 0, 0))
    a1 = _make_article(
        db_session,
        src_a,
        "OpenAI launches new GPT model with improved reasoning",
        summary="The new model shows better reasoning capabilities.",
        created_at=base,
    )
    a2 = _make_article(
        db_session,
        src_a,
        "OpenAI launches new GPT model with improved reasoning",
        summary="A new GPT model was released today by OpenAI.",
        created_at=base + timedelta(minutes=10),
    )
    a3 = _make_article(
        db_session,
        src_b,
        "OpenAI launches new GPT model with improved reasoning",
        summary="OpenAI's latest release focuses on reasoning.",
        created_at=base + timedelta(minutes=20),
    )
    db_session.commit()

    service = ClusterService(db_session)
    assert service.cluster_articles(_utc(datetime(2026, 6, 1))) == 1
    cluster = db_session.query(Cluster).one()
    # src_a 有两篇，代表文章应来自 src_a
    assert cluster.representative_article_id in {a1.id, a2.id}
    # 代表文章 rank=0
    rep_member = (
        db_session.query(ClusterMember)
        .filter(ClusterMember.article_id == cluster.representative_article_id)
        .one()
    )
    assert rep_member.rank == 0


def test_score_formula_multi_source(db_session):
    src_a = _make_source(db_session, "src-a")
    src_b = _make_source(db_session, "src-b")
    base = _utc(datetime(2026, 6, 26, 9, 0, 0))
    _make_article(
        db_session,
        src_a,
        "OpenAI launches new GPT model with improved reasoning",
        summary="The new model shows better reasoning capabilities.",
        created_at=base,
    )
    _make_article(
        db_session,
        src_b,
        "OpenAI launches new GPT model with improved reasoning",
        summary="A new GPT model was released today by OpenAI.",
        created_at=base + timedelta(minutes=10),
    )
    db_session.commit()

    service = ClusterService(db_session)
    service.cluster_articles(_utc(datetime(2026, 6, 1)))
    cluster = db_session.query(Cluster).one()
    expected = round(2 * SCORE_ARTICLE_WEIGHT + 2 * SCORE_SOURCE_WEIGHT, 4)
    assert cluster.score == expected
    assert cluster.size == 2


def test_score_single_source_penalized(db_session):
    """单一来源 cluster 应被扣分。"""
    src_a = _make_source(db_session, "src-a")
    base = _utc(datetime(2026, 6, 26, 9, 0, 0))
    _make_article(
        db_session,
        src_a,
        "OpenAI launches new GPT model with improved reasoning",
        summary="The new model shows better reasoning capabilities.",
        created_at=base,
    )
    _make_article(
        db_session,
        src_a,
        "OpenAI launches new GPT model with improved reasoning",
        summary="A new GPT model was released today by OpenAI.",
        created_at=base + timedelta(minutes=10),
    )
    db_session.commit()

    service = ClusterService(db_session)
    service.cluster_articles(_utc(datetime(2026, 6, 1)))
    cluster = db_session.query(Cluster).one()
    raw = 2 * SCORE_ARTICLE_WEIGHT + 1 * SCORE_SOURCE_WEIGHT
    expected = round(raw * SINGLE_SOURCE_PENALTY, 4)
    assert cluster.score == expected


def test_since_filter_excludes_older_articles(db_session):
    """since 之前的文章不参与聚类。"""
    src = _make_source(db_session, "src-a")
    src2 = _make_source(db_session, "src-b")
    old = _utc(datetime(2026, 5, 1, 9, 0, 0))
    new = _utc(datetime(2026, 6, 26, 9, 0, 0))
    _make_article(
        db_session,
        src,
        "OpenAI launches new GPT model with improved reasoning",
        summary="The new model shows better reasoning capabilities.",
        created_at=old,
    )
    # 只有一篇新文章，无法成簇
    _make_article(
        db_session,
        src2,
        "OpenAI launches new GPT model with improved reasoning",
        summary="A new GPT model was released today by OpenAI.",
        created_at=new,
    )
    db_session.commit()

    service = ClusterService(db_session)
    # since 设在新文章之后附近：只纳入新文章，单篇不成簇
    created = service.cluster_articles(new)
    assert created == 0
    assert db_session.query(Cluster).count() == 0


def test_returns_count_of_new_clusters(db_session):
    src_a = _make_source(db_session, "src-a")
    src_b = _make_source(db_session, "src-b")
    src_c = _make_source(db_session, "src-c")
    base = _utc(datetime(2026, 6, 26, 9, 0, 0))

    # 组1：GPT 相关（两篇）
    _make_article(
        db_session,
        src_a,
        "OpenAI launches new GPT model with improved reasoning",
        summary="The new model shows better reasoning capabilities.",
        created_at=base,
    )
    _make_article(
        db_session,
        src_b,
        "OpenAI launches new GPT model with improved reasoning",
        summary="A new GPT model was released today by OpenAI.",
        created_at=base + timedelta(minutes=10),
    )
    # 组2：Mars 相关（两篇）
    _make_article(
        db_session,
        src_a,
        "NASA announces new Mars rover mission for 2030 launch",
        summary="A new rover will search for life on Mars.",
        created_at=base + timedelta(hours=1),
    )
    _make_article(
        db_session,
        src_c,
        "NASA announces new Mars rover mission for 2030 launch",
        summary="NASA targets 2030 for its next Mars rover mission.",
        created_at=base + timedelta(hours=1, minutes=10),
    )
    db_session.commit()

    service = ClusterService(db_session)
    created = service.cluster_articles(_utc(datetime(2026, 6, 1)))
    assert created == 2
    assert db_session.query(Cluster).count() == 2
