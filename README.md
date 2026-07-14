# trail-gmd

Global Macro Database (GMD) data source for [Trail](https://github.com/trail-language/trail-py).
It exposes GMD's country-by-year macroeconomic indicators as a Trail panel - `security = ISO3
country`, `period = year` - so you can screen, rank, and factor countries and macro series with the
same language you use for equities.

## ⚠️ License: non-commercial research use only

The GMD **data** is distributed under **CC BY-NC-SA 4.0** plus the maintainers' **GMD Research Use
Terms**, which **prohibit commercial and for-profit use** (including internal use at banks, asset
managers, hedge funds, and consultancies) and prohibit embedding the data into monetized products,
APIs, models, indices, or signals. This adapter's **code** is MIT, but the **data it fetches is
not**. By using it you agree to the GMD terms.

trail-gmd therefore **fetches on demand and never bundles or re-hosts GMD data**, caches only on your
machine, and prints the required citation on first load:

> Mueller, K., Xu, C., Lehbib, M., & Chen, Z. (2025). *The Global Macro Database: A New International
> Macroeconomic Dataset.* NBER Working Paper No. 33714. https://www.globalmacrodata.com

If your use is commercial, do not use this source; contact the GMD maintainers.

## Install

```bash
pip install trail-gmd
```

## Configure

```yaml
sources:
  macro:
    driver: gmd
    options:
      countries: [USA, DEU, JPN, GBR, CHN]   # ISO3; omit for all countries
      version: current                        # or a pinned "YYYY_MM"
      historical_only: true                   # mask IMF-WEO projections to null (default)
      cache_dir: ".gmd-cache"
precedence:
  default: [macro]
panel:
  periods: [1990, 2024]
  strict: true
```

Then:

```bash
trail catalog gmd            # the gmd.* field vocabulary
trail run model.trail --model m --config trail.yaml
```

## Fields

Macro indicators use GMD's own short codes under a `gmd.` prefix, for example: `gmd.rGDP` (real GDP),
`gmd.nGDP`, `gmd.rGDP_pc` (per capita), `gmd.CPI`, `gmd.infl` (inflation %), `gmd.unemp`,
`gmd.govdebt_GDP` (government debt, % of GDP), `gmd.CA_GDP` (current account, % of GDP),
`gmd.strate`/`gmd.ltrate`/`gmd.cbrate` (rates), `gmd.M0`-`gmd.M4`, `gmd.REER`, `gmd.HPI`,
`gmd.pop`, the three fiscal tiers (`gmd.gov*` / `gmd.gen_gov*` / `gmd.cgov*`), the crisis dummies
(`gmd.BankingCrisis`, `gmd.SovDebtCrisis`, `gmd.CurrencyCrisis`), and `gmd.income_group`.

`historical_only` (default true) masks any IMF-WEO projection value (2025+) to null so models see
realized history unless you opt in to forecasts.

## Notes

Annual only. The panel is sparse before roughly 1950 for most countries. National-accounts
identities need not reconcile exactly (each series is independently chain-linked). Data revises near
the frontier between vintages; pin `version` for reproducibility.

## License

Code: MIT. Data: CC BY-NC-SA 4.0 + GMD Research Use Terms (non-commercial), fetched on demand.
