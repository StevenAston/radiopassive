"""Shared pytest fixtures for the Radiopassive validator tests (Task 0.2, SCHEMA v2).

Written from SCHEMA.md section 6 alone (spec-blind). The temporary project root
mirrors the layout in SCHEMA.md section 2: the real reference tables and JSON
schemas are copied in, together with the fixture registries:

* data/sources.csv                  <- fixtures/sources.csv        (S0001-S0005)
* data/events.csv                   <- fixtures/events.csv         (E001, E002)
* data/activity/series.csv          <- fixtures/activity.csv       (driver series for the factors)
* data/factors/coal.csv             <- fixtures/factors_coal.csv   (coal:0001, coal:0002)

data/baselines.csv and data/reference/commodity_factors.csv are optional files
and are NOT installed by default; tests that need them use the
`install_baselines` and `install_commodity_factors` fixtures.
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
    """A temporary project root: real reference tables and schemas plus the fixture registries."""
    root = tmp_path / "root"
    (root / "data").mkdir(parents=True)
    shutil.copytree(PROJECT_ROOT / "data" / "reference", root / "data" / "reference")
    shutil.copytree(PROJECT_ROOT / "schema", root / "schema")
    shutil.copy(FIXTURES / "sources.csv", root / "data" / "sources.csv")
    shutil.copy(FIXTURES / "events.csv", root / "data" / "events.csv")
    (root / "data" / "activity").mkdir()
    shutil.copy(FIXTURES / "activity.csv", root / "data" / "activity" / "series.csv")
    (root / "data" / "factors").mkdir()
    shutil.copy(FIXTURES / "factors_coal.csv", root / "data" / "factors" / "coal.csv")
    (root / "data" / "streams").mkdir()
    return root


@pytest.fixture
def install_baselines(tmp_root: Path) -> Path:
    """Install the optional fixture data/baselines.csv and return its path."""
    shutil.copy(FIXTURES / "baselines.csv", tmp_root / "data" / "baselines.csv")
    return tmp_root / "data" / "baselines.csv"


@pytest.fixture
def install_commodity_factors(tmp_root: Path) -> Path:
    """Install the optional fixture data/reference/commodity_factors.csv and return its path."""
    dest = tmp_root / "data" / "reference" / "commodity_factors.csv"
    shutil.copy(FIXTURES / "commodity_factors.csv", dest)
    return dest
