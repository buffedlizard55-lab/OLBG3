# OLBG3 — multi-sport lines, verification and predictions

A static GitHub Pages dashboard covering all **15 in-scope OLBG sports**. It publishes independently originated Money Line / Win Match, Handicap / Spread / Run Line / Puck Line, Totals and Outright/Race prices; LOW/MEDIUM/HIGH grades; unique sourced analysis of at least 30 words; and row-level official-source and Flagged for Review links.

**Live site:** <https://buffedlizard55-lab.github.io/OLBG3/>

**Current capture:** deterministic snapshot **`2026-10-22T08:29:05Z`**. The merged harvest carries the 07:25Z primary rows and fresh 08:29Z reads of OLBG event ids **101904, 101903 and 536021**. It is not a claim of a complete live feed or hidden-pagination coverage.

## Published pages

| Page | Current contents |
|---|---|
| `index.html` | Root dashboard: **228 rows**, **41 live HIGH picks across 11 sports** |
| `predictions.html` | **41 HIGH + 21 archived/analysis pieces**, all sourced and at least 30 words |
| `lines.html` | **224 priced rows**, **186 handicaps**, **99 totals**, **27 outright/race rows** |
| `verification.html` | **215 verified / 0 corroborated / 13 unverified** root rows |
| `sports/<sport>.html` | Dedicated subpage for each of the 15 sports |
| `flagged.html` | **73-item** review register with affected rows and direct sources |
| `method.html` | Formulas, scope exclusions, price band and disclosed assumptions |
| `/olbg/` | Separate 21-page audit track: **270 rows**, **31 HIGH across 12 sports**, **40 written pieces**, **73 flags** |
| `feed-overview.html`, `matches.html`, `coverage.html`, `review.html`, `markets.html` | Official NHL/MLB/NBA schedule-feed pipeline |

## Latest integration — `session-1cecbd59`, 22 October 2026

- **Traceable harvest:** [`olbg-harvest-20261022T0829Z.tsv`](data/raw/olbg-harvest-20261022T0829Z.tsv) contains 150 rows; the root overlay contains 136 dated rows and the separate outright/race capture contains 27. Historical raw files are not rewritten.
- **Five more official fixture upgrades on both tracks:** JGTO Fortinet, Sunshine Tour Stella Artois, Samsung–KCC, Mobis–Changwon and Gibson–Krueger. `/olbg/` now records **216 verified, 7 verified-market-row, 2 verified-secondary-only and 45 unverified** rows.
- **Field evidence is independent of fixture evidence:** [JGTO’s entrant list](https://www.jgto.org/en/tournament/3048/player) explicitly states **Confirmed 96 / Planned 96**, so Fortinet’s 96-player field is official. Bermuda 120, BMW 78 and the without-Antonelli 21-runner value remain disclosed model inputs (`FL-066`).
- **Official/raw conflicts stay visible:** WTA’s Osaka draw supports Gibson–Krueger while OLBG’s raw Guangzhou label remains displayed and flagged (`FL-067`). KBL lists Mobis–Changwon at 19:00 KST on 22 October; that official instant governs expiry while the conflicting raw “Tomorrow” date remains visible (`FL-068`).
- **Current market support:** Bermuda is Seamus Power 6/24, Ben James 4/24, Corey Conners 4/24, Other 10/24. Stifel is Stewart Cink 3/12, Alker/Cejka 2/12, Other 5/12. Three exact, source-backed selection aliases restore Knicks, Nordsjælland and Salthill-Knocknacarra prices without fuzzy identity matching (`FL-072`).
- **Started HIGH picks are withdrawn:** four root and four `/olbg/` pieces moved to archived MEDIUM analysis at 08:29Z. They are not left as live recommendations with a cosmetic started badge.
- **Regression coverage:** 38 unit tests include independent field provenance, exact aliases, official/derived-start freshness, outright expiry and prediction/row selection consistency. Full build, checker, link and deployment receipts are maintained in `COORDINATION.md`.

- **Sibling source-health repairs preserved:** the merged WST match-centre links, SHL shootout wording and MLB joint-best home-record correction remain intact as `FL-063`–`FL-065`; see `docs/source-health-20261022.md`.

Key official reads: [PGA Bermuda](https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview), [Seamus Power’s 2026 profile](https://www.pgatour.com/player/28252/seamus-power), [JGTO Fortinet](https://www.jgto.org/en/tournament/3048), [Sunshine Tour Stella Artois](https://sunshinetour.com/tournament?id=226S&code=SAPC), [KBL schedule](https://www.kbl.or.kr/match/schedule), [Mobis](https://phoebus.kbl.or.kr/), [Samsung](https://thunders.kbl.or.kr/), and the [official WTA Osaka draw PDF](https://wtafiles.wtatennis.com/pdf/draws/2026/405/MDS.pdf).

Historical audit narratives remain in Git history and `COORDINATION.md`; the generated Flagged for Review pages are the current register.

## Scope and strict exclusions

**228 root rows = 201 fixtures + 27 outright/race rows:**

| Sport | Rows | Sport | Rows | Sport | Rows |
|---|---:|---|---:|---|---:|
| Tennis | 37 | Handball | 31 | Basketball | 30 |
| Volleyball | 29 | Darts | 16 | Rugby Union | 15 |
| Snooker | 14 | Ice Hockey | 13 | Cricket | 10 |
| Golf | 10 | Greyhounds | 10 | Gaelic Football | 6 |
| Motor Racing | 3 | Rugby League | 3 | Baseball | 1 |

The `/olbg/` track separately chains **270 rows**. Soccer/football, American football, boxing, UFC/MMA, hurling, horse racing, cycling and specials have **zero published rows**. Gaelic football, greyhound racing and Formula 1 are not named by the exclusion list; they remain included with explicit ambiguity notes.

## Line origination and HIGH rules

- **Root track:** official standings, rankings and scoring tables where available; otherwise a shrunk consensus input with confidence capped accordingly. Every price is originated here, not copied from a bookmaker. Outrights use Beta shrinkage toward `1/N` and publish `N`, prior strength and independent field provenance.
- **`/olbg/` track:** a separate Beta/Dirichlet implementation with disclosed home-edge logits and audited official-strength inputs. It is not silently interchanged with root prices.
- **Band:** HIGH prices must be within **-250 through +10000 American**, equivalent to **1.40 through 101.00 decimal**. `/olbg/` also requires fair probability strictly below 70%.
- **Freshness:** a HIGH pick must not have started at `SNAPSHOT_UTC`. `OLBG_NOW_UTC=YYYY-MM-DDTHH:MMZ` and `OLBG_AS_OF=YYYY-MM-DD` support deterministic reproduction.
- **Writing:** current root HIGH American odds span **-238 to +635**; `/olbg/` HIGH odds span **-227 to +578**. Every written piece names an explicit selection, cites sources and exceeds 30 words. Checkers compare each selection and quoted price to its originated row.

See [`docs/method.md`](docs/method.md), [`data/model.md`](data/model.md) and the generated method pages for implementation details.

## Reproduce and verify

Run the same order as `.github/workflows/pages.yml`:

```bash
python3 scripts/update.py
python3 -m unittest discover -s tests -v   # 38 tests
python3 scripts/build.py
python3 scripts/build_gap_sports.py
python3 scripts/model.py
python3 scripts/build_site.py
python3 scripts/check_board.py
python3 tools/build_dataset.py
python3 tools/originate.py
python3 tools/build_site.py
python3 tools/check_site.py
mkdir -p site/olbg && cp -r olbg-board/. site/olbg/
python3 scripts/build_site.py --snapshot
python3 scripts/check.py
python3 scripts/check_links.py
```

## Current data metrics

| File | Contents |
|---|---|
| `data/events.json` | **201 fixtures**, all verified; **197 priced**, **39 HIGH** |
| `data/gap_sports.json` | **27 outright/race rows**: 14 verified, 13 unverified; **27 priced**, **2 HIGH** |
| `data/predictions.json` | **62 pieces = 41 HIGH + 21 analysis** |
| `data/matches.json`, `data/lines.json` | **270 `/olbg/` rows**: 216 verified, 7 verified-market-row, 2 verified-secondary-only, 45 unverified |
| `data/predictions-olbg.json` | **40 pieces = 31 HIGH + 9 analysis** |
| `data/flagged.json` | **73 review items**, `FL-001` through `FL-073` |

## Limitations

A structural check cannot prove that a source supports a claim. Official links are supplied for manual review, missing values remain blank, and unresolved irregularities stay flagged rather than blocking an otherwise valid build. The board is a dated capture, not a guaranteed current odds feed; automated rebuilds do not independently re-fetch every official assertion. HIGH is a model evidence grade inside the requested band, not a guarantee of profit or an empirically calibrated betting edge.
