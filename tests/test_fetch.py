"""Fetch robustness: version ordering, offline fallback, download hygiene."""
import httpx
import pytest

from trail_gmd import fetch


def test_version_key_orders_numerically():
    # string max would put 2025_9 above 2025_10
    assert max(["2025_9", "2025_10", "2024_12"], key=fetch._version_key) == "2025_10"


def test_resolve_version_passthrough():
    assert fetch.resolve_version("2025_06") == "2025_06"


def test_offline_fallback_uses_newest_cached(tmp_path, monkeypatch):
    (tmp_path / "GMD_2024_12.csv").write_text("ISO3,year\n")
    (tmp_path / "GMD_2025_09.csv").write_text("ISO3,year\n")
    monkeypatch.setattr(fetch, "default_cache_dir", lambda: tmp_path)

    class _DeadClient:
        def get(self, url):
            raise httpx.ConnectError("offline")

        def close(self):
            pass

    with pytest.warns(fetch.GmdFetchWarning, match="W-GMD-OFFLINE"):
        v = fetch.resolve_version("current", client=_DeadClient())
    assert v == "2025_09"


def test_offline_without_cache_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "default_cache_dir", lambda: tmp_path)

    class _DeadClient:
        def get(self, url):
            raise httpx.ConnectError("offline")

        def close(self):
            pass

    with pytest.raises(httpx.ConnectError):
        fetch.resolve_version("current", client=_DeadClient())
