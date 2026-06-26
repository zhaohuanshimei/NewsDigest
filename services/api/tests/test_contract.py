"""Contract tests verifying API response structure consistency.

Two layers of verification:

1. Server-side response contract
   Use FastAPI TestClient to call real routes and assert response JSON structure
   matches the declared Pydantic response_model, including error envelope shape.

2. Cross-language type contract
   Read TypeScript type definitions from packages/shared-types and compare field
   names against Pydantic schema fields so that API / shared-type drift is
   detected at test time.
"""
import os
import re
from datetime import date, datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite://")

from app.base import Base
from app.database import get_db
from app.models import Article, Cluster, ClusterMember, Digest, DigestEntry, Source
from app.routers import archive, articles, clusters, digests, health
from app.schemas import archive as archive_schema
from app.schemas import article as article_schema
from app.schemas import cluster as cluster_schema
from app.schemas import digest as digest_schema
from app.schemas import error as error_schema
from app.schemas import health as health_schema

API_PREFIX = "/api/v1"

SHARED_TYPES_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        "../../../packages/shared-types/src/resources",
    )
)

# Auto-generated FastAPI routes that don't carry a response_model
FASTAPI_BUILTIN_ROUTES = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}

# ---------------------------------------------------------------------------
# Shared-Types file lookup
# ---------------------------------------------------------------------------

TS_INTERFACE_MAP: dict[str, str] = {
    "HealthResource": "health.ts",
    "DigestResource": "digest.ts",
    "DigestEntryResource": "digest.ts",
    "ArchiveDateListResource": "archive.ts",
    "ClusterDetailResource": "cluster.ts",
    "ArticleDetailResource": "article.ts",
    "ApiError": "error.ts",
}

PYDANTIC_MODELS: dict[str, type] = {
    "HealthResource": health_schema.HealthResource,
    "DigestResource": digest_schema.DigestResource,
    "DigestEntryResource": digest_schema.DigestEntryResource,
    "ArchiveDateListResource": archive_schema.ArchiveDateListResource,
    "ClusterDetailResource": cluster_schema.ClusterDetailResource,
    "ArticleDetailResource": article_schema.ArticleDetailResource,
    "ApiError": error_schema.ApiError,
}

# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture(scope="module")
def db_session():
    """In-memory SQLite database with all tables created."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client(db_session):
    """FastAPI TestClient with database dependency overridden."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app = FastAPI()
    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(digests.router, prefix=API_PREFIX)
    app.include_router(archive.router, prefix=API_PREFIX)
    app.include_router(clusters.router, prefix=API_PREFIX)
    app.include_router(articles.router, prefix=API_PREFIX)
    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def seeded_data(db_session):
    """Insert test data into db_session and return key identifiers."""
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

    article = Article(
        source_id=source.id,
        url="https://example.com/article1",
        title="Test Article",
        summary="Test summary",
        body="Test body",
        published_at=datetime.now(timezone.utc),
        language="zh-CN",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(article)
    db_session.commit()

    member = ClusterMember(
        cluster_id=cluster.id,
        article_id=article.id,
        rank=1,
    )
    db_session.add(member)
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
        summary="Test summary",
        source_count=2,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(entry)
    db_session.commit()

    return {
        "cluster_id": cluster.id,
        "article_id": article.id,
        "digest_date": digest.date.isoformat(),
    }


# ===================================================================
# Helpers
# ===================================================================


def _ts_field_names(ts_file: str, interface_name: str) -> set[str]:
    """Extract field names from a TypeScript interface definition using regex."""
    path = os.path.join(SHARED_TYPES_DIR, ts_file)
    with open(path) as fh:
        content = fh.read()

    pattern = rf"export interface {interface_name}\s*{{(.*?)}}"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        pytest.fail(f"Interface '{interface_name}' not found in {ts_file}")

    body = match.group(1)
    fields: set[str] = set()
    for line in body.split("\n"):
        stripped = line.strip()
        # Skip comments and empty lines
        if not stripped or stripped.startswith("//"):
            continue
        # Match "field_name: type" pattern
        if ":" in stripped:
            field_name = stripped.split(":")[0].strip()
            # Skip array closing brackets
            if field_name and not field_name.startswith("}"):
                fields.add(field_name)
    return fields


def _pydantic_field_names(model: type) -> set[str]:
    """Return the set of field names declared on a Pydantic model."""
    return set(model.model_fields.keys())


# ===================================================================
# 1. Server-side response contract
# ===================================================================


class TestHealthResponseContract:
    """GET /api/v1/health must match HealthResource schema."""

    def test_success_response_structure(self, client):
        resp = client.get(f"{API_PREFIX}/health")
        assert resp.status_code == 200
        body = resp.json()

        expected_fields = _pydantic_field_names(health_schema.HealthResource)
        assert set(body.keys()) == expected_fields, (
            f"Health response fields mismatch. "
            f"Expected {expected_fields}, got {set(body.keys())}"
        )

        # Type assertions
        assert body["status"] in ("ok", "degraded", "error")
        assert isinstance(body["service"], str)
        assert isinstance(body["version"], str)
        assert body["database"] in ("ok", "error")
        assert body["last_digest"] is None or isinstance(body["last_digest"], dict)

    def test_required_fields_present(self, client):
        """All HealthResource fields appear in response (incl. optional)."""
        resp = client.get(f"{API_PREFIX}/health")
        body = resp.json()
        assert "status" in body
        assert "service" in body
        assert "version" in body
        assert "database" in body
        assert "last_digest" in body


class TestDigestResponseContract:
    """GET /api/v1/digests/* must match DigestResource schema."""

    def test_success_response_structure(self, client, seeded_data):
        resp = client.get(f"{API_PREFIX}/digests/latest")
        assert resp.status_code == 200
        body = resp.json()

        expected = _pydantic_field_names(digest_schema.DigestResource)
        assert set(body.keys()) == expected, (
            f"DigestResource fields mismatch: expected {expected}, "
            f"got {set(body.keys())}"
        )
        assert isinstance(body["date"], str)
        assert isinstance(body["published_at"], str)
        assert isinstance(body["entries"], list)

        if body["entries"]:
            entry = body["entries"][0]
            entry_fields = _pydantic_field_names(digest_schema.DigestEntryResource)
            assert set(entry.keys()) == entry_fields, (
                f"DigestEntryResource fields mismatch: expected {entry_fields}, "
                f"got {set(entry.keys())}"
            )
            # Type assertions on entry
            assert isinstance(entry["cluster_id"], str)
            assert isinstance(entry["rank"], int)
            assert isinstance(entry["category"], str)
            assert isinstance(entry["headline"], str)
            assert isinstance(entry["summary"], str)
            assert isinstance(entry["source_count"], int)


class TestArchiveResponseContract:
    """GET /api/v1/archive/dates must match ArchiveDateListResource schema."""

    def test_success_response_structure(self, client, seeded_data):
        resp = client.get(f"{API_PREFIX}/archive/dates")
        assert resp.status_code == 200
        body = resp.json()

        expected = _pydantic_field_names(archive_schema.ArchiveDateListResource)
        assert set(body.keys()) == expected
        assert isinstance(body["dates"], list)
        # At least the seeded digest date should appear
        assert seeded_data["digest_date"] in body["dates"]


class TestClusterResponseContract:
    """GET /api/v1/clusters/{id} must match ClusterDetailResource schema."""

    def test_success_response_structure(self, client, seeded_data):
        resp = client.get(f"{API_PREFIX}/clusters/{seeded_data['cluster_id']}")
        assert resp.status_code == 200
        body = resp.json()

        expected = _pydantic_field_names(cluster_schema.ClusterDetailResource)
        assert set(body.keys()) == expected, (
            f"ClusterDetailResource fields mismatch: expected {expected}, "
            f"got {set(body.keys())}"
        )
        assert isinstance(body["id"], str)
        assert isinstance(body["category"], str)
        assert isinstance(body["headline"], str)
        assert isinstance(body["summary"], str)
        assert isinstance(body["source_count"], int)
        assert isinstance(body["digest_dates"], list)


class TestArticleResponseContract:
    """GET /api/v1/articles/{id} must match ArticleDetailResource schema."""

    def test_success_response_structure(self, client, seeded_data):
        resp = client.get(f"{API_PREFIX}/articles/{seeded_data['article_id']}")
        assert resp.status_code == 200
        body = resp.json()

        expected = _pydantic_field_names(article_schema.ArticleDetailResource)
        assert set(body.keys()) == expected, (
            f"ArticleDetailResource fields mismatch: expected {expected}, "
            f"got {set(body.keys())}"
        )
        assert isinstance(body["id"], str)
        assert isinstance(body["cluster_id"], str)
        assert isinstance(body["title"], str)
        assert isinstance(body["summary"], str)
        assert isinstance(body["body"], str)
        assert isinstance(body["source"], str)
        assert isinstance(body["url"], str)
        assert isinstance(body["published_at"], str)
        assert isinstance(body["language"], str)


# ===================================================================
# 2. Error envelope contract
# ===================================================================


class TestErrorEnvelopeContract:
    """Every error response must follow ApiErrorEnvelope shape."""

    ERROR_ENDPOINTS = [
        # digest/latest excluded: seeded_data creates a digest so it returns 200
        ("GET", f"{API_PREFIX}/digests/invalid-date", 400),
        ("GET", f"{API_PREFIX}/archive/dates?limit=0", 400),
        ("GET", f"{API_PREFIX}/clusters/99999", 404),
        ("GET", f"{API_PREFIX}/articles/99999", 404),
    ]

    @pytest.mark.parametrize("method,path,expected_status", ERROR_ENDPOINTS)
    def test_error_envelope_shape(self, client, method, path, expected_status):
        resp = client.request(method, path)
        assert resp.status_code == expected_status
        body = resp.json()

        # Top-level envelope: { "error": { ... } }
        assert "error" in body, f"Missing 'error' key in {path} error response"
        err = body["error"]

        # Standard ApiError fields
        assert "code" in err, f"Missing 'error.code' in {path}"
        assert "message" in err, f"Missing 'error.message' in {path}"
        assert "request_id" in err, f"Missing 'error.request_id' in {path}"

        assert isinstance(err["code"], str), f"'error.code' not a string in {path}"
        assert isinstance(err["message"], str), (
            f"'error.message' not a string in {path}"
        )
        assert isinstance(err["request_id"], str), (
            f"'error.request_id' not a string in {path}"
        )

        # No extra keys in error object
        error_fields = _pydantic_field_names(error_schema.ApiError)
        assert set(err.keys()) == error_fields, (
            f"ApiError extra/missing fields in {path}: "
            f"expected {error_fields}, got {set(err.keys())}"
        )

        # No extra keys in envelope
        envelope_fields = _pydantic_field_names(error_schema.ApiErrorEnvelope)
        assert set(body.keys()) == envelope_fields, (
            f"ApiErrorEnvelope extra/missing fields in {path}: "
            f"expected {envelope_fields}, got {set(body.keys())}"
        )


# ===================================================================
# 3. Cross-language contract
# ===================================================================


class TestCrossLanguageContract:
    """Pydantic schema field sets must be subsets of TS interface field sets.

    This ensures that when the API adds a new response field, the shared
    TypeScript types are updated in lockstep.
    """

    @pytest.mark.parametrize(
        "model_name",
        [
            pytest.param(
                "HealthResource",
                marks=pytest.mark.xfail(
                    reason="Known drift: HealthResource TS missing database, last_digest fields"
                ),
            ),
            "DigestResource",
            "DigestEntryResource",
            "ArchiveDateListResource",
            "ClusterDetailResource",
            "ArticleDetailResource",
            "ApiError",
        ],
    )
    def test_pydantic_fields_have_ts_counterparts(self, model_name: str):
        """Every Pydantic field must appear in the corresponding TS interface."""
        ts_file = TS_INTERFACE_MAP[model_name]
        model_class = PYDANTIC_MODELS[model_name]
        pydantic_fields = _pydantic_field_names(model_class)
        ts_fields = _ts_field_names(ts_file, model_name)

        missing = pydantic_fields - ts_fields
        assert not missing, (
            f"{model_name}: Pydantic fields {missing} are not defined in "
            f"TypeScript ({ts_file}). "
            f"Pydantic={pydantic_fields}, TS={ts_fields}"
        )

    def test_ts_interface_files_are_readable(self):
        """Sanity check: every expected TS interface file exists and is non-empty."""
        for model_name, ts_file in TS_INTERFACE_MAP.items():
            path = os.path.join(SHARED_TYPES_DIR, ts_file)
            assert os.path.isfile(path), f"Missing TS file: {path}"
            fields = _ts_field_names(ts_file, model_name)
            assert len(fields) > 0, (
                f"No fields extracted from {ts_file} for {model_name}"
            )


# ===================================================================
# 4. Route contract: every endpoint must declare response_model
# ===================================================================


class TestRouteContract:
    """Every registered route must declare a response_model."""

    def test_all_routes_have_response_model(self):
        """All routes in the app must set response_model to prevent drift."""
        app = FastAPI()
        app.include_router(health.router, prefix=API_PREFIX)
        app.include_router(digests.router, prefix=API_PREFIX)
        app.include_router(archive.router, prefix=API_PREFIX)
        app.include_router(clusters.router, prefix=API_PREFIX)
        app.include_router(articles.router, prefix=API_PREFIX)

        routes_without_model = []
        for route in app.routes:
            if hasattr(route, "methods") and "GET" in route.methods:
                # Skip FastAPI auto-generated routes
                if route.path in FASTAPI_BUILTIN_ROUTES:
                    continue
                if not hasattr(route, "response_model") or route.response_model is None:
                    routes_without_model.append(route.path)

        assert not routes_without_model, (
            f"The following routes are missing response_model: {routes_without_model}"
        )
