"""Baseline API integration tests — covers all 5 router groups.

Tests validate happy path, empty data, and error handling for every
public route exposed by the API layer.
"""

from datetime import date, datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_test_data(db_session):
    """Insert a full row of test data (source, cluster, articles, digest)."""
    from app.models import Source, Cluster, ClusterMember, Article, Digest, DigestEntry

    source = Source(
        name="Test Source",
        kind="rss",
        url="https://example.com/feed",
        language="zh-CN",
        enabled=True,
        fetch_interval_minutes=30,
    )
    db_session.add(source)
    db_session.commit()

    cluster = Cluster(
        size=3,
        score=0.85,
        first_seen_at=datetime.now(timezone.utc),
        last_updated_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(cluster)
    db_session.commit()

    article1 = Article(
        source_id=source.id,
        url="https://example.com/article1",
        title="Test Article 1",
        summary="Summary of test article 1",
        body="Body of test article 1",
        published_at=datetime.now(timezone.utc),
        language="zh-CN",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    article2 = Article(
        source_id=source.id,
        url="https://example.com/article2",
        title="Test Article 2",
        summary="Summary of test article 2",
        body="Body of test article 2",
        published_at=datetime.now(timezone.utc),
        language="zh-CN",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add_all([article1, article2])
    db_session.commit()

    db_session.add_all(
        [
            ClusterMember(cluster_id=cluster.id, article_id=article1.id, rank=1),
            ClusterMember(cluster_id=cluster.id, article_id=article2.id, rank=2),
        ]
    )
    db_session.commit()

    digest = Digest(
        date=date.today(),
        status="published",
        published_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(digest)
    db_session.commit()

    entry = DigestEntry(
        digest_id=digest.id,
        cluster_id=cluster.id,
        rank=1,
        category="technology",
        headline="Test Headline",
        summary="Test headline summary",
        source_count=2,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(entry)
    db_session.commit()

    return {
        "source": source,
        "cluster": cluster,
        "articles": [article1, article2],
        "digest": digest,
        "entry": entry,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/health
# ---------------------------------------------------------------------------

def test_health_returns_200_with_metadata(test_client, db_session):
    """Health endpoint returns service metadata even when DB is empty."""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "news-digest-api"
    assert body["version"] == "0.1.0"
    assert body["database"] == "ok"
    assert body["last_digest"] is None


def test_health_shows_last_digest_when_data_exists(test_client, db_session):
    """Health endpoint includes last_digest info when digests exist."""
    _create_test_data(db_session)

    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["last_digest"] is not None
    assert body["last_digest"]["date"] == date.today().isoformat()


# ---------------------------------------------------------------------------
# GET /api/v1/digests/latest
# ---------------------------------------------------------------------------

def test_digest_latest_returns_200(test_client, db_session):
    """Latest digest returns full digest with entries."""
    data = _create_test_data(db_session)

    response = test_client.get("/api/v1/digests/latest")
    assert response.status_code == 200
    result = response.json()
    assert result["date"] == data["digest"].date.isoformat()
    assert "published_at" in result
    assert len(result["entries"]) == 1
    assert result["entries"][0]["rank"] == 1
    assert result["entries"][0]["category"] == "technology"
    assert result["entries"][0]["headline"] == "Test Headline"


def test_digest_latest_returns_404_when_empty(test_client, db_session):
    """Latest digest returns 404 when no digest exists."""
    response = test_client.get("/api/v1/digests/latest")
    assert response.status_code == 404
    result = response.json()
    assert result["error"]["code"] == "digest_not_found"


# ---------------------------------------------------------------------------
# GET /api/v1/digests/{date}
# ---------------------------------------------------------------------------

def test_digest_by_date_returns_200(test_client, db_session):
    """Digest lookup by valid date succeeds."""
    data = _create_test_data(db_session)
    target_date = data["digest"].date.isoformat()

    response = test_client.get(f"/api/v1/digests/{target_date}")
    assert response.status_code == 200
    result = response.json()
    assert result["date"] == target_date
    assert len(result["entries"]) == 1


def test_digest_by_date_returns_400_for_invalid_format(test_client, db_session):
    """Digest lookup with a non-date string returns 400."""
    response = test_client.get("/api/v1/digests/not-a-date")
    assert response.status_code == 400
    result = response.json()
    assert result["error"]["code"] == "invalid_date_format"
    assert "YYYY-MM-DD" in result["error"]["message"]


def test_digest_by_date_returns_404_for_missing_date(test_client, db_session):
    """Digest lookup for a date without a digest returns 404."""
    _create_test_data(db_session)

    response = test_client.get("/api/v1/digests/2020-01-01")
    assert response.status_code == 404
    result = response.json()
    assert result["error"]["code"] == "digest_not_found"


# ---------------------------------------------------------------------------
# GET /api/v1/archive/dates
# ---------------------------------------------------------------------------

def test_archive_dates_returns_200_with_dates(test_client, db_session):
    """Archive dates list includes the date of an existing digest."""
    _create_test_data(db_session)

    response = test_client.get("/api/v1/archive/dates")
    assert response.status_code == 200
    result = response.json()
    assert "dates" in result
    assert len(result["dates"]) >= 1
    assert date.today().isoformat() in result["dates"]


def test_archive_dates_returns_empty_when_no_digests(test_client, db_session):
    """Archive dates returns an empty list when no digests exist."""
    response = test_client.get("/api/v1/archive/dates")
    assert response.status_code == 200
    result = response.json()
    assert result["dates"] == []


def test_archive_dates_returns_400_for_invalid_limit(test_client, db_session):
    """Archive dates returns 400 when limit is outside 1-365."""
    response = test_client.get("/api/v1/archive/dates?limit=0")
    assert response.status_code == 400
    result = response.json()
    assert result["error"]["code"] == "invalid_limit"

    response = test_client.get("/api/v1/archive/dates?limit=366")
    assert response.status_code == 400
    result = response.json()
    assert result["error"]["code"] == "invalid_limit"


def test_archive_dates_respects_limit(test_client, db_session):
    """Archive dates limit parameter is honoured."""
    _create_test_data(db_session)

    response = test_client.get("/api/v1/archive/dates?limit=1")
    assert response.status_code == 200
    result = response.json()
    assert len(result["dates"]) == 1


# ---------------------------------------------------------------------------
# GET /api/v1/clusters/{cluster_id}
# ---------------------------------------------------------------------------

def test_cluster_detail_returns_200(test_client, db_session):
    """Cluster detail returns full cluster with digest dates and articles."""
    data = _create_test_data(db_session)

    response = test_client.get(f"/api/v1/clusters/{data['cluster'].id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == str(data["cluster"].id)
    assert len(result["digest_dates"]) >= 1
    assert result["category"] == "technology"
    assert result["headline"] == "Test Headline"
    assert result["source_count"] == 2


def test_cluster_detail_returns_404_for_missing(test_client, db_session):
    """Cluster detail returns 404 for a non-existent cluster id."""
    response = test_client.get("/api/v1/clusters/99999")
    assert response.status_code == 404
    result = response.json()
    assert result["error"]["code"] == "cluster_not_found"


# ---------------------------------------------------------------------------
# GET /api/v1/articles/{article_id}
# ---------------------------------------------------------------------------

def test_article_detail_returns_200(test_client, db_session):
    """Article detail returns full article metadata."""
    data = _create_test_data(db_session)

    response = test_client.get(f"/api/v1/articles/{data['articles'][0].id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == str(data["articles"][0].id)
    assert result["title"] == "Test Article 1"
    assert result["summary"] == "Summary of test article 1"
    assert result["language"] == "zh-CN"


def test_article_detail_returns_404_for_missing(test_client, db_session):
    """Article detail returns 404 for a non-existent article id."""
    response = test_client.get("/api/v1/articles/99999")
    assert response.status_code == 404
    result = response.json()
    assert result["error"]["code"] == "article_not_found"
