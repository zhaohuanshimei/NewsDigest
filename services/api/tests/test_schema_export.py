"""Tests for the API schema export pipeline.

These tests verify:
1. The FastAPI app can produce a valid OpenAPI schema.
2. The schema contains all expected public resource models.
3. The export helper writes a parseable JSON file.
4. The sync script can generate TypeScript interfaces from the schema.
"""

import json
import os

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def openapi_schema():
    """Return the raw OpenAPI schema dict from the FastAPI app."""
    os.environ.setdefault("DATABASE_URL", "sqlite://")
    from app.main import app
    return app.openapi()


@pytest.fixture()
def exported_schema_path(tmp_path, openapi_schema):
    """Write the OpenAPI schema to a temp file and return its path."""
    path = tmp_path / "openapi.json"
    path.write_text(json.dumps(openapi_schema, indent=2))
    return str(path)


# ---------------------------------------------------------------------------
# 1. Schema validity
# ---------------------------------------------------------------------------

class TestSchemaValidity:
    """The FastAPI app must expose a well-formed OpenAPI schema."""

    def test_schema_has_openapi_version(self, openapi_schema):
        assert "openapi" in openapi_schema
        assert openapi_schema["openapi"].startswith("3.")

    def test_schema_has_info(self, openapi_schema):
        info = openapi_schema["info"]
        assert "title" in info
        assert "version" in info

    def test_schema_has_paths(self, openapi_schema):
        assert "paths" in openapi_schema
        assert isinstance(openapi_schema["paths"], dict)

    def test_schema_has_components(self, openapi_schema):
        assert "components" in openapi_schema
        assert "schemas" in openapi_schema["components"]


# ---------------------------------------------------------------------------
# 2. Expected resource models
# ---------------------------------------------------------------------------

EXPECTED_RESOURCES = [
    "HealthResource",
    "ApiError",
    "DigestResource",
    "DigestEntryResource",
    "ArchiveDateListResource",
    "ClusterDetailResource",
    "ArticleDetailResource",
]


class TestResourceModelsPresent:
    """All public resource models must be registered in the schema."""

    @pytest.mark.parametrize("model", EXPECTED_RESOURCES)
    def test_model_in_schema(self, openapi_schema, model):
        schemas = openapi_schema["components"]["schemas"]
        assert model in schemas, f"{model} missing from components.schemas"

    def test_health_resource_fields(self, openapi_schema):
        schema = openapi_schema["components"]["schemas"]["HealthResource"]
        props = schema["properties"]
        assert "status" in props
        assert "service" in props
        assert "version" in props

    def test_digest_resource_has_entries(self, openapi_schema):
        schema = openapi_schema["components"]["schemas"]["DigestResource"]
        props = schema["properties"]
        assert "date" in props
        assert "published_at" in props
        assert "entries" in props

    def test_article_detail_fields(self, openapi_schema):
        schema = openapi_schema["components"]["schemas"]["ArticleDetailResource"]
        required = schema.get("required", [])
        assert "id" in required
        assert "title" in required
        assert "url" in required


# ---------------------------------------------------------------------------
# 3. Export function
# ---------------------------------------------------------------------------

class TestExportFunction:
    """The export helper must write valid JSON to disk."""

    def test_export_writes_file(self, tmp_path):
        from scripts_export_helper import export_schema_to_file

        dest = str(tmp_path / "schema.json")
        export_schema_to_file(dest)

        assert os.path.isfile(dest)
        with open(dest) as fh:
            data = json.load(fh)
        assert "openapi" in data
        assert "components" in data


# ---------------------------------------------------------------------------
# 4. Sync function (TypeScript generation)
# ---------------------------------------------------------------------------

class TestSyncFunction:
    """The sync helper must generate TypeScript interfaces."""

    def test_sync_generates_files(self, exported_schema_path, tmp_path):
        from scripts_export_helper import sync_types_from_schema

        output_dir = str(tmp_path / "generated")
        files = sync_types_from_schema(exported_schema_path, output_dir)

        assert len(files) > 0
        # index.ts barrel should exist
        index_files = [f for f in files if f.endswith("index.ts")]
        assert len(index_files) == 1

    def test_sync_generates_health_resource(self, exported_schema_path, tmp_path):
        from scripts_export_helper import sync_types_from_schema

        output_dir = str(tmp_path / "generated")
        sync_types_from_schema(exported_schema_path, output_dir)

        # Find the health resource file
        ts_files = [
            f for f in os.listdir(output_dir)
            if f.endswith(".ts") and f != "index.ts"
        ]
        assert len(ts_files) > 0

        # At least one file should contain "HealthResource"
        found = False
        for ts_file in ts_files:
            content = open(os.path.join(output_dir, ts_file)).read()
            if "HealthResource" in content:
                found = True
                assert "status" in content
                assert "string" in content
                break
        assert found, "No generated file contains HealthResource"
