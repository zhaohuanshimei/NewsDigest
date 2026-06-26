"""Router integration tests."""
import pytest
from datetime import date, datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.base import Base
# Import all models to ensure tables are created
from app.models import Digest, DigestEntry, Cluster, ClusterMember, Article, Source, Translation
from app.routers import digests, archive, clusters, articles


@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_client(db_session):
    """Create test client with dependency override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app = FastAPI()
    app.include_router(digests.router, prefix="/api/v1")
    app.include_router(archive.router, prefix="/api/v1")
    app.include_router(clusters.router, prefix="/api/v1")
    app.include_router(articles.router, prefix="/api/v1")
    app.dependency_overrides[digests.get_db] = override_get_db
    app.dependency_overrides[archive.get_db] = override_get_db
    app.dependency_overrides[clusters.get_db] = override_get_db
    app.dependency_overrides[articles.get_db] = override_get_db

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _create_test_data(db_session):
    """Create test data in database."""
    # Create source
    source = Source(
        name="Test Source",
        kind="rss",
        url="https://example.com/feed",
        language="zh-CN",
        enabled=True,
        fetch_interval_minutes=30
    )
    db_session.add(source)
    db_session.commit()

    # Create cluster
    cluster = Cluster(
        size=3,
        score=0.85,
        first_seen_at=datetime.now(timezone.utc),
        last_updated_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(cluster)
    db_session.commit()

    # Create articles
    article1 = Article(
        source_id=source.id,
        url="https://example.com/article1",
        title="测试文章1",
        summary="这是第一篇测试文章的摘要",
        body="这是第一篇测试文章的完整内容",
        published_at=datetime.now(timezone.utc),
        language="zh-CN",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    article2 = Article(
        source_id=source.id,
        url="https://example.com/article2",
        title="测试文章2",
        summary="这是第二篇测试文章的摘要",
        body="这是第二篇测试文章的完整内容",
        published_at=datetime.now(timezone.utc),
        language="zh-CN",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add_all([article1, article2])
    db_session.commit()

    # Create cluster members
    member1 = ClusterMember(
        cluster_id=cluster.id,
        article_id=article1.id,
        rank=1
    )
    member2 = ClusterMember(
        cluster_id=cluster.id,
        article_id=article2.id,
        rank=2
    )
    db_session.add_all([member1, member2])
    db_session.commit()

    # Create digest
    digest = Digest(
        date=date.today(),
        status="published",
        published_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(digest)
    db_session.commit()

    # Create digest entries
    entry1 = DigestEntry(
        digest_id=digest.id,
        cluster_id=cluster.id,
        rank=1,
        category="technology",
        headline="测试头条新闻",
        summary="这是测试头条新闻的摘要",
        source_count=2,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(entry1)
    db_session.commit()

    return {
        "source": source,
        "cluster": cluster,
        "articles": [article1, article2],
        "digest": digest,
        "entry": entry1
    }


def test_digest_latest_success(test_client, db_session):
    """Test GET /digests/latest returns 200 with valid digest."""
    data = _create_test_data(db_session)

    response = test_client.get("/api/v1/digests/latest")
    assert response.status_code == 200
    result = response.json()
    assert result["date"] == data["digest"].date.isoformat()
    assert len(result["entries"]) == 1
    assert result["entries"][0]["rank"] == 1
    assert result["entries"][0]["category"] == "technology"


def test_digest_latest_not_found(test_client, db_session):
    """Test GET /digests/latest returns 404 when no digest exists."""
    response = test_client.get("/api/v1/digests/latest")
    assert response.status_code == 404
    result = response.json()
    assert result["error"]["code"] == "digest_not_found"


def test_digest_by_date_success(test_client, db_session):
    """Test GET /digests/{date} returns 200 with valid digest."""
    data = _create_test_data(db_session)
    target_date = data["digest"].date.isoformat()

    response = test_client.get(f"/api/v1/digests/{target_date}")
    assert response.status_code == 200
    result = response.json()
    assert result["date"] == target_date


def test_digest_by_date_not_found(test_client, db_session):
    """Test GET /digests/{date} returns 404 for non-existent date."""
    _create_test_data(db_session)

    response = test_client.get("/api/v1/digests/2020-01-01")
    assert response.status_code == 404
    result = response.json()
    assert result["error"]["code"] == "digest_not_found"


def test_archive_dates_success(test_client, db_session):
    """Test GET /archive/dates returns 200 with date list."""
    _create_test_data(db_session)

    response = test_client.get("/api/v1/archive/dates")
    assert response.status_code == 200
    result = response.json()
    assert "dates" in result
    assert len(result["dates"]) >= 1


def test_archive_dates_empty(test_client, db_session):
    """Test GET /archive/dates returns empty list when no digests."""
    response = test_client.get("/api/v1/archive/dates")
    assert response.status_code == 200
    result = response.json()
    assert result["dates"] == []


def test_archive_dates_invalid_limit(test_client, db_session):
    """Test GET /archive/dates returns 400 for invalid limit."""
    response = test_client.get("/api/v1/archive/dates?limit=0")
    assert response.status_code == 400
    result = response.json()
    assert result["error"]["code"] == "invalid_limit"


def test_cluster_detail_success(test_client, db_session):
    """Test GET /clusters/{cluster_id} returns 200 with cluster details."""
    data = _create_test_data(db_session)

    response = test_client.get(f"/api/v1/clusters/{data['cluster'].id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == str(data["cluster"].id)
    assert len(result["digest_dates"]) >= 1


def test_cluster_detail_not_found(test_client, db_session):
    """Test GET /clusters/{cluster_id} returns 404 for non-existent cluster."""
    response = test_client.get("/api/v1/clusters/99999")
    assert response.status_code == 404
    result = response.json()
    assert result["error"]["code"] == "cluster_not_found"


def test_article_detail_success(test_client, db_session):
    """Test GET /articles/{article_id} returns 200 with article details."""
    data = _create_test_data(db_session)

    response = test_client.get(f"/api/v1/articles/{data['articles'][0].id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == str(data["articles"][0].id)
    assert result["title"] == data["articles"][0].title


def test_article_detail_not_found(test_client, db_session):
    """Test GET /articles/{article_id} returns 404 for non-existent article."""
    response = test_client.get("/api/v1/articles/99999")
    assert response.status_code == 404
    result = response.json()
    assert result["error"]["code"] == "article_not_found"
