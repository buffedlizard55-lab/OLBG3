# OLBG3 — reverse-engineered multi-sport board, our own lines, our own picks

A static dashboard built from a captured [OLBG.com](https://www.olbg.com/betting-tips) listing: in-scope rows,
our originated lines where the captured market inputs support them, confidence grades, written predictions for
HIGH picks, and a verification log linking checks to official sources. It is a dated snapshot, not a live feed.

**Live site:** <https://buffedlizard55-lab.github.io/OLBG3/>

**Freshness warning:** The latest OLBG capture in this repository completed **2026-10-21 07:05 UTC**
(`data/meta.json`, `data/raw/olbg-harvest-20261021T0650Z.tsv`). This work session is dated 2026-10-22; no new
OLBG capture was made here. Relative start labels such as “Tomorrow” were captured verbatim and must not be
interpreted as today's schedule. The official-feed updater does not refresh this OLBG capture. Treat match times,
tip counts and featured-market selections as stale until a new source capture is verified. No bookmaker-market
prices were captured; the displayed decimals are our model quotes, so the requested American-odds range (-250
to +10000) and market-implied >70% chance cannot be verified or used as a filter.

| Page | What it is |
|---|---|
| `index.html` | Dashboard: coverage by sport, high-confidence picks, every row in one filterable table |
| `predictions.html` | The written predictions (high-confidence picks, 30+ words, sourced, plus any kept after a downgrade) |
| `lines.html` | Every market we originated for every row: money line, handicap, total, basis |
| `verification.html` | Row-by-row verification log: OLBG row, official value, official link, status |
| `audit.html` | This build's review log: what was checked, what failed, what changed, sources for manual review |
| `flagged.html` | Flagged for Review: every finding and every unverified row, with links |
| `method.html` | Scope, model, disclosed assumptions, price formula, what we refuse to do |
| `sports/<sport>.html` | One page per sport (15 sports) |
| `feed-overview.html`, `matches.html`, `coverage.html`, `review.html`, `markets.html` | The separate official-feed pipeline (NHL/MLB/NBA raw schedules, no picks) |
| `/olbg/` | The OLBG lines audit track (189 captured rows, its own pages) |

## Scope

Included (15 sports, 137 rows): Tennis 14, Basketball 14, Ice Hockey 7, Cricket 9, Baseball 1, Volleyball 15,
Darts 14, Snooker 6, Rugby Union 15, Rugby League 3, Handball 15, Gaelic Football 5, Golf 10, Motor Racing 3,
Greyhounds 6.

Of those 137 rows, **114 are two-sided fixtures** and **23 are outright or race markets** (golf tournaments,
the F1 race and drivers' championship, greyhound races, rugby league futures, the All-Ireland championship).
The same 16 outright markets are listed twice upstream (in `data/sports/*.json` and again in
`data/gap_sports.json`); the board counts and prices each OLBG event id once, which is why it reports 137 rows
rather than 153 — a golf tournament is not a two-sided fixture.

Excluded as instructed: soccer/football, American football, boxing, UFC/MMA, hurling, horse racing, cycling,
specials. Gaelic football, greyhound racing and motor racing are **not** on that list, so they are included —
each with the ambiguity recorded on the Flagged for Review page.

## How the numbers are produced

1. **Capture** — each OLBG sport listing is read and transcribed row by row with its event URL, market,
   most-tipped selection and tip count (`data/matches.json`, `data/events.json`, and for the outright
   markets `data/raw/gap_sports_capture_20261021.json`).
2. **Origination** — our own prices, never bookmaker quotes:
   * two-sided model (`scripts/model.py`): official league data where it exists, otherwise the de-vigged
     OLBG tip share, with a 5% overround;
   * one-selection model (`scripts/build_gap_sports.py`): `p = (wins + a) / (total + k)` with a
     `Beta(a, b)` prior whose mean is `1/N` (N = the field size) and strength `k`, then `odds = 0.95 / p`.
     N and k are disclosed assumptions and are written into every row.
3. **Grading** — HIGH / MEDIUM / LOW from three scored factors: fixture verified (+2), official form for
   both sides (+2), model probability strictly >70% (+2) or ≥55% (+1). HIGH ≥ 6, MEDIUM 3–5, LOW ≤ 2. The
   >70% rule is about our model, not sportsbook market odds.
4. **Predictions** — written only for HIGH picks, at least 30 words, with a clear selection. Source tiers are
   shown on the page; non-official supporting links are explicitly flagged rather than presented as official
   verification. The current board has **13** HIGH predictions: eight rugby union, four ice hockey, one EuroLeague
   basketball. Two former picks (65.13%, 66.85%) were downgraded to MEDIUM and removed from the HIGH list.
5. **Verification** — a row is `verified` only when the specific fixture or tournament appears on the
   competition's own site (or one of the two clubs' own sites) and the official wording is copied into the row.
   A reputable third-party listing is labelled `corroborated`, never `verified`; a row with no source says
   `unverified`, keeps its official fields blank, and is listed on the Flagged page. Currently **115 verified** (103 official + 6 club-official fixtures + 6 official outright/race events) / **4 corroborated / 18 unverified**. There are
   originated prices on **132/137** rows, 83 handicaps, and 25 totals. Five fixtures have no winner price: their
   captured OLBG leading selections are non-winner markets (one total and four ties), so the model refuses to
   turn those into match-winner probabilities. This board is not a complete market-by-market inventory.

## Build and checks

```bash
python3 scripts/model.py              # board rows, prices, picks, confidence -> data/events.json
python3 scripts/build.py              # official-feed pages/data -> site/
python3 scripts/check.py              # official-feed invariants
python3 scripts/build_gap_sports.py   # price outright/race markets -> data/gap_sports.json
python3 scripts/build_site.py         # combined board pages -> site/ (after feed build)

python3 scripts/check_board.py        # board invariants (sources, verification, prices, predictions)
python3 scripts/check_links.py        # combined site: no broken local links
python3 tools/build_dataset.py        # /olbg/ audit track
python3 tools/originate.py
python3 tools/build_site.py
python3 tools/check_site.py
python3 -m unittest discover -s tests # source-policy tests
```

The CI workflow (`.github/workflows/pages.yml`) additionally runs the official-feed pipeline
(`scripts/update.py`, `scripts/build.py`, `scripts/check.py`), rebuilds both tracks, and publishes `site/`.
Pages is currently published from the branch root (`main`, `/`), so the root HTML is a committed snapshot of
`site/`; the workflow keeps the two in step.

## Data files

| File | Rows | Used by |
|---|---|---|
| `data/events.json` | 114 two-sided fixtures | board |
| `data/gap_sports.json` | 23 outright/race rows (generated) | board |
| `data/raw/gap_sports_capture_20261021.json` | the same 23 rows as captured, plus assumptions | generator input |
| `data/predictions.json` | 13 predictions, one per HIGH row | board |
| `data/matches.json`, `data/lines.json` | 189 captured rows + 189 model lines | `/olbg/` audit track |
| `data/master_matches.json` | 76 legacy rows, slated for deletion | **nothing** — see `data/LEGACY-NOTICE.md` |
| `data/flagged.json` | findings for the `/olbg/` audit track | documentation |

## Known limitations (also on the site)

* 18 of 137 rows are unverified and 4 more are corroborated only by a third-party listing. Both groups are
  published and labelled, not quietly dropped. The latest source capture is 2026-10-21 07:05 UTC; this is not a
  current live slate, and OLBG's relative date labels can now be stale.
* Handicaps exist for 83 rows; totals for 25 (rugby union and ice hockey only, where the model has an official
  scoring baseline). Cricket, darts and Gaelic football have no handicap by design — see `docs/method.md`.
* Five fixtures have no originated moneyline because OLBG's captured leading selection was a total or a tie;
  the code explicitly refuses to infer a win probability from those selections. The board does not enumerate
  every available OLBG market.
* The HIGH grade now requires a modeled selection probability strictly above 70%, plus verified fixture/form
  evidence. It is not a market-implied probability, and no sportsbook prices were captured; the requested
  American-odds window (-250 to +10000) cannot be checked. Do not treat the current model picks as satisfying
  that market-price filter.
* OLBG's listings paginate ("Load More Tips"): the board is the first page of each sport.
* OLBG's clock labels carry no time zone and run a few minutes late; they are published verbatim and no
  start time is derived from them.
* Tip counts move between captures (`Genesis Championship` 5/18 → 6/20 within two hours); every share is a
  timestamped snapshot.
* Prices, handicaps, totals and confidence grades are **our model output**, not facts and not market quotes.

18+. If gambling is causing you harm, contact [GamCare](https://www.gamcare.org.uk/) or
[GambleAware](https://www.gambleaware.org/).
