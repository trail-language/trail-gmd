"""The gmd.* field vocabulary contributed to trail's active schema.

`SCHEMA_FIELDS` is a mapping of dotted trail column -> kind string, registered via the
`trail.schema` entry point. Field codes are GMD's own short names (see the upstream data
dictionary); kinds are trail measure hints (`level`/`rate`/`index`/`ratio`/`meta`).
"""
from __future__ import annotations

# GMD value columns (the released wide file minus countryname/ISO3/id/year and forecast_* flags).
GMD_CODES: list[str] = [
    # national accounts / output
    "nGDP", "nGDP_USD", "rGDP", "rGDP_pc", "rGDP_USD", "rGDP_pc_USD", "deflator",
    # consumption / investment
    "cons", "cons_GDP", "cons_USD", "hcons", "hcons_GDP", "hcons_USD",
    "gcons", "gcons_GDP", "gcons_USD", "inv", "inv_GDP", "inv_USD",
    "finv", "finv_GDP", "finv_USD",
    # external sector
    "exports", "exports_GDP", "exports_USD", "imports", "imports_GDP", "imports_USD",
    "CA", "CA_GDP", "CA_USD", "USDfx", "REER",
    # fiscal: expenditure / revenue / tax / deficit / debt (best / general / central tiers)
    "govexp", "govexp_GDP", "gen_govexp", "gen_govexp_GDP", "cgovexp", "cgovexp_GDP",
    "govrev", "govrev_GDP", "gen_govrev", "gen_govrev_GDP", "cgovrev", "cgovrev_GDP",
    "govtax", "govtax_GDP", "gen_govtax", "gen_govtax_GDP", "cgovtax", "cgovtax_GDP",
    "govdef", "govdef_GDP", "gen_govdef", "gen_govdef_GDP", "cgovdef", "cgovdef_GDP",
    "govdebt", "govdebt_GDP", "gen_govdebt", "gen_govdebt_GDP", "cgovdebt", "cgovdebt_GDP",
    # prices / housing
    "CPI", "infl", "HPI", "rHPI",
    # labor / population
    "pop", "unemp",
    # rates
    "strate", "ltrate", "cbrate",
    # money / credit
    "M0", "M1", "M2", "M3", "M4",
    # crisis dummies (0/1)
    "SovDebtCrisis", "CurrencyCrisis", "BankingCrisis",
    # classification
    "income_group",
]

_RATE = {"infl", "unemp", "strate", "ltrate", "cbrate"}
_INDEX = {"CPI", "deflator", "REER", "HPI", "rHPI"}
_META = {"income_group"}


def _kind(code: str) -> str:
    if code in _META:
        return "meta"
    if code.endswith("_GDP"):
        return "ratio"
    if code in _RATE:
        return "rate"
    if code in _INDEX:
        return "index"
    return "level"


#: entry-point target: {"gmd.rGDP": "level", "gmd.infl": "rate", ...}
SCHEMA_FIELDS: dict[str, str] = {f"gmd.{code}": _kind(code) for code in GMD_CODES}
