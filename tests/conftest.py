"""Offline fixtures: a synthetic GMD-shaped CSV (our own rows, NOT GMD data) and a wired
GmdSource whose fetch is monkeypatched to that file, so the suite never hits the network.
"""
from pathlib import Path

import pytest

from trail_gmd import fetch
from trail_gmd.source import GmdSource

FIXTURE = Path(__file__).parent / "fixtures" / "gmd_sample.csv"


@pytest.fixture
def gmd_csv() -> Path:
    return FIXTURE


@pytest.fixture
def gmd_source(monkeypatch):
    monkeypatch.setattr(fetch, "resolve_version", lambda version="current", **k: "2099_01")
    monkeypatch.setattr(fetch, "fetch_csv", lambda version, cache_dir=None: FIXTURE)
    return GmdSource({"countries": ["USA", "DEU"]})
