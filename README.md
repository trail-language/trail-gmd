# trail-gmd

Global Macro Database ([NBER Working Paper 33714](https://www.globalmacrodata.com)) country-by-year
macro indicators for [Trail](https://github.com/trail-language).

trail-gmd is **country-keyed**, not stock-keyed: its `capabilities()` declare `entity_dim="country"`
(rows are ISO3 codes, not tickers) and `bridge_field="meta.country"`. It carries no stock universe of
its own - Trail remaps its `gmd.*` fields onto each stock via that stock's `meta.country`, supplied by
an entity-keyed source such as [trail-fmp](https://pypi.org/project/trail-fmp) or trail-edgar. So gmd
always rides alongside a stock source:

```yaml
# trail.yaml
sources:
  fmp:
    driver: fmp
    options:
      api_key: ${FMP_API_KEY}
      tickers: [AAPL, MSFT, DTE.DE]
  gmd:
    driver: gmd
    options:
      countries: [USA, DEU]   # optional: narrows the fetch; omit for every GMD country
precedence:
  default: [fmp, gmd]
```

```trail
model factor {
  export revenue = income.revenue        # from fmp - entity-keyed, native to the stock
  export cpi     = gmd.CPI                # from gmd - country-keyed, bridged via meta.country
}
```

**Non-commercial data license** - see [Attribution](#attribution) below before you use this in
anything commercial.

## Provides

The `gmd.*` namespace: GMD's own short indicator codes, one field each, at **annual** frequency on the
country dimension - 81 fields in total. A representative sample, with the `kind` hint Trail uses for
each:

| Field | Kind | Meaning |
|---|---|---|
| `gmd.rGDP` | level | Real GDP |
| `gmd.rGDP_pc` | level | Real GDP per capita |
| `gmd.CPI` | index | Consumer price index |
| `gmd.infl` | rate | Inflation, % |
| `gmd.unemp` | rate | Unemployment, % |
| `gmd.strate` / `gmd.ltrate` / `gmd.cbrate` | rate | Short-term / long-term / central bank rates |
| `gmd.govdebt_GDP` | ratio | Government debt, % of GDP (also `gen_gov*` / `cgov*` tiers) |
| `gmd.CA_GDP` | ratio | Current account, % of GDP |
| `gmd.REER` | index | Real effective exchange rate |
| `gmd.HPI` | index | House price index |
| `gmd.M0`-`gmd.M4` | level | Money supply aggregates |
| `gmd.BankingCrisis` / `gmd.SovDebtCrisis` / `gmd.CurrencyCrisis` | level | Crisis dummies (0/1) |
| `gmd.income_group` | meta | World Bank income classification |

Full coverage otherwise: national accounts and output (GDP, deflator), consumption/investment/trade
(each with `_GDP`-share and USD variants), the three fiscal tiers (budgetary / general-government /
central-government expenditure, revenue, tax, deficit, debt), external balances and FX, money and
credit, population, and the crisis/classification fields above. Kinds break down as 47 `level`, 23
`ratio`, 5 `rate`, 5 `index`, 1 `meta`. Run `trail catalog gmd` for the full, current list.

## Configure

```yaml
# trail.yaml
sources:
  fmp:
    driver: fmp
    options:
      api_key: ${FMP_API_KEY}
      tickers: [AAPL, MSFT]
  gmd:
    driver: gmd
    options:
      countries: [USA, DEU, JPN]   # optional; omit to fetch every GMD country
      version: current              # or a pinned "2025_09"
      historical_only: true         # mask IMF-WEO projections to null (default)
      cache_dir: .gmd-cache
precedence:
  default: [fmp, gmd]
panel:
  periods: [1990, 2024]
```

gmd needs **no credentials** - it fetches an unauthenticated, public CSV release. Then:

```bash
trail catalog gmd            # the gmd.* field vocabulary
trail run model.trail --model m --config trail.yaml
```

## Options

Every option `GmdSource.__init__` reads from `options:`:

| Option | Type | Default | Notes |
|---|---|---|---|
| `countries` (alias `tickers`) | `list[str]` | every GMD country | ISO3 codes to scope the fetch; the loaded panel is filtered to these. `tickers` is accepted as an alias so the same key works across entity- and country-keyed sources in one config |
| `version` | `str` | `"current"` | The GMD release to fetch. `"current"` resolves to the newest version listed in the upstream `helpers/versions.csv` (one network call); any other value (e.g. `"2025_09"`) is used as-is, no resolution call. If resolution fails and a version is already cached locally, the newest cached version is used instead, with a `GmdFetchWarning` |
| `historical_only` | `bool` | `true` | Mask any cell GMD flags via its `forecast_<code>` column (an IMF-WEO projection, currently 2025+) to null, so models see only realized history. Set `false` to include projected values |
| `cache_dir` | `str` | `$TRAIL_GMD_CACHE`, else `~/.cache/trail-gmd` | Local directory the versioned release CSV (`GMD_<version>.csv`) is cached in; reused across loads |

There is no `pit` option: gmd's point-in-time behavior isn't configurable, because it has nothing to
be configured - see below.

## Point-in-time / bridge

gmd is **naive**: annual macro data has no filing coordinate, so `capabilities().pit` is left at its
default (`False`) - unlike a restated-statement source, there's no historical-vs-current distinction
to opt into. Its only role in Trail's point-in-time model is as a country-level series **remapped by
the bridge**, not as a series with its own PIT.

`capabilities()` declares `entity_dim="country"` (the `entity` column is an ISO3 code, not a ticker)
and `bridge_field="meta.country"`. At align time Trail:

1. Reads each canonical entity's (stock's) `meta.country` value, supplied by an entity-keyed source
   in the same config (e.g. trail-fmp normalizes this to ISO3 for exactly this purpose).
2. Joins gmd's row for that country onto the stock, as-of each period - gmd is coarser (annual) than
   most target frequencies, so this is a "most recent known value" match, not an exact one.

If no loaded source supplies `meta.country`, Trail raises `E-DIM-UNMAPPED`; a foreign-dimension source
that declared no `bridge_field` at all would raise `E-DIM-NOBRIDGE`. In practice: always pair gmd with
a stock source that resolves country, or its fields simply have nowhere to land.

## Attribution

> [!WARNING]
> The GMD **data** is licensed **CC BY-NC-SA 4.0** plus the maintainers' **GMD Research Use Terms**,
> which **prohibit commercial and for-profit use** - including internal use at banks, asset managers,
> hedge funds, and consultancies - and prohibit embedding the data into monetized products, APIs,
> models, indices, or signals. This adapter's **code** is MIT; the **data it fetches is not**. If your
> use is commercial, do not use this source - contact the GMD maintainers instead.

Required citation:

> Mueller, K., Xu, C., Lehbib, M., & Chen, Z. (2025). *The Global Macro Database: A New International
> Macroeconomic Dataset.* NBER Working Paper No. 33714. https://www.globalmacrodata.com

trail-gmd prints this citation as a `GmdCitationNotice` warning (not stdout) the first time a load
happens in a process, and never bundles, re-hosts, or commits GMD data - it fetches on demand and
caches only on your machine (`cache_dir`).

Code: MIT. Data: CC BY-NC-SA 4.0 + GMD Research Use Terms (non-commercial), fetched on demand.
