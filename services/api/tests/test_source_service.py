from app.repositories.source_repository import SourceRepository
from app.services.source_service import SourceService


class TestSourceService:

    def test_get_default_sources_returns_all_defaults(self, db_session):
        repo = SourceRepository(db_session)
        svc = SourceService(repo)
        defaults = svc.get_default_sources()
        assert len(defaults) >= 5

    def test_get_default_sources_has_rss_kind(self, db_session):
        repo = SourceRepository(db_session)
        svc = SourceService(repo)
        for src in svc.get_default_sources():
            assert src["kind"] == "rss"

    def test_get_default_sources_has_valid_structure(self, db_session):
        repo = SourceRepository(db_session)
        svc = SourceService(repo)
        for src in svc.get_default_sources():
            assert "name" in src
            assert "url" in src
            assert "kind" in src
            assert "language" in src

    def test_seed_default_sources_when_empty(self, db_session):
        repo = SourceRepository(db_session)
        svc = SourceService(repo)
        seeded = svc.seed_default_sources(db_session)
        assert len(seeded) >= 5
        assert repo.list_all() == seeded

    def test_seed_default_sources_when_not_empty(self, db_session):
        repo = SourceRepository(db_session)
        repo.create(name="Existing", kind="rss", url="https://existing.com/rss")
        svc = SourceService(repo)
        seeded = svc.seed_default_sources(db_session)
        assert len(seeded) == 1
        assert seeded[0].name == "Existing"

    def test_get_active_fetchable_sources(self, db_session):
        repo = SourceRepository(db_session)
        repo.create(name="RSS1", kind="rss", url="https://rss1.com/rss", enabled=True)
        repo.create(name="RSS2", kind="rss", url="https://rss2.com/rss", enabled=True)
        repo.create(name="Web", kind="web", url="https://web.com", enabled=True)
        svc = SourceService(repo)
        active = svc.get_active_fetchable_sources()
        assert len(active) == 2
        assert all(s.kind == "rss" and s.enabled for s in active)
