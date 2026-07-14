import polars as pl

from trail_gmd import convert


def test_panel_shape_keys_and_dtypes(gmd_csv):
    panel = convert.to_panel(gmd_csv, {"gmd.rGDP", "gmd.infl", "gmd.income_group"})
    assert panel.columns[:2] == ["security", "period"]
    assert set(panel.columns) == {"security", "period", "gmd.rGDP", "gmd.infl", "gmd.income_group"}
    assert panel.schema["security"] == pl.Utf8
    assert panel.schema["period"] == pl.Int32
    assert panel.schema["gmd.rGDP"] == pl.Float64
    assert panel.schema["gmd.income_group"] == pl.Utf8
    assert sorted(panel["security"].unique().to_list()) == ["DEU", "USA"]


def test_historical_only_masks_projection_cells(gmd_csv):
    masked = convert.to_panel(gmd_csv, {"gmd.rGDP", "gmd.nGDP"}, historical_only=True)
    usa22 = masked.filter((pl.col("security") == "USA") & (pl.col("period") == 2022)).to_dicts()[0]
    assert usa22["gmd.rGDP"] is None       # forecast_rGDP == 1 -> masked
    assert usa22["gmd.nGDP"] == 25000.0    # no forecast flag column -> kept


def test_include_forecasts_when_disabled(gmd_csv):
    full = convert.to_panel(gmd_csv, {"gmd.rGDP"}, historical_only=False)
    usa22 = full.filter((pl.col("security") == "USA") & (pl.col("period") == 2022)).to_dicts()[0]
    assert usa22["gmd.rGDP"] == 20100.0


def test_unknown_and_absent_fields_are_ignored(gmd_csv):
    # gmd.M2 is a real field but absent from the fixture columns; income.revenue is not gmd.*
    panel = convert.to_panel(gmd_csv, {"gmd.rGDP", "gmd.M2", "income.revenue"})
    assert panel.columns == ["security", "period", "gmd.rGDP"]
