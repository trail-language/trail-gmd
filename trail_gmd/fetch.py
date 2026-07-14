"""On-demand fetch of the GMD release file from its public S3 bucket.

The full harmonized panel is a single stable, versioned, unauthenticated CSV. We resolve
the current version from a tiny helper file, then download the CSV to a per-version file in
a user-scoped cache. GMD data is never bundled or committed (non-commercial license); it is
fetched fresh and cached only on the end-user's machine.
"""
from __future__ import annotations

import io
import os
from pathlib import Path

import httpx
import polars as pl

BASE = "https://gmd-releases.s3.ap-southeast-2.amazonaws.com/data"


def default_cache_dir() -> Path:
    env = os.environ.get("TRAIL_GMD_CACHE")
    return Path(env) if env else Path.home() / ".cache" / "trail-gmd"


def resolve_version(version: str = "current", *, client: httpx.Client | None = None) -> str:
    """Return a concrete `YYYY_MM` version. `current` resolves to the latest via helpers/versions.csv."""
    if version and version != "current":
        return version
    own = client is None
    c = client or httpx.Client(timeout=30.0, follow_redirects=True)
    try:
        resp = c.get(f"{BASE}/helpers/versions.csv")
        resp.raise_for_status()
        df = pl.read_csv(io.BytesIO(resp.content))
        col = "versions" if "versions" in df.columns else df.columns[0]
        versions = [str(v) for v in df[col].to_list() if v is not None]
        if not versions:
            raise RuntimeError("E-GMD-VERSION versions.csv has no versions")
        return max(versions)
    finally:
        if own:
            c.close()


def fetch_csv(version: str, cache_dir: str | os.PathLike | None = None) -> Path:
    """Download `GMD_{version}.csv` to the cache (reusing an existing copy) and return its path."""
    cache = Path(cache_dir) if cache_dir else default_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"GMD_{version}.csv"
    if path.exists() and path.stat().st_size > 0:
        return path
    tmp = path.with_suffix(".csv.part")
    with httpx.stream(
        "GET", f"{BASE}/distribute/GMD_{version}.csv", timeout=180.0, follow_redirects=True
    ) as resp:
        resp.raise_for_status()
        with open(tmp, "wb") as fh:
            for chunk in resp.iter_bytes():
                fh.write(chunk)
    tmp.replace(path)
    return path
