"""Bridge module so tests can import functions from scripts/ via importlib.

Tests run from services/api/ but the real scripts live at the repo root.
This module uses importlib to load the scripts and re-exports their helpers.
"""

import importlib.util
import os

_SCRIPTS_DIR = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, os.pardir, "scripts"
)
_SCRIPTS_DIR = os.path.abspath(_SCRIPTS_DIR)


def _load_script(name: str):
    """Load a Python script by filename and return the module."""
    path = os.path.join(_SCRIPTS_DIR, name)
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_export_mod = _load_script("export-api-schema.py")
_sync_mod = _load_script("sync-shared-types.py")

export_schema_to_file = _export_mod.export_schema
sync_types_from_schema = _sync_mod.sync_shared_types
