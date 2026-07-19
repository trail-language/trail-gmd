from pathlib import Path

from trail.source import LoadRequest
from trail.testing import assert_source_conforms

from trail_gmd.schema_fields import SCHEMA_FIELDS

FIXTURE = Path(__file__).parent / "fixtures" / "gmd_sample.csv"


def test_conforms_to_contract(gmd_source):
    assert_source_conforms(gmd_source, {"gmd.rGDP", "gmd.infl", "gmd.govdebt_GDP", "gmd.income_group"})


def test_available_fields_is_the_gmd_vocabulary(gmd_source):
    avail = gmd_source.available_fields()
    assert avail == set(SCHEMA_FIELDS)
    assert "gmd.rGDP" in avail and "income.revenue" not in avail


def test_describe_field(gmd_source):
    info = gmd_source.describe_field("gmd.rGDP")
    assert info is not None and info.available and info.strategy == "direct"
    assert gmd_source.describe_field("not.a.field") is None


def test_country_and_period_filter(monkeypatch):
    from trail_gmd import fetch
    from trail_gmd.source import GmdSource

    monkeypatch.setattr(fetch, "resolve_version", lambda version="current", **k: "2099_01")
    monkeypatch.setattr(fetch, "fetch_csv", lambda version, cache_dir=None: FIXTURE)
    src = GmdSource({"countries": ["USA"]})
    panel = src.load(LoadRequest(fields=frozenset({"gmd.rGDP"}), periods=(2020, 2021)))
    assert panel["entity"].unique().to_list() == ["USA"]
    assert sorted(panel["time"].dt.year().unique().to_list()) == [2020, 2021]


def test_capabilities(gmd_source):
    caps = gmd_source.capabilities()
    assert caps.frequency == "annual" and "Global Macro Database" in caps.provenance
    # entities are ISO3 countries; the engine remaps them onto stocks via meta.country
    assert caps.entity_dim == "country"
