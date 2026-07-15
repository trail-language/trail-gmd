"""Turn a GMD release CSV into a Trail (country x year) panel.

The released file is wide: one row per (ISO3, year), one column per indicator code, plus a
`forecast_<code>` flag per variable. We select the requested `gmd.*` fields, optionally mask
IMF-WEO projection cells to null, and emit a `(entity, time)` polars panel.
"""
from __future__ import annotations

import os

import polars as pl

from trail_gmd.schema_fields import SCHEMA_FIELDS

ISO3_COL = "ISO3"
YEAR_COL = "year"


def to_panel(
    csv_path: str | os.PathLike,
    fields: set[str],
    *,
    historical_only: bool = True,
) -> pl.DataFrame:
    """Return a `(entity, period, gmd.*)` panel for the requested fields.

    `entity` = ISO3 country, `period` = int year. Value columns are Float64 (meta columns
    Utf8). When `historical_only`, any cell flagged by its `forecast_<code>` column is nulled.
    """
    requested = [f for f in sorted(fields) if f in SCHEMA_FIELDS]
    codes = [f.split(".", 1)[1] for f in requested]

    header = pl.read_csv(csv_path, n_rows=0).columns
    present = [c for c in codes if c in header]
    read_cols = [ISO3_COL, YEAR_COL, *present]
    forecast_flags: dict[str, str] = {}
    if historical_only:
        for code in present:
            flag = f"forecast_{code}"
            if flag in header:
                forecast_flags[code] = flag
                read_cols.append(flag)

    df = pl.read_csv(csv_path, columns=read_cols, infer_schema_length=20000)

    if forecast_flags:
        df = df.with_columns([
            pl.when(pl.col(flag) == 1).then(None).otherwise(pl.col(code)).alias(code)
            for code, flag in forecast_flags.items()
        ])

    value_exprs = []
    for code in present:
        dtype = pl.Utf8 if SCHEMA_FIELDS[f"gmd.{code}"] == "meta" else pl.Float64
        value_exprs.append(pl.col(code).cast(dtype, strict=False).alias(f"gmd.{code}"))

    return (
        df.select([
            pl.col(ISO3_COL).cast(pl.Utf8).alias("entity"),
            pl.datetime(pl.col(YEAR_COL).cast(pl.Int32, strict=False), 12, 31).alias("time"),
            *value_exprs,
        ])
        .drop_nulls("entity")
        .sort(["entity", "time"])
    )
