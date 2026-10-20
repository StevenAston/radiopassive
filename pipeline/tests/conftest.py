"""Shared pytest fixtures for the Radiopassive validator tests (Task 0.2).

Written from SCHEMA.md section 6 alone (spec-blind). The temporary project root
mirrors the layout in SCHEMA.md section 2: the real reference tables and JSON
schemas are copied in, together with the fixture sources and events registries.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
FIXTURES = TESTS_DIR / "fixtures"
# pipeline/tests/conftest.py -> pipeline/tests -> pipeline -> project root
PROJECT_ROOT = TESTS_DIR.parents[1]

# Make `import pipeline.validate` work wherever pytest is launched from.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def project_root() -> Path:
    """The real project root (the parent of `pipeline/`)."""
    return PROJECT_ROOT


@pytest.fixture
def tmp_root(tmp_path: Path) -> Path:
    """A temporary project root: real reference tables and schemas plus fixture sources and events."""
    root = tmp_path / "root"
    (root / "data").mkdir(parents=True)
    shutil.copytree(PROJECT_ROOT / "data" / "reference", root / "data" / "reference")
    shutil.copytree(PROJECT_ROOT / "schema", root / "schema")
    shutil.copy(FIXTURES / "sources.csv", root / "data" / "sources.csv")
    shutil.copy(FIXTURES / "events.csv", root / "data" / "events.csv")
    (root / "data" / "streams").mkdir()
    return root
