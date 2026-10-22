# OLBG3 — reverse-engineered multi-sport board, our own lines, our own picks

A static dashboard built from a captured [OLBG.com](https://www.olbg.com/betting-tips) listing: in-scope rows,
our originated lines where the captured market inputs support them, confidence grades, written predictions for
HIGH picks, and a verification log linking checks to official sources. It is a dated snapshot, not a live feed.

**Live site:** <https://buffedlizard55-lab.github.io/OLBG3/>

**Freshness warning:** The latest OLBG capture in this repository completed **2026-10-21 07:05 UTC**
(`data/meta.json`, `data/raw/olbg-harvest-20261021T0650Z.tsv`). This work session is dated 2026-10-22; no new
OLBG capture was made here. Relative start labels such as “Tomorrow” were captured verbatim and must not be
interpreted as today's schedule. The official-feed updater does not refresh this OLBG capture. Treat match times,
tip counts and featured-market selections as stale until a new source capture is verified.

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
3. **Grading** — three evidence factors scored 0–6: fixture verified (+2), official form for both sides
   (+2), model probability ≥55% (+2). A row is HIGH only when the score is 6 **and** its price is inside the
   requested -250 to +10000 band **and** its kick-off has not passed; a score-6 row that fails either test is
   MEDIUM with the reason published. MEDIUM 3–5, LOW ≤ 2.
4. **Predictions** — written for HIGH picks, at least 30 words, non-repetitive prose naming current form,
   recent match history and an unmistakable betting selection, with every factual claim attached to an
   official source. Currently **6 high-confidence predictions**, one per HIGH row: four Pro D2 fixtures
   (Agen, Soyaux-Angouleme, Valence Romans, Grenoble), Leinster v Munster in the URC, and MLB World Series Game 1.
   Another **14 medium-confidence analysis notes** are published separately and labelled as such; they were
   written for picks that are now too short-priced to meet the band.
5. **Verification** — a row is `verified` only when the specific fixture or tournament appears on the
   competition's own site (or one of the two clubs' own sites) and the official wording is copied into the row.
   A reputable third-party listing is labelled `corroborated`, never `verified`; a row with no source says
   `unverified`, keeps its official fields blank, and is listed on the Flagged page. Currently **115 verified (109 official + 6 club-official) / 4 corroborated / 18 unverified**. There are
   originated prices on **132/137** rows, 83 handicaps, and 25 totals. Five fixtures have no winner price: their
   captured OLBG leading selections are non-winner markets (one total and four ties), so the model refuses to
   turn those into match-winner probabilities. This board is not a complete market-by-market inventory.

6. **Price band** — the brief asks for high-confidence picks on selections priced between **-250 and +10000**
   US odds, i.e. decimal **1.40 to 101.00**. `scripts/board_dates.py` performs the conversion and
   `check_board.py` refuses to publish a HIGH pick outside it. HIGH also requires a live kick-off: rows whose
   21 Oct date has passed at the 22 Oct rebuild are tagged *archive* and cannot be graded HIGH. 70 of 137 rows
   are in that archive state; the board is still the 21 Oct OLBG capture, and a fresh capture is logged as the
   next open task in `COORDINATION.md`.

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
| `data/predictions.json` | 20 written pieces: 6 HIGH predictions + 14 labelled analysis notes | board |
| `data/matches.json`, `data/lines.json` | 189 captured rows + 189 model lines | `/olbg/` audit track |
| `data/master_matches.json` | 76 legacy rows, slated for deletion | **nothing** — see `data/LEGACY-NOTICE.md` |
| `data/flagged.json` | findings for the `/olbg/` audit track | documentation |

## Known limitations (also on the site)

* 18 of 137 rows are unverified and 4 more are corroborated only by a third-party listing. Both groups are
  published and labelled, not quietly dropped. The latest source capture is 2026-10-21 07:05 UTC; this is not a
  current live slate, and OLBG's relative date labels can now be stale.
* The board is a **21 October 2026 capture**. At the 22 October rebuild, 70 rows had already kicked off; they
  are retained, tagged *archive* and excluded from high-confidence grading rather than re-dated.
* The -250 floor and a >70% win probability are mathematically incompatible with a 5% overround
  (0.95/0.70 = 1.36, or -280). The band therefore caps a HIGH pick at ~68%; high confidence means 55%+ model
  probability plus verified evidence, and the Method page says so explicitly.
* Handicaps exist for 83 rows; totals for 25 (rugby union and ice hockey only, where the model has an official
  scoring baseline). Cricket, darts and Gaelic football have no handicap by design — see `docs/method.md`.
* Five fixtures have no originated moneyline because OLBG's captured leading selection was a total or a tie;
  the code explicitly refuses to infer a win probability from those selections. The board does not enumerate
  every available OLBG market.
* The HIGH grade now applies the requested American-odds window (-250 to +10000) as a hard gate, and every
  published HIGH pick sits inside it. It does **not** select matches using bookmaker prices — the prices are
  ours — and it does not establish a >70% market-implied chance. Because a 5% overround caps an in-band pick at
  ~68%, "high confidence" here means 55%+ model probability plus verified evidence, not a 70% market read.
* OLBG's listings paginate ("Load More Tips"): the board is the first page of each sport.
* OLBG's clock labels carry no time zone and run a few minutes late; they are published verbatim and no
  start time is derived from them.
* Tip counts move between captures (`Genesis Championship` 5/18 → 6/20 within two hours); every share is a
  timestamped snapshot.
* Prices, handicaps, totals and confidence grades are **our model output**, not facts and not market quotes.

18+. If gambling is causing you harm, contact [GamCare](https://www.gamcare.org.uk/) or
[GambleAware](https://www.gambleaware.org/).
