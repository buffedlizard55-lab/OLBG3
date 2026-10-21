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

---

## Third track: the OLBG lines audit layer (`arena/9590abcf-olbg3`)

Published at **/olbg/** and reachable from the shared navigation ("OLBG lines (audit)"). It ships in
the Actions artifact (`site/olbg/`) *and* as a committed root snapshot (`olbg/`), because the legacy
Pages publisher serves the repository root — the same two-target arrangement the board track uses, so
whichever publisher runs last still serves these pages. It exists because the board track and this one answer different questions:
the board prices fixtures it could verify against official competition pages, while this track
transcribes **every in-scope row OLBG listed**, keeps the exact OLBG URL on the row, and then
originates a line and a confidence label from that row — including for fixtures nobody could verify.

| Layer | Contents |
|---|---|
| `data/raw/olbg-harvest-20261021.tsv` | 137 rows transcribed from 16 OLBG pages, exact URL parts per row |
| `data/matches.json` | parsed fixtures + verification status per field |
| `data/verifications.json` | 31 source records (official / primary / secondary) + 26 event-level records with the claim each source supports |
| `data/lines.json` | our model: Beta(2,2)-shrunk tip split → sport home edge → price at 5% hold; handicap `−Φ⁻¹(p) × σ_sport`; documented total baselines |
| `data/predictions-olbg.json` | 5 predictions, 71–80 words, sources for every factual sentence |
| `data/flagged.json` | 17 flagged items with sources, published at `/olbg/flagged.html` |
| `olbg-board/` | generated pages (dashboard, lines & picks, predictions, all matches, method, flagged, 15 sport pages) |

```sh
python3 tools/build_dataset.py   # raw TSV + verifications -> data/matches.json
python3 tools/originate.py       # matches -> data/lines.json
python3 tools/build_site.py      # data -> olbg-board/
python3 tools/check_site.py      # links, source links per row, word counts, placeholders
```

Findings this track adds that the other tracks do not publish:

* OLBG prints clock times with **no timezone**, and they are internally inconsistent — snooker and
  greyhound rows behave like US Eastern while an NHL row cannot. No scheduled start is ever taken
  from an OLBG clock time (`flagged.html` FL-002).
* The same golf tournament appears with **two different dates** on two OLBG pages (FL-003), and the
  course par is reported as both 71 and 72 (FL-005).
* **111 of 137 rows** have no competition name anywhere in the source; they stay blank (FL-006).
* Three rows were truncated at the page-boundary; their tip counts stay blank (FL-007).
* The Gaelic football question is recorded on both sides: the feed track excludes it, the board
  track and this track include it, and every Gaelic row here is tagged so it can be dropped in one
  step (FL-001).

`data/predictions.json` belongs to the board track; this track's predictions are
`data/predictions-olbg.json`, so neither can overwrite the other.
