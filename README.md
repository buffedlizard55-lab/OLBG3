# OLBG3 — verified match board, originated lines and picks

Two research tracks run side by side in this repository, and the site publishes both:

1. **The board** (`scripts/build_site.py`, data in `data/sports/`, `data/official.json`, `data/events.json`) —
   every in-scope sport on OLBG.com, reverse-engineered from its listing/event pages, checked against official
   competition sources where we could, priced by our own model, graded by confidence, with sourced written
   predictions for high-confidence picks.
2. **The official feed** (`scripts/update.py` + `scripts/build.py`) — an hourly pull of official NHL / MLB / NBA
   schedule feeds into `data/current.json`, published as `matches.html` and `coverage.html`. It deliberately
   publishes no picks, and its validator (`scripts/check.py`) enforces that any betting field in *that* dataset
   stays blank until it is validated.

Keeping them separate is deliberate: one is sourced facts plus clearly-labelled model opinion, the other is
untouched official feed data. Neither one is allowed to quietly fill the other's gaps.

## Website
https://buffedlizard55-lab.github.io/OLBG3/

## Build locally
```sh
python3 scripts/update.py            # optional: refresh official feeds (needs network)
python3 -m unittest discover -s tests -v
python3 scripts/build.py             # official-feed pages -> site/
python3 scripts/build_site.py        # board pages -> site/ (run after build.py)
python3 scripts/check.py             # feed data + links
python3 scripts/check_links.py       # every local link in site/, recursively
python3 -m http.server 8000 --bind 0.0.0.0 --directory site
```

`site/` is generated, not tracked. GitHub Actions rebuilds and deploys it on every push to `main` and hourly.

### Why the built site is also committed at the repository root

The repository's Pages site is configured for **legacy branch publishing** (`source: main`, `path: /`), and every
token available here gets `403 Resource not accessible by integration` from `PUT /repos/{owner}/{repo}/pages`, so that
setting cannot be changed from a session. GitHub therefore runs two publishers — the legacy Jekyll build of `main`
root, and our Actions artifact (`site/`) — and whichever finishes last wins.

To stop the site flapping between two different versions, both targets are made byte-identical: `--snapshot` mirrors
the build into the repository root. **After any change to the site, regenerate and commit the snapshot:**

```sh
python3 scripts/build.py && python3 scripts/build_site.py --snapshot && python3 scripts/check_links.py
```

Row data lives in `data/`, so the root snapshot is a build output, not a second source of truth.

## Where to check us
- Dashboard: `index.html` · Predictions: `predictions.html` · Verification log: `verification.html`
- **Flagged for Review: `flagged.html`** — every irregularity and every row we could not verify
- Method, scope and disclosed modelling assumptions: `method.html`
- Official-feed notes: `coverage.html`, `markets.html`, `review.html`

## Rules this repo runs on
- No inferred values. If OLBG does not state a competition, the cell is blank and the row is flagged.
- Nothing is marked verified without a link to the competition's own source.
- Our prices/handicaps/totals are model output with printed assumptions — never bookmaker prices, never facts.
- Predictions are written only where verified current form exists for both sides.

## Sources
- OLBG listings/event pages (structure documented in `docs/olbg-structure.md`)
- `https://stats.unitedrugby.com/match-centre/2026-27/4`, `.../table/2026-27`
- `https://www.nhl.com/schedule/2026-10-21`, `https://www.nhl.com/standings`
- `https://www.nba.com/schedule?date=10%2F21%2F2026`
- Official feeds: `api-web.nhle.com`, `statsapi.mlb.com`, `cdn.nba.com`

Not affiliated with OLBG. 18+.
