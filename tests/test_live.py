"""Live GMD smoke test. Skipped by default (marker 'live').

Run with: uv run pytest -m live   (needs network; downloads the ~20MB release CSV)
"""
import pytest

from trail_gmd import fetch
from trail_gmd.source import GmdSource


@pytest.mark.live
def test_live_resolve_fetch_and_load():
    version = fetch.resolve_version("current")
    assert len(version) == 7 and version[4] == "_"  # YYYY_MM
    src = GmdSource({"countries": ["USA"], "version": version})
    panel = src.load({"gmd.rGDP", "gmd.CPI", "gmd.infl"}, periods=(2000, 2020))
    assert panel.height > 0
    assert panel["gmd.rGDP"].drop_nulls().len() > 0
    latest = panel.sort("period").tail(1).to_dicts()[0]
    assert latest["gmd.rGDP"] and latest["gmd.rGDP"] > 0
