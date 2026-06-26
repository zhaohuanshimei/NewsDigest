
from datetime import datetime

from app.repositories.source_repository import SourceRepository


class TestSourceRepository:

    def test_create_source(self, db_session):
        repo = SourceRepository(db_session)
        source = repo.create(
            name="Test Source",
            kind="rss",
            url="https://example.com/rss",
            language="en",
        )
        assert source.id is not None
        assert source.name == "Test Source"
        assert source.kind == "rss"
        assert source.enabled is True

    def test_get_by_id(self, db_session):
        repo = SourceRepository(db_session)
        created = repo.create(name="Find Me", kind="rss", url="https://example.com/rss")
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.name == "Find Me"

    def test_get_by_id_not_found(self, db_session):
        repo = SourceRepository(db_session)
        assert repo.get_by_id(999) is None

    def test_get_by_name(self, db_session):
        repo = SourceRepository(db_session)
        repo.create(name="Unique Name", kind="rss", url="https://example.com/rss")
        found = repo.get_by_name("Unique Name")
        assert found is not None
        assert found.name == "Unique Name"

    def test_get_by_name_not_found(self, db_session):
        repo = SourceRepository(db_session)
        assert repo.get_by_name("Does Not Exist") is None

    def test_list_all(self, db_session):
        repo = SourceRepository(db_session)
        repo.create(name="Src A", kind="rss", url="https://a.com/rss")
        repo.create(name="Src B", kind="rss", url="https://b.com/rss")
        all_sources = repo.list_all()
        assert len(all_sources) == 2

    def test_get_enabled_sources(self, db_session):
        repo = SourceRepository(db_session)
        repo.create(name="Enabled1", kind="rss", url="https://e1.com/rss", enabled=True)
        repo.create(name="Enabled2", kind="rss", url="https://e2.com/rss", enabled=True)
        repo.create(name="Disabled", kind="rss", url="https://d.com/rss", enabled=False)
        enabled = repo.get_enabled_sources()
        assert len(enabled) == 2
        assert all(s.enabled for s in enabled)

    def test_get_active_fetchable_sources(self, db_session):
        repo = SourceRepository(db_session)
        repo.create(name="RSS Enabled", kind="rss", url="https://rss.com/rss", enabled=True)
        repo.create(name="Web Enabled", kind="web", url="https://web.com", enabled=True)
        repo.create(name="RSS Disabled", kind="rss", url="https://disabled.com/rss", enabled=False)
        active = repo.get_active_fetchable_sources()
        assert len(active) == 1
        assert active[0].name == "RSS Enabled"

    def test_update_source(self, db_session):
        repo = SourceRepository(db_session)
        source = repo.create(name="Before", kind="rss", url="https://example.com/rss")
        updated = repo.update(source.id, name="After", language="zh")
        assert updated is not None
        assert updated.name == "After"
        assert updated.language == "zh"

    def test_update_not_found(self, db_session):
        repo = SourceRepository(db_session)
        assert repo.update(999, name="Nope") is None

    def test_update_last_fetched_at(self, db_session):
        repo = SourceRepository(db_session)
        source = repo.create(name="Fetcher", kind="rss", url="https://example.com/rss")
        assert source.last_fetched_at is None
        updated = repo.update_last_fetched_at(source.id)
        assert updated is not None
        assert updated.last_fetched_at is not None
        assert isinstance(updated.last_fetched_at, datetime)

    def test_delete_source(self, db_session):
        repo = SourceRepository(db_session)
        source = repo.create(name="Delete Me", kind="rss", url="https://example.com/rss")
        deleted = repo.delete(source.id)
        assert deleted is True
        assert repo.get_by_id(source.id) is None

    def test_delete_not_found(self, db_session):
        repo = SourceRepository(db_session)
        assert repo.delete(999) is False
