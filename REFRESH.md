# Refreshing the comp sheet

The page is fully static: `index.html` reads a generated `data.js`. To refresh,
you regenerate three input files from the **S&P Global connector**, rebuild
`data.js`, and push to `main` (GitHub Pages redeploys automatically).

## Inputs (regenerate these to refresh)

| File | Contents | How |
|------|----------|-----|
| `build/prices.json` | `{ "<id>": [close, "CCY"], "_date": "YYYY-MM-DD" }` | `get_prices_from_identifiers` for all ids |
| `build/fx.json` | `{ "CCY": <USD per 1 unit>, "_date": ... }` | spot FX for GBP, EUR, SEK (others static) |
| `build/estimates_raw.json` | one JSON line per id (consensus EPS/revenue per FY) | `get_consensus_estimates_from_identifiers` |

The identifier → display-ticker → sub-sector map is stable and lives in
`build/build_data.py` (`SECTORS`). The S&P identifiers to pull are the keys of
`build/prices.json` (use `NYSE:BAM` for the price of `BAM`).

## Steps

1. **Prices** — `get_prices_from_identifiers(<all ids>)`; write close + currency
   into `build/prices.json` with `_date` = the price date.
2. **FX** — get GBPUSD, EURUSD, EURSEK; write `build/fx.json` as USD-per-unit
   (`SEK = EURUSD / EURSEK`). CHF/CAD are ~static and only used as fallbacks.
3. **Estimates** — `get_consensus_estimates_from_identifiers(<ids>, period_type=annual,
   fiscal_start_year=<cur yr>, fiscal_end_year=<cur yr+2>)` in batches; extract
   per id/period with the jq filter below (picks the **max-magnitude** consensus
   value, which de-dupes ADR/GDR lines e.g. Adyen/LSEG/Deutsche Börse), into
   `build/estimates_raw.json`.
4. **Build** — `python3 build/build_data.py` (regenerates `data.js`; the price
   date and FX note are taken from the JSON inputs automatically).
5. **Ship** — commit `data.js` + the three inputs and push to `main`. The
   *Deploy comp sheet to GitHub Pages* workflow publishes within ~30s.

### jq extraction filter

```jq
def pick(n): [.estimates[] | select(.name==n) | .value]
             | map(select(.!=null)|tonumber) | (if length>0 then max else null end);
.results | to_entries[] | {
  id: .key, name: .value.company_name, eps_ccy: .value.data.currency,
  fy: (.value.data.periods | to_entries | map({ (.key): {
        eps:      (.value | pick("EPS Normalized Consensus Mean")),
        eps_gaap: (.value | pick("EPS (GAAP) Consensus Mean")),
        n:        (.value | pick("EPS Normalized - # of Estimates")),
        n_gaap:   (.value | pick("EPS (GAAP) - # of Estimates")),
        rev:      (.value | pick("Revenue Consensus Mean")) } }) | add)
}
```

## Automating a daily 7am refresh

> **A plain GitHub Actions cron cannot do the data pull** — the prices/estimates
> come from the **S&P Global MCP connector**, which only exists inside a Claude
> Code session (CI has no access to it or its credentials). So the *refresh* must
> run in an agent that has the connector; the *deploy* is already automated.

Set it up as a **scheduled session/trigger in Claude Code on the web**
(see https://code.claude.com/docs/en/claude-code-on-the-web) pointed at this repo,
running every day at 07:00 with this prompt:

> *"Follow REFRESH.md: re-pull prices, FX and consensus estimates from the S&P
> Global connector for every identifier in build/prices.json, regenerate
> build/{prices,fx,estimates_raw}.json, run build/build_data.py, then commit and
> push the result straight to `main` (skip the PR) so GitHub Pages redeploys."*

Pick 07:00 in your timezone (markets are closed pre-open, so you'll get the prior
session's close). Once pushed to `main`, the existing Pages workflow redeploys
the site with no further action.
