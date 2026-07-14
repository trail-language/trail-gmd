from trail_gmd.schema_fields import SCHEMA_FIELDS


def test_all_keys_are_gmd_namespaced_strings():
    assert len(SCHEMA_FIELDS) > 70
    assert all(k.startswith("gmd.") for k in SCHEMA_FIELDS)
    assert all(isinstance(v, str) for v in SCHEMA_FIELDS.values())


def test_kinds():
    assert SCHEMA_FIELDS["gmd.rGDP"] == "level"
    assert SCHEMA_FIELDS["gmd.infl"] == "rate"
    assert SCHEMA_FIELDS["gmd.CPI"] == "index"
    assert SCHEMA_FIELDS["gmd.govdebt_GDP"] == "ratio"
    assert SCHEMA_FIELDS["gmd.income_group"] == "meta"
    assert SCHEMA_FIELDS["gmd.cbrate"] == "rate"


def test_no_forecast_or_key_columns_leak_in():
    assert not any("forecast" in k for k in SCHEMA_FIELDS)
    for leaked in ("gmd.ISO3", "gmd.year", "gmd.id", "gmd.countryname"):
        assert leaked not in SCHEMA_FIELDS
