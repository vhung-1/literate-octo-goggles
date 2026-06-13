# Financials & Market Infrastructure — Valuation Comp Sheet

An interactive, single-page valuation comp sheet for ~87 listed exchanges,
information-services, payments/fintech, M&A advisory, alternative- and
traditional-asset managers, and wealth/brokerage names — categorised by
sub-sector. All data is sourced from the **S&P Global** connector.

**Live page:** once GitHub Pages is enabled (see below) the site is served at
`https://<owner>.github.io/literate-octo-goggles/`.

## What's in it

- **Comp table**, grouped by sub-sector, with per-group median P/E and revenue CAGR:
  - Current price (in the listing currency)
  - Forward consensus **EPS** for the next three fiscal years (’26E / ’27E / ’28E)
  - **P/E** for each of those three years
  - **Revenue CAGR** and **EPS CAGR**, FY1→FY3 (consensus, 2-year)
  - Click any column header to sort; filter by sub-sector or search by name.
- **Regression scatter** — growth vs. valuation, with toggles for:
  - **X axis:** Revenue CAGR ↔ EPS CAGR
  - **Y axis:** which P/E year to plot (FY1 ’26E / FY2 ’27E / FY3 ’28E — "2-yr forward")
  - **Sub-sector:** all names (coloured by sector) or a single sub-sector
  - An OLS best-fit line with slope, intercept and R² is drawn for the visible set.

## Methodology & caveats

- **EPS** uses consensus *normalized* EPS where available, falling back to GAAP
  consensus where a name has no normalized estimate (flagged `†`).
- **P/E** = price ÷ EPS, both expressed in the company's **reporting currency**.
  Where a stock trades in a different currency than it reports (e.g. EQT, Adyen,
  Experian), the price is FX-adjusted (flagged `‡`).
- Columns are labelled calendar **’26 / ’27 / ’28E** for comparability. A handful
  of **March fiscal year-end** names (Experian, Houlihan Lokey, ICG, StepStone,
  Hamilton Lane) and the newly-listed Wealthfront use **FY27 / 28 / 29E** and are
  flagged `*`.
- Prices and FX are as of the date shown in the page header. Estimates are
  consensus means and may not reflect the very latest revisions.
- **For research use only — not investment advice.**

## Reproducing the dataset

The dataset (`data.js`) is generated from raw S&P Global connector pulls:

```
build/estimates_raw.json   # consensus EPS/revenue per name, per fiscal year
build/build_data.py        # merges prices + estimates, applies FX, computes P/E & CAGR
```

Run `python3 build/build_data.py` to regenerate `data.js`. Prices and FX rates
are embedded in the script (they were point-in-time pulls from the connector).

## Enabling GitHub Pages (one-time)

The repo includes a workflow (`.github/workflows/pages.yml`) that publishes the
static site on every push to `main`. To turn it on:

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
2. Merge this PR into `main` (or re-run the *Deploy comp sheet to GitHub Pages*
   workflow). The page URL appears in the workflow run and under Settings → Pages.
