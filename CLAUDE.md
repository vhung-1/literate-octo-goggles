# Project notes for Claude

Interactive valuation comp sheet (financials & market-infrastructure names),
hosted on GitHub Pages. See `README.md` for structure and `REFRESH.md` for the
data-refresh runbook.

## Standing preferences

- **When the user asks to "update" (refresh the data):** after merging the
  refresh PR, reply with the **GitHub link** — primarily the **merged PR URL**
  for that update — alongside the live site link
  (https://vhung-1.github.io/literate-octo-goggles/).
- Refreshes go through a PR into `main` (squash-merge); GitHub Pages redeploys
  automatically on merge.
