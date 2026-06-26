#!/usr/bin/env python3
"""Export FastAPI OpenAPI schema to packages/shared-types/openapi.json.

Usage:
    python scripts/export-api-schema.py           # from repo root
    cd services/api && python ../scripts/export-api-schema.py

The script resolves the repo root from its own location, so it works
regardless of the caller's cwd.
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# Resolve paths relative to this script so it works from any cwd.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
_API_DIR = os.path.join(_REPO_ROOT, "services", "api")
_OUTPUT_PATH = os.path.join(
    _REPO_ROOT, "packages", "shared-types", "openapi.json"
)


def _ensure_api_on_path() -> None:
    """Add services/api to sys.path if it is not already there."""
    if _API_DIR not in sys.path:
        sys.path.insert(0, _API_DIR)
    # Prevent database connection during schema export
    os.environ.setdefault("DATABASE_URL", "sqlite://")


def export_schema(output_path: str | None = None) -> str:
    """Generate the OpenAPI schema from the FastAPI app and write it to disk.

    Parameters
    ----------
    output_path:
        Destination file.  Defaults to
        ``packages/shared-types/openapi.json`` at the repo root.

    Returns
    -------
    str
        The absolute path the schema was written to.
    """
    _ensure_api_on_path()

    from app.main import app  # noqa: WPS433 (deferred import)

    schema = app.openapi()
    dest = output_path or _OUTPUT_PATH
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(schema, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    return os.path.abspath(dest)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    path = export_schema()
    print(f"Schema exported to {path}")
