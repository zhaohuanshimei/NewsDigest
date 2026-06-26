import os

os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.base import Base
from app.models.source import Source
from app.models.article import Article


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
