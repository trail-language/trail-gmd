"""GmdSource: a Trail data source backed by the Global Macro Database.

Country-by-year macro indicators as a Trail panel (`entity` = ISO3, `time` = year-end).
Implements the full ExtendedDataSource contract and contributes the `gmd.*` field
vocabulary (see trail_gmd.schema_fields). Data is fetched on demand under GMD's
non-commercial terms; the required citation is printed on first load.
"""
from __future__ import annotations

import warnings
from functools import lru_cache

import polars as pl

from trail.source import Capabilities, ExtendedDataSource, FieldInfo

from trail_gmd import convert, fetch
from trail_gmd.schema_fields import SCHEMA_FIELDS

CITATION = (
    "Global Macro Database - Mueller, Xu, Lehbib, Chen (2025), NBER Working Paper 33714. "
    "Data under CC BY-NC-SA 4.0 + GMD Research Use Terms (non-commercial). "
    "https://www.globalmacrodata.com"
)

@lru_cache(maxsize=1)
def _cite() -> None:
    warnings.warn(f"[trail-gmd] {CITATION}", GmdCitationNotice, stacklevel=3)


class GmdCitationNotice(UserWarning):
    """The required GMD attribution (printed once per process, via warnings not stdout)."""


class GmdSource(ExtendedDataSource):
    """Global Macro Database indicators as a country-by-year Trail panel."""

    name = "gmd"

    def __init__(self, options: dict | None = None) -> None:
        super().__init__(options)
        self.version = str(self.options.get("version", "current"))
        self.cache_dir = self.options.get("cache_dir")
        self.historical_only = bool(self.options.get("historical_only", True))
        countries = self.options.get("countries") or self.options.get("tickers") or []
        self._countries = [str(c).upper() for c in countries]

    def load(self, fields: set[str], *, periods: tuple[int, int] | None = None) -> pl.DataFrame:
        _cite()
        version = fetch.resolve_version(self.version)
        path = fetch.fetch_csv(version, self.cache_dir)
        panel = convert.to_panel(path, fields, historical_only=self.historical_only)
        if self._countries:
            panel = panel.filter(pl.col("entity").is_in(self._countries))
        if periods is not None:
            lo, hi = periods
            yr = pl.col("time").dt.year()
            panel = panel.filter((yr >= lo) & (yr <= hi))
        return panel

    def available_fields(self) -> set[str]:
        return set(SCHEMA_FIELDS)

    def describe_field(self, field: str) -> FieldInfo | None:
        if field in SCHEMA_FIELDS:
            return FieldInfo(field, True, "direct", f"GMD column '{field.split('.', 1)[1]}'")
        return None

    def entities(self, universe: str | None = None) -> list[str]:
        return list(self._countries)

    def capabilities(self) -> Capabilities:
        return Capabilities(
            frequency="annual",
            entity_dim="country",  # entities are ISO3 countries, remapped onto stocks via meta.country
            provides_meta=True,
            provenance="Global Macro Database (NBER WP 33714)",
        )

    def close(self) -> None:
        pass
