# OLBG3 — reverse-engineered multi-sport board, multi-market line origination & verified predictions

A static dashboard built from live-captured [OLBG.com](https://www.olbg.com/betting-tips) sport listings and individual multi-market event pages across all **15 in-scope sports**, paired with our independently originated betting lines (Money Line / Win Match, Handicap / Spread / Run Line / Puck Line, Match Totals Over/Under, and Tournament/Race Outrights), confidence grades (`LOW`, `MEDIUM`, `HIGH`), non-repetitive human predictions (`>= 30` words) strictly inside the **`-250` to `+10000` American odds window (`1.40` to `101.00` decimal)**, and line-by-line official governing-body verification logs.

**Live site:** <https://buffedlizard55-lab.github.io/OLBG3/>

**Latest live OLBG harvest:** **2026-10-22 01:26–01:32 UTC** (`data/meta.json` run `S-20261022-A`, `data/raw/olbg-harvest-20261022.tsv`), refreshing all 15 allowed OLBG sport pages plus multi-market event pages while retaining 70 passed 2026-10-21 rows on the root board explicitly tagged *archive* and excluded from `HIGH` confidence.

| Page | What it is |
|---|---|
| `index.html` | Main dashboard: coverage across all 15 sports, 33 live in-band `HIGH` picks across 10 sports, filterable 196-row table |
| `predictions.html` | Written human predictions: **33 live `HIGH` picks** across 10 sports (all in `-250..+10000`, `>= 30` words, player- & form-verified) + **14 `analysis` notes** on short chalk / archived rows |
| `lines.html` | Multi-market originated lines: Money Line / Win Match (`192` priced), Handicap / Spread (`158`), Match Totals Over/Under (`75`), Outrights (`23`) |
| `verification.html` | Line-by-line official governing-body verification table (`172` official/club-verified, `2` third-party corroborated, `22` unverified left blank) |
| `audit.html` | Audit log documenting every defect caught, corrected, or flagged across passes |
| `flagged.html` | **Flagged for Review**: every audit finding + the 51-item `/olbg/` register with direct official & OLBG source links |
| `method.html` | Scope exclusions, multi-market formulas, American/decimal odds band math, and disclosed assumptions |
| `sports/<sport>.html` | Dedicated category subpage per covered sport (15 sports) |
| `feed-overview.html`, `matches.html`, `coverage.html`, `review.html`, `markets.html` | Hourly official schedule feed pipeline (NHL / MLB / NBA raw schedules) |
| `/olbg/` | Live `2026-10-22` OLBG multi-market lines & audit track (**21 pages**: `145` fixtures across all 15 sports, `144` priced, `23` in-band `HIGH` predictions across 10 sports, `51` flagged items) |

## Latest audit — independent pass, 2026-10-22 07:20 UTC

Two defects fixed and one method gap closed; full detail on the Flagged page (`FL-050`, `FL-051`).

| Finding | What was wrong | Fix |
|---|---|---|
| FL-050 | OLBG prints a bare clock with no time zone and the board only resolved a **date**, so a same-day fixture could be published as live after its start. Reading the captured labels as **US Eastern (UTC−4)** reproduces the organiser's own times exactly — 04:00 → 13:00 Almaty, 08:00 → 14:00 Lyon, 09:00 → the second Centre Court match in Brussels (from 13:30), 13:00 → 19:00 CEST handball — and at 07:20 UTC that put **TEN-20** (05:00 UTC), **TEN-21** (05:30 UTC) and **CRK-04** (07:00 UTC; the ICC live score already had New Zealand batting) past kick-off while still published as live HIGH picks | Every row now carries a derived UTC kick-off (`board_dates.resolve_kickoff_utc`) plus a `started` marker in the table and on the prediction card (74 of 196 rows, 3 of them HIGH). Grades are deliberately **not** rewritten by the wall clock: the hourly CI rebuild re-derives the board from committed inputs, so a clock-dependent grade would be irreproducible. The date-level archive gate is unchanged |
| FL-051 | `TEN-20` published "world No. 12" for Iva Jovic in both the headline and the body; the official Ningbo main-draw sheet (released 21 Oct 2026 22:13) prints her at **rank 11**. The same piece's "No. 35" for Paolini and `TEN-21`'s "No. 77" for Linette are not published for unseeded players on any reachable official page | Ranks corrected to the published No. 11; the two unverifiable ranks removed rather than guessed. `TEN-21` now cites the official Osaka main-draw sheet, which carries its scorelines, instead of the player-list page that does not |

Re-verified line by line during this pass: the Almaty Day 6 order of play (Machac v Khachanov NB 13:00, Bublik v Marozsan NB 19:30,
seeds 5 and 3), the Lyon Day 5 order of play (Vacherot v Van Assche NB 14:00, Cobolli v Wawrinka NB 19:00, Jacquet v Nakashima
closing, Gojo v Altmaier on Court 1), the Brussels Day 6 order of play (Goffin v Michelsen, Dzumhur v Bergs NB 17:00, seeds 5 and 6),
the Ningbo and Osaka main-draw sheets (Jovic rank 11, Shnaider 13; Eala 6-3 6-1 Parry; Paolini 6-2 7-5 Kalinina; Siniakova
6-4 0-6 4-0 ret. Stearns; Linette 6-4 6-3 Liu; Linette v Siniakova is the R16 pairing), the China Open sheet (Swiatek 6-1 6-3 Jovic;
Siniakova 6-4 6-3 Linette), the Handbollsligan table (Ystads 6th, 6 pts, 125-112; Önnereds 12th, 2 pts, 140-152; Skånela 13th, 2 pts,
142-155; Karlskrona 11th, 4 pts, 156-164), the LNH table (Aix 8th, 6 pts, 227-223; Toulouse 13th, 6 pts, 198-201; Dunkerque lowest on
175), the EHF Group D table (Szeged 3rd, 3 pts, 139:136; GOG 2nd, 6 pts), the ICC ODI team rankings (Ireland 12th/51, Namibia 16th/32),
the ICC ODI batting/blocks pages and the 2026 T20 World Cup final (India 255/5, New Zealand 159, Samson 89), the Pakistan tri-series
results (Pakistan beat Sri Lanka by 37 on 18 Oct and England by 87 on 20 Oct), the MLB standings and Game 1 schedule, and the two
remaining same-day live cards (BKB-20/21, HTR/HBL/Darts rows) against the competitions' own pages — no further contradiction found.

## Latest audit — `session-8c24595c` (2026-10-22)

Re-verified live against official sources and fixed. Full register on `flagged.html` (49 items).

| Finding | What was wrong | Fix |
|---|---|---|
| FL-044 | The `/olbg/` track graded `HIGH` without looking at the fixture date, so **3 picks** were published for matches already played on 2026-10-21 (`BKB-534839`, `BKB-535674`, `TEN-902063`) | Kick-off gate added in `tools/originate.py`; rows archived to `medium` with the `kick_off_passed_archived` flag; write-ups moved under a labelled **Archived analysis** section; `tools/check_site.py` now rejects a past-dated `HIGH`. Live `HIGH` 26 → **23** |
| FL-045 | `GLF-02`/`GLF-04` claimed the official pages confirmed a 120- and a 78-player field — they do not | Field sizes re-labelled as disclosed model inputs; `GLF-02` prose no longer says "confirmed" |
| FL-046 | `BKB-20` credited a win to "Shane Larkin and Vincent Poirier" and `BKB-21` to "Walter Tavares and Facundo Campazzo"; the official EuroLeague Round 7 page names neither | Both rewritten to the official wording (Cam Payne in for the injured Mike James; Theo Maledon) and the official Game Center added as a source |
| Price drift | `GLF-02` quoted `+738 / 8.38` and `MTR-01` quoted `+254 / 3.54` while their published lines were `+740 / 8.40` and `+241 / 3.41` | Corrected, and `check_board.py` now fails the build if any price quoted in a write-up disagrees with its row (negative-tested) |
| Conflict markers | PR #44 merged four `<<<<<<<`/`=======`/`>>>>>>>` marker lines into `COORDINATION.md` | Removed; `check_board.py` rule 6 now guards every data file |
| Prior text | `gap_sports` rows with a field override repeated the generic "assumed 156-player field" / "22-car grid" text next to `field: 120` / `78` / `21` | Per-row basis text now names the field actually used |

Re-verified exactly against the governing body during this pass: MLB World Series Game 1 (TB @ MIL, Fri 23 Oct,
8:00 PM ET, Misiorowski starting, Brewers 103-59 / 832-618, Rays 98-64 / 736-650); URC table (Leinster 10th,
8 pts, 75/58; Munster 9th, 9 pts, 72/74); LNR Pro D2 J7 (Agen 10th 15 pts, Nissa 13th 11 pts, Soyaux 7th 17 pts,
Dax 6th 19 pts / 269-264, Valence Romans 11th 13 pts, Colomiers 12th 12 pts, Grenoble 3rd 22 pts / 213-176 +37,
Biarritz 5th 20 pts / 213-191); ATP Almaty Day 6 (Bublik v Marozsan R16 NB 19:30, Machac v Khachanov NB 13:00);
ATP Lyon (Wawrinka beat Landaluce 6-3 6-7(2) 7-6(5); Gojo v Altmaier R16); EuroLeague Round 7 game center;
PGA Tour Bermuda overview + facts article (Oct 22-25, Port Royal, par 71, 6,828 yd, $6M, Power won 2022);
LPGA BMW Ladies overview (Oct 22-25, Pine Beach, par 72, 6,784 yd, $2.35M, Sei Young Kim 2025 winner).

## Scope & Strict Exclusions

- **Included (all 15 non-excluded OLBG sports — `196` combined board rows = `173` two-sided fixtures + `23` outright/race rows; `145` live `2026-10-22` `/olbg/` rows):**
  Tennis (`34`), Handball (`31`), Basketball (`24`), Volleyball (`21`), Darts (`16`), Rugby Union (`15`), Cricket (`10`), Ice Hockey (`10`), Golf (`10`), Greyhounds (`6`), Snooker (`6`), Gaelic Football (`6`), Rugby League (`3`), Motor Racing (`3`), Baseball (`1`).
- **Strictly excluded (`0` rows published across both tracks):**
  `soccer`, `boxing`, `ufc`, `mma`, `football`, `american football`, `hurling`, `horse racing`, `cycling`, `specials`.
  *(Ambiguity note: Gaelic football, greyhound racing, and Formula 1 motor racing are distinct sports not named in the exclusion list; they are included and explicitly flagged on `flagged.html`.)*

## How Lines, Markets & `-250` to `+10000` Confidence Work

1. **Multi-Market Origination (`scripts/model.py`, `scripts/build_gap_sports.py`, `tools/originate.py`):**
   - **Win Match / Money Line:** Computed from verbatim official competition standings, world rankings, and scoring tables in `data/official.json` (`MLB`, `EuroLeague`, `ATP Tour`, `WTA Tour`, `ICC Cricket`, `PDC Darts`, `SHL`, `NHL`, `ICEHL`, `URC`, `Pro D2`, `Top 14`, `EHF Champions League`, `DAIKIN HBL`) with 5% overround, or shrunk tip-share priors where official form tables are unavailable.
   - **Handicap / Spread / Run Line / Puck Line (`157` root rows; all 2-way `/olbg/` sports):** Derived from projected score margin or sport-specific margin scale (`sigma * Phi^-1(p)`) in native units (`points`, `runs`, `goals`, `games`, `legs`, `sets`, `frames`).
   - **Match Totals — Over / Under (`68` official-form root rows; all scoring `/olbg/` sports):** Derived from team offensive/defensive scoring rates and audited against OLBG event-page totals markets (`Over 6.5` runs MLB World Series Game 1, `Over 233.5` pts GSW@LAL, `Under 226.5` pts SAC@LAC, `Over 9.5` legs Noppert vs Bunting).
   - **Outrights & Multi-Runner Fields (`23` rows):** Dirichlet-multinomial shrinkage toward `1 / N` field priors (`120` PGA Bermuda field, `22` F1 Austin grid, etc.).
2. **Focusing `HIGH` Confidence on `-250` to `+10000` Odds (`1.40` to `101.00` Decimal):**
   - Heavy >70% moneyline chalk (`price < 1.40`, shorter than `-250`) retains its honest calibrated probability and short price and is explicitly capped at **`MEDIUM`** with its reason disclosed.
   - A selection earns **`HIGH`** only when: (a) confirmed on an official governing-body / club domain (`verified`), (b) backed by official competition form/rankings, (c) kick-off has not passed as of `2026-10-22`, AND (d) its originated price sits strictly inside **`-250` to `+10000` (`1.40 <= price <= 101.00`)**.
   - **Result:** **33 live `HIGH` predictions across 10 sports** on `/` (`Baseball`, `Basketball`, `Cricket`, `Darts`, `Golf`, `Handball`, `Ice Hockey`, `Motor Racing`, `Rugby Union`, `Tennis`, spanning `-238` to `+740` US odds) and **23 live `HIGH` predictions across 10 sports** on `/olbg/` (spanning `-227` to `+660` US odds), every one `>= 30` words of unique human prose citing verified 2026 players, current form, recent match scores, explicit betting selections, and official source URLs.

## Reproducible Build & Verification Commands

```bash
python3 scripts/build.py              # official-feed pages/data -> site/
python3 scripts/build_gap_sports.py   # price outright/race markets -> data/gap_sports.json
python3 scripts/model.py              # multi-sport lines, handicaps, totals, picks -> data/events.json
python3 scripts/build_site.py         # combined root site -> site/
python3 scripts/check_board.py        # enforce OLBG links, tiers, price recomputation, -250..+10000 band & >=30w predictions
python3 tools/build_dataset.py        # live 2026-10-22 /olbg/ dataset -> data/matches.json
python3 tools/originate.py            # multi-market /olbg/ lines -> data/lines.json
python3 tools/build_site.py           # 21 /olbg/ HTML pages -> olbg-board/ & olbg/
python3 tools/check_site.py           # enforce host allowlist, links, -250..+10000 band & unique >=30w predictions
python3 scripts/build_site.py --snapshot
python3 scripts/check.py              # official-feed invariants
python3 scripts/check_links.py        # 0 broken local links across combined site
python3 -m unittest discover -s tests # 28 unit, clock & band invariant tests
```

## Summary Data Metrics (`2026-10-22`)

| File | Contents | Track |
|---|---|---|
| `data/raw/olbg-harvest-20261022.tsv` | Live `2026-10-22` OLBG harvest across all active sports + multi-market notes | `/olbg/` & root |
| `data/events.json` + `data/gap_sports.json` | `173` two-sided fixtures + `23` outright/race rows = **`196` rows** (`172` verified, `192` priced) | root board |
| `data/predictions.json` | **`47` written pieces**: **`33` live `HIGH` predictions** + `14` `analysis` notes | root board |
| `data/matches.json` + `data/lines.json` | **`145` fixtures & multi-market lines** across all 15 allowed sports (`112` official-verified, `0` corroborated debt) | `/olbg/` track |
| `data/predictions-olbg.json` | **`23` live `HIGH` predictions** across 10 sports (`-227` to `+660` US, all `< 70%` prob) plus `3` archived analysis pieces | `/olbg/` track |
| `data/flagged.json` | **`51` flagged review items** with direct source links | both tracks |

## Freshness and verification limitations (independent audit, 2026-10-22)

The captured board is **not a complete live fixture feed**. Hourly rebuilding does not re-fetch
all OLBG listings or independently re-check the official-source assertions stored in JSON.
The root board now expires past fixture dates against the actual UTC build date, rather than a
frozen session date. For an explicit historical reproduction, set `OLBG_AS_OF=2026-10-22`.
This override does not change capture dates or source verification timestamps.
Same-day fixtures can already have started: the OLBG clock labels lack a confirmed timezone.
`HIGH` is a model evidence grade, not an empirically calibrated probability or proven betting edge;
matching the requested price band alone does not establish value. The `/olbg/` track uses separate logic.
Automated URL/schema checks establish structural consistency, **not that a source supports a claim**.

This session re-read the [official MLB standings](https://www.mlb.com/standings/2026):
Tampa Bay 98–64, 736 RS / 650 RA; Milwaukee 103–59, 832 RS / 618 RA match the stored figures.
This targeted check must not be treated as independent re-verification of every row or prediction.
