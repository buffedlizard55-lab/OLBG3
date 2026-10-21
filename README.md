# OLBG3 — reverse-engineered multi-sport board, our own lines, our own picks

A static dashboard built by reverse-engineering [OLBG.com](https://www.olbg.com/betting-tips): every in-scope
sport's rows, a betting line **we** originate for each row, a pick with a confidence grade, written
predictions for the high-confidence picks, and a verification log that links every check to an official source.

**Live site:** <https://buffedlizard55-lab.github.io/OLBG3/>

| Page | What it is |
|---|---|
| `index.html` | Dashboard: coverage by sport, high-confidence picks, every row in one filterable table |
| `predictions.html` | The written predictions (high-confidence picks only, 30+ words, sourced) |
| `verification.html` | Row-by-row verification log: OLBG row, official value, official link, status |
| `audit.html` | This build's review log: what was checked, what failed, what changed, sources for manual review |
| `flagged.html` | Flagged for Review: every finding and every unverified row, with links |
| `audit.html` | Audit log: every check this build ran, against which official page, and what changed |
| `method.html` | Scope, model, disclosed assumptions, price formula, what we refuse to do |
| `sports/<sport>.html` | One page per sport (15 sports) |
| `feed-overview.html`, `matches.html`, `coverage.html`, `review.html`, `markets.html` | The separate official-feed pipeline (NHL/MLB/NBA raw schedules, no picks) |
| `/olbg/` | The OLBG lines audit track (137 captured rows, its own pages) |

## Scope

Included (15 sports, 137 rows): Tennis 14, Basketball 14, Ice Hockey 7, Cricket 9, Baseball 1, Volleyball 15,
Darts 14, Snooker 6, Rugby Union 15, Rugby League 3, Handball 15, Gaelic Football 5, Golf 10, Motor Racing 3,
Greyhounds 6.

Of those 137 rows, **114 are two-sided fixtures** and **23 are outright or race markets** (golf tournaments,
the F1 race and drivers' championship, greyhound races, rugby league futures, the All-Ireland championship).

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
   both sides (+2), model probability ≥65% (+2) or ≥55% (+1). HIGH ≥ 6, MEDIUM 3–5, LOW ≤ 2.
4. **Predictions** — written only for HIGH picks, at least 30 words, every factual claim attached to a
   source that was actually read. Currently **13** predictions: eight rugby union fixtures (four URC,
   four Pro D2), one Top 14 fixture and four ice-hockey fixtures. Each one was re-verified line by line
   on 2026-10-21; eight were corrected and one (IHO-01) was withdrawn when its fixture turned out not to
   be confirmed by an official page. The corrections are listed on `audit.html` and `flagged.html`.
5. **Verification** — a row is `verified` only when the specific fixture appears on the competition's own
   site, and the official wording is copied into the row. Otherwise it is `unverified`, the official fields
   stay blank, and the row is listed on the Flagged page. Currently **71 verified / 66 unverified**
   (the curve moved up as later sessions verified fixtures; the count here is always the built count).

## Build and checks

```bash
python3 scripts/build_gap_sports.py   # price the outright/race markets -> data/gap_sports.json
python3 scripts/build_site.py         # board pages -> site/
python3 scripts/check_board.py        # board invariants (sources, verification, prices, predictions)
python3 scripts/check_links.py        # no broken local links
python3 tools/check_site.py           # /olbg/ audit track
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
| `data/predictions.json` | 13 predictions (HIGH picks only) | board |
| `data/matches.json`, `data/lines.json` | 137 captured rows + 137 model lines | `/olbg/` audit track |
| `data/master_matches.json` | 76 legacy rows, slated for deletion | **nothing** — see `data/LEGACY-NOTICE.md` |
| `data/flagged.json`, `data/flagged_review.json` | findings | documentation |

## Known limitations (also on the site)

* 66 of 137 rows have no official fixture-level confirmation yet. They are published as unverified, not
  quietly dropped. One row that had been marked verified (IHO-01) was downgraded on 2026-10-21 because its
  only source was a betting preview rather than an official page.
* OLBG's listings paginate ("Load More Tips"): the board is the first page of each sport.
* OLBG's clock labels carry no time zone and run a few minutes late; they are published verbatim and no
  start time is derived from them.
* Tip counts move between captures (`Genesis Championship` 5/18 → 6/20 within two hours); every share is a
  timestamped snapshot.
* Prices, handicaps, totals and confidence grades are **our model output**, not facts and not market quotes.

18+. If gambling is causing you harm, contact [GamCare](https://www.gamcare.org.uk/) or
[GambleAware](https://www.gambleaware.org/).
