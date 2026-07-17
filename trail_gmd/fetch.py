"""On-demand fetch of the GMD release file from its public S3 bucket.

The full harmonized panel is a single stable, versioned, unauthenticated CSV. We resolve
the current version from a tiny helper file, then download the CSV to a per-version file in
a user-scoped cache. GMD data is never bundled or committed (non-commercial license); it is
fetched fresh and cached only on the end-user's machine.
"""
from __future__ import annotations

import io
import os
import warnings
from pathlib import Path

import httpx
import polars as pl


class GmdFetchWarning(UserWarning):
    """Network degradation while fetching GMD data (an offline fallback was used)."""


def _version_key(v: str) -> tuple[int, int]:
    """Sortable (year, month) from 'YYYY_MM' - a plain string max would order
    '2025_9' above '2025_10'."""
    try:
        year, month = v.split("_", 1)
        return int(year), int(month)
    except ValueError:
        return (0, 0)


def _newest_cached(cache: Path) -> str | None:
    versions = [p.stem.removeprefix("GMD_") for p in cache.glob("GMD_*.csv")]
    return max(versions, key=_version_key) if versions else None

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
        return max(versions, key=_version_key)
    except (httpx.HTTPError, OSError) as e:
        cached = _newest_cached(default_cache_dir())
        if cached is not None:  # warm cache: a flaky network must not block a load
            warnings.warn(f"W-GMD-OFFLINE version resolution failed ({e}); using cached "
                          f"release {cached}", GmdFetchWarning, stacklevel=2)
            return cached
        raise
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
    last_err: Exception | None = None
    for attempt in (1, 2):  # one retry on transient stream failure
        try:
            with httpx.stream(
                "GET", f"{BASE}/distribute/GMD_{version}.csv", timeout=180.0, follow_redirects=True
            ) as resp:
                resp.raise_for_status()
                with open(tmp, "wb") as fh:
                    for chunk in resp.iter_bytes():
                        fh.write(chunk)
            head = tmp.open("rb").read(256).decode("utf-8", "replace")
            if "ISO3" not in head or "year" not in head:  # validate before promoting to cache
                raise RuntimeError(f"E-GMD-DOWNLOAD GMD_{version}.csv does not look like a GMD release")
            tmp.replace(path)
            return path
        except (httpx.HTTPError, OSError, RuntimeError) as e:
            last_err = e
            tmp.unlink(missing_ok=True)  # never leave .part debris
            if attempt == 2 or isinstance(e, RuntimeError):
                raise
            warnings.warn(f"W-GMD-RETRY download attempt {attempt} failed ({e}); retrying",
                          GmdFetchWarning, stacklevel=2)
    raise last_err  # unreachable; satisfies control-flow analysis
