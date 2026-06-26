import os
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.base import Base
# Import all models so tables are registered with Base.metadata
from app.models import Digest, DigestEntry, Cluster, ClusterMember, Article, Source, Translation  # noqa: F401
from app.database import get_db
from app.routers import archive, articles, clusters, digests, health


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client(db_session):
    """Create a FastAPI TestClient with get_db dependency overridden.

    The fixture builds a minimal app with all 5 routers registered,
    then overrides the centralized ``app.database.get_db`` dependency
    so every request uses the in-memory ``db_session``.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app = FastAPI()
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(digests.router, prefix="/api/v1")
    app.include_router(archive.router, prefix="/api/v1")
    app.include_router(clusters.router, prefix="/api/v1")
    app.include_router(articles.router, prefix="/api/v1")

    # Single override targeting the canonical function imported by all routers
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
